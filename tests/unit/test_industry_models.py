"""
Unit Tests for Industry-Specific Models
"""

import pytest
from datetime import datetime
from decimal import Decimal

from backend.shared.models import (
    Order,
    OrderItem,
    OrderType,
    OrderSource,
    IndustryCategory,
    EcommerceOrderData,
    RetailOrderData,
    FoodDeliveryOrderData,
    ManufacturingOrderData,
    ThirdPartyOrderData,
    OrderStatus,
    Priority,
)


class TestIndustryTypes:
    """Test industry type enumerations"""
    
    def test_industry_categories(self):
        """Test all industry categories are defined"""
        assert IndustryCategory.ECOMMERCE.value == "ecommerce"
        assert IndustryCategory.RETAIL.value == "retail"
        assert IndustryCategory.FOOD_DELIVERY.value == "food_delivery"
        assert IndustryCategory.MANUFACTURING.value == "manufacturing"
        assert IndustryCategory.THIRD_PARTY_LOGISTICS.value == "3pl"
    
    def test_order_types(self):
        """Test order types span all industries"""
        # E-commerce types
        assert OrderType.ECOMMERCE_DIRECT.value == "ecommerce_direct"
        assert OrderType.ECOMMERCE_MARKETPLACE.value == "ecommerce_marketplace"
        
        # Retail types
        assert OrderType.RETAIL_PURCHASE_ORDER.value == "retail_po"
        
        # Food delivery types
        assert OrderType.FOOD_DELIVERY_CUSTOMER.value == "food_delivery_customer"
        
        # Manufacturing types
        assert OrderType.MANUFACTURING_PRODUCTION.value == "manufacturing_production"
        
        # 3PL types
        assert OrderType.THIRD_PARTY_FULFILLMENT.value == "3pl_fulfillment"
    
    def test_order_sources(self):
        """Test order sources include major platforms"""
        assert OrderSource.SHOPIFY.value == "shopify"
        assert OrderSource.WOOCOMMERCE.value == "woocommerce"
        assert OrderSource.AMAZON_MARKETPLACE.value == "amazon_marketplace"
        assert OrderSource.UBER_EATS.value == "uber_eats"
        assert OrderSource.EDI_SYSTEM.value == "edi_system"


class TestEcommerceOrderData:
    """Test e-commerce order data model"""
    
    def test_create_ecommerce_data(self):
        """Test creating e-commerce order data"""
        ecom_data = EcommerceOrderData(
            platform_order_id="SHOP-12345",
            platform_name="shopify",
            customer_email="test@example.com",
            customer_segment="loyal",
            is_subscription=True,
            subscription_id="SUB-789"
        )
        
        assert ecom_data.platform_order_id == "SHOP-12345"
        assert ecom_data.customer_email == "test@example.com"
        assert ecom_data.is_subscription is True
    
    def test_ecommerce_data_to_dict(self):
        """Test e-commerce data serialization"""
        ecom_data = EcommerceOrderData(
            platform_order_id="SHOP-12345",
            platform_name="shopify",
            customer_email="test@example.com"
        )
        
        data_dict = ecom_data.to_dict()
        assert data_dict['platform_order_id'] == "SHOP-12345"
        assert data_dict['customer_email'] == "test@example.com"
    
    def test_ecommerce_data_from_dict(self):
        """Test e-commerce data deserialization"""
        data_dict = {
            'platform_order_id': "SHOP-12345",
            'platform_name': "shopify",
            'customer_email': "test@example.com",
            'customer_segment': "VIP"
        }
        
        ecom_data = EcommerceOrderData.from_dict(data_dict)
        assert ecom_data.platform_order_id == "SHOP-12345"
        assert ecom_data.customer_segment == "VIP"


class TestRetailOrderData:
    """Test retail order data model"""
    
    def test_create_retail_data(self):
        """Test creating retail order data"""
        retail_data = RetailOrderData(
            po_number="PO-2025-001",
            vendor_id="VEND-456",
            vendor_name="ABC Distributors",
            buyer_id="BUYER-789",
            buyer_name="Retail Chain Inc",
            payment_terms="Net 30",
            delivery_terms="FOB Destination",
            inspection_required=True
        )
        
        assert retail_data.po_number == "PO-2025-001"
        assert retail_data.inspection_required is True


class TestFoodDeliveryOrderData:
    """Test food delivery order data model"""
    
    def test_create_food_delivery_data(self):
        """Test creating food delivery order data"""
        food_data = FoodDeliveryOrderData(
            restaurant_id="REST-123",
            restaurant_name="Pizza Palace",
            restaurant_address={"street": "123 Main St", "city": "SF"},
            restaurant_phone="555-0100",
            customer_phone="555-0200",
            preparation_time_minutes=20,
            temperature_requirements="hot",
            allergen_info=["gluten", "dairy"]
        )
        
        assert food_data.restaurant_id == "REST-123"
        assert food_data.preparation_time_minutes == 20
        assert "gluten" in food_data.allergen_info


