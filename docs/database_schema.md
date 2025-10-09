# Logix Platform - Database Schema Design

## Firestore Collections Structure

### 1. Users Collection (`users`)
```javascript
{
  uid: string,                    // Firebase UID (document ID)
  email: string,
  role: enum,                     // super_admin, operations_manager, warehouse_staff, driver, customer
  first_name: string,
  last_name: string,
  phone: string?,
  profile_picture: string?,
  is_active: boolean,
  email_verified: boolean,
  created_at: timestamp,
  updated_at: timestamp,
  last_login: timestamp?,
  warehouse_ids: array<string>?,  // For warehouse staff
  vehicle_info: object?,          // For drivers
  preferences: object?
}
```

### 2. Products Collection (`products`)
```javascript
{
  sku: string,                    // Document ID
  name: string,
  description: string,
  category: string,
  brand: string?,
  unit_price: number?,
  weight: number?,               // kg
  dimensions: {                  // cm
    length: number,
    width: number,
    height: number
  }?,
  barcode: string?,
  qr_code: string?,
  status: enum,                  // active, inactive, discontinued
  reorder_point: number,
  reorder_quantity: number,
  supplier_id: string?,
  supplier_sku: string?,
  tags: array<string>?,
  images: array<string>?,
  created_at: timestamp,
  updated_at: timestamp
}
```

### 3. Warehouses Collection (`warehouses`)
```javascript
{
  warehouse_id: string,          // Document ID
  name: string,
  address: string,
  city: string,
  state: string,
  zip_code: string,
  country: string,
  latitude: number?,
  longitude: number?,
  phone: string?,
  email: string?,
  manager_id: string?,
  is_active: boolean,
  operating_hours: object?,
  capacity: number?,
  created_at: timestamp,
  updated_at: timestamp
}
```

### 4. Inventory Collection (`inventory`)
```javascript
{
  inventory_id: string,          // Document ID: warehouse_id + "_" + sku
  warehouse_id: string,
  sku: string,
  quantity_on_hand: number,
  quantity_reserved: number,
  quantity_available: number,
  status: enum,                  // available, reserved, damaged, expired
  location: string?,             // Shelf/bin location
  batch_number: string?,
  expiry_date: timestamp?,
  cost_per_unit: number?,
  last_counted: timestamp?,
  last_movement: timestamp?,
  created_at: timestamp,
  updated_at: timestamp
}
```

### 5. Orders Collection (`orders`) - ENHANCED v2.0
```javascript
{
  order_id: string,              // Document ID
  customer_id: string,
  status: enum,                  // Extended: pending, confirmed, processing, picked, packed, shipped, 
                                 // out_for_delivery, delivered, cancelled, returned, inspected, approved,
                                 // received, inventoried, preparing, ready_for_pickup, picked_up,
                                 // materials_allocated, production_started, quality_checked, etc.
  priority: enum,                // low, normal, high, urgent
  
  // NEW: Industry Classification
  order_type: enum?,             // ecommerce_direct, retail_po, food_delivery_customer, 
                                 // manufacturing_production, 3pl_fulfillment, etc.
  order_source: enum?,           // shopify, edi_system, uber_eats, erp_system, client_portal, etc.
  industry_category: enum?,      // ecommerce, retail, food_delivery, manufacturing, 3pl
  
  // Order details
  items: array<{
    sku: string,
    product_name: string,
    quantity: number,
    unit_price: number,
    total_price: number,
    warehouse_id: string?,
    batch_number: string?,
    notes: string?
  }>,
  subtotal: number,
  tax_amount: number,
  shipping_cost: number,
  discount_amount: number,
  total_amount: number,
  
  // Delivery information
  delivery_address: {
    name: string,
    company: string?,
    street: string,
    city: string,
    state: string,
    zip_code: string,
    country: string,
    phone: string?
  },
  delivery_instructions: string?,
  requested_delivery_date: timestamp?,
  estimated_delivery_date: timestamp?,
  actual_delivery_date: timestamp?,
  
  // Payment information
  payment_method: string?,
  payment_status: enum,          // pending, authorized, captured, failed, refunded
  payment_reference: string?,
  
  // Fulfillment information
  warehouse_id: string?,
  assigned_driver: string?,
  route_id: string?,
  tracking_number: string?,
  
  // NEW: Industry-Specific Data (Conditional)
  ecommerce_data: {              // Present only for e-commerce orders
    platform_order_id: string,
    platform_name: string,
    customer_email: string,
    customer_segment: string?,
    campaign_id: string?,
    utm_source: string?,
    subscription_id: string?,
    is_subscription: boolean,
    return_policy_days: number?,
    // ... additional e-commerce fields
  }?,
  
  retail_data: {                 // Present only for retail orders
    po_number: string,
    vendor_id: string,
    vendor_name: string,
    payment_terms: string,
    delivery_terms: string,
    compliance_certifications: array<string>?,
    inspection_required: boolean,
    quality_standards: array<string>?,
    // ... additional retail fields
  }?,
  
  food_delivery_data: {          // Present only for food delivery orders
    restaurant_id: string,
    restaurant_name: string,
    customer_phone: string,
    preparation_time_minutes: number,
    temperature_requirements: string?,
    allergen_info: array<string>?,
    platform_fee: number?,
    // ... additional food delivery fields
  }?,
  
  manufacturing_data: {          // Present only for manufacturing orders
    production_order_id: string,
    work_order_id: string?,
    production_start_date: timestamp?,
    production_end_date: timestamp?,
    quality_control_points: array<string>?,
    certification_requirements: array<string>?,
    // ... additional manufacturing fields
  }?,
  
  third_party_data: {            // Present only for 3PL orders
    client_id: string,
    client_name: string,
    service_type: string,
    billing_model: string,
    sla_delivery_time: number?,
    white_label: boolean,
    // ... additional 3PL fields
  }?,
  
  // Metadata
  source: string,                // DEPRECATED: Use order_source instead
  notes: string?,
  tags: array<string>?,
  created_at: timestamp,
  updated_at: timestamp,
  shipped_at: timestamp?,
  delivered_at: timestamp?
}
```

