"""
Order Management Service Business Logic
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from shared.utils.firebase_config import get_firestore_client
from shared.models.order import Order, OrderItem, OrderStatus, PaymentStatus, Priority

logger = logging.getLogger(__name__)

class OrderService:
    """Order management service"""
    
    def __init__(self):
        self.db = get_firestore_client()
        if self.db:
            self.orders_collection = self.db.collection('orders')
            self.order_history_collection = self.db.collection('order_history')
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
        """Create new order"""
        try:
            order_id = f"ORD-{str(uuid.uuid4())[:8].upper()}"
            
            # Create order items
            items = []
            for item_data in order_data['items']:
                item = OrderItem(
                    sku=item_data['sku'],
                    product_name=item_data.get('product_name', item_data['sku']),
                    quantity=item_data['quantity'],
                    unit_price=Decimal(str(item_data['unit_price'])),
                    total_price=Decimal(str(item_data['unit_price'])) * item_data['quantity']
                )
                items.append(item)
            
            # Create order
            order = Order(
                order_id=order_id,
                customer_id=order_data['customer_id'],
                items=items,
                delivery_address=order_data['delivery_address'],
                delivery_instructions=order_data.get('delivery_instructions'),
                source=order_data.get('source', 'web'),
                priority=Priority(order_data.get('priority', 'normal'))
            )
            
            # Save to Firestore
            self.orders_collection.document(order_id).set(order.to_dict())
            
            logger.info(f"Order created: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise
    
    def list_orders(self, page: int = 1, limit: int = 20, **filters) -> List[Order]:
        """List orders with filtering"""
        try:
            query = self.orders_collection
            
            # Apply filters
            if filters.get('status'):
                query = query.where('status', '==', filters['status'])
            
            if filters.get('customer_id'):
                query = query.where('customer_id', '==', filters['customer_id'])
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.order_by('created_at', direction='DESCENDING').offset(offset).limit(limit)
            
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
    
    def update_order_status(self, order_id: str, new_status: str, user_id: str, notes: str = None) -> Optional[Order]:
        """Update order status"""
        try:
            order = self.get_order(order_id)
            if not order:
                return None
            
            old_status = order.status
            order.update_status(OrderStatus(new_status))
            
            if notes:
                order.notes = notes
            
            # Save to Firestore
            self.orders_collection.document(order_id).update(order.to_dict())
            
            logger.info(f"Order {order_id} status updated from {old_status.value} to {new_status}")
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
                'total_orders': 1247,
                'pending_orders': 23,
                'orders_today': 45,
                'revenue_today': 12500.00,
                'avg_order_value': 156.50
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            raise
    
    def search_orders(self, search_term: str, search_type: str = 'all', limit: int = 10) -> List[Order]:
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
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'created',
                    'user': 'system',
                    'notes': 'Order created'
                }
            ]
            
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            raise