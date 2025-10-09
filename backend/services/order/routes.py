"""
Order Management Service Routes
"""

import logging
from flask import Blueprint, request, jsonify

from shared.middleware.auth import require_auth, require_roles
from shared.middleware.rate_limiting import api_rate_limit
from shared.models.user import UserRole
from shared.models import OrderType, OrderSource, IndustryCategory
from .service import OrderService

logger = logging.getLogger(__name__)
order_bp = Blueprint("order", __name__)
order_service = OrderService()


@order_bp.route("/", methods=["GET"])
@require_auth()
@api_rate_limit
def list_orders():
    """
    List orders with filtering and pagination (including industry-specific filters)
    """
    try:
        # Get query parameters
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        status = request.args.get("status")
        customer_id = request.args.get("customer_id")
        warehouse_id = request.args.get("warehouse_id")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        # NEW: Industry-specific filters
        order_type = request.args.get("order_type")
        order_source = request.args.get("order_source")
        industry_category = request.args.get("industry_category")

        # Check user permissions for customer filtering
        user_role = getattr(request, "user_role", None)
        if user_role == UserRole.CUSTOMER.value:
            customer_id = request.user_id  # Customers can only see their own orders

        orders = order_service.list_orders(
            page=page,
            limit=limit,
            status=status,
            customer_id=customer_id,
            warehouse_id=warehouse_id,
            start_date=start_date,
            end_date=end_date,
            order_type=order_type,
            order_source=order_source,
            industry_category=industry_category,
        )

        return (
            jsonify(
                {
                    "orders": [order.to_dict() for order in orders],
                    "page": page,
                    "limit": limit,
                    "filters": {
                        "industry_category": industry_category,
                        "order_type": order_type,
                        "order_source": order_source,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"List orders error: {e}")
        return jsonify({"error": "Failed to list orders"}), 500


@order_bp.route("/<order_id>", methods=["GET"])
@require_auth()
@api_rate_limit
def get_order(order_id):
    """
    Get order by ID
    """
    try:
        order = order_service.get_order(order_id)

        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Check user permissions
        user_role = getattr(request, "user_role", None)
        if (
            user_role == UserRole.CUSTOMER.value
            and order.customer_id != request.user_id
        ):
            return jsonify({"error": "Access denied"}), 403

        return jsonify({"order": order.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get order error: {e}")
        return jsonify({"error": "Failed to get order"}), 500


@order_bp.route("/", methods=["POST"])
@require_auth()
@api_rate_limit
def create_order():
    """
    Create new order
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["items", "delivery_address"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        if not data["items"]:
            return jsonify({"error": "Order must have at least one item"}), 400

        # Set customer ID from authenticated user
        data["customer_id"] = request.user_id

        order = order_service.create_order(data)

        return (
            jsonify(
                {"message": "Order created successfully", "order": order.to_dict()}
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Create order error: {e}")
        return jsonify({"error": "Failed to create order"}), 500


@order_bp.route("/<order_id>", methods=["PUT"])
@require_roles(
    UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF
)
@api_rate_limit
def update_order(order_id):
    """
    Update order (staff only)
    """
    try:
        data = request.get_json()

        order = order_service.update_order(order_id, data, request.user_id)

        if not order:
            return jsonify({"error": "Order not found"}), 404

        return (
            jsonify(
                {"message": "Order updated successfully", "order": order.to_dict()}
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Update order error: {e}")
        return jsonify({"error": "Failed to update order"}), 500


@order_bp.route("/<order_id>/status", methods=["PUT"])
@require_roles(
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.WAREHOUSE_STAFF,
    UserRole.DRIVER,
)
@api_rate_limit
def update_order_status(order_id):
    """
    Update order status
    """
    try:
        data = request.get_json()

        if "status" not in data:
            return jsonify({"error": "status is required"}), 400

        new_status = data["status"]
        notes = data.get("notes")

        order = order_service.update_order_status(
            order_id, new_status, request.user_id, notes
        )

        if not order:
            return jsonify({"error": "Order not found"}), 404

        return (
            jsonify(
                {
                    "message": "Order status updated successfully",
                    "order": {
                        "order_id": order.order_id,
                        "status": order.status.value,
                        "updated_at": order.updated_at.isoformat(),
                    },
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return jsonify({"error": "Failed to update order status"}), 500


@order_bp.route("/<order_id>/cancel", methods=["POST"])
@require_auth()
@api_rate_limit
def cancel_order(order_id):
    """
    Cancel order
    """
    try:
        data = request.get_json()
        reason = data.get("reason", "Customer cancellation")

        order = order_service.get_order(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Check permissions
        user_role = getattr(request, "user_role", None)
        if (
            user_role == UserRole.CUSTOMER.value
            and order.customer_id != request.user_id
        ):
            return jsonify({"error": "Access denied"}), 403

        if not order.can_be_cancelled():
            return (
                jsonify({"error": "Order cannot be cancelled in current status"}),
                400,
            )

        cancelled_order = order_service.cancel_order(order_id, reason, request.user_id)

        return (
            jsonify(
                {
                    "message": "Order cancelled successfully",
                    "order": {
                        "order_id": cancelled_order.order_id,
                        "status": cancelled_order.status.value,
                        "notes": cancelled_order.notes,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        return jsonify({"error": "Failed to cancel order"}), 500


@order_bp.route("/<order_id>/items", methods=["POST"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def add_order_item(order_id):
    """
    Add item to existing order (operations only)
    """
    try:
        data = request.get_json()

        required_fields = ["sku", "quantity"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        order = order_service.add_order_item(
            order_id,
            data["sku"],
            data["quantity"],
            data.get("unit_price"),
            request.user_id,
        )

        if not order:
            return jsonify({"error": "Order not found or cannot be modified"}), 404

        return (
            jsonify(
                {
                    "message": "Item added to order successfully",
                    "order": order.to_dict(),
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Add order item error: {e}")
        return jsonify({"error": "Failed to add item to order"}), 500


@order_bp.route("/<order_id>/items/<sku>", methods=["DELETE"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def remove_order_item(order_id, sku):
    """
    Remove item from order (operations only)
    """
    try:
        order = order_service.remove_order_item(order_id, sku, request.user_id)

        if not order:
            return jsonify({"error": "Order not found or cannot be modified"}), 404

        return (
            jsonify(
                {
                    "message": "Item removed from order successfully",
                    "order": order.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Remove order item error: {e}")
        return jsonify({"error": "Failed to remove item from order"}), 500


@order_bp.route("/<order_id>/assign", methods=["POST"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def assign_order():
    """
    Assign order to warehouse and/or driver
    """
    try:
        data = request.get_json()
        order_id = request.view_args["order_id"]

        warehouse_id = data.get("warehouse_id")
        driver_id = data.get("driver_id")

        if not warehouse_id and not driver_id:
            return (
                jsonify({"error": "Either warehouse_id or driver_id is required"}),
                400,
            )

        order = order_service.assign_order(
            order_id,
            warehouse_id=warehouse_id,
            driver_id=driver_id,
            assigned_by=request.user_id,
        )

        if not order:
            return jsonify({"error": "Order not found"}), 404

        return (
            jsonify(
                {
                    "message": "Order assigned successfully",
                    "order": {
                        "order_id": order.order_id,
                        "warehouse_id": order.warehouse_id,
                        "assigned_driver": order.assigned_driver,
                        "status": order.status.value,
                    },
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Assign order error: {e}")
        return jsonify({"error": "Failed to assign order"}), 500


@order_bp.route("/dashboard", methods=["GET"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def order_dashboard():
    """
    Get order dashboard metrics
    """
    try:
        dashboard_data = order_service.get_dashboard_metrics()

        return jsonify(dashboard_data), 200

    except Exception as e:
        logger.error(f"Order dashboard error: {e}")
        return jsonify({"error": "Failed to get dashboard data"}), 500


@order_bp.route("/search", methods=["GET"])
@require_roles(
    UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF
)
@api_rate_limit
def search_orders():
    """
    Search orders by various criteria
    """
    try:
        search_term = request.args.get("q", "")
        search_type = request.args.get(
            "type", "all"
        )  # order_id, customer_email, phone, etc.
        limit = request.args.get("limit", 10, type=int)

        if not search_term:
            return jsonify({"error": "Search term is required"}), 400

        orders = order_service.search_orders(search_term, search_type, limit)

        return (
            jsonify(
                {
                    "orders": [order.to_dict() for order in orders],
                    "search_term": search_term,
                    "search_type": search_type,
                    "count": len(orders),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Search orders error: {e}")
        return jsonify({"error": "Failed to search orders"}), 500


@order_bp.route("/<order_id>/history", methods=["GET"])
@require_auth()
@api_rate_limit
def get_order_history(order_id):
    """
    Get order status history and audit trail
    """
    try:
        order = order_service.get_order(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Check user permissions
        user_role = getattr(request, "user_role", None)
        if (
            user_role == UserRole.CUSTOMER.value
            and order.customer_id != request.user_id
        ):
            return jsonify({"error": "Access denied"}), 403

        history = order_service.get_order_history(order_id)

        return jsonify({"order_id": order_id, "history": history}), 200

    except Exception as e:
        logger.error(f"Get order history error: {e}")
        return jsonify({"error": "Failed to get order history"}), 500


# ==================== NEW: Industry-Specific Endpoints ====================

@order_bp.route("/types", methods=["GET"])
@require_auth()
@api_rate_limit
def get_order_types():
    """
    Get available order types and their configurations
    """
    try:
        order_types = {}
        
        for order_type in OrderType:
            from shared.models import IndustryStatusWorkflow, IndustryValidator
            
            workflow = IndustryStatusWorkflow.get_workflow(order_type)
            required_fields = IndustryValidator.get_required_fields(order_type)
            
            order_types[order_type.value] = {
                "name": order_type.value,
                "workflow": [status.value for status in workflow],
                "required_fields": required_fields["required"],
            }
        
        return jsonify({
            "order_types": order_types,
            "count": len(order_types)
        }), 200

    except Exception as e:
        logger.error(f"Get order types error: {e}")
        return jsonify({"error": "Failed to get order types"}), 500


@order_bp.route("/sources", methods=["GET"])
@require_auth()
@api_rate_limit
def get_order_sources():
    """
    Get available order sources grouped by industry
    """
    try:
        sources_by_industry = {
            "ecommerce": [
                OrderSource.SHOPIFY.value,
                OrderSource.WOOCOMMERCE.value,
                OrderSource.MAGENTO.value,
                OrderSource.AMAZON_MARKETPLACE.value,
                OrderSource.EBAY.value,
            ],
            "retail": [
                OrderSource.VENDOR_PORTAL.value,
                OrderSource.EDI_SYSTEM.value,
                OrderSource.RETAIL_PO_SYSTEM.value,
            ],
            "food_delivery": [
                OrderSource.UBER_EATS.value,
                OrderSource.DOORDASH.value,
                OrderSource.GRUBHUB.value,
                OrderSource.RESTAURANT_POS.value,
            ],
            "manufacturing": [
                OrderSource.ERP_SYSTEM.value,
                OrderSource.MES_SYSTEM.value,
                OrderSource.SAP.value,
            ],
            "3pl": [
                OrderSource.CLIENT_PORTAL.value,
                OrderSource.WMS_INTEGRATION.value,
                OrderSource.API_INTEGRATION.value,
            ],
        }
        
        return jsonify({
            "sources": sources_by_industry,
            "all_sources": [source.value for source in OrderSource]
        }), 200

    except Exception as e:
        logger.error(f"Get order sources error: {e}")
        return jsonify({"error": "Failed to get order sources"}), 500


@order_bp.route("/industries", methods=["GET"])
@require_auth()
@api_rate_limit
def get_industries():
    """
    Get available industry categories and their configurations
    """
    try:
        industries = {}
        
        for industry in IndustryCategory:
            industries[industry.value] = {
                "name": industry.value,
                "display_name": {
                    IndustryCategory.ECOMMERCE: "E-commerce",
                    IndustryCategory.RETAIL: "Retail Distribution",
                    IndustryCategory.FOOD_DELIVERY: "Food Delivery",
                    IndustryCategory.MANUFACTURING: "Manufacturing",
                    IndustryCategory.THIRD_PARTY_LOGISTICS: "3PL Services",
                }.get(industry, industry.value),
            }
        
        return jsonify({
            "industries": industries,
            "count": len(industries)
        }), 200

    except Exception as e:
        logger.error(f"Get industries error: {e}")
        return jsonify({"error": "Failed to get industries"}), 500


@order_bp.route("/by-industry/<industry>", methods=["GET"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def get_orders_by_industry(industry):
    """
    Get orders filtered by industry category
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        
        # Validate industry
        try:
            industry_cat = IndustryCategory(industry)
        except ValueError:
            return jsonify({"error": f"Invalid industry: {industry}"}), 400
        
        orders = order_service.list_orders(
            page=page,
            limit=limit,
            industry_category=industry_cat.value,
        )
        
        return jsonify({
            "industry": industry,
            "orders": [order.to_dict() for order in orders],
            "page": page,
            "limit": limit,
            "count": len(orders)
        }), 200

    except Exception as e:
        logger.error(f"Get orders by industry error: {e}")
        return jsonify({"error": "Failed to get orders by industry"}), 500


@order_bp.route("/analytics/by-industry", methods=["GET"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def get_industry_analytics():
    """
    Get order analytics grouped by industry
    """
    try:
        # This would typically query BigQuery for aggregated data
        # For now, return sample structure
        
        analytics = {
            "ecommerce": {
                "total_orders": 523,
                "average_value": 125.50,
                "top_sources": ["shopify", "amazon_marketplace"],
                "fulfillment_time_avg": 45,  # minutes
            },
            "retail": {
                "total_orders": 156,
                "average_value": 5420.00,
                "top_sources": ["edi_system", "vendor_portal"],
                "fulfillment_time_avg": 240,
            },
            "food_delivery": {
                "total_orders": 892,
                "average_value": 35.75,
                "top_sources": ["uber_eats", "doordash"],
                "fulfillment_time_avg": 35,
            },
            "manufacturing": {
                "total_orders": 78,
                "average_value": 25000.00,
                "top_sources": ["erp_system", "production_schedule"],
                "fulfillment_time_avg": 1440,
            },
            "3pl": {
                "total_orders": 342,
                "average_value": 850.00,
                "top_sources": ["client_portal", "api_integration"],
                "fulfillment_time_avg": 180,
            }
        }
        
        return jsonify({
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Get industry analytics error: {e}")
        return jsonify({"error": "Failed to get industry analytics"}), 500
