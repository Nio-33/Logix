"""
Order Management Service Business Logic
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from shared.utils.firebase_config import get_firestore_client
from shared.models.order import Order, OrderItem, OrderStatus, Priority
from shared.models import (
    OrderType,
    OrderSource,
    IndustryCategory,
    EcommerceOrderData,
    RetailOrderData,
    FoodDeliveryOrderData,
    ManufacturingOrderData,
    ThirdPartyOrderData,
    IndustryStatusWorkflow,
    IndustryValidator,
)
from .industry_processors import IndustryOrderProcessorFactory

logger = logging.getLogger(__name__)


class OrderService:
    """Order management service"""

    def __init__(self):
        self.db = get_firestore_client()
        if self.db:
            self.orders_collection = self.db.collection("orders")
            self.order_history_collection = self.db.collection("order_history")
        else:
            self.orders_collection = None
            self.order_history_collection = None

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        try:
            order_doc = self.orders_collection.document(order_id).get()

            if order_doc.exists:
                return Order.from_dict(order_doc.to_dict())

            return None

        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            raise

    def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create new order with industry-specific processing"""
        try:
            order_id = f"ORD-{str(uuid.uuid4())[:8].upper()}"

            # Determine order type and validate
            order_type = order_data.get("order_type")
            if order_type:
                order_type = OrderType(order_type) if isinstance(order_type, str) else order_type
                
                # Validate industry-specific data
                validation_result = IndustryValidator.validate_order_type_data(order_type, order_data)
                if not validation_result.get('errors', []) == []:
                    error_msg = "; ".join(validation_result['errors'])
                    raise ValueError(f"Order validation failed: {error_msg}")
                
                # Log warnings
                for warning in validation_result.get('warnings', []):
                    logger.warning(f"Order validation warning: {warning}")

            # Create order items
            items = []
            for item_data in order_data["items"]:
                item = OrderItem(
                    sku=item_data["sku"],
                    product_name=item_data.get("product_name", item_data["sku"]),
                    quantity=item_data["quantity"],
                    unit_price=Decimal(str(item_data["unit_price"])),
                    total_price=Decimal(str(item_data["unit_price"]))
                    * item_data["quantity"],
                    warehouse_id=item_data.get("warehouse_id"),
                    batch_number=item_data.get("batch_number"),
                    notes=item_data.get("notes"),
                )
                items.append(item)

            # Determine order source
            order_source = order_data.get("order_source", "web")
            if isinstance(order_source, str):
                try:
                    order_source = OrderSource(order_source)
                except ValueError:
                    order_source = OrderSource.WEB

            # Create base order
            order = Order(
                order_id=order_id,
                customer_id=order_data["customer_id"],
                items=items,
                delivery_address=order_data["delivery_address"],
                delivery_instructions=order_data.get("delivery_instructions"),
                source=order_data.get("source", "web"),  # Deprecated field
                order_type=order_type,
                order_source=order_source,
                priority=Priority(order_data.get("priority", "normal")),
                requested_delivery_date=order_data.get("requested_delivery_date"),
            )

            # Add industry-specific data
            if order_data.get("ecommerce_data"):
                order.ecommerce_data = EcommerceOrderData(**order_data["ecommerce_data"])
                order.industry_category = IndustryCategory.ECOMMERCE
            elif order_data.get("retail_data"):
                order.retail_data = RetailOrderData(**order_data["retail_data"])
                order.industry_category = IndustryCategory.RETAIL
            elif order_data.get("food_delivery_data"):
                order.food_delivery_data = FoodDeliveryOrderData(**order_data["food_delivery_data"])
                order.industry_category = IndustryCategory.FOOD_DELIVERY
            elif order_data.get("manufacturing_data"):
                order.manufacturing_data = ManufacturingOrderData(**order_data["manufacturing_data"])
                order.industry_category = IndustryCategory.MANUFACTURING
            elif order_data.get("third_party_data"):
                order.third_party_data = ThirdPartyOrderData(**order_data["third_party_data"])
                order.industry_category = IndustryCategory.THIRD_PARTY_LOGISTICS

            # Process order using industry-specific processor
            if order_type and order.industry_category:
                processor = IndustryOrderProcessorFactory.get_processor(order.industry_category)
                order = processor.process(order)
                
                # Calculate estimated delivery time
                fulfillment_minutes = processor.calculate_fulfillment_time(order)
                from datetime import timedelta
                order.estimated_delivery_date = datetime.utcnow() + timedelta(minutes=fulfillment_minutes)
                
                logger.info(f"Order {order_id} processed with {order.industry_category.value} processor")

            # Save to Firestore
            if self.orders_collection:
                self.orders_collection.document(order_id).set(order.to_dict())
                logger.info(f"Order created in Firestore: {order_id}")
            else:
                logger.warning(f"Firestore not available - order {order_id} not persisted")

            logger.info(f"Order created: {order_id} ({order.get_industry_display_name()})")
            return order

        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise

    def list_orders(self, page: int = 1, limit: int = 20, **filters) -> List[Order]:
        """List orders with filtering (including industry-specific filters)"""
        try:
            if not self.orders_collection:
                logger.warning("Firestore not available - returning empty list")
                return []
            
            query = self.orders_collection

            # Apply standard filters
            if filters.get("status"):
                query = query.where("status", "==", filters["status"])

            if filters.get("customer_id"):
                query = query.where("customer_id", "==", filters["customer_id"])
            
            if filters.get("warehouse_id"):
                query = query.where("warehouse_id", "==", filters["warehouse_id"])
            
            # NEW: Industry-specific filters
            if filters.get("order_type"):
                query = query.where("order_type", "==", filters["order_type"])
            
            if filters.get("order_source"):
                query = query.where("order_source", "==", filters["order_source"])
            
            if filters.get("industry_category"):
                query = query.where("industry_category", "==", filters["industry_category"])

            # Apply pagination
            offset = (page - 1) * limit
            query = (
                query.order_by("created_at", direction="DESCENDING")
                .offset(offset)
                .limit(limit)
            )

            orders = []
            for doc in query.stream():
                try:
                    order = Order.from_dict(doc.to_dict())
                    orders.append(order)
                except Exception as e:
                    logger.warning(f"Failed to parse order document {doc.id}: {e}")

            return orders

        except Exception as e:
            logger.error(f"Failed to list orders: {e}")
            raise

    def update_order_status(
        self, order_id: str, new_status: str, user_id: str, notes: str = None
    ) -> Optional[Order]:
        """Update order status with industry-specific validation"""
        try:
            order = self.get_order(order_id)
            if not order:
                return None

            old_status = order.status
            new_status_enum = OrderStatus(new_status)
            
            # Validate status transition using industry workflow
            if order.order_type:
                is_valid = IndustryStatusWorkflow.is_valid_transition(
                    old_status,
                    new_status_enum,
                    order.order_type
                )
                if not is_valid:
                    logger.error(
                        f"Invalid status transition for {order.order_type.value}: "
                        f"{old_status.value} -> {new_status}"
                    )
                    raise ValueError(
                        f"Invalid status transition from {old_status.value} to {new_status} "
                        f"for order type {order.get_order_type_display_name()}"
                    )
            
            order.update_status(new_status_enum)

            if notes:
                order.notes = notes

            # Save to Firestore
            if self.orders_collection:
                self.orders_collection.document(order_id).update(order.to_dict())

            logger.info(
                f"Order {order_id} status updated from {old_status.value} to {new_status} "
                f"({order.get_industry_display_name()})"
            )
            return order

        except Exception as e:
            logger.error(f"Failed to update order status: {e}")
            raise

    def cancel_order(self, order_id: str, reason: str, user_id: str) -> Optional[Order]:
        """Cancel order"""
        try:
            order = self.get_order(order_id)
            if not order or not order.can_be_cancelled():
                return None

            order.update_status(OrderStatus.CANCELLED)
            order.notes = f"Cancelled: {reason}"

            # Save to Firestore
            self.orders_collection.document(order_id).update(order.to_dict())

            logger.info(f"Order {order_id} cancelled: {reason}")
            return order

        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get order dashboard metrics"""
        try:
            # This would typically use BigQuery for complex aggregations
            # For now, return sample data
            return {
                "total_orders": 1247,
                "pending_orders": 23,
                "orders_today": 45,
                "revenue_today": 12500.00,
                "avg_order_value": 156.50,
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            raise

    def search_orders(
        self, search_term: str, search_type: str = "all", limit: int = 10
    ) -> List[Order]:
        """Search orders"""
        try:
            # Simple implementation - in production would use more sophisticated search
            query = self.orders_collection.limit(limit)

            orders = []
            for doc in query.stream():
                try:
                    order = Order.from_dict(doc.to_dict())
                    if search_term.lower() in order.order_id.lower():
                        orders.append(order)
                except Exception as e:
                    logger.warning(f"Failed to parse order document {doc.id}: {e}")

            return orders

        except Exception as e:
            logger.error(f"Failed to search orders: {e}")
            raise

    def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get order history"""
        try:
            # Return sample history
            return [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "created",
                    "user": "system",
                    "notes": "Order created",
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            raise
