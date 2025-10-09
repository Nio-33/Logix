"""
Industry-Specific Workflow and Status Management
"""

from typing import List, Dict, Optional
from .order import OrderStatus
from .industry_types import OrderType, IndustryCategory


class IndustryStatusWorkflow:
    """Industry-specific status workflows"""
    
    # Define allowed status transitions for each industry
    WORKFLOWS = {
        # E-commerce Workflows
        OrderType.ECOMMERCE_DIRECT: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.PICKED,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
        ],
        
        OrderType.ECOMMERCE_MARKETPLACE: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.PICKED,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
        ],
        
        OrderType.ECOMMERCE_SUBSCRIPTION: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.PICKED,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
        ],
        
        # Retail Distribution Workflows
        OrderType.RETAIL_PURCHASE_ORDER: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.INSPECTED,
            OrderStatus.APPROVED,
            OrderStatus.RECEIVED,
            OrderStatus.INVENTORIED,
        ],
        
        OrderType.RETAIL_TRANSFER: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PICKED,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.RECEIVED,
            OrderStatus.INVENTORIED,
        ],
        
        OrderType.RETAIL_RESTOCK: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.PICKED,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.RECEIVED,
            OrderStatus.INVENTORIED,
        ],
        
        # Food Delivery Workflows
        OrderType.FOOD_DELIVERY_CUSTOMER: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.PICKED_UP,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
        ],
        
        OrderType.FOOD_DELIVERY_CATERING: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.PICKED_UP,
            OrderStatus.DELIVERED,
        ],
        
        OrderType.FOOD_DELIVERY_PICKUP: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.PICKED_UP,
        ],
        
        # Manufacturing Workflows
        OrderType.MANUFACTURING_PRODUCTION: [
            OrderStatus.PENDING,
            OrderStatus.APPROVED,
            OrderStatus.MATERIALS_ALLOCATED,
            OrderStatus.PRODUCTION_STARTED,
            OrderStatus.PRODUCTION_IN_PROGRESS,
            OrderStatus.PRODUCTION_COMPLETED,
            OrderStatus.QUALITY_CHECKED,
            OrderStatus.PACKAGED,
            OrderStatus.SHIPPED,
        ],
        
        OrderType.MANUFACTURING_RAW_MATERIALS: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.SHIPPED,
            OrderStatus.RECEIVED,
            OrderStatus.INSPECTED,
            OrderStatus.APPROVED,
            OrderStatus.INVENTORIED,
        ],
        
        OrderType.MANUFACTURING_FINISHED_GOODS: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PICKED,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ],
        
        # 3PL Workflows
        OrderType.THIRD_PARTY_FULFILLMENT: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.RECEIVED,
            OrderStatus.INVENTORIED,
            OrderStatus.PROCESSING,
            OrderStatus.PICKED,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ],
        
        OrderType.THIRD_PARTY_CROSS_DOCK: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.RECEIVED,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ],
        
        OrderType.THIRD_PARTY_STORAGE: [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.RECEIVED,
            OrderStatus.INVENTORIED,
        ],
    }
    
    @classmethod
    def get_workflow(cls, order_type: OrderType) -> List[OrderStatus]:
        """Get status workflow for specific order type"""
        # Return specific workflow or default e-commerce workflow
        return cls.WORKFLOWS.get(
            order_type,
            cls.WORKFLOWS[OrderType.ECOMMERCE_DIRECT]
        )
    
    @classmethod
    def get_next_statuses(cls, current_status: OrderStatus, order_type: OrderType) -> List[OrderStatus]:
        """Get allowed next statuses from current status"""
        workflow = cls.get_workflow(order_type)
        
        try:
            current_index = workflow.index(current_status)
            # Can move to next status or skip to cancelled/returned
            next_statuses = []
            
            # Next status in workflow
            if current_index < len(workflow) - 1:
                next_statuses.append(workflow[current_index + 1])
            
            # Always allow cancel and return (if applicable)
            if current_status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
                next_statuses.append(OrderStatus.CANCELLED)
            
            if current_status == OrderStatus.DELIVERED:
                next_statuses.append(OrderStatus.RETURNED)
            
            return next_statuses
        except ValueError:
            # Current status not in workflow
            return []
    
    @classmethod
    def is_valid_transition(
        cls,
        current_status: OrderStatus,
        new_status: OrderStatus,
        order_type: OrderType
    ) -> bool:
        """Check if status transition is valid for order type"""
        allowed_next = cls.get_next_statuses(current_status, order_type)
        return new_status in allowed_next
    
    @classmethod
    def get_initial_status(cls, order_type: OrderType) -> OrderStatus:
        """Get initial status for order type"""
        workflow = cls.get_workflow(order_type)
        return workflow[0] if workflow else OrderStatus.PENDING
    
    @classmethod
    def get_completion_statuses(cls) -> List[OrderStatus]:
        """Get statuses that represent order completion"""
        return [
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
            OrderStatus.RETURNED,
            OrderStatus.INVENTORIED,  # For storage/receiving orders
            OrderStatus.PICKED_UP,     # For pickup orders
        ]
    
    @classmethod
    def is_completed(cls, status: OrderStatus) -> bool:
        """Check if order is in a completed state"""
        return status in cls.get_completion_statuses()


