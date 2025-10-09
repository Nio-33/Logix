# Industry-Specific Order Architecture Design

## Overview
This document outlines how the Logix platform should handle different industry-specific order processes and data management requirements.

## Current System Limitations

### 1. Generic Order Model Issues
- Single `source` field (web, mobile, api, phone) doesn't capture industry-specific origins
- Generic status workflow doesn't reflect industry-specific processes
- No order type classification for different business models
- Missing industry-specific metadata and workflow requirements

## Enhanced Architecture Design

### 1. Order Type Classification System

```python
class OrderType(Enum):
    """Order type based on industry/business model"""
    
    # E-commerce Orders
    ECOMMERCE_DIRECT = "ecommerce_direct"           # Direct from e-commerce platform
    ECOMMERCE_MARKETPLACE = "ecommerce_marketplace" # Amazon, eBay, etc.
    ECOMMERCE_SUBSCRIPTION = "ecommerce_subscription" # Subscription boxes
    
    # Retail Distribution Orders
    RETAIL_PURCHASE_ORDER = "retail_po"             # Vendor to retailer
    RETAIL_TRANSFER = "retail_transfer"             # Store to store
    RETAIL_RESTOCK = "retail_restock"               # Central warehouse to store
    
    # Food Delivery Orders
    FOOD_DELIVERY_CUSTOMER = "food_delivery_customer" # Customer orders
    FOOD_DELIVERY_CATERING = "food_delivery_catering" # Bulk catering orders
    FOOD_DELIVERY_GROCERY = "food_delivery_grocery"   # Grocery delivery
    
    # Manufacturing Orders
    MANUFACTURING_PRODUCTION = "manufacturing_production" # Production orders
    MANUFACTURING_RAW_MATERIALS = "manufacturing_raw_materials" # Raw material orders
    MANUFACTURING_FINISHED_GOODS = "manufacturing_finished_goods" # Finished goods distribution
    
    # Third-Party Logistics (3PL)
    THIRD_PARTY_FULFILLMENT = "3pl_fulfillment"     # 3PL fulfillment services
    THIRD_PARTY_STORAGE = "3pl_storage"             # Storage-only services
    THIRD_PARTY_CROSS_DOCK = "3pl_cross_dock"       # Cross-docking operations
```

### 2. Industry-Specific Order Sources

```python
class OrderSource(Enum):
    """Detailed order source classification"""
    
    # E-commerce Sources
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"
    AMAZON_MARKETPLACE = "amazon_marketplace"
    EBAY = "ebay"
    WALMART_MARKETPLACE = "walmart_marketplace"
    CUSTOM_ECOMMERCE = "custom_ecommerce"
    
    # Retail Distribution Sources
    VENDOR_PORTAL = "vendor_portal"
    EDI_SYSTEM = "edi_system"
    RETAIL_PO_SYSTEM = "retail_po_system"
    DISTRIBUTOR_PORTAL = "distributor_portal"
    
    # Food Delivery Sources
    UBER_EATS = "uber_eats"
    DOORDASH = "doordash"
    GRUBHUB = "grubhub"
    RESTAURANT_POS = "restaurant_pos"
    MOBILE_APP = "mobile_app"
    PHONE_ORDER = "phone_order"
    
    # Manufacturing Sources
    ERP_SYSTEM = "erp_system"
    MES_SYSTEM = "mes_system"  # Manufacturing Execution System
    SUPPLIER_PORTAL = "supplier_portal"
    PRODUCTION_SCHEDULE = "production_schedule"
    
    # 3PL Sources
    CLIENT_PORTAL = "client_portal"
    WMS_INTEGRATION = "wms_integration"
    API_INTEGRATION = "api_integration"
    MANUAL_ENTRY = "manual_entry"
```

### 3. Enhanced Order Model

```python
@dataclass
class EnhancedOrder:
    """Enhanced order model with industry-specific fields"""
    
    # Core Fields (existing)
    order_id: str
    customer_id: str
    status: OrderStatus
    priority: Priority
    
    # Industry Classification
    order_type: OrderType
    order_source: OrderSource
    industry_category: str  # ecommerce, retail, food, manufacturing, 3pl
    
    # Industry-Specific Metadata
    industry_metadata: Dict[str, Any] = None
    
    # E-commerce Specific Fields
    ecommerce_data: Optional[EcommerceOrderData] = None
    
    # Retail Distribution Specific Fields
    retail_data: Optional[RetailOrderData] = None
    
    # Food Delivery Specific Fields
    food_delivery_data: Optional[FoodDeliveryOrderData] = None
    
    # Manufacturing Specific Fields
    manufacturing_data: Optional[ManufacturingOrderData] = None
    
    # 3PL Specific Fields
    third_party_data: Optional[ThirdPartyOrderData] = None
    
    # Existing fields...
    items: List[OrderItem] = None
    delivery_address: Dict[str, str] = None
    # ... other existing fields
```

### 4. Industry-Specific Data Models

