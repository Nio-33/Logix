"""
WooCommerce E-commerce Platform Integration
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from requests.auth import HTTPBasicAuth

from shared.models import (
    Order,
    OrderItem,
    OrderType,
    OrderSource,
    IndustryCategory,
    EcommerceOrderData,
)

logger = logging.getLogger(__name__)


class WooCommerceConnector:
    """WooCommerce platform integration connector"""
    
    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        """
        Initialize WooCommerce connector
        
        Args:
            store_url: WooCommerce store URL
            consumer_key: WooCommerce REST API consumer key
            consumer_secret: WooCommerce REST API consumer secret
        """
        self.store_url = store_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.base_url = f"{self.store_url}/wp-json/wc/v3"
        
        logger.info(f"WooCommerce connector initialized for {store_url}")
    
    def get_auth(self) -> HTTPBasicAuth:
        """Get HTTP Basic Auth"""
        return HTTPBasicAuth(self.consumer_key, self.consumer_secret)
    
    def fetch_new_orders(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch new orders from WooCommerce"""
        try:
            url = f"{self.base_url}/orders"
            params = {
                'per_page': 100,
                'status': 'processing,pending',
            }
            
            if since:
                params['after'] = since.isoformat()
            
            response = requests.get(
                url,
                auth=self.get_auth(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            orders = response.json()
            logger.info(f"Fetched {len(orders)} orders from WooCommerce")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to fetch WooCommerce orders: {e}")
            raise
    
    def convert_woocommerce_order_to_logix(self, woo_order: Dict[str, Any]) -> Order:
        """Convert WooCommerce order to Logix Order"""
        try:
            woo_id = str(woo_order['id'])
            order_id = f"WOO-{woo_id}"
            
            # Convert line items
            items = []
            for line_item in woo_order.get('line_items', []):
                item = OrderItem(
                    sku=line_item.get('sku') or str(line_item['product_id']),
                    product_name=line_item['name'],
                    quantity=line_item['quantity'],
                    unit_price=Decimal(str(line_item['price'])),
                    total_price=Decimal(str(line_item['total'])),
                )
                items.append(item)
            
            # Extract delivery address
            shipping = woo_order.get('shipping', {})
            billing = woo_order.get('billing', {})
            delivery_address = {
                'name': f"{shipping.get('first_name', '')} {shipping.get('last_name', '')}".strip(),
                'company': shipping.get('company', ''),
                'street': f"{shipping.get('address_1', '')} {shipping.get('address_2', '')}".strip(),
                'city': shipping.get('city', ''),
                'state': shipping.get('state', ''),
                'zip_code': shipping.get('postcode', ''),
                'country': shipping.get('country', ''),
                'phone': billing.get('phone', ''),
            }
            
            # Create E-commerce data
            ecommerce_data = EcommerceOrderData(
                platform_order_id=woo_id,
                platform_name='woocommerce',
                customer_email=billing.get('email', ''),
                customer_phone=billing.get('phone'),
                customer_service_notes=woo_order.get('customer_note'),
            )
            
            # Create Order
            order = Order(
                order_id=order_id,
                customer_id=str(woo_order.get('customer_id', 0)),
                items=items,
                delivery_address=delivery_address,
                delivery_instructions=woo_order.get('customer_note'),
                order_type=OrderType.ECOMMERCE_DIRECT,
                order_source=OrderSource.WOOCOMMERCE,
                industry_category=IndustryCategory.ECOMMERCE,
                ecommerce_data=ecommerce_data,
                subtotal=Decimal(str(woo_order.get('total', 0))) - Decimal(str(woo_order.get('total_tax', 0))),
                tax_amount=Decimal(str(woo_order.get('total_tax', 0))),
                shipping_cost=Decimal(str(woo_order.get('shipping_total', 0))),
                total_amount=Decimal(str(woo_order.get('total', 0))),
                payment_method=woo_order.get('payment_method_title'),
            )
            
            logger.info(f"Converted WooCommerce order {woo_id} to Logix order {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to convert WooCommerce order: {e}")
            raise
    
    def update_order_status(self, woo_order_id: str, status: str) -> bool:
        """Update order status in WooCommerce"""
        try:
            url = f"{self.base_url}/orders/{woo_order_id}"
            payload = {'status': status}
            
            response = requests.put(
                url,
                auth=self.get_auth(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Updated WooCommerce order {woo_order_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update WooCommerce order status: {e}")
            return False

