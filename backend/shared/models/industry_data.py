"""
Industry-Specific Order Data Models
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


# ==================== E-COMMERCE DATA MODELS ====================

@dataclass
class EcommerceOrderData:
    """E-commerce specific order data"""
    
    # Platform Integration (required fields first)
    platform_order_id: str
    platform_name: str
    customer_email: str
    
    # Platform Integration (optional)
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    
    # Customer Data (optional)
    customer_phone: Optional[str] = None
    customer_segment: Optional[str] = None  # VIP, regular, new, loyal
    customer_lifetime_value: Optional[Decimal] = None
    
    # Marketing Attribution
    campaign_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    affiliate_id: Optional[str] = None
    referral_code: Optional[str] = None
    
    # Subscription Data
    subscription_id: Optional[str] = None
    subscription_type: Optional[str] = None  # monthly, quarterly, annual
    subscription_frequency: Optional[int] = None  # days
    next_delivery_date: Optional[datetime] = None
    is_subscription: bool = False
    
    # Returns & Exchanges
    return_policy_days: Optional[int] = 30
    exchange_allowed: bool = True
    restocking_fee: Optional[Decimal] = None
    
    # Gift Options
    is_gift: bool = False
    gift_message: Optional[str] = None
    gift_wrap_requested: bool = False
    
    # Customer Service
    customer_service_notes: Optional[str] = None
    special_instructions: Optional[str] = None
    previous_order_count: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert Decimal to float
        if self.customer_lifetime_value:
            data['customer_lifetime_value'] = float(self.customer_lifetime_value)
        if self.restocking_fee:
            data['restocking_fee'] = float(self.restocking_fee)
        # Convert datetime to timestamp
        if self.next_delivery_date:
            data['next_delivery_date'] = self.next_delivery_date.timestamp()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EcommerceOrderData":
        """Create from dictionary"""
        if data.get('customer_lifetime_value'):
            data['customer_lifetime_value'] = Decimal(str(data['customer_lifetime_value']))
        if data.get('restocking_fee'):
            data['restocking_fee'] = Decimal(str(data['restocking_fee']))
        if data.get('next_delivery_date'):
            data['next_delivery_date'] = datetime.fromtimestamp(data['next_delivery_date'])
        return cls(**data)


# ==================== RETAIL DISTRIBUTION DATA MODELS ====================

@dataclass
class RetailOrderData:
    """Retail distribution specific order data"""
    
    # Purchase Order Information (required fields first)
    po_number: str
    vendor_id: str
    vendor_name: str
    buyer_id: str
    buyer_name: str
    payment_terms: str  # Net 30, Net 60, COD, etc.
    delivery_terms: str  # FOB Origin, FOB Destination, DDP, etc.
    
    # Optional fields
    buyer_contact: Optional[str] = None
    incoterms: Optional[str] = None
    currency: str = "USD"
    
    # Store Information
    store_chain_id: Optional[str] = None
    store_number: Optional[str] = None
    store_name: Optional[str] = None
    store_address: Optional[Dict[str, str]] = None
    distribution_center: Optional[str] = None
    
    # Compliance & Certification
    compliance_certifications: Optional[List[str]] = None
    safety_data_sheets_required: bool = False
    hazmat_classification: Optional[str] = None
    regulatory_approvals: Optional[List[str]] = None
    
    # Quality Control
    inspection_required: bool = False
    inspection_type: Optional[str] = None  # visual, sampling, full
    quality_standards: Optional[List[str]] = None
    batch_tracking_required: bool = False
    lot_tracking_required: bool = False
    
    # Pricing
    volume_discount: Optional[Decimal] = None
    early_payment_discount: Optional[Decimal] = None
    minimum_order_value: Optional[Decimal] = None
    
    # Delivery
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    loading_dock: Optional[str] = None
    appointment_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert Decimal to float
        decimal_fields = ['volume_discount', 'early_payment_discount', 'minimum_order_value']
        for field in decimal_fields:
            if data.get(field):
                data[field] = float(data[field])
        # Convert datetime to timestamp
        if self.delivery_window_start:
            data['delivery_window_start'] = self.delivery_window_start.timestamp()
        if self.delivery_window_end:
            data['delivery_window_end'] = self.delivery_window_end.timestamp()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetailOrderData":
        """Create from dictionary"""
        decimal_fields = ['volume_discount', 'early_payment_discount', 'minimum_order_value']
        for field in decimal_fields:
            if data.get(field):
                data[field] = Decimal(str(data[field]))
        if data.get('delivery_window_start'):
            data['delivery_window_start'] = datetime.fromtimestamp(data['delivery_window_start'])
        if data.get('delivery_window_end'):
            data['delivery_window_end'] = datetime.fromtimestamp(data['delivery_window_end'])
        return cls(**data)


# ==================== FOOD DELIVERY DATA MODELS ====================

@dataclass
class FoodDeliveryOrderData:
    """Food delivery specific order data"""
    
    # Restaurant Information (required)
    restaurant_id: str
    restaurant_name: str
    restaurant_address: Dict[str, str]
    restaurant_phone: str
    customer_phone: str
    
    # Optional Restaurant fields
    restaurant_email: Optional[str] = None
    
    # Customer Information (optional)
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    delivery_instructions: Optional[str] = None
    contactless_delivery: bool = False
    
    # Timing
    preparation_time_minutes: int = 15
    estimated_prep_completion: Optional[datetime] = None
    pickup_time: Optional[datetime] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    order_ready_time: Optional[datetime] = None
    
    # Food Safety & Quality
    temperature_requirements: Optional[str] = None  # hot, cold, frozen, ambient
    allergen_info: Optional[List[str]] = None
    special_dietary_requirements: Optional[List[str]] = None  # vegan, gluten_free, etc.
    food_safety_seal_required: bool = True
    
    # Delivery Platform Integration
    platform_order_id: Optional[str] = None
    platform_name: Optional[str] = None  # uber_eats, doordash, grubhub
    platform_fee: Optional[Decimal] = None
    restaurant_commission: Optional[Decimal] = None
    driver_tip: Optional[Decimal] = None
    service_fee: Optional[Decimal] = None
    
    # Packaging
    packaging_requirements: Optional[List[str]] = None
    utensils_requested: bool = True
    napkins_requested: bool = True
    condiments_requested: Optional[List[str]] = None
    
    # Quality Control
    food_quality_check: bool = False
    temperature_verification: bool = False
    seal_integrity_check: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert Decimal to float
        decimal_fields = ['platform_fee', 'restaurant_commission', 'driver_tip', 'service_fee']
        for field in decimal_fields:
            if data.get(field):
                data[field] = float(data[field])
        # Convert datetime to timestamp
        datetime_fields = [
            'estimated_prep_completion', 'pickup_time', 'delivery_window_start',
            'delivery_window_end', 'order_ready_time'
        ]
        for field in datetime_fields:
            if data.get(field):
                data[field] = data[field].timestamp()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FoodDeliveryOrderData":
        """Create from dictionary"""
        decimal_fields = ['platform_fee', 'restaurant_commission', 'driver_tip', 'service_fee']
        for field in decimal_fields:
            if data.get(field):
                data[field] = Decimal(str(data[field]))
        datetime_fields = [
            'estimated_prep_completion', 'pickup_time', 'delivery_window_start',
            'delivery_window_end', 'order_ready_time'
        ]
        for field in datetime_fields:
            if data.get(field):
                data[field] = datetime.fromtimestamp(data[field])
        return cls(**data)


# ==================== MANUFACTURING DATA MODELS ====================

@dataclass
class ManufacturingOrderData:
    """Manufacturing specific order data"""
    
    # Production Information
    production_order_id: str
    work_order_id: Optional[str] = None
    bill_of_materials_id: Optional[str] = None
    product_code: Optional[str] = None
    
    # Production Schedule
    production_start_date: Optional[datetime] = None
    production_end_date: Optional[datetime] = None
    production_line: Optional[str] = None
    shift_information: Optional[str] = None
    production_batch_number: Optional[str] = None
    
    # Raw Materials
    raw_material_requirements: Optional[List[Dict[str, Any]]] = None
    supplier_requirements: Optional[List[Dict[str, Any]]] = None
    material_availability_confirmed: bool = False
    
    # Quality Control
    quality_control_points: Optional[List[str]] = None
    inspection_requirements: Optional[List[str]] = None
    certification_requirements: Optional[List[str]] = None
    quality_standards: Optional[List[str]] = None
    defect_tolerance: Optional[Decimal] = None
    
    # Compliance & Regulations
    safety_requirements: Optional[List[str]] = None
    environmental_compliance: Optional[List[str]] = None
    regulatory_requirements: Optional[List[str]] = None
    traceability_required: bool = True
    serialization_required: bool = False
    
    # Equipment & Resources
    equipment_required: Optional[List[str]] = None
    tooling_requirements: Optional[List[str]] = None
    labor_hours_estimated: Optional[Decimal] = None
    
    # Packaging
    packaging_specifications: Optional[str] = None
    labeling_requirements: Optional[List[str]] = None
    pallet_configuration: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert Decimal to float
        if self.defect_tolerance:
            data['defect_tolerance'] = float(self.defect_tolerance)
        if self.labor_hours_estimated:
            data['labor_hours_estimated'] = float(self.labor_hours_estimated)
        # Convert datetime to timestamp
        if self.production_start_date:
            data['production_start_date'] = self.production_start_date.timestamp()
        if self.production_end_date:
            data['production_end_date'] = self.production_end_date.timestamp()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManufacturingOrderData":
        """Create from dictionary"""
        if data.get('defect_tolerance'):
            data['defect_tolerance'] = Decimal(str(data['defect_tolerance']))
        if data.get('labor_hours_estimated'):
            data['labor_hours_estimated'] = Decimal(str(data['labor_hours_estimated']))
        if data.get('production_start_date'):
            data['production_start_date'] = datetime.fromtimestamp(data['production_start_date'])
        if data.get('production_end_date'):
            data['production_end_date'] = datetime.fromtimestamp(data['production_end_date'])
        return cls(**data)


# ==================== THIRD-PARTY LOGISTICS DATA MODELS ====================

@dataclass
class ThirdPartyOrderData:
    """3PL specific order data"""
    
    # Client Information (required)
    client_id: str
    client_name: str
    client_contact: str
    service_type: str  # fulfillment, storage, cross_dock, returns, kitting
    service_level: str  # standard, expedited, white_glove, specialized
    fulfillment_center: str
    billing_model: str  # per_order, per_item, monthly, storage_based
    
    # Optional Client Information
    client_email: Optional[str] = None
    client_account_number: Optional[str] = None
    
    # Service Configuration (optional)
    white_label: bool = False
    client_branding: Optional[str] = None
    
    # Warehouse Operations (optional)
    storage_location: Optional[str] = None
    storage_requirements: Optional[Dict[str, Any]] = None  # climate, security, etc.
    handling_instructions: Optional[List[str]] = None
    special_handling_required: bool = False
    
    # Client Integration (optional)
    client_system: Optional[str] = None
    integration_method: Optional[str] = None  # API, EDI, FTP, manual
    data_format: Optional[str] = None  # JSON, XML, CSV
    webhook_url: Optional[str] = None
    
    # Billing & SLA (optional)
    billing_rate: Optional[Decimal] = None
    sla_delivery_time: Optional[int] = None  # hours
    sla_accuracy_requirement: Optional[Decimal] = None  # percentage
    additional_services: Optional[List[str]] = None
    additional_service_fees: Optional[Dict[str, Decimal]] = None
    
    # Value-Added Services
    kitting_required: bool = False
    labeling_required: bool = False
    custom_packaging: bool = False
    quality_inspection: bool = False
    
    # Reporting
    reporting_frequency: Optional[str] = None  # daily, weekly, monthly
    custom_reports: Optional[List[str]] = None
    inventory_snapshot_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert Decimal to float
        if self.billing_rate:
            data['billing_rate'] = float(self.billing_rate)
        if self.sla_accuracy_requirement:
            data['sla_accuracy_requirement'] = float(self.sla_accuracy_requirement)
        if self.additional_service_fees:
            data['additional_service_fees'] = {
                k: float(v) for k, v in self.additional_service_fees.items()
            }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThirdPartyOrderData":
        """Create from dictionary"""
        if data.get('billing_rate'):
            data['billing_rate'] = Decimal(str(data['billing_rate']))
        if data.get('sla_accuracy_requirement'):
            data['sla_accuracy_requirement'] = Decimal(str(data['sla_accuracy_requirement']))
        if data.get('additional_service_fees'):
            data['additional_service_fees'] = {
                k: Decimal(str(v)) for k, v in data['additional_service_fees'].items()
            }
        return cls(**data)

