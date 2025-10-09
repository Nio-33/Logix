"""
Industry-Specific Order Processors
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from shared.models import (
    Order,
    OrderType,
    OrderSource,
    IndustryCategory,
    OrderStatus,
    EcommerceOrderData,
    RetailOrderData,
    FoodDeliveryOrderData,
    ManufacturingOrderData,
    ThirdPartyOrderData,
    IndustryStatusWorkflow,
    IndustryValidator,
)

logger = logging.getLogger(__name__)


class BaseIndustryProcessor(ABC):
    """Base class for industry-specific order processing"""
    
    def __init__(self, industry_category: IndustryCategory):
        self.industry_category = industry_category
    
    @abstractmethod
    def validate(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data for industry-specific requirements"""
        pass
    
    @abstractmethod
    def process(self, order: Order) -> Order:
        """Process order with industry-specific logic"""
        pass
    
    @abstractmethod
    def calculate_fulfillment_time(self, order: Order) -> int:
        """Calculate estimated fulfillment time in minutes"""
        pass
    
    def enrich_order_data(self, order: Order) -> Order:
        """Enrich order with calculated fields and defaults"""
        return order


class EcommerceOrderProcessor(BaseIndustryProcessor):
    """E-commerce order processing logic"""
    
    def __init__(self):
        super().__init__(IndustryCategory.ECOMMERCE)
    
    def validate(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate e-commerce order data"""
        errors = []
        warnings = []
        
        # Validate ecommerce_data exists
        if not order_data.get('ecommerce_data'):
            errors.append("E-commerce orders require ecommerce_data")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        ecom_data = order_data['ecommerce_data']
        
        # Required fields
        if not ecom_data.get('platform_order_id'):
            errors.append("platform_order_id is required for e-commerce orders")
        if not ecom_data.get('platform_name'):
            errors.append("platform_name is required for e-commerce orders")
        if not ecom_data.get('customer_email'):
            errors.append("customer_email is required for e-commerce orders")
        
        # Warnings for optional but recommended fields
        if not ecom_data.get('customer_phone'):
            warnings.append("customer_phone is recommended for delivery coordination")
        if not ecom_data.get('customer_segment'):
            warnings.append("customer_segment helps with order prioritization")
        
        # Validate subscription data if present
        if ecom_data.get('is_subscription'):
            if not ecom_data.get('subscription_id'):
                errors.append("subscription_id required for subscription orders")
            if not ecom_data.get('next_delivery_date'):
                warnings.append("next_delivery_date recommended for subscription orders")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def process(self, order: Order) -> Order:
        """Process e-commerce order"""
        logger.info(f"Processing e-commerce order: {order.order_id}")
        
        # Set industry category
        order.industry_category = IndustryCategory.ECOMMERCE
        
        # Determine priority based on customer segment
        if order.ecommerce_data:
            segment = order.ecommerce_data.customer_segment
            if segment in ['VIP', 'loyal']:
                from shared.models.order import Priority
                order.priority = Priority.HIGH
        
        # Set initial status
        if not order.status or order.status == OrderStatus.PENDING:
            order.status = IndustryStatusWorkflow.get_initial_status(order.order_type)
        
        return order
    
    def calculate_fulfillment_time(self, order: Order) -> int:
        """Calculate estimated fulfillment time for e-commerce order"""
        base_time = 30  # 30 minutes base processing time
        
        # Add time based on number of items
        item_time = len(order.items) * 5  # 5 minutes per item
        
        # Priority multiplier
        from shared.models.order import Priority
        priority_multipliers = {
            Priority.URGENT: 0.5,
            Priority.HIGH: 0.75,
            Priority.NORMAL: 1.0,
            Priority.LOW: 1.5,
        }
        multiplier = priority_multipliers.get(order.priority, 1.0)
        
        total_time = int((base_time + item_time) * multiplier)
        
        logger.info(f"E-commerce order {order.order_id} estimated fulfillment: {total_time} minutes")
        return total_time


class RetailOrderProcessor(BaseIndustryProcessor):
    """Retail distribution order processing logic"""
    
    def __init__(self):
        super().__init__(IndustryCategory.RETAIL)
    
    def validate(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate retail order data"""
        errors = []
        warnings = []
        
        if not order_data.get('retail_data'):
            errors.append("Retail orders require retail_data")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        retail_data = order_data['retail_data']
        
        # Required fields
        required_fields = ['po_number', 'vendor_id', 'vendor_name', 'payment_terms', 'delivery_terms']
        for field in required_fields:
            if not retail_data.get(field):
                errors.append(f"{field} is required for retail orders")
        
        # Compliance validation
        if retail_data.get('hazmat_classification'):
            if not retail_data.get('safety_data_sheets_required'):
                warnings.append("Hazmat orders typically require safety data sheets")
        
        # Inspection requirements
        if retail_data.get('quality_standards') and not retail_data.get('inspection_required'):
            warnings.append("Quality standards specified but inspection not required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def process(self, order: Order) -> Order:
        """Process retail order"""
        logger.info(f"Processing retail order: {order.order_id}")
        
        order.industry_category = IndustryCategory.RETAIL
        
        # Set priority based on delivery terms
        if order.retail_data:
            from shared.models.order import Priority
            if 'URGENT' in order.retail_data.delivery_terms.upper():
                order.priority = Priority.URGENT
            elif 'EXPEDITED' in order.retail_data.delivery_terms.upper():
                order.priority = Priority.HIGH
        
        # Set initial status
        if not order.status or order.status == OrderStatus.PENDING:
            order.status = IndustryStatusWorkflow.get_initial_status(order.order_type)
        
        return order
    
    def calculate_fulfillment_time(self, order: Order) -> int:
        """Calculate estimated fulfillment time for retail order"""
        base_time = 240  # 4 hours base (longer for B2B)
        
        # Inspection adds time
        if order.retail_data and order.retail_data.inspection_required:
            base_time += 120  # Add 2 hours for inspection
        
        # Quality control adds time
        if order.retail_data and order.retail_data.quality_standards:
            base_time += 60  # Add 1 hour for QC
        
        logger.info(f"Retail order {order.order_id} estimated fulfillment: {base_time} minutes")
        return base_time


class FoodDeliveryOrderProcessor(BaseIndustryProcessor):
    """Food delivery order processing logic"""
    
    def __init__(self):
        super().__init__(IndustryCategory.FOOD_DELIVERY)
    
    def validate(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate food delivery order data"""
        errors = []
        warnings = []
        
        if not order_data.get('food_delivery_data'):
            errors.append("Food delivery orders require food_delivery_data")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        food_data = order_data['food_delivery_data']
        
        # Required fields
        required_fields = ['restaurant_id', 'restaurant_name', 'customer_phone', 'preparation_time_minutes']
        for field in required_fields:
            if not food_data.get(field):
                errors.append(f"{field} is required for food delivery orders")
        
        # Time validation
        if food_data.get('delivery_window_start') and food_data.get('delivery_window_end'):
            # Validate delivery window is reasonable
            if isinstance(food_data['delivery_window_start'], datetime):
                window_duration = (food_data['delivery_window_end'] - food_data['delivery_window_start']).total_seconds()
                if window_duration < 900:  # Less than 15 minutes
                    warnings.append("Delivery window is very tight (< 15 minutes)")
                elif window_duration > 3600:  # More than 1 hour
                    warnings.append("Delivery window is quite wide (> 1 hour)")
        
        # Food safety warnings
        if not food_data.get('temperature_requirements'):
            warnings.append("Temperature requirements not specified")
        if food_data.get('allergen_info') and not food_data.get('special_dietary_requirements'):
            warnings.append("Allergen info provided but dietary requirements not specified")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def process(self, order: Order) -> Order:
        """Process food delivery order"""
        logger.info(f"Processing food delivery order: {order.order_id}")
        
        order.industry_category = IndustryCategory.FOOD_DELIVERY
        
        # All food orders are high priority (time-sensitive)
        from shared.models.order import Priority
        order.priority = Priority.HIGH
        
        # Calculate estimated delivery time based on prep time
        if order.food_delivery_data:
            prep_time = order.food_delivery_data.preparation_time_minutes
            # Estimated delivery = prep time + 20 minutes delivery
            estimated_total = prep_time + 20
            order.estimated_delivery_date = datetime.utcnow() + timedelta(minutes=estimated_total)
        
        # Set initial status
        if not order.status or order.status == OrderStatus.PENDING:
            order.status = IndustryStatusWorkflow.get_initial_status(order.order_type)
        
        return order
    
    def calculate_fulfillment_time(self, order: Order) -> int:
        """Calculate estimated fulfillment time for food delivery order"""
        if order.food_delivery_data:
            prep_time = order.food_delivery_data.preparation_time_minutes
            delivery_time = 20  # Average 20 minutes delivery
            total_time = prep_time + delivery_time
        else:
            total_time = 45  # Default 45 minutes total
        
        logger.info(f"Food delivery order {order.order_id} estimated fulfillment: {total_time} minutes")
        return total_time


class ManufacturingOrderProcessor(BaseIndustryProcessor):
    """Manufacturing order processing logic"""
    
    def __init__(self):
        super().__init__(IndustryCategory.MANUFACTURING)
    
    def validate(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate manufacturing order data"""
        errors = []
        warnings = []
        
        if not order_data.get('manufacturing_data'):
            errors.append("Manufacturing orders require manufacturing_data")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        mfg_data = order_data['manufacturing_data']
        
        # Required fields
        if not mfg_data.get('production_order_id'):
            errors.append("production_order_id is required for manufacturing orders")
        
        # Production schedule validation
        if mfg_data.get('production_start_date') and mfg_data.get('production_end_date'):
            if isinstance(mfg_data['production_start_date'], datetime):
                if mfg_data['production_end_date'] < mfg_data['production_start_date']:
                    errors.append("Production end date cannot be before start date")
        
        # Quality control warnings
        if not mfg_data.get('quality_control_points'):
            warnings.append("No quality control points specified")
        if not mfg_data.get('inspection_requirements'):
            warnings.append("No inspection requirements specified")
        
        # Traceability
        if mfg_data.get('traceability_required') and not mfg_data.get('production_batch_number'):
            warnings.append("Traceability required but no batch number specified")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def process(self, order: Order) -> Order:
        """Process manufacturing order"""
        logger.info(f"Processing manufacturing order: {order.order_id}")
        
        order.industry_category = IndustryCategory.MANUFACTURING
        
        # Manufacturing orders are typically high priority
        from shared.models.order import Priority
        order.priority = Priority.HIGH
        
        # Set initial status
        if not order.status or order.status == OrderStatus.PENDING:
            order.status = IndustryStatusWorkflow.get_initial_status(order.order_type)
        
        return order
    
    def calculate_fulfillment_time(self, order: Order) -> int:
        """Calculate estimated fulfillment time for manufacturing order"""
        if order.manufacturing_data:
            if order.manufacturing_data.production_start_date and order.manufacturing_data.production_end_date:
                duration = (order.manufacturing_data.production_end_date - order.manufacturing_data.production_start_date).total_seconds() / 60
                return int(duration)
        
        # Default: 24 hours for manufacturing
        logger.info(f"Manufacturing order {order.order_id} using default fulfillment time")
        return 1440  # 24 hours


class ThirdPartyOrderProcessor(BaseIndustryProcessor):
    """3PL order processing logic"""
    
    def __init__(self):
        super().__init__(IndustryCategory.THIRD_PARTY_LOGISTICS)
    
    def validate(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 3PL order data"""
        errors = []
        warnings = []
        
        if not order_data.get('third_party_data'):
            errors.append("3PL orders require third_party_data")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        tpl_data = order_data['third_party_data']
        
        # Required fields
        required_fields = ['client_id', 'client_name', 'service_type', 'fulfillment_center', 'billing_model']
        for field in required_fields:
            if not tpl_data.get(field):
                errors.append(f"{field} is required for 3PL orders")
        
        # SLA validation
        if tpl_data.get('sla_delivery_time') and tpl_data['sla_delivery_time'] < 60:
            warnings.append("SLA delivery time less than 1 hour may be difficult to meet")
        
        # Billing validation
        if tpl_data.get('billing_model') == 'per_order' and not tpl_data.get('billing_rate'):
            errors.append("billing_rate required for per_order billing model")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def process(self, order: Order) -> Order:
        """Process 3PL order"""
        logger.info(f"Processing 3PL order: {order.order_id}")
        
        order.industry_category = IndustryCategory.THIRD_PARTY_LOGISTICS
        
        # Set priority based on SLA
        if order.third_party_data and order.third_party_data.sla_delivery_time:
            from shared.models.order import Priority
            sla_hours = order.third_party_data.sla_delivery_time / 60
            if sla_hours < 4:
                order.priority = Priority.URGENT
            elif sla_hours < 24:
                order.priority = Priority.HIGH
            else:
                order.priority = Priority.NORMAL
        
        # Set initial status
        if not order.status or order.status == OrderStatus.PENDING:
            order.status = IndustryStatusWorkflow.get_initial_status(order.order_type)
        
        return order
    
    def calculate_fulfillment_time(self, order: Order) -> int:
        """Calculate estimated fulfillment time for 3PL order"""
        if order.third_party_data and order.third_party_data.sla_delivery_time:
            # Use SLA time
            return order.third_party_data.sla_delivery_time
        
        # Default based on service type
        if order.third_party_data:
            service_type = order.third_party_data.service_type
            service_times = {
                'fulfillment': 240,      # 4 hours
                'cross_dock': 120,       # 2 hours
                'storage': 60,           # 1 hour
                'returns': 180,          # 3 hours
            }
            return service_times.get(service_type, 240)
        
        return 240  # Default 4 hours


class ManufacturingOrderProcessor(BaseIndustryProcessor):
    """Manufacturing order processing logic"""
    
    def __init__(self):
        super().__init__(IndustryCategory.MANUFACTURING)
    
    def validate(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate manufacturing order data"""
        errors = []
        warnings = []
        
        if not order_data.get('manufacturing_data'):
            errors.append("Manufacturing orders require manufacturing_data")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        mfg_data = order_data['manufacturing_data']
        
        if not mfg_data.get('production_order_id'):
            errors.append("production_order_id is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def process(self, order: Order) -> Order:
        """Process manufacturing order"""
        logger.info(f"Processing manufacturing order: {order.order_id}")
        
        order.industry_category = IndustryCategory.MANUFACTURING
        
        from shared.models.order import Priority
        order.priority = Priority.HIGH
        
        if not order.status or order.status == OrderStatus.PENDING:
            order.status = IndustryStatusWorkflow.get_initial_status(order.order_type)
        
        return order
    
    def calculate_fulfillment_time(self, order: Order) -> int:
        """Calculate estimated fulfillment time for manufacturing order"""
        return 1440  # 24 hours default


class IndustryOrderProcessorFactory:
    """Factory for creating industry-specific processors"""
    
    _processors = {
        IndustryCategory.ECOMMERCE: EcommerceOrderProcessor,
        IndustryCategory.RETAIL: RetailOrderProcessor,
        IndustryCategory.FOOD_DELIVERY: FoodDeliveryOrderProcessor,
        IndustryCategory.MANUFACTURING: ManufacturingOrderProcessor,
        IndustryCategory.THIRD_PARTY_LOGISTICS: ThirdPartyOrderProcessor,
    }
    
    @classmethod
    def get_processor(cls, industry_category: IndustryCategory) -> BaseIndustryProcessor:
        """Get appropriate processor for industry category"""
        processor_class = cls._processors.get(industry_category)
        if not processor_class:
            logger.warning(f"No processor found for {industry_category}, using e-commerce processor")
            processor_class = EcommerceOrderProcessor
        
        return processor_class()
    
    @classmethod
    def get_processor_for_order_type(cls, order_type: OrderType) -> BaseIndustryProcessor:
        """Get processor based on order type"""
        # Map order types to industry categories
        type_to_category = {
            OrderType.ECOMMERCE_DIRECT: IndustryCategory.ECOMMERCE,
            OrderType.ECOMMERCE_MARKETPLACE: IndustryCategory.ECOMMERCE,
            OrderType.ECOMMERCE_SUBSCRIPTION: IndustryCategory.ECOMMERCE,
            OrderType.ECOMMERCE_B2B: IndustryCategory.ECOMMERCE,
            
            OrderType.RETAIL_PURCHASE_ORDER: IndustryCategory.RETAIL,
            OrderType.RETAIL_TRANSFER: IndustryCategory.RETAIL,
            OrderType.RETAIL_RESTOCK: IndustryCategory.RETAIL,
            OrderType.RETAIL_RETURN: IndustryCategory.RETAIL,
            
            OrderType.FOOD_DELIVERY_CUSTOMER: IndustryCategory.FOOD_DELIVERY,
            OrderType.FOOD_DELIVERY_CATERING: IndustryCategory.FOOD_DELIVERY,
            OrderType.FOOD_DELIVERY_GROCERY: IndustryCategory.FOOD_DELIVERY,
            OrderType.FOOD_DELIVERY_PICKUP: IndustryCategory.FOOD_DELIVERY,
            
            OrderType.MANUFACTURING_PRODUCTION: IndustryCategory.MANUFACTURING,
            OrderType.MANUFACTURING_RAW_MATERIALS: IndustryCategory.MANUFACTURING,
            OrderType.MANUFACTURING_FINISHED_GOODS: IndustryCategory.MANUFACTURING,
            OrderType.MANUFACTURING_TRANSFER: IndustryCategory.MANUFACTURING,
            
            OrderType.THIRD_PARTY_FULFILLMENT: IndustryCategory.THIRD_PARTY_LOGISTICS,
            OrderType.THIRD_PARTY_STORAGE: IndustryCategory.THIRD_PARTY_LOGISTICS,
            OrderType.THIRD_PARTY_CROSS_DOCK: IndustryCategory.THIRD_PARTY_LOGISTICS,
            OrderType.THIRD_PARTY_RETURNS: IndustryCategory.THIRD_PARTY_LOGISTICS,
        }
        
        category = type_to_category.get(order_type, IndustryCategory.ECOMMERCE)
        return cls.get_processor(category)

