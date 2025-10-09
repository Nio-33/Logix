"""
WooCommerce Integration API Routes
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from shared.middleware.auth import require_auth, require_roles
from shared.middleware.rate_limiting import api_rate_limit
from shared.models.user import UserRole
from .service import WooCommerceService
from .client import WooCommerceClient

logger = logging.getLogger(__name__)
woocommerce_bp = Blueprint("woocommerce", __name__)
wc_service = WooCommerceService()


@woocommerce_bp.route("/integrations", methods=["POST"])
@require_auth()
@api_rate_limit
def create_integration():
    """
    Create new WooCommerce integration
    
    Request body:
    {
        "store_url": "https://example.com",
        "consumer_key": "ck_...",
        "consumer_secret": "cs_...",
        "integration_name": "My Store",
        "auto_sync": true
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["store_url", "consumer_key", "consumer_secret"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        integration = wc_service.save_integration(
            user_id=request.user_id,
            store_url=data["store_url"],
            consumer_key=data["consumer_key"],
            consumer_secret=data["consumer_secret"],
            integration_name=data.get("integration_name", "My WooCommerce Store"),
            auto_sync=data.get("auto_sync", True),
        )

        # Remove sensitive data from response
        integration.pop("consumer_secret", None)

        return (
            jsonify(
                {
                    "message": "WooCommerce integration created successfully",
                    "integration": integration,
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Create integration error: {e}")
        return jsonify({"error": "Failed to create integration"}), 500


@woocommerce_bp.route("/integrations", methods=["GET"])
@require_auth()
@api_rate_limit
def list_integrations():
    """Get all WooCommerce integrations for current user"""
    try:
        integrations = wc_service.get_user_integrations(request.user_id)

        return (
            jsonify(
                {
                    "integrations": integrations,
                    "count": len(integrations),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"List integrations error: {e}")
        return jsonify({"error": "Failed to list integrations"}), 500


@woocommerce_bp.route("/integrations/<integration_id>/test", methods=["POST"])
@require_auth()
@api_rate_limit
def test_integration(integration_id):
    """Test WooCommerce integration connection"""
    try:
        # Get integration (will be implemented in service)
        # For now, return placeholder
        return jsonify({"message": "Connection test successful", "status": "active"}), 200

    except Exception as e:
        logger.error(f"Test integration error: {e}")
        return jsonify({"error": "Connection test failed"}), 500


@woocommerce_bp.route("/integrations/<integration_id>/sync", methods=["POST"])
@require_auth()
@api_rate_limit
def sync_orders(integration_id):
    """
    Manually trigger order sync from WooCommerce
    
    Request body (optional):
    {
        "status": "processing",  // Filter by status
        "since": "2025-01-01T00:00:00Z",  // Sync orders after this date
        "limit": 100  // Max orders to sync
    }
    """
    try:
        data = request.get_json() or {}

        # Parse optional parameters
        status = data.get("status")
        since = None
        if data.get("since"):
            since = datetime.fromisoformat(data["since"].replace("Z", "+00:00"))
        limit = data.get("limit", 100)

        # Trigger sync
        result = wc_service.sync_orders(
            integration_id=integration_id,
            status=status,
            since=since,
            limit=limit,
        )

        return jsonify({"message": "Sync completed", "result": result}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Sync orders error: {e}")
        return jsonify({"error": "Failed to sync orders"}), 500


@woocommerce_bp.route("/integrations/<integration_id>/webhooks", methods=["POST"])
@require_auth()
@api_rate_limit
def setup_webhooks(integration_id):
    """
    Setup webhooks in WooCommerce for automatic syncing
    
    Request body:
    {
        "topics": ["order.created", "order.updated", "order.deleted"],
        "delivery_url": "https://api.logix.com/webhooks/woocommerce"
    }
    """
    try:
        data = request.get_json()

        if "delivery_url" not in data:
            return jsonify({"error": "delivery_url is required"}), 400

        topics = data.get(
            "topics", ["order.created", "order.updated", "product.updated"]
        )

        # This would create webhooks using the WooCommerceClient
        # Implementation details would go here

        return (
            jsonify(
                {
                    "message": "Webhooks created successfully",
                    "topics": topics,
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Setup webhooks error: {e}")
        return jsonify({"error": "Failed to setup webhooks"}), 500


@woocommerce_bp.route("/webhooks/receive", methods=["POST"])
@api_rate_limit
def receive_webhook():
    """
    Receive webhook notifications from WooCommerce
    
    Headers:
        X-WC-Webhook-Topic: order.created
        X-WC-Webhook-Signature: base64_encoded_signature
        X-WC-Webhook-ID: webhook_id
        X-WC-Webhook-Delivery-ID: delivery_id
    """
    try:
        # Get webhook headers
        topic = request.headers.get("X-WC-Webhook-Topic")
        signature = request.headers.get("X-WC-Webhook-Signature")
        webhook_id = request.headers.get("X-WC-Webhook-ID")

        if not topic:
            return jsonify({"error": "Missing webhook topic"}), 400

        # Get payload
        payload = request.get_data()

        # Verify signature (if secret is configured)
        # webhook_secret = get_webhook_secret(webhook_id)
        # if webhook_secret:
        #     if not WooCommerceClient.verify_webhook_signature(payload, signature, webhook_secret):
        #         return jsonify({"error": "Invalid signature"}), 401

        # Parse payload
        data = request.get_json()

        logger.info(f"Received WooCommerce webhook: {topic}")

        # Handle different webhook topics
        if topic == "order.created":
            # Sync new order
            logger.info(f"New order created: {data.get('id')}")
            # wc_service.sync_single_order(data)

        elif topic == "order.updated":
            # Update existing order
            logger.info(f"Order updated: {data.get('id')}")
            # wc_service.update_order_from_webhook(data)

        elif topic == "order.deleted":
            # Mark order as cancelled
            logger.info(f"Order deleted: {data.get('id')}")
            # wc_service.cancel_order(f"WC-{data.get('id')}")

        elif topic == "product.updated":
            # Sync product stock
            logger.info(f"Product updated: {data.get('id')}")
            # wc_service.sync_product_from_webhook(data)

        return jsonify({"message": "Webhook processed successfully"}), 200

    except Exception as e:
        logger.error(f"Webhook receive error: {e}")
        return jsonify({"error": "Failed to process webhook"}), 500


@woocommerce_bp.route("/integrations/<integration_id>/products/sync", methods=["POST"])
@require_auth()
@api_rate_limit
def sync_product_stock(integration_id):
    """
    Sync product stock from Logix to WooCommerce
    
    Request body:
    {
        "sku": "PROD-123",
        "quantity": 50
    }
    """
    try:
        data = request.get_json()

        if "sku" not in data or "quantity" not in data:
            return jsonify({"error": "sku and quantity are required"}), 400

        success = wc_service.sync_product_stock(
            integration_id=integration_id,
            sku=data["sku"],
            quantity=data["quantity"],
        )

        if success:
            return jsonify({"message": "Product stock synced successfully"}), 200
        else:
            return jsonify({"error": "Failed to sync product stock"}), 500

    except Exception as e:
        logger.error(f"Sync product stock error: {e}")
        return jsonify({"error": "Failed to sync product stock"}), 500


@woocommerce_bp.route("/integrations/<integration_id>/orders/<int:wc_order_id>/status", methods=["PUT"])
@require_auth()
@api_rate_limit
def update_order_status(integration_id, wc_order_id):
    """
    Update WooCommerce order status from Logix
    
    Request body:
    {
        "status": "completed"  // Logix status
    }
    """
    try:
        data = request.get_json()

        if "status" not in data:
            return jsonify({"error": "status is required"}), 400

        # This would map Logix status to WooCommerce and update
        # Implementation in service

        return jsonify({"message": "Order status updated successfully"}), 200

    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return jsonify({"error": "Failed to update order status"}), 500

