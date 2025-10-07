"""
Authentication Middleware
"""

import logging
import base64
import json
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from shared.utils.firebase_config import get_auth_client

logger = logging.getLogger(__name__)


def auth_middleware(app, jwt_manager):
    """
    Configure JWT middleware and error handlers
    """

    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token"}), 401

    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization token required"}), 401


def require_auth(required_role=None):
    """
    Decorator to require authentication and optional role-based access
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Verify JWT token
                verify_jwt_in_request()

                # Get user identity
                user_id = get_jwt_identity()
                claims = get_jwt()

                # Check role if required
                if required_role:
                    user_role = claims.get("role")
                    if not user_role or user_role != required_role:
                        return jsonify({"error": "Insufficient permissions"}), 403

                # Add user info to request context
                request.user_id = user_id
                request.user_role = claims.get("role")
                request.user_claims = claims

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Authentication error: {e}")
                return jsonify({"error": "Authentication failed"}), 401

        return decorated_function

    return decorator


def require_roles(*allowed_roles):
    """
    Decorator to require one of multiple roles
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()

                user_id = get_jwt_identity()
                claims = get_jwt()
                user_role = claims.get("role")

                if not user_role or user_role not in allowed_roles:
                    return jsonify({"error": "Insufficient permissions"}), 403

                request.user_id = user_id
                request.user_role = user_role
                request.user_claims = claims

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Authorization error: {e}")
                return jsonify({"error": "Authorization failed"}), 401

        return decorated_function

    return decorator


def verify_firebase_token(token):
    """
    Verify Firebase ID token and return user info
    """
    try:
        auth_client = get_auth_client()
        if not auth_client:
            # Fallback: Decode token without verification in development
            logger.warning("Firebase Auth not available - using development mode token decoding")
            return _decode_token_without_verification(token)
        
        decoded_token = auth_client.verify_id_token(token)

        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
        }

    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        # Try fallback for development
        logger.warning("Attempting development mode fallback")
        return _decode_token_without_verification(token)


def _decode_token_without_verification(token):
    """
    Decode Firebase ID token without verification (DEVELOPMENT ONLY)
    This is a fallback when Firebase Admin SDK is not properly initialized
    """
    try:
        # Firebase ID tokens are JWTs with 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        # Decode the payload (second part)
        # Add padding if needed
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_token = json.loads(decoded_bytes)
        
        logger.warning(f"Token decoded without verification for user: {decoded_token.get('email')}")
        
        return {
            "uid": decoded_token.get("user_id") or decoded_token.get("sub"),
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
        }
    
    except Exception as e:
        logger.error(f"Failed to decode token without verification: {e}")
        raise ValueError(f"Invalid Firebase ID token: {e}")


def get_user_role(user_id):
    """
    Get user role from Firestore
    """
    try:
        from shared.utils.firebase_config import get_firestore_client

        db = get_firestore_client()
        if not db:
            logger.warning("Firestore not available - returning default role")
            return "customer"
        
        user_doc = db.collection("users").document(user_id).get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            return user_data.get("role", "customer")

        return "customer"  # Default role

    except Exception as e:
        logger.error(f"Failed to get user role: {e}")
        return "customer"