class TestEnhancedOrderModel:
    """Test enhanced Order model with industry support"""
    
    def test_create_ecommerce_order(self):
        """Test creating an e-commerce order"""
        items = [
            OrderItem(
                sku="SKU-001",
                product_name="Test Product",
                quantity=2,
                unit_price=Decimal("29.99"),
                total_price=Decimal("59.98")
            )
        ]
        
        ecom_data = EcommerceOrderData(
            platform_order_id="SHOP-789",
            platform_name="shopify",
            customer_email="test@shop.com"
        )
        
        order = Order(
            order_id="ORD-TEST-001",
            customer_id="CUST-123",
            items=items,
            delivery_address={"street": "123 Test St", "city": "SF"},
            order_type=OrderType.ECOMMERCE_DIRECT,
            order_source=OrderSource.SHOPIFY,
            industry_category=IndustryCategory.ECOMMERCE,
            ecommerce_data=ecom_data
        )
        
        assert order.order_type == OrderType.ECOMMERCE_DIRECT
        assert order.industry_category == IndustryCategory.ECOMMERCE
        assert order.has_industry_data() is True
        assert order.get_industry_display_name() == "E-commerce"
    
    def test_order_to_dict_with_industry_data(self):
        """Test order serialization with industry data"""
        ecom_data = EcommerceOrderData(
            platform_order_id="SHOP-789",
            platform_name="shopify",
            customer_email="test@shop.com"
        )
        
        order = Order(
            order_id="ORD-TEST-002",
            customer_id="CUST-123",
            items=[],
            delivery_address={},
            industry_category=IndustryCategory.ECOMMERCE,
            ecommerce_data=ecom_data
        )
        
        order_dict = order.to_dict()
        
        assert 'industry_category' in order_dict
        assert order_dict['industry_category'] == "ecommerce"
        assert 'ecommerce_data' in order_dict
        assert order_dict['ecommerce_data']['platform_order_id'] == "SHOP-789"
    
    def test_order_time_sensitive_detection(self):
        """Test time-sensitive order detection"""
        # Food delivery orders are always time-sensitive
        food_data = FoodDeliveryOrderData(
            restaurant_id="REST-123",
            restaurant_name="Fast Food",
            restaurant_address={},
            restaurant_phone="555-0100",
            customer_phone="555-0200",
            preparation_time_minutes=15
        )
        
        order = Order(
            order_id="ORD-TEST-003",
            customer_id="CUST-123",
            items=[],
            delivery_address={},
            industry_category=IndustryCategory.FOOD_DELIVERY,
            food_delivery_data=food_data
        )
        
        assert order.is_time_sensitive is True
    
    def test_order_special_handling_detection(self):
        """Test special handling detection"""
        # Retail order with hazmat
        retail_data = RetailOrderData(
            po_number="PO-001",
            vendor_id="VEND-123",
            vendor_name="Vendor",
            buyer_id="BUYER-456",
            buyer_name="Buyer",
            payment_terms="Net 30",
            delivery_terms="FOB",
            hazmat_classification="Class 3"
        )
        
        order = Order(
            order_id="ORD-TEST-004",
            customer_id="CUST-123",
            items=[],
            delivery_address={},
            industry_category=IndustryCategory.RETAIL,
            retail_data=retail_data
        )
        
        assert order.requires_special_handling is True


class TestIndustryWorkflows:
    """Test industry-specific workflows"""
    
    def test_get_workflow_for_ecommerce(self):
        """Test e-commerce workflow"""
        from backend.shared.models.industry_workflows import IndustryStatusWorkflow
        
        workflow = IndustryStatusWorkflow.get_workflow(OrderType.ECOMMERCE_DIRECT)
        
        assert OrderStatus.PENDING in workflow
        assert OrderStatus.CONFIRMED in workflow
        assert OrderStatus.SHIPPED in workflow
        assert OrderStatus.DELIVERED in workflow
    
    def test_get_workflow_for_food_delivery(self):
        """Test food delivery workflow includes PREPARING status"""
        from backend.shared.models.industry_workflows import IndustryStatusWorkflow
        
        workflow = IndustryStatusWorkflow.get_workflow(OrderType.FOOD_DELIVERY_CUSTOMER)
        
        assert OrderStatus.PREPARING in workflow
        assert OrderStatus.READY_FOR_PICKUP in workflow
        assert OrderStatus.PICKED_UP in workflow
    
    def test_valid_status_transition(self):
        """Test valid status transitions"""
        from backend.shared.models.industry_workflows import IndustryStatusWorkflow
        
        is_valid = IndustryStatusWorkflow.is_valid_transition(
            current_status=OrderStatus.CONFIRMED,
            new_status=OrderStatus.PROCESSING,
            order_type=OrderType.ECOMMERCE_DIRECT
        )
        
        assert is_valid is True
    
    def test_invalid_status_transition(self):
        """Test invalid status transitions are blocked"""
        from backend.shared.models.industry_workflows import IndustryStatusWorkflow
        
        # Can't go from PENDING directly to DELIVERED
        is_valid = IndustryStatusWorkflow.is_valid_transition(
            current_status=OrderStatus.PENDING,
            new_status=OrderStatus.DELIVERED,
            order_type=OrderType.ECOMMERCE_DIRECT
        )
        
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

