"""
Order Data Models
"""

from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from decimal import Decimal

# Import industry-specific types
from .industry_types import OrderType, OrderSource, IndustryCategory
from .industry_data import (
    EcommerceOrderData,
    RetailOrderData,
    FoodDeliveryOrderData,
    ManufacturingOrderData,
    ThirdPartyOrderData,
)


class OrderStatus(Enum):
    """Order status enumeration"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    
    # E-commerce & General statuses
    PICKED = "picked"
    PACKED = "packed"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    
    # Retail-specific statuses
    INSPECTED = "inspected"
    APPROVED = "approved"
    RECEIVED = "received"
    INVENTORIED = "inventoried"
    
    # Food delivery-specific statuses
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    
    # Manufacturing-specific statuses
    MATERIALS_ALLOCATED = "materials_allocated"
    PRODUCTION_STARTED = "production_started"
    PRODUCTION_IN_PROGRESS = "production_in_progress"
    PRODUCTION_COMPLETED = "production_completed"
    QUALITY_CHECKED = "quality_checked"
    QUALITY_FAILED = "quality_failed"
    PACKAGED = "packaged"


class PaymentStatus(Enum):
    """Payment status enumeration"""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class Priority(Enum):
    """Order priority enumeration"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class OrderItem:
    """Order line item model"""

    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    warehouse_id: Optional[str] = None
    batch_number: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Calculate total price"""
        self.total_price = self.unit_price * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = asdict(self)
        data["unit_price"] = float(self.unit_price)
        data["total_price"] = float(self.total_price)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderItem":
        """Create OrderItem from dictionary"""
        data["unit_price"] = Decimal(str(data["unit_price"]))
        data["total_price"] = Decimal(str(data["total_price"]))
        return cls(**data)


@dataclass
class Order:
    """Enhanced order model with industry-specific support"""

    order_id: str
    customer_id: str
    status: OrderStatus = OrderStatus.PENDING
    priority: Priority = Priority.NORMAL

    # Industry Classification (NEW)
    order_type: Optional[OrderType] = None
    order_source: Optional[OrderSource] = OrderSource.WEB
    industry_category: Optional[IndustryCategory] = None

    # Order details
    items: List[OrderItem] = None
    subtotal: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    shipping_cost: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")

    # Delivery information
    delivery_address: Dict[str, str] = None
    delivery_instructions: Optional[str] = None
    requested_delivery_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None

    # Payment information
    payment_method: Optional[str] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_reference: Optional[str] = None

    # Fulfillment information
    warehouse_id: Optional[str] = None
    assigned_driver: Optional[str] = None
    route_id: Optional[str] = None
    tracking_number: Optional[str] = None

    # Industry-Specific Data (NEW - Conditional based on order_type)
    ecommerce_data: Optional[EcommerceOrderData] = None
    retail_data: Optional[RetailOrderData] = None
    food_delivery_data: Optional[FoodDeliveryOrderData] = None
    manufacturing_data: Optional[ManufacturingOrderData] = None
    third_party_data: Optional[ThirdPartyOrderData] = None

    # Metadata
    source: str = "web"  # Deprecated: Use order_source instead
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default timestamps and calculate totals"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        if self.items is None:
            self.items = []

        self.calculate_totals()

    def calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.total_amount = (
            self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        )

    def add_item(self, item: OrderItem):
        """Add item to order"""
        self.items.append(item)
        self.calculate_totals()
        self.updated_at = datetime.utcnow()

    def remove_item(self, sku: str):
        """Remove item from order"""
        self.items = [item for item in self.items if item.sku != sku]
        self.calculate_totals()
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: OrderStatus):
        """Update order status with timestamp tracking"""
        old_status = self.status  # noqa: F841
        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Set specific timestamps based on status
        if new_status == OrderStatus.SHIPPED:
            self.shipped_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            self.delivered_at = datetime.utcnow()
            self.actual_delivery_date = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = asdict(self)

        # Convert enums to strings
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        data["payment_status"] = self.payment_status.value
        
        # Convert industry enums to strings (NEW)
        if self.order_type:
            data["order_type"] = self.order_type.value
        if self.order_source:
            data["order_source"] = self.order_source.value
        if self.industry_category:
            data["industry_category"] = self.industry_category.value

        # Convert Decimal to float
        for field in [
            "subtotal",
            "tax_amount",
            "shipping_cost",
            "discount_amount",
            "total_amount",
        ]:
            if data[field]:
                data[field] = float(data[field])

        # Convert items
        if self.items:
            data["items"] = [item.to_dict() for item in self.items]
        
        # Convert industry-specific data (NEW)
        if self.ecommerce_data:
            data["ecommerce_data"] = self.ecommerce_data.to_dict()
        if self.retail_data:
            data["retail_data"] = self.retail_data.to_dict()
        if self.food_delivery_data:
            data["food_delivery_data"] = self.food_delivery_data.to_dict()
        if self.manufacturing_data:
            data["manufacturing_data"] = self.manufacturing_data.to_dict()
        if self.third_party_data:
            data["third_party_data"] = self.third_party_data.to_dict()

        # Convert datetime objects to timestamps
        datetime_fields = [
            "created_at",
            "updated_at",
            "shipped_at",
            "delivered_at",
            "requested_delivery_date",
            "estimated_delivery_date",
            "actual_delivery_date",
        ]
        for field in datetime_fields:
            if data[field]:
                data[field] = data[field].timestamp()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        """Create Order from Firestore document"""
        # Convert enums
        if "status" in data:
            data["status"] = OrderStatus(data["status"])
        if "priority" in data:
            data["priority"] = Priority(data["priority"])
        if "payment_status" in data:
            data["payment_status"] = PaymentStatus(data["payment_status"])
        
        # Convert industry enums (NEW)
        if data.get("order_type"):
            data["order_type"] = OrderType(data["order_type"])
        if data.get("order_source"):
            data["order_source"] = OrderSource(data["order_source"])
        if data.get("industry_category"):
            data["industry_category"] = IndustryCategory(data["industry_category"])

        # Convert Decimal fields
        decimal_fields = [
            "subtotal",
            "tax_amount",
            "shipping_cost",
            "discount_amount",
            "total_amount",
        ]
        for field in decimal_fields:
            if data.get(field) is not None:
                data[field] = Decimal(str(data[field]))

        # Convert items
        if "items" in data and data["items"]:
            data["items"] = [
                OrderItem.from_dict(item_data) for item_data in data["items"]
            ]
        
        # Convert industry-specific data (NEW)
        if data.get("ecommerce_data"):
            data["ecommerce_data"] = EcommerceOrderData.from_dict(data["ecommerce_data"])
        if data.get("retail_data"):
            data["retail_data"] = RetailOrderData.from_dict(data["retail_data"])
        if data.get("food_delivery_data"):
            data["food_delivery_data"] = FoodDeliveryOrderData.from_dict(data["food_delivery_data"])
        if data.get("manufacturing_data"):
            data["manufacturing_data"] = ManufacturingOrderData.from_dict(data["manufacturing_data"])
        if data.get("third_party_data"):
            data["third_party_data"] = ThirdPartyOrderData.from_dict(data["third_party_data"])

        # Convert datetime fields
        datetime_fields = [
            "created_at",
            "updated_at",
            "shipped_at",
            "delivered_at",
            "requested_delivery_date",
            "estimated_delivery_date",
            "actual_delivery_date",
        ]
        for field in datetime_fields:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])

        return cls(**data)

    @property
    def total_items(self) -> int:
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items)

    @property
    def total_weight(self) -> float:
        """Calculate total weight (would need product weights)"""
        # This would require looking up product weights
        return 0.0

    @property
    def is_deliverable(self) -> bool:
        """Check if order is ready for delivery"""
        return self.status in [OrderStatus.PACKED, OrderStatus.SHIPPED]

    @property
    def days_since_created(self) -> int:
        """Get number of days since order was created"""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0

    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        cancellable_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
        ]
        return self.status in cancellable_statuses
    
    # ==================== Industry-Specific Methods (NEW) ====================
    
    def get_industry_display_name(self) -> str:
        """Get human-readable industry category name"""
        if not self.industry_category:
            return "General"
        
        industry_names = {
            IndustryCategory.ECOMMERCE: "E-commerce",
            IndustryCategory.RETAIL: "Retail Distribution",
            IndustryCategory.FOOD_DELIVERY: "Food Delivery",
            IndustryCategory.MANUFACTURING: "Manufacturing",
            IndustryCategory.THIRD_PARTY_LOGISTICS: "3PL Services",
        }
        return industry_names.get(self.industry_category, "General")
    
    def get_order_type_display_name(self) -> str:
        """Get human-readable order type name"""
        if not self.order_type:
            return "Standard Order"
        
        type_names = {
            OrderType.ECOMMERCE_DIRECT: "Direct E-commerce",
            OrderType.ECOMMERCE_MARKETPLACE: "Marketplace Order",
            OrderType.ECOMMERCE_SUBSCRIPTION: "Subscription Order",
            OrderType.RETAIL_PURCHASE_ORDER: "Purchase Order",
            OrderType.RETAIL_TRANSFER: "Store Transfer",
            OrderType.RETAIL_RESTOCK: "Restocking Order",
            OrderType.FOOD_DELIVERY_CUSTOMER: "Food Delivery",
            OrderType.FOOD_DELIVERY_CATERING: "Catering Order",
            OrderType.FOOD_DELIVERY_GROCERY: "Grocery Delivery",
            OrderType.MANUFACTURING_PRODUCTION: "Production Order",
            OrderType.MANUFACTURING_RAW_MATERIALS: "Raw Materials",
            OrderType.MANUFACTURING_FINISHED_GOODS: "Finished Goods",
            OrderType.THIRD_PARTY_FULFILLMENT: "3PL Fulfillment",
            OrderType.THIRD_PARTY_STORAGE: "3PL Storage",
            OrderType.THIRD_PARTY_CROSS_DOCK: "Cross-Dock",
        }
        return type_names.get(self.order_type, "Standard Order")
    
    def get_industry_specific_data(self) -> Optional[Any]:
        """Get the populated industry-specific data object"""
        if self.ecommerce_data:
            return self.ecommerce_data
        elif self.retail_data:
            return self.retail_data
        elif self.food_delivery_data:
            return self.food_delivery_data
        elif self.manufacturing_data:
            return self.manufacturing_data
        elif self.third_party_data:
            return self.third_party_data
        return None
    
    def has_industry_data(self) -> bool:
        """Check if order has industry-specific data"""
        return self.get_industry_specific_data() is not None
    
    @property
    def is_time_sensitive(self) -> bool:
        """Check if order has time-sensitive delivery requirements"""
        # Food delivery orders are always time-sensitive
        if self.industry_category == IndustryCategory.FOOD_DELIVERY:
            return True
        
        # Manufacturing with production schedules
        if self.industry_category == IndustryCategory.MANUFACTURING:
            if self.manufacturing_data and self.manufacturing_data.production_start_date:
                return True
        
        # Check if has narrow delivery window
        if self.requested_delivery_date and self.estimated_delivery_date:
            time_diff = abs((self.estimated_delivery_date - self.requested_delivery_date).total_seconds())
            return time_diff < 7200  # Less than 2 hours window
        
        return False
    
    @property
    def requires_special_handling(self) -> bool:
        """Check if order requires special handling"""
        # Food safety requirements
        if self.food_delivery_data:
            if self.food_delivery_data.temperature_requirements:
                return True
            if self.food_delivery_data.allergen_info:
                return True
        
        # Retail compliance requirements
        if self.retail_data:
            if self.retail_data.hazmat_classification:
                return True
            if self.retail_data.inspection_required:
                return True
        
        # Manufacturing quality control
        if self.manufacturing_data:
            if self.manufacturing_data.quality_control_points:
                return True
        
        # 3PL special handling
        if self.third_party_data:
            if self.third_party_data.special_handling_required:
                return True
        
        return False
