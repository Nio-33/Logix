"""
Unit tests for data models
"""

import pytest
from datetime import datetime, timezone
from shared.models.user import User, UserRole, UserSession

class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User(
            uid="test123",
            email="test@example.com",
            role=UserRole.CUSTOMER,
            first_name="John",
            last_name="Doe"
        )
        
        assert user.uid == "test123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.CUSTOMER
        assert user.full_name == "John Doe"
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_to_dict(self):
        """Test user serialization to dictionary"""
        user = User(
            uid="test123",
            email="test@example.com",
            role=UserRole.CUSTOMER,
            first_name="John",
            last_name="Doe"
        )
        
        data = user.to_dict()
        assert data['uid'] == "test123"
        assert data['role'] == "customer"
        assert 'created_at' in data
    
    def test_user_from_dict(self):
        """Test user creation from dictionary"""
        data = {
            'uid': 'test123',
            'email': 'test@example.com',
            'role': 'customer',
            'first_name': 'John',
            'last_name': 'Doe',
            'created_at': datetime.now(timezone.utc).timestamp()
        }
        
        user = User.from_dict(data)
        assert user.uid == "test123"
        assert user.role == UserRole.CUSTOMER
    
    def test_user_permissions(self):
        """Test user permission checking"""
        customer = User(
            uid="customer123",
            email="customer@example.com",
            role=UserRole.CUSTOMER,
            first_name="Jane",
            last_name="Customer"
        )
        
        admin = User(
            uid="admin123",
            email="admin@example.com",
            role=UserRole.SUPER_ADMIN,
            first_name="Admin",
            last_name="User"
        )
        
        # Customer should not have admin permissions
        assert not customer.has_permission(UserRole.SUPER_ADMIN)
        assert not customer.has_permission(UserRole.OPERATIONS_MANAGER)
        
        # Admin should have all permissions
        assert admin.has_permission(UserRole.CUSTOMER)
        assert admin.has_permission(UserRole.SUPER_ADMIN)
    
    def test_update_last_login(self):
        """Test last login update"""
        user = User(
            uid="test123",
            email="test@example.com",
            role=UserRole.CUSTOMER,
            first_name="John",
            last_name="Doe"
        )
        
        initial_login = user.last_login
        user.update_last_login()
        
        assert user.last_login is not None
        assert user.last_login != initial_login
        assert user.updated_at is not None

class TestUserSessionModel:
    """Test UserSession model functionality"""
    
    def test_session_creation(self):
        """Test session creation"""
        now = datetime.now(timezone.utc)
        session = UserSession(
            user_id="test123",
            session_id="session456",
            device_info="Chrome/Windows",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            created_at=now,
            expires_at=now
        )
        
        assert session.user_id == "test123"
        assert session.is_active is True
    
    def test_session_expiration(self):
        """Test session expiration check"""
        now = datetime.now(timezone.utc)
        past_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        expired_session = UserSession(
            user_id="test123",
            session_id="session456",
            device_info="Chrome/Windows",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            created_at=past_time,
            expires_at=past_time
        )
        
        assert expired_session.is_expired() is True
