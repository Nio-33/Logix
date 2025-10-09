"""
WooCommerce Integration Service
Handles order synchronization and data mapping between WooCommerce and Logix
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

from shared.utils.firebase_config import get_firestore_client
from shared.models.order import Order, OrderItem, OrderStatus, Priority, PaymentStatus
from .client import WooCommerceClient

logger = logging.getLogger(__name__)


class WooCommerceService:
    """Service for WooCommerce integration"""

    def __init__(self):
        self.db = get_firestore_client()
        if self.db:
            self.integrations_collection = self.db.collection("integrations")
            self.sync_log_collection = self.db.collection("sync_logs")
        else:
            self.integrations_collection = None
            self.sync_log_collection = None

    def save_integration(
        self,
        user_id: str,
        store_url: str,
        consumer_key: str,
        consumer_secret: str,
        integration_name: str = "My WooCommerce Store",
        auto_sync: bool = True,
    ) -> Dict[str, Any]:
        """
        Save WooCommerce integration credentials
        
        Args:
            user_id: User ID who owns the integration
            store_url: WooCommerce store URL
            consumer_key: API consumer key
            consumer_secret: API consumer secret
            integration_name: Friendly name for the integration
            auto_sync: Enable automatic order synchronization
            
        Returns:
            Integration data
        """
        try:
            # Test connection first
            client = WooCommerceClient(store_url, consumer_key, consumer_secret)
            if not client.test_connection():
                raise ValueError("Failed to connect to WooCommerce store")

            integration_data = {
                "user_id": user_id,
                "platform": "woocommerce",
                "store_url": store_url,
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
                "integration_name": integration_name,
                "auto_sync": auto_sync,
                "status": "active",
                "created_at": datetime.utcnow(),
                "last_sync": None,
            }

            if self.integrations_collection:
                doc_ref = self.integrations_collection.add(integration_data)
                integration_data["id"] = doc_ref[1].id
            else:
                integration_data["id"] = f"wc_{int(datetime.utcnow().timestamp())}"

            logger.info(f"WooCommerce integration saved for user {user_id}")
            return integration_data

        except Exception as e:
            logger.error(f"Failed to save WooCommerce integration: {e}")
            raise

    def get_user_integrations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all WooCommerce integrations for a user"""
        try:
            if not self.integrations_collection:
                return []

            integrations = []
            query = (
                self.integrations_collection.where("user_id", "==", user_id)
                .where("platform", "==", "woocommerce")
                .stream()
            )

            for doc in query:
                data = doc.to_dict()
                data["id"] = doc.id
                # Don't expose secrets in list
                data.pop("consumer_secret", None)
                integrations.append(data)

            return integrations

        except Exception as e:
            logger.error(f"Failed to get user integrations: {e}")
            return []

    def _map_woocommerce_order_to_logix(
        self, wc_order: Dict[str, Any], integration_id: str
    ) -> Order:
        """
        Map WooCommerce order to Logix order format
        
        Args:
            wc_order: WooCommerce order data
            integration_id: Integration ID for reference
            
        Returns:
            Logix Order object
        """
        # Map order items
        items = []
        for wc_item in wc_order.get("line_items", []):
            item = OrderItem(
                sku=wc_item.get("sku", f"wc_{wc_item['product_id']}"),
                product_name=wc_item["name"],
                quantity=wc_item["quantity"],
                unit_price=Decimal(str(wc_item["price"])),
                total_price=Decimal(str(wc_item["total"])),
            )
            items.append(item)

        # Map order status
        status_mapping = {
            "pending": OrderStatus.PENDING,
            "processing": OrderStatus.PROCESSING,
            "on-hold": OrderStatus.PENDING,
            "completed": OrderStatus.DELIVERED,
            "cancelled": OrderStatus.CANCELLED,
            "refunded": OrderStatus.RETURNED,
            "failed": OrderStatus.CANCELLED,
        }
        status = status_mapping.get(wc_order["status"], OrderStatus.PENDING)

        # Map payment status
        payment_status_mapping = {
            "pending": PaymentStatus.PENDING,
            "processing": PaymentStatus.AUTHORIZED,
            "on-hold": PaymentStatus.PENDING,
            "completed": PaymentStatus.CAPTURED,
            "cancelled": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
            "failed": PaymentStatus.FAILED,
        }
        payment_status = payment_status_mapping.get(
            wc_order["status"], PaymentStatus.PENDING
        )

        # Build delivery address
        billing = wc_order.get("billing", {})
        shipping = wc_order.get("shipping", {})
        
        # Prefer shipping address, fallback to billing
        delivery_address = {
            "name": shipping.get("first_name", billing.get("first_name", ""))
            + " "
            + shipping.get("last_name", billing.get("last_name", "")),
            "company": shipping.get("company", billing.get("company", "")),
            "street": shipping.get("address_1", billing.get("address_1", "")),
            "city": shipping.get("city", billing.get("city", "")),
            "state": shipping.get("state", billing.get("state", "")),
            "zip_code": shipping.get("postcode", billing.get("postcode", "")),
            "country": shipping.get("country", billing.get("country", "")),
            "phone": billing.get("phone", ""),
        }

        # Create order
        order = Order(
            order_id=f"WC-{wc_order['id']}",
            customer_id=f"wc_customer_{wc_order['customer_id']}",
            status=status,
            priority=Priority.NORMAL,
            items=items,
            subtotal=Decimal(str(wc_order.get("total", 0)))
            - Decimal(str(wc_order.get("total_tax", 0)))
            - Decimal(str(wc_order.get("shipping_total", 0))),
            tax_amount=Decimal(str(wc_order.get("total_tax", 0))),
            shipping_cost=Decimal(str(wc_order.get("shipping_total", 0))),
            discount_amount=Decimal(str(wc_order.get("discount_total", 0))),
            total_amount=Decimal(str(wc_order.get("total", 0))),
            delivery_address=delivery_address,
            delivery_instructions=wc_order.get("customer_note", ""),
            payment_method=wc_order.get("payment_method_title", ""),
            payment_status=payment_status,
            payment_reference=wc_order.get("transaction_id", ""),
            source="woocommerce",
            notes=f"WooCommerce Order #{wc_order['id']} from {integration_id}",
            tags=["woocommerce", integration_id],
            created_at=datetime.fromisoformat(
                wc_order["date_created"].replace("Z", "+00:00")
            ),
        )

        return order

    def sync_orders(
        self,
        integration_id: str,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Synchronize orders from WooCommerce to Logix
        
        Args:
            integration_id: Integration ID
            status: Filter by order status
            since: Only sync orders after this date
            limit: Maximum orders to sync
            
        Returns:
            Sync results
        """
        try:
            # Get integration credentials
            if self.integrations_collection:
                integration_doc = self.integrations_collection.document(
                    integration_id
                ).get()
                if not integration_doc.exists:
                    raise ValueError(f"Integration {integration_id} not found")
                integration_data = integration_doc.to_dict()
            else:
                raise ValueError("Firestore not available")

            # Initialize WooCommerce client
            client = WooCommerceClient(
                store_url=integration_data["store_url"],
                consumer_key=integration_data["consumer_key"],
                consumer_secret=integration_data["consumer_secret"],
            )

            # Prepare sync parameters
            params = {
                "per_page": min(limit, 100),
                "page": 1,
            }
            if status:
                params["status"] = status
            if since:
                params["after"] = since.isoformat()

            # Fetch orders from WooCommerce
            wc_orders = client.get_orders(**params)

            # Convert and save orders
            synced_count = 0
            failed_count = 0
            errors = []

            from backend.services.order.service import OrderService

            order_service = OrderService()

            for wc_order in wc_orders:
                try:
                    logix_order = self._map_woocommerce_order_to_logix(
                        wc_order, integration_id
                    )
                    
                    # Check if order already exists
                    existing = order_service.get_order(logix_order.order_id)
                    if existing:
                        # Update existing order
                        order_service.update_order(
                            logix_order.order_id, logix_order.to_dict(), "system"
                        )
                    else:
                        # Create new order
                        order_service.create_order(logix_order.to_dict())
                    
                    synced_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Order {wc_order['id']}: {str(e)}")
                    logger.error(f"Failed to sync order {wc_order['id']}: {e}")

            # Update last sync time
            if self.integrations_collection:
                self.integrations_collection.document(integration_id).update(
                    {"last_sync": datetime.utcnow()}
                )

            # Log sync results
            sync_result = {
                "integration_id": integration_id,
                "timestamp": datetime.utcnow(),
                "total_orders": len(wc_orders),
                "synced": synced_count,
                "failed": failed_count,
                "errors": errors,
            }

            if self.sync_log_collection:
                self.sync_log_collection.add(sync_result)

            logger.info(
                f"WooCommerce sync completed: {synced_count} synced, {failed_count} failed"
            )
            return sync_result

        except Exception as e:
            logger.error(f"WooCommerce sync failed: {e}")
            raise

    def update_woocommerce_order_status(
        self, integration_id: str, wc_order_id: int, logix_status: OrderStatus
    ) -> bool:
        """
        Update order status in WooCommerce based on Logix status
        
        Args:
            integration_id: Integration ID
            wc_order_id: WooCommerce order ID
            logix_status: Logix order status
            
        Returns:
            True if successful
        """
        try:
            # Get integration credentials
            if self.integrations_collection:
                integration_doc = self.integrations_collection.document(
                    integration_id
                ).get()
                if not integration_doc.exists:
                    raise ValueError(f"Integration {integration_id} not found")
                integration_data = integration_doc.to_dict()
            else:
                raise ValueError("Firestore not available")

            # Map Logix status to WooCommerce status
            status_mapping = {
                OrderStatus.PENDING: "pending",
                OrderStatus.CONFIRMED: "processing",
                OrderStatus.PROCESSING: "processing",
                OrderStatus.PICKED: "processing",
                OrderStatus.PACKED: "processing",
                OrderStatus.SHIPPED: "processing",
                OrderStatus.OUT_FOR_DELIVERY: "processing",
                OrderStatus.DELIVERED: "completed",
                OrderStatus.CANCELLED: "cancelled",
                OrderStatus.RETURNED: "refunded",
            }

            wc_status = status_mapping.get(logix_status, "processing")

            # Initialize client and update status
            client = WooCommerceClient(
                store_url=integration_data["store_url"],
                consumer_key=integration_data["consumer_key"],
                consumer_secret=integration_data["consumer_secret"],
            )

            client.update_order_status(
                wc_order_id,
                wc_status,
                note=f"Status updated from Logix to {logix_status.value}",
            )

            logger.info(
                f"Updated WooCommerce order {wc_order_id} to status {wc_status}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update WooCommerce order status: {e}")
            return False

    def sync_product_stock(
        self, integration_id: str, sku: str, quantity: int
    ) -> bool:
        """
        Sync product stock from Logix to WooCommerce
        
        Args:
            integration_id: Integration ID
            sku: Product SKU
            quantity: New stock quantity
            
        Returns:
            True if successful
        """
        try:
            # Get integration credentials
            if self.integrations_collection:
                integration_doc = self.integrations_collection.document(
                    integration_id
                ).get()
                if not integration_doc.exists:
                    raise ValueError(f"Integration {integration_id} not found")
                integration_data = integration_doc.to_dict()
            else:
                raise ValueError("Firestore not available")

            # Initialize client
            client = WooCommerceClient(
                store_url=integration_data["store_url"],
                consumer_key=integration_data["consumer_key"],
                consumer_secret=integration_data["consumer_secret"],
            )

            # Find product by SKU
            products = client.get_products(sku=sku)
            if not products:
                logger.warning(f"Product with SKU {sku} not found in WooCommerce")
                return False

            product = products[0]
            client.update_product_stock(product["id"], quantity)

            logger.info(
                f"Updated WooCommerce product {sku} stock to {quantity}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to sync product stock: {e}")
            return False

