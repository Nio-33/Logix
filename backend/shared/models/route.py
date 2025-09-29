"""
Route and Delivery Data Models
"""

from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

class RouteStatus(Enum):
    """Route status enumeration"""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class StopStatus(Enum):
    """Stop status enumeration"""
    PENDING = "pending"
    ARRIVED = "arrived"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DeliveryProof:
    """Delivery proof model"""
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    notes: Optional[str] = None
    recipient_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.timestamp()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeliveryProof':
        """Create from dictionary"""
        if data.get('timestamp'):
            data['timestamp'] = datetime.fromtimestamp(data['timestamp'])
        return cls(**data)

@dataclass
class RouteStop:
    """Route stop model"""
    stop_id: str
    order_id: str
    sequence: int
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    planned_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: StopStatus = StopStatus.PENDING
    delivery_proof: Optional[DeliveryProof] = None
    attempt_count: int = 0
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        
        for field in ['planned_arrival', 'actual_arrival']:
            if data[field]:
                data[field] = data[field].timestamp()
        
        if self.delivery_proof:
            data['delivery_proof'] = self.delivery_proof.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RouteStop':
        """Create from dictionary"""
        if 'status' in data:
            data['status'] = StopStatus(data['status'])
        
        for field in ['planned_arrival', 'actual_arrival']:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])
        
        if data.get('delivery_proof'):
            data['delivery_proof'] = DeliveryProof.from_dict(data['delivery_proof'])
        
        return cls(**data)

@dataclass
class Route:
    """Route model"""
    route_id: str
    driver_id: str
    vehicle_id: Optional[str] = None
    status: RouteStatus = RouteStatus.PLANNED
    
    # Timing
    planned_start_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    
    # Route metrics
    total_distance: float = 0.0  # km
    estimated_duration: int = 0  # minutes
    actual_duration: Optional[int] = None  # minutes
    fuel_estimate: float = 0.0  # liters
    
    # Stops
    stops: List[RouteStop] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default values"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.stops is None:
            self.stops = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        
        # Convert datetime fields
        datetime_fields = [
            'planned_start_time', 'actual_start_time', 
            'planned_end_time', 'actual_end_time',
            'created_at', 'updated_at'
        ]
        for field in datetime_fields:
            if data[field]:
                data[field] = data[field].timestamp()
        
        # Convert stops
        if self.stops:
            data['stops'] = [stop.to_dict() for stop in self.stops]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Route':
        """Create from dictionary"""
        if 'status' in data:
            data['status'] = RouteStatus(data['status'])
        
        # Convert datetime fields
        datetime_fields = [
            'planned_start_time', 'actual_start_time',
            'planned_end_time', 'actual_end_time', 
            'created_at', 'updated_at'
        ]
        for field in datetime_fields:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])
        
        # Convert stops
        if data.get('stops'):
            data['stops'] = [RouteStop.from_dict(stop_data) for stop_data in data['stops']]
        
        return cls(**data)