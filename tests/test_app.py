"""
Integration tests for the main application
"""

import os
import pytest
import requests
import json

# Use PORT env (defaults to dev 5000) so tests hit the active server
BASE_URL = f"http://127.0.0.1:{int(os.getenv('PORT', 5000))}"

class TestApplicationIntegration:
    """Test application integration with external requests"""
    
    def test_health_endpoint_external(self):
        """Test health endpoint with external request"""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'service' in data
        assert 'version' in data
    
    def test_api_info_external(self):
        """Test API info endpoint with external request"""
        response = requests.get(f"{BASE_URL}/api/v1", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data['name'] == 'Logix Platform API'
        assert 'endpoints' in data
    
    def test_dashboard_external(self):
        """Test dashboard with external request"""
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        assert 'Dashboard' in response.text
    
    def test_demo_endpoints_external(self):
        """Test demo endpoints with external requests"""
        # Test KPIs
        response = requests.get(f"{BASE_URL}/api/v1/analytics/kpis", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'totalOrders' in data
        
        # Test orders
        response = requests.get(f"{BASE_URL}/api/v1/orders", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'orders' in data
        
        # Test inventory
        response = requests.get(f"{BASE_URL}/api/v1/inventory", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'inventory' in data
        
        # Test notifications
        response = requests.get(f"{BASE_URL}/api/v1/notifications", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'notifications' in data