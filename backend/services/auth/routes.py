"""
Authentication Service Routes
"""

import logging
from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from shared.middleware.auth import verify_firebase_token, require_auth
from shared.middleware.rate_limiting import rate_limit
from shared.models.user import UserRole
from .service import AuthService

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


@auth_bp.route("/login", methods=["POST"])
@rate_limit(requests_per_minute=10)
def login():
    """
    User login with Firebase ID token
    """
    try:
        data = request.get_json()
        if not data or "id_token" not in data:
            return jsonify({"error": "Firebase ID token required"}), 400

        # Verify Firebase token
        user_info = verify_firebase_token(data["id_token"])
        user_id = user_info["uid"]

        # Get or create user in Firestore
        user = auth_service.get_or_create_user(user_info)

        # Update last login
        user.update_last_login()
        auth_service.update_user(user)

        # Create JWT tokens with user role
        additional_claims = {
            "role": user.role.value,
            "email": user.email,
            "name": user.full_name,
        }

        access_token = create_access_token(
            identity=user_id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1),
        )

        refresh_token = create_refresh_token(
            identity=user_id, expires_delta=timedelta(days=30)
        )

        # Log successful login
        logger.info(f"User {user.email} logged in successfully")

        return (
            jsonify(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "uid": user.uid,
                        "email": user.email,
                        "name": user.full_name,
                        "role": user.role.value,
                        "profile_picture": user.profile_picture,
                        "last_login": (
                            user.last_login.isoformat() if user.last_login else None
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Authentication failed"}), 401


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    """
    try:
        user_id = get_jwt_identity()

        # Get user info
        user = auth_service.get_user(user_id)
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 404

        # Create new access token
        additional_claims = {
            "role": user.role.value,
            "email": user.email,
            "name": user.full_name,
        }

        access_token = create_access_token(
            identity=user_id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1),
        )

        return jsonify({"access_token": access_token}), 200

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({"error": "Token refresh failed"}), 401


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    User logout (client-side token removal)
    """
    try:
        user_id = get_jwt_identity()

        # Log logout event
        logger.info(f"User {user_id} logged out")

        return jsonify({"message": "Logged out successfully"}), 200

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": "Logout failed"}), 500


@auth_bp.route("/me", methods=["GET"])
@require_auth()
def get_current_user():
    """
    Get current user information
    """
    try:
        user_id = get_jwt_identity()
        user = auth_service.get_user(user_id)

        if not user:
            # If Firestore is not available, return user data from JWT token
            if not auth_service.users_collection:
                logger.warning("Firestore not available - returning user data from JWT token")
                from flask_jwt_extended import get_jwt
                jwt_data = get_jwt()
                
                return (
                    jsonify(
                        {
                            "user": {
                                "uid": user_id,
                                "email": jwt_data.get("email", ""),
                                "name": jwt_data.get("name", ""),
                                "role": jwt_data.get("role", "customer"),
                                "phone": "",
                                "profile_picture": None,
                                "is_active": True,
                                "email_verified": jwt_data.get("email_verified", False),
                                "created_at": None,
                                "last_login": None,
                                "warehouse_ids": [],
                                "vehicle_info": {},
                                "preferences": {},
                            }
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": "User not found"}), 404

        return (
            jsonify(
                {
                    "user": {
                        "uid": user.uid,
                        "email": user.email,
                        "name": user.full_name,
                        "role": user.role.value,
                        "phone": user.phone,
                        "profile_picture": user.profile_picture,
                        "is_active": user.is_active,
                        "email_verified": user.email_verified,
                        "created_at": (
                            user.created_at.isoformat() if user.created_at else None
                        ),
                        "last_login": (
                            user.last_login.isoformat() if user.last_login else None
                        ),
                        "warehouse_ids": user.warehouse_ids,
                        "vehicle_info": user.vehicle_info,
                        "preferences": user.preferences,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({"error": "Failed to get user information"}), 500


@auth_bp.route("/me", methods=["PUT"])
@require_auth()
def update_current_user():
    """
    Update current user profile
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        user = auth_service.get_user(user_id)
        if not user:
            # If Firestore is not available, return success without updating
            if not auth_service.users_collection:
                logger.warning("Firestore not available - profile update skipped in development mode")
                from flask_jwt_extended import get_jwt
                jwt_data = get_jwt()
                
                # Return updated user data from JWT + request data
                updated_user_data = {
                    "uid": user_id,
                    "email": jwt_data.get("email", ""),
                    "name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                    "role": jwt_data.get("role", "customer"),
                    "phone": data.get("phone", ""),
                    "preferences": data.get("preferences", {}),
                }
                
                return (
                    jsonify(
                        {
                            "message": "Profile updated successfully (development mode)",
                            "user": updated_user_data,
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": "User not found"}), 404

        # Update allowed fields
        allowed_fields = ["first_name", "last_name", "phone", "preferences"]
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        # Update user in Firestore
        auth_service.update_user(user)

        return (
            jsonify(
                {
                    "message": "Profile updated successfully",
                    "user": {
                        "uid": user.uid,
                        "email": user.email,
                        "name": user.full_name,
                        "phone": user.phone,
                        "preferences": user.preferences,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Update user error: {e}")
        return jsonify({"error": "Failed to update profile"}), 500


@auth_bp.route("/users", methods=["GET"])
@require_auth(required_role=UserRole.OPERATIONS_MANAGER)
def list_users():
    """
    List all users (admin/operations manager only)
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        role_filter = request.args.get("role")

        users = auth_service.list_users(page=page, limit=limit, role_filter=role_filter)

        return (
            jsonify(
                {
                    "users": [
                        {
                            "uid": user.uid,
                            "email": user.email,
                            "name": user.full_name,
                            "role": user.role.value,
                            "is_active": user.is_active,
                            "created_at": (
                                user.created_at.isoformat() if user.created_at else None
                            ),
                            "last_login": (
                                user.last_login.isoformat() if user.last_login else None
                            ),
                        }
                        for user in users
                    ]
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({"error": "Failed to list users"}), 500


@auth_bp.route("/users/<user_id>/role", methods=["PUT"])
@require_auth(required_role=UserRole.SUPER_ADMIN)
def update_user_role(user_id):
    """
    Update user role (super admin only)
    """
    try:
        data = request.get_json()
        new_role = data.get("role")

        if not new_role:
            return jsonify({"error": "Role is required"}), 400

        # Validate role
        try:
            role_enum = UserRole(new_role)
        except ValueError:
            return jsonify({"error": "Invalid role"}), 400

        user = auth_service.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update role
        user.role = role_enum
        auth_service.update_user(user)

        logger.info(f"User {user.email} role updated to {new_role}")

        return (
            jsonify(
                {
                    "message": "User role updated successfully",
                    "user": {
                        "uid": user.uid,
                        "email": user.email,
                        "role": user.role.value,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Update user role error: {e}")
        return jsonify({"error": "Failed to update user role"}), 500


@auth_bp.route("/users/<user_id>/activate", methods=["POST"])
@require_auth(required_role=UserRole.OPERATIONS_MANAGER)
def activate_user(user_id):
    """
    Activate/deactivate user account
    """
    try:
        data = request.get_json()
        is_active = data.get("is_active", True)

        user = auth_service.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.is_active = is_active
        auth_service.update_user(user)

        action = "activated" if is_active else "deactivated"
        logger.info(f"User {user.email} {action}")

        return (
            jsonify(
                {
                    "message": f"User {action} successfully",
                    "user": {
                        "uid": user.uid,
                        "email": user.email,
                        "is_active": user.is_active,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Activate user error: {e}")
        return jsonify({"error": "Failed to update user status"}), 500