### 6. Routes Collection (`routes`)
```javascript
{
  route_id: string,              // Document ID
  driver_id: string,
  vehicle_id: string?,
  status: enum,                  // planned, active, completed, cancelled
  
  // Route details
  planned_start_time: timestamp,
  actual_start_time: timestamp?,
  planned_end_time: timestamp,
  actual_end_time: timestamp?,
  
  // Route optimization
  total_distance: number,        // km
  estimated_duration: number,    // minutes
  actual_duration: number?,      // minutes
  fuel_estimate: number?,        // liters
  
  // Stops
  stops: array<{
    stop_id: string,
    order_id: string,
    sequence: number,
    address: string,
    latitude: number,
    longitude: number,
    planned_arrival: timestamp,
    actual_arrival: timestamp?,
    status: enum,                // pending, arrived, completed, failed
    delivery_proof: {
      photo_url: string?,
      signature_url: string?,
      notes: string?,
      recipient_name: string?,
      timestamp: timestamp?
    }?,
    attempt_count: number,
    notes: string?
  }>,
  
  created_at: timestamp,
  updated_at: timestamp
}
```

### 7. Notifications Collection (`notifications`)
```javascript
{
  notification_id: string,       // Document ID
  user_id: string,
  type: enum,                    // order_update, delivery_alert, inventory_low, system_alert
  title: string,
  message: string,
  priority: enum,                // low, normal, high, urgent
  is_read: boolean,
  action_url: string?,
  metadata: object?,
  created_at: timestamp,
  expires_at: timestamp?
}
```

### 8. System Logs Collection (`system_logs`)
```javascript
{
  log_id: string,                // Document ID
  level: enum,                   // info, warning, error, critical
  service: string,               // auth, inventory, order, route, analytics
  event_type: string,
  message: string,
  user_id: string?,
  entity_id: string?,
  metadata: object?,
  timestamp: timestamp
}
```

## BigQuery Tables for Analytics

### 1. Order Analytics (`logix_analytics.orders`)
```sql
CREATE TABLE logix_analytics.orders (
  order_id STRING NOT NULL,
  customer_id STRING,
  status STRING,
  priority STRING,
  total_amount NUMERIC,
  item_count INTEGER,
  total_weight NUMERIC,
  warehouse_id STRING,
  driver_id STRING,
  source STRING,
  created_at TIMESTAMP,
  shipped_at TIMESTAMP,
  delivered_at TIMESTAMP,
  processing_time_minutes INTEGER,
  delivery_time_minutes INTEGER,
  date_partition DATE
) PARTITION BY date_partition;
```

### 2. Delivery Performance (`logix_analytics.deliveries`)
```sql
CREATE TABLE logix_analytics.deliveries (
  delivery_id STRING NOT NULL,
  order_id STRING,
  route_id STRING,
  driver_id STRING,
  warehouse_id STRING,
  planned_distance NUMERIC,
  actual_distance NUMERIC,
  planned_duration INTEGER,
  actual_duration INTEGER,
  fuel_consumed NUMERIC,
  delivery_status STRING,
  on_time BOOLEAN,
  customer_rating INTEGER,
  delivery_date DATE,
  created_at TIMESTAMP
) PARTITION BY delivery_date;
```

