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
            # If Firestore is not available, return user data from JWT token + dev storage
            if not auth_service.users_collection:
                logger.warning("Firestore not available - returning user data from JWT token + dev storage")
                from flask_jwt_extended import get_jwt
                jwt_data = get_jwt()
                
                # Get saved profile data from development storage
                dev_profile = auth_service.get_dev_profile(user_id)
                
                # Parse name into first_name and last_name
                full_name = jwt_data.get("name", "")
                name_parts = full_name.split(" ", 1) if full_name else ["", ""]
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                # Use saved profile data if available, otherwise use JWT data
                if dev_profile:
                    first_name = dev_profile.get("first_name", first_name)
                    last_name = dev_profile.get("last_name", last_name)
                    full_name = f"{first_name} {last_name}".strip()
                
                return (
                    jsonify(
                        {
                            "user": {
                                "uid": user_id,
                                "email": jwt_data.get("email", ""),
                                "first_name": first_name,
                                "last_name": last_name,
                                "name": full_name,
                                "role": jwt_data.get("role", "customer"),
                                "phone": dev_profile.get("phone", "") if dev_profile else "",
                                "profile_picture": None,
                                "is_active": True,
                                "email_verified": jwt_data.get("email_verified", False),
                                "created_at": None,
                                "last_login": None,
                                "warehouse_ids": [],
                                "vehicle_info": {},
                                "preferences": dev_profile.get("preferences", {}) if dev_profile else {},
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
            # If Firestore is not available, save to development storage
            if not auth_service.users_collection:
                logger.warning("Firestore not available - saving profile to development storage")
                from flask_jwt_extended import get_jwt
                jwt_data = get_jwt()
                
                # Prepare profile data to save
                profile_data = {
                    "first_name": data.get("first_name", ""),
                    "last_name": data.get("last_name", ""),
                    "phone": data.get("phone", ""),
                    "preferences": data.get("preferences", {}),
                }
                
                # Save to development storage
                auth_service.save_dev_profile(user_id, profile_data)
                
                # Return updated user data
                updated_user_data = {
                    "uid": user_id,
                    "email": jwt_data.get("email", ""),
                    "first_name": profile_data["first_name"],
                    "last_name": profile_data["last_name"],
                    "name": f"{profile_data['first_name']} {profile_data['last_name']}".strip(),
                    "role": jwt_data.get("role", "customer"),
                    "phone": profile_data["phone"],
                    "preferences": profile_data["preferences"],
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


@auth_bp.route("/users", methods=["POST"])
@require_auth()  # Allow any authenticated user for now
def create_user():
    """
    Create a new user (admin/operations manager only)
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["name", "email", "password", "role"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate role
        try:
            role_enum = UserRole(data["role"])
        except ValueError:
            return jsonify({"error": "Invalid role"}), 400
        
        # Create User object
        from shared.models.user import User
        import uuid
        
        # Parse name into first_name and last_name
        name_parts = data["name"].split(" ", 1) if data["name"] else ["", ""]
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Generate a unique user ID (in production, this would come from Firebase Auth)
        user_id = str(uuid.uuid4())
        
        user = User(
            uid=user_id,
            email=data["email"],
            role=role_enum,
            first_name=first_name,
            last_name=last_name,
            is_active=data.get("is_active", True),
            email_verified=False,
            warehouse_ids=[],
            vehicle_info={},
            preferences={}
        )
        
        # Create user via AuthService
        created_user = auth_service.create_user(user)
        
        logger.info(f"User {created_user.email} created successfully")
        
        return (
            jsonify(
                {
                    "message": "User created successfully",
                    "user": {
                        "uid": created_user.uid,
                        "email": created_user.email,
                        "name": created_user.full_name,
                        "role": created_user.role.value,
                        "is_active": created_user.is_active,
                        "created_at": (
                            created_user.created_at.isoformat() if created_user.created_at else None
                        ),
                    }
                }
            ),
            201,
        )
        
    except ValueError as e:
        # Handle email uniqueness errors
        if "already registered" in str(e):
            return jsonify({"error": str(e)}), 400
        logger.error(f"Create user validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({"error": "Failed to create user"}), 500


@auth_bp.route("/users", methods=["GET"])
@require_auth()  # Allow any authenticated user for now
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


@auth_bp.route("/users/<user_id>", methods=["PUT"])
@require_auth()  # Allow any authenticated user for now
def update_user(user_id):
    """
    Update user information (admin/operations manager only)
    """
    try:
        data = request.get_json()
        
        logger.info(f"Update user request - user_id: {user_id}, data: {data}")
        logger.info(f"Development storage users: {list(auth_service._dev_users_storage.keys())}")
        
        user = auth_service.get_user(user_id)
        if not user:
            logger.error(f"User {user_id} not found in storage")
            return jsonify({"error": "User not found"}), 404
        
        logger.info(f"Found user: {user.email}, role: {user.role}")
        
        # Update allowed fields
        if "name" in data:
            user.full_name = data["name"]
        if "email" in data:
            # Check email uniqueness (excluding current user)
            if auth_service._email_exists(data["email"], exclude_user_id=user_id):
                return jsonify({"error": "Email is already registered by another user"}), 400
            user.email = data["email"]
        if "role" in data:
            try:
                user.role = UserRole(data["role"])
            except ValueError:
                return jsonify({"error": "Invalid role"}), 400
        if "is_active" in data:
            user.is_active = data["is_active"]
        
        # Update user in database
        auth_service.update_user(user)
        
        logger.info(f"User {user.email} updated successfully")
        
        return (
            jsonify(
                {
                    "message": "User updated successfully",
                    "user": {
                        "uid": user.uid,
                        "email": user.email,
                        "name": user.full_name,
                        "role": user.role.value,
                        "is_active": user.is_active,
                        "updated_at": (
                            user.updated_at.isoformat() if user.updated_at else None
                        ),
                    }
                }
            ),
            200,
        )
        
    except Exception as e:
        logger.error(f"Update user error: {e}")
        return jsonify({"error": "Failed to update user"}), 500


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
@require_auth()  # Allow any authenticated user for now
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
