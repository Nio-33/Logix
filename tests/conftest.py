"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

@pytest.fixture
def app():
    """Create application instance for testing"""
    from app import create_app
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def mock_firebase():
    """Mock Firebase services"""
    with patch('shared.utils.firebase_config.initialize_firebase') as mock_init:
        with patch('shared.utils.firebase_config.get_firestore_client') as mock_firestore:
            with patch('shared.utils.firebase_config.get_auth_client') as mock_auth:
                mock_init.return_value = None
                mock_firestore.return_value = Mock()
                mock_auth.return_value = Mock()
                yield {
                    'init': mock_init,
                    'firestore': mock_firestore,
                    'auth': mock_auth
                }

@pytest.fixture
def mock_jwt():
    """Mock JWT operations"""
    with patch('flask_jwt_extended.create_access_token') as mock_create:
        with patch('flask_jwt_extended.get_jwt_identity') as mock_identity:
            mock_create.return_value = 'mock_token'
            mock_identity.return_value = 'test_user_id'
            yield {
                'create': mock_create,
                'identity': mock_identity
            }
