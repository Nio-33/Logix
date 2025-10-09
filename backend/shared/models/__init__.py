"""
Shared Data Models for Logix Platform
"""

from .user import User, UserRole
from .inventory import Product, InventoryItem, Warehouse
from .order import Order, OrderItem, OrderStatus, PaymentStatus, Priority
from .route import Route, RouteStop, DeliveryProof

# Industry-specific models (NEW)
from .industry_types import (
    IndustryCategory,
    OrderType,
    OrderSource,
    ServiceLevel,
    TemperatureRequirement,
    ComplianceStandard,
    BillingModel,
)
from .industry_data import (
    EcommerceOrderData,
    RetailOrderData,
    FoodDeliveryOrderData,
    ManufacturingOrderData,
    ThirdPartyOrderData,
)
from .industry_workflows import IndustryStatusWorkflow, IndustryValidator

__all__ = [
    # User models
    "User",
    "UserRole",
    # Inventory models
    "Product",
    "InventoryItem",
    "Warehouse",
    # Order models
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    "Priority",
    # Route models
    "Route",
    "RouteStop",
    "DeliveryProof",
    # Industry types
    "IndustryCategory",
    "OrderType",
    "OrderSource",
    "ServiceLevel",
    "TemperatureRequirement",
    "ComplianceStandard",
    "BillingModel",
    # Industry-specific data
    "EcommerceOrderData",
    "RetailOrderData",
    "FoodDeliveryOrderData",
    "ManufacturingOrderData",
    "ThirdPartyOrderData",
    # Industry workflows
    "IndustryStatusWorkflow",
    "IndustryValidator",
]