### 3. Inventory Movement (`logix_analytics.inventory_movements`)
```sql
CREATE TABLE logix_analytics.inventory_movements (
  movement_id STRING NOT NULL,
  warehouse_id STRING,
  sku STRING,
  movement_type STRING,      -- inbound, outbound, adjustment, transfer
  quantity INTEGER,
  unit_cost NUMERIC,
  total_value NUMERIC,
  reference_id STRING,       -- order_id, transfer_id, etc.
  reason STRING,
  timestamp TIMESTAMP,
  date_partition DATE
) PARTITION BY date_partition;
```

### 4. KPI Metrics (`logix_analytics.kpi_metrics`)
```sql
CREATE TABLE logix_analytics.kpi_metrics (
  metric_id STRING NOT NULL,
  metric_name STRING,
  metric_value NUMERIC,
  unit STRING,
  dimension_1 STRING,        -- warehouse_id, driver_id, etc.
  dimension_2 STRING,
  calculation_date DATE,
  created_at TIMESTAMP
) PARTITION BY calculation_date;
```

## Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Users can read/write their own profile
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager'];
    }
    
    // Products - read for all authenticated users, write for staff
    match /products/{productId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager', 'warehouse_staff'];
    }
    
    // Orders - customers can read their own, staff can read all
    match /orders/{orderId} {
      allow read: if request.auth != null && (
        resource.data.customer_id == request.auth.uid ||
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager', 'warehouse_staff', 'driver']
      );
      allow create: if request.auth != null;
      allow update: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager', 'warehouse_staff', 'driver'];
    }
    
    // Routes - drivers can read their assigned routes, staff can read all
    match /routes/{routeId} {
      allow read: if request.auth != null && (
        resource.data.driver_id == request.auth.uid ||
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager']
      );
      allow write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager'];
    }
    
    // Inventory - staff only
    match /inventory/{inventoryId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager', 'warehouse_staff'];
    }
    
    // Warehouses - staff only
    match /warehouses/{warehouseId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager', 'warehouse_staff'];
    }
    
    // Notifications - users can read their own
    match /notifications/{notificationId} {
      allow read, update: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
      allow create: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in 
        ['super_admin', 'operations_manager'];
    }
  }
}
```

## Indexes

### Firestore Composite Indexes
```javascript
// Orders by customer and status
{
  collection: "orders",
  fields: [
    { field: "customer_id", mode: "ASCENDING" },
    { field: "status", mode: "ASCENDING" },
    { field: "created_at", mode: "DESCENDING" }
  ]
}

// NEW: Orders by industry category and status
{
  collection: "orders",
  fields: [
    { field: "industry_category", mode: "ASCENDING" },
    { field: "status", mode: "ASCENDING" },
    { field: "created_at", mode: "DESCENDING" }
  ]
}

// NEW: Orders by order type and status
{
  collection: "orders",
  fields: [
    { field: "order_type", mode: "ASCENDING" },
    { field: "status", mode: "ASCENDING" },
    { field: "created_at", mode: "DESCENDING" }
  ]
}

// NEW: Orders by order source and created date
{
  collection: "orders",
  fields: [
    { field: "order_source", mode: "ASCENDING" },
    { field: "created_at", mode: "DESCENDING" }
  ]
}

// NEW: Orders by industry and priority
{
  collection: "orders",
  fields: [
    { field: "industry_category", mode: "ASCENDING" },
    { field: "priority", mode: "ASCENDING" },
    { field: "created_at", mode: "DESCENDING" }
  ]
}

// Inventory by warehouse and status
{
  collection: "inventory",
  fields: [
    { field: "warehouse_id", mode: "ASCENDING" },
    { field: "status", mode: "ASCENDING" },
    { field: "quantity_available", mode: "ASCENDING" }
  ]
}

// Routes by driver and status
{
  collection: "routes",
  fields: [
    { field: "driver_id", mode: "ASCENDING" },
    { field: "status", mode: "ASCENDING" },
    { field: "planned_start_time", mode: "ASCENDING" }
  ]
}
```

This schema design supports:
- Real-time updates through Firestore
- Scalable analytics through BigQuery
- Secure multi-tenant access
- Efficient querying with proper indexes
- Future extensibility