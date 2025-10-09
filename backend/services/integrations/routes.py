"""
Platform Integration API Routes
Handles connections to external e-commerce and logistics platforms
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from shared.middleware.auth import require_auth, require_roles
from shared.middleware.rate_limiting import api_rate_limit
from shared.models.user import UserRole

logger = logging.getLogger(__name__)
integrations_bp = Blueprint("integrations", __name__)


@integrations_bp.route("/shopify/connect", methods=["POST"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def connect_shopify():
    """
    Connect a Shopify store
    """
    try:
        data = request.get_json()
        
        required_fields = ['shop_url', 'access_token']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        from .shopify import ShopifyConnector
        
        # Initialize connector
        connector = ShopifyConnector(
            shop_url=data['shop_url'],
            access_token=data['access_token']
        )
        
        # Test connection by fetching a few orders
        test_orders = connector.fetch_new_orders()
        
        # In production, save connection details to database
        # For now, return success
        
        return jsonify({
            "message": "Shopify store connected successfully",
            "shop_url": data['shop_url'],
            "test_orders_found": len(test_orders),
            "status": "connected"
        }), 200
        
    except Exception as e:
        logger.error(f"Shopify connection error: {e}")
        return jsonify({"error": "Failed to connect Shopify store"}), 500


@integrations_bp.route("/shopify/sync", methods=["POST"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def sync_shopify_orders():
    """
    Sync orders from Shopify
    """
    try:
        data = request.get_json()
        
        # Get stored connection details (would come from database)
        shop_url = data.get('shop_url')
        access_token = data.get('access_token')
        
        if not shop_url or not access_token:
            return jsonify({"error": "Shop credentials required"}), 400
        
        from .shopify import ShopifyConnector
        from services.order.service import OrderService
        
        connector = ShopifyConnector(shop_url, access_token)
        order_service = OrderService()
        
        # Sync orders from last sync time
        since = data.get('since')
        if since:
            since = datetime.fromisoformat(since)
        
        logix_orders = connector.sync_orders(since=since)
        
        # Save orders to Logix system
        saved_count = 0
        for order in logix_orders:
            try:
                # Process through order service (includes automation)
                from services.order.intelligent_automation import intelligent_automation_service
                automation_result = intelligent_automation_service.process_new_order(order)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save order {order.order_id}: {e}")
        
        return jsonify({
            "message": "Shopify orders synced successfully",
            "orders_found": len(logix_orders),
            "orders_imported": saved_count,
            "sync_time": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Shopify sync error: {e}")
        return jsonify({"error": "Failed to sync Shopify orders"}), 500


@integrations_bp.route("/woocommerce/connect", methods=["POST"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def connect_woocommerce():
    """
    Connect a WooCommerce store
    """
    try:
        data = request.get_json()
        
        required_fields = ['store_url', 'consumer_key', 'consumer_secret']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        from .woocommerce import WooCommerceConnector
        
        connector = WooCommerceConnector(
            store_url=data['store_url'],
            consumer_key=data['consumer_key'],
            consumer_secret=data['consumer_secret']
        )
        
        # Test connection
        test_orders = connector.fetch_new_orders()
        
        return jsonify({
            "message": "WooCommerce store connected successfully",
            "store_url": data['store_url'],
            "test_orders_found": len(test_orders),
            "status": "connected"
        }), 200
        
    except Exception as e:
        logger.error(f"WooCommerce connection error: {e}")
        return jsonify({"error": "Failed to connect WooCommerce store"}), 500


@integrations_bp.route("/platforms", methods=["GET"])
@require_auth()
@api_rate_limit
def get_available_platforms():
    """
    Get list of available integration platforms
    """
    try:
        platforms = {
            "ecommerce": [
                {
                    "id": "shopify",
                    "name": "Shopify",
                    "category": "ecommerce",
                    "status": "available",
                    "features": ["order_sync", "inventory_sync", "fulfillment_update"],
                    "setup_fields": ["shop_url", "access_token"]
                },
                {
                    "id": "woocommerce",
                    "name": "WooCommerce",
                    "category": "ecommerce",
                    "status": "available",
                    "features": ["order_sync", "inventory_sync"],
                    "setup_fields": ["store_url", "consumer_key", "consumer_secret"]
                },
                {
                    "id": "amazon",
                    "name": "Amazon Marketplace",
                    "category": "ecommerce",
                    "status": "planned",
                    "features": ["order_sync", "fulfillment_update"]
                }
            ],
            "retail": [
                {
                    "id": "edi",
                    "name": "EDI System",
                    "category": "retail",
                    "status": "planned",
                    "features": ["po_import", "asn_export"]
                }
            ],
            "food_delivery": [
                {
                    "id": "uber_eats",
                    "name": "Uber Eats",
                    "category": "food_delivery",
                    "status": "planned",
                    "features": ["order_sync", "status_update"]
                }
            ],
            "manufacturing": [
                {
                    "id": "sap",
                    "name": "SAP ERP",
                    "category": "manufacturing",
                    "status": "planned",
                    "features": ["production_order_sync"]
                }
            ]
        }
        
        return jsonify({
            "platforms": platforms,
            "total_available": sum(
                len([p for p in category if p['status'] == 'available'])
                for category in platforms.values()
            )
        }), 200
        
    except Exception as e:
        logger.error(f"Get platforms error: {e}")
        return jsonify({"error": "Failed to get platforms"}), 500


@integrations_bp.route("/webhooks/shopify", methods=["POST"])
@api_rate_limit
def shopify_webhook():
    """
    Handle Shopify webhooks
    """
    try:
        # Verify webhook signature
        hmac_header = request.headers.get('X-Shopify-Hmac-SHA256')
        shop_domain = request.headers.get('X-Shopify-Shop-Domain')
        
        if not hmac_header:
            return jsonify({"error": "Missing HMAC header"}), 401
        
        from .shopify import ShopifyWebhookHandler
        
        # Get webhook secret from environment/database
        # For now, skip verification in development
        
        webhook_data = request.get_json()
        
        # Handle different webhook topics
        topic = request.headers.get('X-Shopify-Topic')
        
        if topic == 'orders/create':
            order = ShopifyWebhookHandler.handle_order_created(webhook_data)
            
            # Process order through automation
            from services.order.intelligent_automation import intelligent_automation_service
            automation_result = intelligent_automation_service.process_new_order(order)
            
            logger.info(f"Shopify webhook processed: {order.order_id}")
            
        return jsonify({"status": "processed"}), 200
        
    except Exception as e:
        logger.error(f"Shopify webhook error: {e}")
        return jsonify({"error": "Webhook processing failed"}), 500

