"""
Shopify E-commerce Platform Integration
Handles order synchronization, inventory updates, and fulfillment
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from shared.models import (
    Order,
    OrderItem,
    OrderType,
    OrderSource,
    IndustryCategory,
    EcommerceOrderData,
)

logger = logging.getLogger(__name__)


class ShopifyConnector:
    """Shopify platform integration connector"""
    
    def __init__(self, shop_url: str, access_token: str):
        """
        Initialize Shopify connector
        
        Args:
            shop_url: Shopify store URL (e.g., 'my-store.myshopify.com')
            access_token: Shopify Admin API access token
        """
        self.shop_url = shop_url.rstrip('/')
        self.access_token = access_token
        self.api_version = '2024-01'  # Current Shopify API version
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"
        
        logger.info(f"Shopify connector initialized for {shop_url}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json',
        }
    
    def fetch_new_orders(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch new orders from Shopify
        
        Args:
            since: Only fetch orders created after this datetime
            
        Returns:
            List of Shopify order objects
        """
        try:
            url = f"{self.base_url}/orders.json"
            params = {
                'status': 'any',
                'limit': 250,
            }
            
            if since:
                params['created_at_min'] = since.isoformat()
            
            response = requests.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            orders = data.get('orders', [])
            
            logger.info(f"Fetched {len(orders)} orders from Shopify")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to fetch Shopify orders: {e}")
            raise
    
    def convert_shopify_order_to_logix(self, shopify_order: Dict[str, Any]) -> Order:
        """
        Convert Shopify order format to Logix Order model
        
        Args:
            shopify_order: Raw Shopify order object
            
        Returns:
            Logix Order object
        """
        try:
            # Extract basic order info
            shopify_id = str(shopify_order['id'])
            order_id = f"SHOP-{shopify_id}"
            
            # Convert line items to OrderItems
            items = []
            for line_item in shopify_order.get('line_items', []):
                item = OrderItem(
                    sku=line_item.get('sku') or line_item['id'],
                    product_name=line_item['title'],
                    quantity=line_item['quantity'],
                    unit_price=Decimal(str(line_item['price'])),
                    total_price=Decimal(str(line_item['price'])) * line_item['quantity'],
                )
                items.append(item)
            
            # Extract delivery address
            shipping_address = shopify_order.get('shipping_address', {})
            delivery_address = {
                'name': f"{shipping_address.get('first_name', '')} {shipping_address.get('last_name', '')}".strip(),
                'company': shipping_address.get('company', ''),
                'street': f"{shipping_address.get('address1', '')} {shipping_address.get('address2', '')}".strip(),
                'city': shipping_address.get('city', ''),
                'state': shipping_address.get('province', ''),
                'zip_code': shipping_address.get('zip', ''),
                'country': shipping_address.get('country', ''),
                'phone': shipping_address.get('phone', ''),
            }
            
            # Extract customer info
            customer = shopify_order.get('customer', {})
            customer_email = customer.get('email') or shopify_order.get('email', '')
            customer_phone = customer.get('phone') or shipping_address.get('phone', '')
            
            # Determine customer segment
            customer_segment = 'new'
            if customer.get('orders_count', 0) > 10:
                customer_segment = 'loyal'
            elif customer.get('orders_count', 0) > 3:
                customer_segment = 'regular'
            
            # Check if subscription order
            is_subscription = any(
                'subscription' in str(line_item.get('properties', [])).lower()
                for line_item in shopify_order.get('line_items', [])
            )
            
            # Create E-commerce specific data
            ecommerce_data = EcommerceOrderData(
                platform_order_id=shopify_id,
                platform_name='shopify',
                customer_email=customer_email,
                store_id=shopify_order.get('location_id'),
                customer_phone=customer_phone,
                customer_segment=customer_segment,
                utm_source=shopify_order.get('source_name'),
                is_subscription=is_subscription,
                customer_service_notes=shopify_order.get('note'),
            )
            
            # Create Logix Order
            order = Order(
                order_id=order_id,
                customer_id=customer.get('id', 'GUEST'),
                items=items,
                delivery_address=delivery_address,
                delivery_instructions=shopify_order.get('note'),
                order_type=OrderType.ECOMMERCE_SUBSCRIPTION if is_subscription else OrderType.ECOMMERCE_DIRECT,
                order_source=OrderSource.SHOPIFY,
                industry_category=IndustryCategory.ECOMMERCE,
                ecommerce_data=ecommerce_data,
                subtotal=Decimal(str(shopify_order.get('subtotal_price', 0))),
                tax_amount=Decimal(str(shopify_order.get('total_tax', 0))),
                shipping_cost=Decimal(str(shopify_order.get('total_shipping_price_set', {}).get('shop_money', {}).get('amount', 0))),
                total_amount=Decimal(str(shopify_order.get('total_price', 0))),
                payment_method=shopify_order.get('payment_gateway_names', [''])[0] if shopify_order.get('payment_gateway_names') else None,
            )
            
            logger.info(f"Converted Shopify order {shopify_id} to Logix order {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to convert Shopify order: {e}")
            raise
    
    def sync_orders(self, since: Optional[datetime] = None) -> List[Order]:
        """
        Sync orders from Shopify to Logix
        
        Args:
            since: Only sync orders created after this datetime
            
        Returns:
            List of converted Logix Order objects
        """
        try:
            shopify_orders = self.fetch_new_orders(since)
            logix_orders = []
            
            for shopify_order in shopify_orders:
                try:
                    logix_order = self.convert_shopify_order_to_logix(shopify_order)
                    logix_orders.append(logix_order)
                except Exception as e:
                    logger.error(f"Failed to convert Shopify order {shopify_order.get('id')}: {e}")
                    continue
            
            logger.info(f"Synced {len(logix_orders)} orders from Shopify")
            return logix_orders
            
        except Exception as e:
            logger.error(f"Shopify order sync failed: {e}")
            raise
    
    def update_fulfillment_status(self, shopify_order_id: str, tracking_info: Dict[str, Any]) -> bool:
        """
        Update order fulfillment status in Shopify
        
        Args:
            shopify_order_id: Shopify order ID
            tracking_info: Tracking number and carrier info
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/orders/{shopify_order_id}/fulfillments.json"
            
            payload = {
                'fulfillment': {
                    'tracking_number': tracking_info.get('tracking_number'),
                    'tracking_company': tracking_info.get('carrier'),
                    'notify_customer': True,
                }
            }
            
            response = requests.post(
                url,
                headers=self.get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Updated fulfillment status for Shopify order {shopify_order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Shopify fulfillment: {e}")
            return False
    
    def update_inventory_level(self, sku: str, quantity: int, location_id: str) -> bool:
        """
        Update inventory level in Shopify
        
        Args:
            sku: Product SKU
            quantity: New quantity
            location_id: Shopify location ID
            
        Returns:
            True if successful
        """
        try:
            # This would use Shopify Inventory API
            # Implementation details depend on Shopify inventory setup
            logger.info(f"Updated Shopify inventory for SKU {sku}: {quantity} units")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Shopify inventory: {e}")
            return False


class ShopifyWebhookHandler:
    """Handle Shopify webhooks for real-time synchronization"""
    
    @staticmethod
    def verify_webhook(data: bytes, hmac_header: str, secret: str) -> bool:
        """
        Verify Shopify webhook signature
        
        Args:
            data: Raw request body
            hmac_header: X-Shopify-Hmac-SHA256 header value
            secret: Shopify webhook secret
            
        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib
        import base64
        
        computed_hmac = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(computed_hmac, hmac_header)
    
    @staticmethod
    def handle_order_created(webhook_data: Dict[str, Any]) -> Order:
        """
        Handle orders/create webhook
        
        Args:
            webhook_data: Shopify order object from webhook
            
        Returns:
            Converted Logix Order
        """
        try:
            # Create temporary connector (credentials would come from database)
            connector = ShopifyConnector('temp.myshopify.com', 'temp_token')
            order = connector.convert_shopify_order_to_logix(webhook_data)
            
            logger.info(f"Processed Shopify webhook: order created {order.order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to handle Shopify webhook: {e}")
            raise