class IndustryValidator:
    """Validate industry-specific order data"""
    
    @classmethod
    def validate_order_type_data(cls, order_type: OrderType, order_data: Dict) -> Dict[str, List[str]]:
        """
        Validate that required industry-specific data is present
        Returns dict with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []
        
        if order_type in [
            OrderType.ECOMMERCE_DIRECT,
            OrderType.ECOMMERCE_MARKETPLACE,
            OrderType.ECOMMERCE_SUBSCRIPTION
        ]:
            if not order_data.get('ecommerce_data'):
                errors.append("E-commerce orders require ecommerce_data")
            else:
                ecom_data = order_data['ecommerce_data']
                if not ecom_data.get('platform_order_id'):
                    errors.append("E-commerce orders require platform_order_id")
                if not ecom_data.get('customer_email'):
                    errors.append("E-commerce orders require customer_email")
        
        elif order_type in [
            OrderType.RETAIL_PURCHASE_ORDER,
            OrderType.RETAIL_TRANSFER,
            OrderType.RETAIL_RESTOCK
        ]:
            if not order_data.get('retail_data'):
                errors.append("Retail orders require retail_data")
            else:
                retail_data = order_data['retail_data']
                if not retail_data.get('po_number'):
                    errors.append("Retail orders require po_number")
                if not retail_data.get('vendor_id'):
                    errors.append("Retail orders require vendor_id")
        
        elif order_type in [
            OrderType.FOOD_DELIVERY_CUSTOMER,
            OrderType.FOOD_DELIVERY_CATERING,
            OrderType.FOOD_DELIVERY_GROCERY
        ]:
            if not order_data.get('food_delivery_data'):
                errors.append("Food delivery orders require food_delivery_data")
            else:
                food_data = order_data['food_delivery_data']
                if not food_data.get('restaurant_id'):
                    errors.append("Food delivery orders require restaurant_id")
                if not food_data.get('customer_phone'):
                    errors.append("Food delivery orders require customer_phone")
                if not food_data.get('preparation_time_minutes'):
                    warnings.append("No preparation time specified, using default")
        
        elif order_type in [
            OrderType.MANUFACTURING_PRODUCTION,
            OrderType.MANUFACTURING_RAW_MATERIALS,
            OrderType.MANUFACTURING_FINISHED_GOODS
        ]:
            if not order_data.get('manufacturing_data'):
                errors.append("Manufacturing orders require manufacturing_data")
            else:
                mfg_data = order_data['manufacturing_data']
                if not mfg_data.get('production_order_id'):
                    errors.append("Manufacturing orders require production_order_id")
        
        elif order_type in [
            OrderType.THIRD_PARTY_FULFILLMENT,
            OrderType.THIRD_PARTY_STORAGE,
            OrderType.THIRD_PARTY_CROSS_DOCK
        ]:
            if not order_data.get('third_party_data'):
                errors.append("3PL orders require third_party_data")
            else:
                tpl_data = order_data['third_party_data']
                if not tpl_data.get('client_id'):
                    errors.append("3PL orders require client_id")
                if not tpl_data.get('service_type'):
                    errors.append("3PL orders require service_type")
        
        return {"errors": errors, "warnings": warnings}
    
    @classmethod
    def get_required_fields(cls, order_type: OrderType) -> Dict[str, List[str]]:
        """Get required fields for specific order type"""
        
        base_required = ["order_id", "customer_id", "items", "delivery_address"]
        
        industry_required = {
            OrderType.ECOMMERCE_DIRECT: base_required + [
                "ecommerce_data.platform_order_id",
                "ecommerce_data.customer_email"
            ],
            OrderType.RETAIL_PURCHASE_ORDER: base_required + [
                "retail_data.po_number",
                "retail_data.vendor_id",
                "retail_data.payment_terms"
            ],
            OrderType.FOOD_DELIVERY_CUSTOMER: base_required + [
                "food_delivery_data.restaurant_id",
                "food_delivery_data.customer_phone",
                "food_delivery_data.preparation_time_minutes"
            ],
            OrderType.MANUFACTURING_PRODUCTION: base_required + [
                "manufacturing_data.production_order_id",
                "manufacturing_data.production_start_date"
            ],
            OrderType.THIRD_PARTY_FULFILLMENT: base_required + [
                "third_party_data.client_id",
                "third_party_data.service_type",
                "third_party_data.billing_model"
            ],
        }
        
        return {
            "required": industry_required.get(order_type, base_required),
            "optional": []
        }

