"""
Inventory Data Models
"""

from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from decimal import Decimal

class ProductStatus(Enum):
    """Product status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"

class InventoryStatus(Enum):
    """Inventory status enumeration"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    DAMAGED = "damaged"
    EXPIRED = "expired"

@dataclass
class Product:
    """Product master data model"""
    sku: str
    name: str
    description: str
    category: str
    brand: Optional[str] = None
    unit_price: Optional[Decimal] = None
    weight: Optional[float] = None  # kg
    dimensions: Optional[Dict[str, float]] = None  # length, width, height in cm
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    status: ProductStatus = ProductStatus.ACTIVE
    reorder_point: int = 10
    reorder_quantity: int = 50
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = None
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default timestamps"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = asdict(self)
        data['status'] = self.status.value
        
        # Convert Decimal to float for JSON serialization
        if self.unit_price:
            data['unit_price'] = float(self.unit_price)
        
        # Convert datetime objects to timestamps
        for field in ['created_at', 'updated_at']:
            if data[field]:
                data[field] = data[field].timestamp()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create Product from Firestore document"""
        if 'status' in data:
            data['status'] = ProductStatus(data['status'])
        
        if 'unit_price' in data and data['unit_price']:
            data['unit_price'] = Decimal(str(data['unit_price']))
        
        for field in ['created_at', 'updated_at']:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])
        
        return cls(**data)

@dataclass
class Warehouse:
    """Warehouse model"""
    warehouse_id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: bool = True
    operating_hours: Optional[Dict[str, str]] = None
    capacity: Optional[int] = None  # Total storage capacity
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default timestamps"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = asdict(self)
        
        for field in ['created_at', 'updated_at']:
            if data[field]:
                data[field] = data[field].timestamp()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Warehouse':
        """Create Warehouse from Firestore document"""
        for field in ['created_at', 'updated_at']:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])
        
        return cls(**data)

@dataclass
class InventoryItem:
    """Inventory item tracking per warehouse"""
    inventory_id: str
    warehouse_id: str
    sku: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    status: InventoryStatus = InventoryStatus.AVAILABLE
    location: Optional[str] = None  # Shelf/bin location
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    cost_per_unit: Optional[Decimal] = None
    last_counted: Optional[datetime] = None
    last_movement: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default timestamps and calculate available quantity"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Calculate available quantity
        self.quantity_available = max(0, self.quantity_on_hand - self.quantity_reserved)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore"""
        data = asdict(self)
        data['status'] = self.status.value
        
        if self.cost_per_unit:
            data['cost_per_unit'] = float(self.cost_per_unit)
        
        for field in ['expiry_date', 'last_counted', 'last_movement', 'created_at', 'updated_at']:
            if data[field]:
                data[field] = data[field].timestamp()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventoryItem':
        """Create InventoryItem from Firestore document"""
        if 'status' in data:
            data['status'] = InventoryStatus(data['status'])
        
        if 'cost_per_unit' in data and data['cost_per_unit']:
            data['cost_per_unit'] = Decimal(str(data['cost_per_unit']))
        
        for field in ['expiry_date', 'last_counted', 'last_movement', 'created_at', 'updated_at']:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])
        
        return cls(**data)
    
    def reserve_quantity(self, quantity: int) -> bool:
        """Reserve quantity for orders"""
        if self.quantity_available >= quantity:
            self.quantity_reserved += quantity
            self.quantity_available = max(0, self.quantity_on_hand - self.quantity_reserved)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def release_quantity(self, quantity: int):
        """Release reserved quantity"""
        self.quantity_reserved = max(0, self.quantity_reserved - quantity)
        self.quantity_available = max(0, self.quantity_on_hand - self.quantity_reserved)
        self.updated_at = datetime.utcnow()
    
    def adjust_quantity(self, new_quantity: int, reason: str = "adjustment"):
        """Adjust on-hand quantity"""
        self.quantity_on_hand = new_quantity
        self.quantity_available = max(0, self.quantity_on_hand - self.quantity_reserved)
        self.last_movement = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @property
    def is_low_stock(self) -> bool:
        """Check if inventory is below reorder point"""
        # This would need to reference the product's reorder point
        return self.quantity_available < 10  # Default threshold
    
    @property
    def is_expired(self) -> bool:
        """Check if inventory item is expired"""
        if self.expiry_date:
            return datetime.utcnow() > self.expiry_date
        return False