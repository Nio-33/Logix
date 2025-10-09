"""
Industry-Specific Type Definitions and Enumerations
"""

from enum import Enum


class IndustryCategory(Enum):
    """Primary industry categories"""
    
    ECOMMERCE = "ecommerce"
    RETAIL = "retail"
    FOOD_DELIVERY = "food_delivery"
    MANUFACTURING = "manufacturing"
    THIRD_PARTY_LOGISTICS = "3pl"


class OrderType(Enum):
    """Order type based on industry and business model"""
    
    # E-commerce Orders
    ECOMMERCE_DIRECT = "ecommerce_direct"
    ECOMMERCE_MARKETPLACE = "ecommerce_marketplace"
    ECOMMERCE_SUBSCRIPTION = "ecommerce_subscription"
    ECOMMERCE_B2B = "ecommerce_b2b"
    
    # Retail Distribution Orders
    RETAIL_PURCHASE_ORDER = "retail_po"
    RETAIL_TRANSFER = "retail_transfer"
    RETAIL_RESTOCK = "retail_restock"
    RETAIL_RETURN = "retail_return"
    
    # Food Delivery Orders
    FOOD_DELIVERY_CUSTOMER = "food_delivery_customer"
    FOOD_DELIVERY_CATERING = "food_delivery_catering"
    FOOD_DELIVERY_GROCERY = "food_delivery_grocery"
    FOOD_DELIVERY_PICKUP = "food_delivery_pickup"
    
    # Manufacturing Orders
    MANUFACTURING_PRODUCTION = "manufacturing_production"
    MANUFACTURING_RAW_MATERIALS = "manufacturing_raw_materials"
    MANUFACTURING_FINISHED_GOODS = "manufacturing_finished_goods"
    MANUFACTURING_TRANSFER = "manufacturing_transfer"
    
    # Third-Party Logistics Orders
    THIRD_PARTY_FULFILLMENT = "3pl_fulfillment"
    THIRD_PARTY_STORAGE = "3pl_storage"
    THIRD_PARTY_CROSS_DOCK = "3pl_cross_dock"
    THIRD_PARTY_RETURNS = "3pl_returns"


class OrderSource(Enum):
    """Detailed order source classification"""
    
    # E-commerce Platforms
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"
    BIGCOMMERCE = "bigcommerce"
    AMAZON_MARKETPLACE = "amazon_marketplace"
    EBAY = "ebay"
    WALMART_MARKETPLACE = "walmart_marketplace"
    ETSY = "etsy"
    CUSTOM_ECOMMERCE = "custom_ecommerce"
    
    # Retail Distribution Sources
    VENDOR_PORTAL = "vendor_portal"
    EDI_SYSTEM = "edi_system"
    RETAIL_PO_SYSTEM = "retail_po_system"
    DISTRIBUTOR_PORTAL = "distributor_portal"
    SUPPLIER_PORTAL = "supplier_portal"
    
    # Food Delivery Platforms
    UBER_EATS = "uber_eats"
    DOORDASH = "doordash"
    GRUBHUB = "grubhub"
    POSTMATES = "postmates"
    RESTAURANT_POS = "restaurant_pos"
    PHONE_ORDER = "phone_order"
    MOBILE_APP = "mobile_app"
    
    # Manufacturing Systems
    ERP_SYSTEM = "erp_system"
    MES_SYSTEM = "mes_system"
    PRODUCTION_SCHEDULE = "production_schedule"
    SAP = "sap"
    ORACLE = "oracle"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    
    # 3PL Sources
    CLIENT_PORTAL = "client_portal"
    WMS_INTEGRATION = "wms_integration"
    API_INTEGRATION = "api_integration"
    MANUAL_ENTRY = "manual_entry"
    
    # Generic
    WEB = "web"
    MOBILE = "mobile"
    API = "api"


class ServiceLevel(Enum):
    """Service level agreements for delivery"""
    
    STANDARD = "standard"
    EXPEDITED = "expedited"
    SAME_DAY = "same_day"
    NEXT_DAY = "next_day"
    TWO_DAY = "two_day"
    SCHEDULED = "scheduled"
    WHITE_GLOVE = "white_glove"


class TemperatureRequirement(Enum):
    """Temperature requirements for food delivery"""
    
    AMBIENT = "ambient"
    HOT = "hot"
    COLD = "cold"
    FROZEN = "frozen"
    TEMPERATURE_CONTROLLED = "temperature_controlled"


class ComplianceStandard(Enum):
    """Compliance and certification standards"""
    
    FDA = "fda"
    HACCP = "haccp"
    ISO_9001 = "iso_9001"
    ISO_14001 = "iso_14001"
    GMP = "gmp"
    ORGANIC = "organic"
    KOSHER = "kosher"
    HALAL = "halal"
    HAZMAT = "hazmat"
    SAFETY_DATA_SHEET = "sds"


class BillingModel(Enum):
    """Billing models for 3PL services"""
    
    PER_ORDER = "per_order"
    PER_ITEM = "per_item"
    PER_UNIT = "per_unit"
    MONTHLY_FLAT = "monthly_flat"
    STORAGE_BASED = "storage_based"
    HYBRID = "hybrid"

