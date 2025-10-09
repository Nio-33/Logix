"""
Authentication Service Business Logic
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from shared.utils.firebase_config import get_firestore_client
from shared.models.user import User, UserRole

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user management"""

    def __init__(self):
        self.db = get_firestore_client()
        if self.db:
            self.users_collection = self.db.collection("users")
        else:
            self.users_collection = None
        
        # Development mode storage for profile data and users
        self._dev_profile_storage = {}
        self._dev_users_storage = {}

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID from Firestore or development storage
        """
        if not self.users_collection:
            logger.warning("Firestore not available - checking development mode storage")
            # Check development mode storage
            if user_id in self._dev_users_storage:
                logger.info(f"User {user_id} found in development storage")
                return self._dev_users_storage[user_id]
            else:
                logger.warning(f"User {user_id} not found in development storage")
                return None

        try:
            user_doc = self.users_collection.document(user_id).get()

            if user_doc.exists:
                return User.from_dict(user_doc.to_dict())

            logger.warning(f"User {user_id} not found in Firestore")
            return None

        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise

    def get_dev_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile data from development storage
        """
        return self._dev_profile_storage.get(user_id)

    def save_dev_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save user profile data to development storage
        """
        self._dev_profile_storage[user_id] = profile_data
        logger.info(f"Saved profile data for user {user_id} in development mode")

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email from Firestore
        """
        try:
            query = self.users_collection.where("email", "==", email).limit(1)
            docs = query.stream()

            for doc in docs:
                return User.from_dict(doc.to_dict())

            return None

        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise

    def get_or_create_user(self, user_info: Dict[str, Any]) -> User:
        """
        Get existing user or create new user from Firebase auth data
        """
        try:
            user_id = user_info["uid"]
            
            # If Firestore is not available, create in-memory user
            if not self.users_collection:
                logger.warning("Firestore not available - creating in-memory user")
                return User(
                    uid=user_id,
                    email=user_info["email"],
                    role=UserRole.CUSTOMER,  # Default role
                    first_name=self._extract_first_name(user_info),
                    last_name=self._extract_last_name(user_info),
                    profile_picture=user_info.get("picture"),
                    email_verified=user_info.get("email_verified", False),
                    is_active=True,
                )
            
            existing_user = self.get_user(user_id)

            if existing_user:
                # Update last login and return existing user
                existing_user.update_last_login()
                self.update_user(existing_user)
                return existing_user

            # Create new user
            new_user = User(
                uid=user_id,
                email=user_info["email"],
                role=UserRole.CUSTOMER,  # Default role
                first_name=self._extract_first_name(user_info),
                last_name=self._extract_last_name(user_info),
                profile_picture=user_info.get("picture"),
                email_verified=user_info.get("email_verified", False),
                is_active=True,
            )

            # Save to Firestore
            self.create_user(new_user)

            logger.info(f"Created new user: {new_user.email}")
            return new_user

        except Exception as e:
            logger.error(f"Failed to get or create user: {e}")
            raise

    def create_user(self, user: User) -> User:
        """
        Create new user in Firestore
        """
        try:
            # Normalize email first
            user.email = user.email.lower().strip()
            
            # Check email uniqueness first
            if self._email_exists(user.email):
                raise ValueError(f"Email {user.email} is already registered")
            
            # Use the normalized storage method
            return self.normalize_and_store_user(user)

        except Exception as e:
            logger.error(f"Failed to create user {user.email}: {e}")
            raise

    def update_user(self, user: User) -> User:
        """
        Update existing user in Firestore
        """
        try:
            # Normalize email first
            user.email = user.email.lower().strip()
            user.updated_at = datetime.now(timezone.utc)
            
            if not self.users_collection:
                logger.warning(f"Firestore not available - user {user.email} updated in development mode")
                # Update in development mode
                self._dev_users_storage[user.uid] = user
                logger.info(f"User updated in development mode: {user.email}")
                return user
            
            user_data = user.to_dict()
            self.users_collection.document(user.uid).update(user_data)

            logger.info(f"User updated: {user.email}")
            return user

        except Exception as e:
            logger.error(f"Failed to update user {user.email}: {e}")
            raise

    def list_users(
        self, page: int = 1, limit: int = 20, role_filter: str = None
    ) -> List[User]:
        """
        List users with pagination and optional role filter
        """
        try:
            if not self.users_collection:
                logger.warning("Firestore not available - returning development mode users")
                # Return development mode users (in-memory storage)
                return self._get_dev_users(role_filter, page, limit)

            query = self.users_collection

            # Apply role filter if provided
            if role_filter:
                try:
                    role_enum = UserRole(role_filter)
                    query = query.where("role", "==", role_enum.value)
                except ValueError:
                    logger.warning(f"Invalid role filter: {role_filter}")

            # Apply pagination
            offset = (page - 1) * limit
            query = (
                query.order_by("created_at", direction="DESCENDING")
                .offset(offset)
                .limit(limit)
            )

            users = []
            for doc in query.stream():
                try:
                    user = User.from_dict(doc.to_dict())
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Failed to parse user document {doc.id}: {e}")

            return users

        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise
    
    def _get_dev_users(self, role_filter: str = None, page: int = 1, limit: int = 20) -> List[User]:
        """
        Get users from development mode storage
        """
        try:
            # Get all users from development storage
            users = list(self._dev_users_storage.values())
            
            # Apply role filter if provided
            if role_filter:
                try:
                    role_enum = UserRole(role_filter)
                    users = [u for u in users if u.role == role_enum]
                except ValueError:
                    logger.warning(f"Invalid role filter: {role_filter}")
            
            # Sort by created_at descending
            users.sort(key=lambda u: u.created_at or datetime.now(timezone.utc), reverse=True)
            
            # Apply pagination
            offset = (page - 1) * limit
            return users[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to get dev users: {e}")
            return []
    
    def _email_exists(self, email: str, exclude_user_id: str = None) -> bool:
        """
        Check if email already exists in the system (case-insensitive)
        """
        try:
            email_lower = email.lower().strip()
            
            if not self.users_collection:
                # Check in development storage
                for user_id, user in self._dev_users_storage.items():
                    if exclude_user_id and user_id == exclude_user_id:
                        continue
                    if user.email.lower().strip() == email_lower:
                        return True
                return False
            
            # Check in Firestore
            query = self.users_collection.where("email", "==", email_lower)
            docs = query.stream()
            
            for doc in docs:
                if exclude_user_id and doc.id == exclude_user_id:
                    continue
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check email existence: {e}")
            return False
    
    def normalize_and_store_user(self, user: User) -> User:
        """
        Normalize email to lowercase and store user
        """
        # Normalize email to lowercase
        user.email = user.email.lower().strip()
        
        if not self.users_collection:
            # Store in development mode
            self._dev_users_storage[user.uid] = user
            logger.info(f"User normalized and stored in development mode: {user.email}")
            return user
        
        # Store in Firestore
        user_data = user.to_dict()
        self.users_collection.document(user.uid).set(user_data)
        logger.info(f"User normalized and stored in Firestore: {user.email}")
        return user
    
    def clean_duplicate_emails(self) -> dict:
        """
        Clean up duplicate emails in development storage
        Returns statistics about the cleanup
        """
        if self.users_collection:
            return {"message": "Not in development mode", "duplicates_removed": 0}
        
        stats = {
            "total_users_before": len(self._dev_users_storage),
            "duplicates_removed": 0,
            "emails_seen": set(),
            "users_to_remove": []
        }
        
        # Find duplicates
        for user_id, user in self._dev_users_storage.items():
            email_lower = user.email.lower().strip()
            
            if email_lower in stats["emails_seen"]:
                # This is a duplicate
                stats["users_to_remove"].append(user_id)
                stats["duplicates_removed"] += 1
                logger.warning(f"Found duplicate email: {user.email} (user_id: {user_id})")
            else:
                # Normalize the email and mark as seen
                user.email = email_lower
                stats["emails_seen"].add(email_lower)
        
        # Remove duplicates (keep the first occurrence)
        for user_id in stats["users_to_remove"]:
            removed_user = self._dev_users_storage.pop(user_id, None)
            if removed_user:
                logger.info(f"Removed duplicate user: {removed_user.email} (user_id: {user_id})")
        
        stats["total_users_after"] = len(self._dev_users_storage)
        logger.info(f"Duplicate cleanup completed: {stats}")
        
        return stats

    def search_users(self, search_term: str, limit: int = 10) -> List[User]:
        """
        Search users by email or name
        """
        try:
            users = []

            # Search by email (exact match and prefix)
            email_queries = [
                self.users_collection.where("email", "==", search_term),
                self.users_collection.where("email", ">=", search_term).where(
                    "email", "<=", search_term + "\uf8ff"
                ),
            ]

            for query in email_queries:
                for doc in query.limit(limit).stream():
                    try:
                        user = User.from_dict(doc.to_dict())
                        if user not in users:  # Avoid duplicates
                            users.append(user)
                    except Exception as e:
                        logger.warning(f"Failed to parse user document {doc.id}: {e}")

            return users[:limit]

        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            raise

    def get_users_by_role(self, role: UserRole) -> List[User]:
        """
        Get all users with specific role
        """
        try:
            query = self.users_collection.where("role", "==", role.value)

            users = []
            for doc in query.stream():
                try:
                    user = User.from_dict(doc.to_dict())
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Failed to parse user document {doc.id}: {e}")

            return users

        except Exception as e:
            logger.error(f"Failed to get users by role {role.value}: {e}")
            raise

    def get_warehouse_staff(self, warehouse_id: str) -> List[User]:
        """
        Get all warehouse staff for a specific warehouse
        """
        try:
            query = (
                self.users_collection.where(
                    "role", "==", UserRole.WAREHOUSE_STAFF.value
                )
                .where("warehouse_ids", "array_contains", warehouse_id)
                .where("is_active", "==", True)
            )

            users = []
            for doc in query.stream():
                try:
                    user = User.from_dict(doc.to_dict())
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Failed to parse user document {doc.id}: {e}")

            return users

        except Exception as e:
            logger.error(f"Failed to get warehouse staff for {warehouse_id}: {e}")
            raise

    def get_active_drivers(self) -> List[User]:
        """
        Get all active drivers
        """
        try:
            query = self.users_collection.where(
                "role", "==", UserRole.DRIVER.value
            ).where("is_active", "==", True)

            users = []
            for doc in query.stream():
                try:
                    user = User.from_dict(doc.to_dict())
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Failed to parse user document {doc.id}: {e}")

            return users

        except Exception as e:
            logger.error(f"Failed to get active drivers: {e}")
            raise

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user (soft delete by deactivating)
        """
        try:
            user = self.get_user(user_id)
            if not user:
                return False

            user.is_active = False
            user.updated_at = datetime.utcnow()

            self.update_user(user)

            logger.info(f"User deactivated: {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise

    def _extract_first_name(self, user_info: Dict[str, Any]) -> str:
        """
        Extract first name from user info
        """
        name = user_info.get("name", "")
        if name:
            return name.split()[0] if name.split() else ""

        # Fallback to email prefix
        email = user_info.get("email", "")
        if email:
            return email.split("@")[0]

        return "User"

    def _extract_last_name(self, user_info: Dict[str, Any]) -> str:
        """
        Extract last name from user info
        """
        name = user_info.get("name", "")
        if name:
            parts = name.split()
            return " ".join(parts[1:]) if len(parts) > 1 else ""

        return ""
