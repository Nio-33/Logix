"""
WooCommerce API Client
Handles authentication and API requests to WooCommerce stores
"""

import logging
import requests
from typing import Optional, Dict, Any, List
from requests.auth import HTTPBasicAuth
import hmac
import hashlib
import time

logger = logging.getLogger(__name__)


class WooCommerceClient:
    """WooCommerce REST API Client"""

    def __init__(
        self,
        store_url: str,
        consumer_key: str,
        consumer_secret: str,
        api_version: str = "wc/v3",
        verify_ssl: bool = True,
    ):
        """
        Initialize WooCommerce client
        
        Args:
            store_url: WooCommerce store URL (e.g., https://example.com)
            consumer_key: WooCommerce API consumer key
            consumer_secret: WooCommerce API consumer secret
            api_version: API version (default: wc/v3)
            verify_ssl: Verify SSL certificates (default: True)
        """
        self.store_url = store_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_version = api_version
        self.verify_ssl = verify_ssl
        self.base_url = f"{self.store_url}/wp-json/{api_version}"
        
        # Authentication
        self.auth = HTTPBasicAuth(consumer_key, consumer_secret)
        
        logger.info(f"WooCommerce client initialized for {store_url}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make API request to WooCommerce
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., 'orders', 'products')
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                params=params,
                json=data,
                verify=self.verify_ssl,
                timeout=30,
            )
            
            response.raise_for_status()
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"WooCommerce API request failed: {e}")
            raise

    # Order Methods
    def get_orders(
        self,
        page: int = 1,
        per_page: int = 100,
        status: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get orders from WooCommerce
        
        Args:
            page: Page number
            per_page: Orders per page (max 100)
            status: Order status filter
            after: Get orders after this date (ISO 8601)
            before: Get orders before this date (ISO 8601)
            
        Returns:
            List of orders
        """
        params = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        
        if status:
            params["status"] = status
        if after:
            params["after"] = after
        if before:
            params["before"] = before
            
        return self._make_request("GET", "orders", params=params)

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get single order by ID"""
        return self._make_request("GET", f"orders/{order_id}")

    def update_order_status(
        self, order_id: int, status: str, note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update order status
        
        Args:
            order_id: WooCommerce order ID
            status: New status (pending, processing, on-hold, completed, cancelled, refunded, failed)
            note: Optional note to add to order
            
        Returns:
            Updated order data
        """
        data = {"status": status}
        
        if note:
            data["customer_note"] = note
            
        return self._make_request("PUT", f"orders/{order_id}", data=data)

    def add_order_note(self, order_id: int, note: str, customer_note: bool = False) -> Dict[str, Any]:
        """
        Add note to order
        
        Args:
            order_id: WooCommerce order ID
            note: Note text
            customer_note: Whether note is visible to customer
            
        Returns:
            Created note data
        """
        data = {
            "note": note,
            "customer_note": customer_note,
        }
        
        return self._make_request("POST", f"orders/{order_id}/notes", data=data)

    # Product Methods
    def get_products(
        self,
        page: int = 1,
        per_page: int = 100,
        search: Optional[str] = None,
        sku: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get products from WooCommerce
        
        Args:
            page: Page number
            per_page: Products per page (max 100)
            search: Search term
            sku: Filter by SKU
            
        Returns:
            List of products
        """
        params = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        
        if search:
            params["search"] = search
        if sku:
            params["sku"] = sku
            
        return self._make_request("GET", "products", params=params)

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get single product by ID"""
        return self._make_request("GET", f"products/{product_id}")

    def update_product_stock(
        self, product_id: int, stock_quantity: int, manage_stock: bool = True
    ) -> Dict[str, Any]:
        """
        Update product stock quantity
        
        Args:
            product_id: WooCommerce product ID
            stock_quantity: New stock quantity
            manage_stock: Enable stock management
            
        Returns:
            Updated product data
        """
        data = {
            "stock_quantity": stock_quantity,
            "manage_stock": manage_stock,
        }
        
        return self._make_request("PUT", f"products/{product_id}", data=data)

    # Customer Methods
    def get_customers(
        self, page: int = 1, per_page: int = 100, email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get customers from WooCommerce
        
        Args:
            page: Page number
            per_page: Customers per page (max 100)
            email: Filter by email
            
        Returns:
            List of customers
        """
        params = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        
        if email:
            params["email"] = email
            
        return self._make_request("GET", "customers", params=params)

    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """Get single customer by ID"""
        return self._make_request("GET", f"customers/{customer_id}")

    # Webhook Methods
    def create_webhook(
        self,
        topic: str,
        delivery_url: str,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create webhook in WooCommerce
        
        Args:
            topic: Webhook topic (e.g., 'order.created', 'order.updated')
            delivery_url: URL to receive webhook notifications
            secret: Optional secret for webhook verification
            
        Returns:
            Created webhook data
        """
        data = {
            "name": f"Logix - {topic}",
            "topic": topic,
            "delivery_url": delivery_url,
            "status": "active",
        }
        
        if secret:
            data["secret"] = secret
            
        return self._make_request("POST", "webhooks", data=data)

    def get_webhooks(self) -> List[Dict[str, Any]]:
        """Get all webhooks"""
        return self._make_request("GET", "webhooks")

    def delete_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """Delete webhook by ID"""
        return self._make_request("DELETE", f"webhooks/{webhook_id}")

    @staticmethod
    def verify_webhook_signature(
        payload: bytes, signature: str, secret: str
    ) -> bool:
        """
        Verify WooCommerce webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Signature from X-WC-Webhook-Signature header
            secret: Webhook secret
            
        Returns:
            True if signature is valid
        """
        expected_signature = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).digest()
        
        import base64
        expected_signature_b64 = base64.b64encode(expected_signature).decode()
        
        return hmac.compare_digest(expected_signature_b64, signature)

    # System Methods
    def test_connection(self) -> bool:
        """
        Test connection to WooCommerce store
        
        Returns:
            True if connection successful
        """
        try:
            # Try to get system status
            self._make_request("GET", "system_status")
            logger.info(f"WooCommerce connection test successful for {self.store_url}")
            return True
        except Exception as e:
            logger.error(f"WooCommerce connection test failed: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Get WooCommerce system status"""
        return self._make_request("GET", "system_status")

