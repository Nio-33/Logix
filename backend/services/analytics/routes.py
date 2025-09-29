"""
Analytics Service Routes
"""

import logging
from flask import Blueprint, request, jsonify

from shared.middleware.auth import require_auth, require_roles
from shared.middleware.rate_limiting import api_rate_limit
from shared.models.user import UserRole
from .service import AnalyticsService

logger = logging.getLogger(__name__)
analytics_bp = Blueprint('analytics', __name__)
analytics_service = AnalyticsService()

@analytics_bp.route('/kpis', methods=['GET'])
@require_auth()
@api_rate_limit
def get_kpis():
    """
    Get key performance indicators
    """
    try:
        kpis = analytics_service.get_kpis()
        
        return jsonify({
            'kpis': kpis
        }), 200
        
    except Exception as e:
        logger.error(f"Get KPIs error: {e}")
        return jsonify({'error': 'Failed to get KPIs'}), 500

@analytics_bp.route('/dashboard', methods=['GET'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def get_dashboard_data():
    """
    Get dashboard analytics data
    """
    try:
        dashboard_data = analytics_service.get_dashboard_data()
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Get dashboard data error: {e}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500