#### E-commerce Order Data
```python
@dataclass
class EcommerceOrderData:
    """E-commerce specific order data"""
    
    # Platform Integration
    platform_order_id: str
    platform_name: str
    store_id: Optional[str] = None
    
    # Customer Data
    customer_email: str
    customer_phone: Optional[str] = None
    customer_segment: Optional[str] = None  # VIP, regular, new
    
    # Marketing Attribution
    campaign_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    affiliate_id: Optional[str] = None
    
    # Subscription Data
    subscription_id: Optional[str] = None
    subscription_type: Optional[str] = None
    next_delivery_date: Optional[datetime] = None
    
    # Returns & Exchanges
    return_policy: Optional[str] = None
    exchange_allowed: bool = True
    
    # Customer Service
    customer_service_notes: Optional[str] = None
    special_instructions: Optional[str] = None
```

#### Retail Distribution Order Data
```python
@dataclass
class RetailOrderData:
    """Retail distribution specific order data"""
    
    # Purchase Order Information
    po_number: str
    vendor_id: str
    vendor_name: str
    buyer_id: str
    buyer_name: str
    
    # Terms & Conditions
    payment_terms: str  # Net 30, Net 60, etc.
    delivery_terms: str  # FOB Origin, FOB Destination
    incoterms: Optional[str] = None
    
    # Store Information
    store_chain_id: Optional[str] = None
    store_number: Optional[str] = None
    store_address: Optional[Dict[str, str]] = None
    
    # Compliance & Certification
    compliance_certifications: List[str] = None
    safety_data_sheets_required: bool = False
    hazmat_classification: Optional[str] = None
    
    # Quality Control
    inspection_required: bool = False
    quality_standards: List[str] = None
    batch_tracking_required: bool = False
```

#### Food Delivery Order Data
```python
@dataclass
class FoodDeliveryOrderData:
    """Food delivery specific order data"""
    
    # Restaurant Information
    restaurant_id: str
    restaurant_name: str
    restaurant_address: Dict[str, str]
    restaurant_phone: str
    
    # Customer Information
    customer_phone: str
    customer_email: Optional[str] = None
    delivery_instructions: Optional[str] = None
    
    # Timing
    preparation_time_minutes: int
    pickup_time: Optional[datetime] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    
    # Food Safety
    temperature_requirements: Optional[str] = None  # Hot, Cold, Frozen
    allergen_info: List[str] = None
    special_dietary_requirements: List[str] = None
    
    # Delivery Platform
    platform_order_id: str
    platform_fee: Decimal
    restaurant_commission: Decimal
    driver_tip: Optional[Decimal] = None
    
    # Quality Control
    food_quality_check: bool = False
    packaging_requirements: List[str] = None
```

#### Manufacturing Order Data
```python
@dataclass
class ManufacturingOrderData:
    """Manufacturing specific order data"""
    
    # Production Information
    production_order_id: str
    work_order_id: Optional[str] = None
    bill_of_materials_id: Optional[str] = None
    
    # Raw Materials
    raw_material_requirements: List[RawMaterialRequirement] = None
    supplier_requirements: List[SupplierRequirement] = None
    
    # Production Schedule
    production_start_date: Optional[datetime] = None
    production_end_date: Optional[datetime] = None
    production_line: Optional[str] = None
    shift_information: Optional[str] = None
    
    # Quality Control
    quality_control_points: List[str] = None
    inspection_requirements: List[str] = None
    certification_requirements: List[str] = None
    
    # Compliance
    safety_requirements: List[str] = None
    environmental_compliance: List[str] = None
    regulatory_requirements: List[str] = None
```

#### Third-Party Logistics Order Data
```python
@dataclass
class ThirdPartyOrderData:
    """3PL specific order data"""
    
    # Client Information
    client_id: str
    client_name: str
    client_contact: str
    
    # Service Type
    service_type: str  # fulfillment, storage, cross_dock, returns
    service_level: str  # standard, expedited, white_glove
    
    # Warehouse Operations
    fulfillment_center: str
    storage_requirements: Dict[str, Any] = None
    handling_instructions: List[str] = None
    
    # Client Integration
    client_system: str
    integration_method: str  # API, EDI, FTP, manual
    data_format: str
    
    # Billing
    billing_method: str  # per_order, per_item, monthly
    billing_rate: Decimal
    additional_services: List[str] = None
```

### 5. Industry-Specific Status Workflows

