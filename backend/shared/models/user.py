"""
User Data Models
"""

from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


class UserRole(Enum):
    """User role enumeration"""

    SUPER_ADMIN = "super_admin"
    OPERATIONS_MANAGER = "operations_manager"
    WAREHOUSE_STAFF = "warehouse_staff"
    DRIVER = "driver"
    CUSTOMER = "customer"


@dataclass
class User:
    """User model for Firestore"""

    uid: str
    email: str
    role: UserRole
    first_name: str
    last_name: str
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    warehouse_ids: Optional[list] = None  # For warehouse staff
    vehicle_info: Optional[Dict[str, Any]] = None  # For drivers
    preferences: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Set default timestamps"""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = asdict(self)
        data["role"] = self.role.value

        # Convert datetime objects to timestamps
        for field in ["created_at", "updated_at", "last_login"]:
            if data[field]:
                data[field] = data[field].timestamp()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create User from Firestore document"""
        # Convert role string back to enum
        if "role" in data:
            data["role"] = UserRole(data["role"])

        # Convert timestamps back to datetime
        for field in ["created_at", "updated_at", "last_login"]:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])

        return cls(**data)

    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher"""
        role_hierarchy = {
            UserRole.CUSTOMER: 1,
            UserRole.DRIVER: 2,
            UserRole.WAREHOUSE_STAFF: 3,
            UserRole.OPERATIONS_MANAGER: 4,
            UserRole.SUPER_ADMIN: 5,
        }

        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class UserSession:
    """User session tracking"""

    user_id: str
    session_id: str
    device_info: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["created_at"] = self.created_at.timestamp()
        data["expires_at"] = self.expires_at.timestamp()
        return data

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at
