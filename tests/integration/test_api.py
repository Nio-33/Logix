"""
Integration tests for API endpoints
"""

import pytest
import json

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health endpoint returns 200"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'service' in data
        assert 'version' in data

class TestAPIDocumentation:
    """Test API documentation endpoint"""
    
    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get('/api/v1')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'Logix Platform API'
        assert 'endpoints' in data

class TestDemoEndpoints:
    """Test demo endpoints for dashboard"""
    
    def test_demo_kpis(self, client):
        """Test demo KPIs endpoint"""
        response = client.get('/api/v1/analytics/kpis')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'totalOrders' in data
        assert 'deliveriesToday' in data
        assert 'avgDeliveryTime' in data
        assert 'customerRating' in data
    
    def test_demo_orders(self, client):
        """Test demo orders endpoint"""
        response = client.get('/api/v1/orders')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'orders' in data
        assert isinstance(data['orders'], list)
    
    def test_demo_inventory(self, client):
        """Test demo inventory endpoint"""
        response = client.get('/api/v1/inventory')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'inventory' in data
        assert isinstance(data['inventory'], list)
    
    def test_demo_notifications(self, client):
        """Test demo notifications endpoint"""
        response = client.get('/api/v1/notifications')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'notifications' in data
        assert isinstance(data['notifications'], list)

class TestDashboard:
    """Test dashboard endpoints"""
    
    def test_dashboard_serves_html(self, client):
        """Test dashboard serves HTML content"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'text/html' in response.content_type
        # New UI headline uses "Dashboard" title
        assert b'Dashboard' in response.data
    
    def test_favicon_handling(self, client):
        """Test favicon endpoint"""
        response = client.get('/favicon.ico')
        assert response.status_code == 204  # No content
