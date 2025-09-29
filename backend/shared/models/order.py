"""
Order Data Models
"""

from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from decimal import Decimal

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PICKED = "picked"
    PACKED = "packed"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

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
        data['unit_price'] = float(self.unit_price)
        data['total_price'] = float(self.total_price)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        """Create OrderItem from dictionary"""
        data['unit_price'] = Decimal(str(data['unit_price']))
        data['total_price'] = Decimal(str(data['total_price']))
        return cls(**data)

@dataclass
class Order:
    """Order model"""
    order_id: str
    customer_id: str
    status: OrderStatus = OrderStatus.PENDING
    priority: Priority = Priority.NORMAL
    
    # Order details
    items: List[OrderItem] = None
    subtotal: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    shipping_cost: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
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
    
    # Metadata
    source: str = "web"  # web, mobile, api, phone
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
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
    
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
        old_status = self.status
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
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['payment_status'] = self.payment_status.value
        
        # Convert Decimal to float
        for field in ['subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total_amount']:
            if data[field]:
                data[field] = float(data[field])
        
        # Convert items
        if self.items:
            data['items'] = [item.to_dict() for item in self.items]
        
        # Convert datetime objects to timestamps
        datetime_fields = [
            'created_at', 'updated_at', 'shipped_at', 'delivered_at',
            'requested_delivery_date', 'estimated_delivery_date', 'actual_delivery_date'
        ]
        for field in datetime_fields:
            if data[field]:
                data[field] = data[field].timestamp()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Create Order from Firestore document"""
        # Convert enums
        if 'status' in data:
            data['status'] = OrderStatus(data['status'])
        if 'priority' in data:
            data['priority'] = Priority(data['priority'])
        if 'payment_status' in data:
            data['payment_status'] = PaymentStatus(data['payment_status'])
        
        # Convert Decimal fields
        decimal_fields = ['subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total_amount']
        for field in decimal_fields:
            if data.get(field) is not None:
                data[field] = Decimal(str(data[field]))
        
        # Convert items
        if 'items' in data and data['items']:
            data['items'] = [OrderItem.from_dict(item_data) for item_data in data['items']]
        
        # Convert datetime fields
        datetime_fields = [
            'created_at', 'updated_at', 'shipped_at', 'delivered_at',
            'requested_delivery_date', 'estimated_delivery_date', 'actual_delivery_date'
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
            OrderStatus.PROCESSING
        ]
        return self.status in cancellable_statuses