```python
class IndustryStatusWorkflow:
    """Industry-specific status workflows"""
    
    @staticmethod
    def get_status_workflow(order_type: OrderType) -> List[OrderStatus]:
        """Get status workflow for specific order type"""
        
        workflows = {
            OrderType.ECOMMERCE_DIRECT: [
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.PROCESSING,
                OrderStatus.PICKED,
                OrderStatus.PACKED,
                OrderStatus.SHIPPED,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.DELIVERED
            ],
            
            OrderType.RETAIL_PURCHASE_ORDER: [
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.PROCESSING,
                OrderStatus.INSPECTED,  # Additional status
                OrderStatus.APPROVED,   # Additional status
                OrderStatus.RECEIVED,   # Additional status
                OrderStatus.INVENTORIED # Additional status
            ],
            
            OrderType.FOOD_DELIVERY_CUSTOMER: [
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.PREPARING,  # Additional status
                OrderStatus.READY_FOR_PICKUP,
                OrderStatus.PICKED_UP,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.DELIVERED
            ],
            
            OrderType.MANUFACTURING_PRODUCTION: [
                OrderStatus.PENDING,
                OrderStatus.APPROVED,
                OrderStatus.MATERIALS_ALLOCATED,
                OrderStatus.PRODUCTION_STARTED,
                OrderStatus.PRODUCTION_IN_PROGRESS,
                OrderStatus.PRODUCTION_COMPLETED,
                OrderStatus.QUALITY_CHECKED,
                OrderStatus.PACKAGED,
                OrderStatus.SHIPPED
            ],
            
            OrderType.THIRD_PARTY_FULFILLMENT: [
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.RECEIVED,
                OrderStatus.INVENTORIED,
                OrderStatus.PROCESSING,
                OrderStatus.PICKED,
                OrderStatus.PACKED,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED
            ]
        }
        
        return workflows.get(order_type, workflows[OrderType.ECOMMERCE_DIRECT])
```

### 6. Industry-Specific Processing Logic

```python
class IndustryOrderProcessor:
    """Industry-specific order processing logic"""
    
    def __init__(self, order_type: OrderType):
        self.order_type = order_type
        self.processor = self._get_processor()
    
    def _get_processor(self):
        """Get industry-specific processor"""
        processors = {
            OrderType.ECOMMERCE_DIRECT: EcommerceOrderProcessor(),
            OrderType.RETAIL_PURCHASE_ORDER: RetailOrderProcessor(),
            OrderType.FOOD_DELIVERY_CUSTOMER: FoodDeliveryOrderProcessor(),
            OrderType.MANUFACTURING_PRODUCTION: ManufacturingOrderProcessor(),
            OrderType.THIRD_PARTY_FULFILLMENT: ThirdPartyOrderProcessor()
        }
        return processors.get(self.order_type)
    
    def process_order(self, order: EnhancedOrder):
        """Process order using industry-specific logic"""
        return self.processor.process(order)
    
    def validate_order(self, order: EnhancedOrder):
        """Validate order using industry-specific rules"""
        return self.processor.validate(order)
    
    def calculate_fulfillment_time(self, order: EnhancedOrder):
        """Calculate fulfillment time using industry-specific metrics"""
        return self.processor.calculate_fulfillment_time(order)
```

### 7. Database Schema Enhancements

```javascript
// Enhanced Orders Collection
{
  order_id: string,
  order_type: enum,           // New field
  order_source: enum,         // New field
  industry_category: string,  // New field
  
  // Industry-specific data (conditional based on order_type)
  ecommerce_data: object?,    // New field
  retail_data: object?,       // New field
  food_delivery_data: object?, // New field
  manufacturing_data: object?, // New field
  third_party_data: object?,  // New field
  
  // Existing fields...
  customer_id: string,
  status: enum,
  items: array,
  // ... rest of existing fields
}
```

### 8. API Enhancements

```python
# Enhanced Order Creation API
@order_bp.route("/", methods=["POST"])
def create_order():
    """Create order with industry-specific processing"""
    
    data = request.get_json()
    
    # Determine order type and industry
    order_type = OrderType(data.get("order_type"))
    industry_processor = IndustryOrderProcessor(order_type)
    
    # Validate industry-specific data
    validation_result = industry_processor.validate(data)
    if not validation_result.is_valid:
        return jsonify({"error": validation_result.errors}), 400
    
    # Create enhanced order
    order = create_enhanced_order(data, order_type)
    
    # Process using industry-specific logic
    processed_order = industry_processor.process_order(order)
    
    return jsonify({"order": processed_order.to_dict()}), 201
```

## Implementation Benefits

### 1. Industry-Specific Workflows
- Each industry gets optimized status workflows
- Industry-specific validation rules
- Tailored user interfaces and experiences

### 2. Enhanced Data Capture
- Industry-specific metadata collection
- Better integration with industry systems
- Improved analytics and reporting

### 3. Scalable Architecture
- Easy to add new industries
- Modular processing logic
- Flexible data models

### 4. Better User Experience
- Industry-appropriate terminology
- Relevant fields and workflows
- Optimized for specific use cases

## Migration Strategy

### Phase 1: Core Infrastructure
1. Add order type and source enums
2. Create industry-specific data models
3. Implement enhanced order model

### Phase 2: Industry Processors
1. Implement industry-specific processors
2. Add validation logic
3. Create status workflows

### Phase 3: API Enhancements
1. Update order creation APIs
2. Add industry-specific endpoints
3. Implement filtering and search

### Phase 4: Frontend Updates
1. Industry-specific UI components
2. Workflow-based interfaces
3. Enhanced reporting and analytics

This architecture provides a robust foundation for handling diverse industry requirements while maintaining a unified core system.
