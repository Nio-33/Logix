"""
Integration Tests for Industry-Specific Order Processors
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
    OrderStatus,
    Priority,
)
from backend.services.order.industry_processors import (
    EcommerceOrderProcessor,
    RetailOrderProcessor,
    FoodDeliveryOrderProcessor,
    IndustryOrderProcessorFactory,
)


class TestEcommerceProcessor:
    """Test e-commerce order processor"""
    
    def test_validate_valid_ecommerce_order(self):
        """Test validation passes for valid e-commerce order"""
        processor = EcommerceOrderProcessor()
        
        order_data = {
            'ecommerce_data': {
                'platform_order_id': 'SHOP-123',
                'platform_name': 'shopify',
                'customer_email': 'test@example.com',
            }
        }
        
        result = processor.validate(order_data)
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields missing"""
        processor = EcommerceOrderProcessor()
        
        order_data = {
            'ecommerce_data': {
                'platform_order_id': 'SHOP-123',
                # Missing platform_name and customer_email
            }
        }
        
        result = processor.validate(order_data)
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_process_ecommerce_order(self):
        """Test e-commerce order processing"""
        processor = EcommerceOrderProcessor()
        
        ecom_data = EcommerceOrderData(
            platform_order_id='SHOP-123',
            platform_name='shopify',
            customer_email='vip@example.com',
            customer_segment='VIP'
        )
        
        order = Order(
            order_id='ORD-TEST',
            customer_id='CUST-123',
            items=[],
            delivery_address={},
            order_type=OrderType.ECOMMERCE_DIRECT,
            ecommerce_data=ecom_data
        )
        
        processed_order = processor.process(order)
        
        assert processed_order.industry_category.value == IndustryCategory.ECOMMERCE.value
        assert processed_order.priority.value == Priority.HIGH.value  # VIP customer gets high priority
    
    def test_calculate_fulfillment_time(self):
        """Test e-commerce fulfillment time calculation"""
        processor = EcommerceOrderProcessor()
        
        items = [
            OrderItem(sku=f"SKU-{i}", product_name=f"Product {i}", quantity=1, 
                     unit_price=Decimal("10"), total_price=Decimal("10"))
            for i in range(3)
        ]
        
        order = Order(
            order_id='ORD-TEST',
            customer_id='CUST-123',
            items=items,
            delivery_address={},
            priority=Priority.NORMAL
        )
        
        time = processor.calculate_fulfillment_time(order)
        
        # Base 30 + (3 items * 5 minutes) = 45 minutes
        assert time == 45


class TestRetailProcessor:
    """Test retail order processor"""
    
    def test_validate_retail_order(self):
        """Test retail order validation"""
        processor = RetailOrderProcessor()
        
        order_data = {
            'retail_data': {
                'po_number': 'PO-2025-001',
                'vendor_id': 'VEND-123',
                'vendor_name': 'Vendor ABC',
                'buyer_id': 'BUYER-456',
                'buyer_name': 'Retailer XYZ',
                'payment_terms': 'Net 30',
                'delivery_terms': 'FOB Destination'
            }
        }
        
        result = processor.validate(order_data)
        assert result['valid'] is True
    
    def test_retail_fulfillment_with_inspection(self):
        """Test retail fulfillment time includes inspection"""
        processor = RetailOrderProcessor()
        
        retail_data = RetailOrderData(
            po_number='PO-001',
            vendor_id='VEND-123',
            vendor_name='Vendor',
            buyer_id='BUYER-456',
            buyer_name='Buyer',
            payment_terms='Net 30',
            delivery_terms='FOB',
            inspection_required=True,
            quality_standards=['ISO 9001']
        )
        
        order = Order(
            order_id='ORD-TEST',
            customer_id='CUST-123',
            items=[],
            delivery_address={},
            retail_data=retail_data
        )
        
        time = processor.calculate_fulfillment_time(order)
        
        # Base 240 + inspection 120 + QC 60 = 420 minutes
        assert time == 420


class TestFoodDeliveryProcessor:
    """Test food delivery order processor"""
    
    def test_food_delivery_priority(self):
        """Test food delivery orders get high priority"""
        processor = FoodDeliveryOrderProcessor()
        
        food_data = FoodDeliveryOrderData(
            restaurant_id='REST-123',
            restaurant_name='Restaurant',
            restaurant_address={},
            restaurant_phone='555-0100',
            customer_phone='555-0200',
            preparation_time_minutes=25
        )
        
        order = Order(
            order_id='ORD-TEST',
            customer_id='CUST-123',
            items=[],
            delivery_address={},
            food_delivery_data=food_data
        )
        
        processed_order = processor.process(order)
        
        assert processed_order.priority.value == Priority.HIGH.value
        assert processed_order.estimated_delivery_date is not None
    
    def test_food_delivery_time_calculation(self):
        """Test food delivery time includes prep + delivery"""
        processor = FoodDeliveryOrderProcessor()
        
        food_data = FoodDeliveryOrderData(
            restaurant_id='REST-123',
            restaurant_name='Restaurant',
            restaurant_address={},
            restaurant_phone='555-0100',
            customer_phone='555-0200',
            preparation_time_minutes=30
        )
        
        order = Order(
            order_id='ORD-TEST',
            customer_id='CUST-123',
            items=[],
            delivery_address={},
            food_delivery_data=food_data
        )
        
        time = processor.calculate_fulfillment_time(order)
        
        # Prep 30 + delivery 20 = 50 minutes
        assert time == 50


class TestProcessorFactory:
    """Test industry processor factory"""
    
    def test_get_processor_for_ecommerce(self):
        """Test factory returns correct processor for e-commerce"""
        processor = IndustryOrderProcessorFactory.get_processor(IndustryCategory.ECOMMERCE)
        assert isinstance(processor, EcommerceOrderProcessor)
    
    def test_get_processor_for_retail(self):
        """Test factory returns correct processor for retail"""
        processor = IndustryOrderProcessorFactory.get_processor(IndustryCategory.RETAIL)
        assert isinstance(processor, RetailOrderProcessor)
        assert processor.industry_category == IndustryCategory.RETAIL
    
    def test_get_processor_for_order_type(self):
        """Test factory can determine processor from order type"""
        processor = IndustryOrderProcessorFactory.get_processor_for_order_type(
            OrderType.FOOD_DELIVERY_CUSTOMER
        )
        assert isinstance(processor, FoodDeliveryOrderProcessor)
        assert processor.industry_category == IndustryCategory.FOOD_DELIVERY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

