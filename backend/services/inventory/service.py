"""
Inventory Service Business Logic
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from shared.utils.firebase_config import get_firestore_client
from shared.models.inventory import (
    Product,
    InventoryItem,
    Warehouse,
    ProductStatus,
    InventoryStatus,
)

logger = logging.getLogger(__name__)


class InventoryService:
    """Inventory management service"""

    def __init__(self):
        self.db = get_firestore_client()
        if self.db:
            self.products_collection = self.db.collection("products")
            self.warehouses_collection = self.db.collection("warehouses")
            self.inventory_collection = self.db.collection("inventory")
            self.movements_collection = self.db.collection("inventory_movements")
        else:
            self.products_collection = None
            self.warehouses_collection = None
            self.inventory_collection = None
            self.movements_collection = None

    # Product Management
    def get_product(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        try:
            product_doc = self.products_collection.document(sku).get()

            if product_doc.exists:
                return Product.from_dict(product_doc.to_dict())

            return None

        except Exception as e:
            logger.error(f"Failed to get product {sku}: {e}")
            raise

    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create new product"""
        try:
            # Check if SKU already exists
            existing_product = self.get_product(product_data["sku"])
            if existing_product:
                raise ValueError(
                    f"Product with SKU {product_data['sku']} already exists"
                )

            # Create product
            product = Product(
                sku=product_data["sku"],
                name=product_data["name"],
                description=product_data["description"],
                category=product_data["category"],
                brand=product_data.get("brand"),
                unit_price=Decimal(str(product_data["unit_price"]))
                if product_data.get("unit_price")
                else None,
                weight=product_data.get("weight"),
                dimensions=product_data.get("dimensions"),
                barcode=product_data.get("barcode"),
                qr_code=product_data.get("qr_code"),
                status=ProductStatus(product_data.get("status", "active")),
                reorder_point=product_data.get("reorder_point", 10),
                reorder_quantity=product_data.get("reorder_quantity", 50),
                supplier_id=product_data.get("supplier_id"),
                supplier_sku=product_data.get("supplier_sku"),
                tags=product_data.get("tags", []),
                images=product_data.get("images", []),
            )

            # Save to Firestore
            self.products_collection.document(product.sku).set(product.to_dict())

            logger.info(f"Product created: {product.sku}")
            return product

        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            raise

    def update_product(
        self, sku: str, update_data: Dict[str, Any]
    ) -> Optional[Product]:
        """Update existing product"""
        try:
            product = self.get_product(sku)
            if not product:
                return None

            # Update allowed fields
            allowed_fields = [
                "name",
                "description",
                "category",
                "brand",
                "unit_price",
                "weight",
                "dimensions",
                "barcode",
                "qr_code",
                "status",
                "reorder_point",
                "reorder_quantity",
                "supplier_id",
                "supplier_sku",
                "tags",
                "images",
            ]

            for field in allowed_fields:
                if field in update_data:
                    if field == "unit_price" and update_data[field] is not None:
                        setattr(product, field, Decimal(str(update_data[field])))
                    elif field == "status":
                        setattr(product, field, ProductStatus(update_data[field]))
                    else:
                        setattr(product, field, update_data[field])

            product.updated_at = datetime.utcnow()

            # Save to Firestore
            self.products_collection.document(sku).update(product.to_dict())

            logger.info(f"Product updated: {sku}")
            return product

        except Exception as e:
            logger.error(f"Failed to update product {sku}: {e}")
            raise

    def list_products(
        self,
        page: int = 1,
        limit: int = 20,
        category: str = None,
        status: str = None,
        search: str = None,
    ) -> List[Product]:
        """List products with filtering and pagination"""
        try:
            query = self.products_collection

            # Apply filters
            if category:
                query = query.where("category", "==", category)

            if status:
                try:
                    status_enum = ProductStatus(status)
                    query = query.where("status", "==", status_enum.value)
                except ValueError:
                    logger.warning(f"Invalid status filter: {status}")

            # Apply pagination
            offset = (page - 1) * limit
            query = query.order_by("name").offset(offset).limit(limit)

            products = []
            for doc in query.stream():
                try:
                    product = Product.from_dict(doc.to_dict())

                    # Apply search filter (client-side for now)
                    if search:
                        search_lower = search.lower()
                        if (
                            search_lower in product.name.lower()
                            or search_lower in product.description.lower()
                            or search_lower in product.sku.lower()
                        ):
                            products.append(product)
                    else:
                        products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse product document {doc.id}: {e}")

            return products

        except Exception as e:
            logger.error(f"Failed to list products: {e}")
            raise

    # Warehouse Management
    def get_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        """Get warehouse by ID"""
        try:
            warehouse_doc = self.warehouses_collection.document(warehouse_id).get()

            if warehouse_doc.exists:
                return Warehouse.from_dict(warehouse_doc.to_dict())

            return None

        except Exception as e:
            logger.error(f"Failed to get warehouse {warehouse_id}: {e}")
            raise

    def create_warehouse(self, warehouse_data: Dict[str, Any]) -> Warehouse:
        """Create new warehouse"""
        try:
            # Check if warehouse ID already exists
            existing_warehouse = self.get_warehouse(warehouse_data["warehouse_id"])
            if existing_warehouse:
                raise ValueError(
                    f"Warehouse with ID {warehouse_data['warehouse_id']} already exists"
                )

            warehouse = Warehouse(
                warehouse_id=warehouse_data["warehouse_id"],
                name=warehouse_data["name"],
                address=warehouse_data["address"],
                city=warehouse_data["city"],
                state=warehouse_data["state"],
                zip_code=warehouse_data["zip_code"],
                country=warehouse_data["country"],
                latitude=warehouse_data.get("latitude"),
                longitude=warehouse_data.get("longitude"),
                phone=warehouse_data.get("phone"),
                email=warehouse_data.get("email"),
                manager_id=warehouse_data.get("manager_id"),
                is_active=warehouse_data.get("is_active", True),
                operating_hours=warehouse_data.get("operating_hours"),
                capacity=warehouse_data.get("capacity"),
            )

            # Save to Firestore
            self.warehouses_collection.document(warehouse.warehouse_id).set(
                warehouse.to_dict()
            )

            logger.info(f"Warehouse created: {warehouse.warehouse_id}")
            return warehouse

        except Exception as e:
            logger.error(f"Failed to create warehouse: {e}")
            raise

    def list_warehouses(self) -> List[Warehouse]:
        """List all active warehouses"""
        try:
            query = self.warehouses_collection.where("is_active", "==", True)

            warehouses = []
            for doc in query.stream():
                try:
                    warehouse = Warehouse.from_dict(doc.to_dict())
                    warehouses.append(warehouse)
                except Exception as e:
                    logger.warning(f"Failed to parse warehouse document {doc.id}: {e}")

            return warehouses

        except Exception as e:
            logger.error(f"Failed to list warehouses: {e}")
            raise

    # Inventory Management
    def get_inventory_item(self, inventory_id: str) -> Optional[InventoryItem]:
        """Get inventory item by ID"""
        try:
            inventory_doc = self.inventory_collection.document(inventory_id).get()

            if inventory_doc.exists:
                return InventoryItem.from_dict(inventory_doc.to_dict())

            return None

        except Exception as e:
            logger.error(f"Failed to get inventory item {inventory_id}: {e}")
            raise

    def get_inventory_by_warehouse_sku(
        self, warehouse_id: str, sku: str
    ) -> Optional[InventoryItem]:
        """Get inventory item by warehouse and SKU"""
        try:
            inventory_id = f"{warehouse_id}_{sku}"
            return self.get_inventory_item(inventory_id)

        except Exception as e:
            logger.error(f"Failed to get inventory for {warehouse_id}/{sku}: {e}")
            raise

    def create_or_update_inventory(
        self,
        warehouse_id: str,
        sku: str,
        quantity: int,
        cost_per_unit: Decimal = None,
        location: str = None,
    ) -> InventoryItem:
        """Create or update inventory item"""
        try:
            inventory_id = f"{warehouse_id}_{sku}"
            existing_item = self.get_inventory_item(inventory_id)

            if existing_item:
                # Update existing item
                existing_item.quantity_on_hand = quantity
                existing_item.quantity_available = max(
                    0, quantity - existing_item.quantity_reserved
                )
                if cost_per_unit:
                    existing_item.cost_per_unit = cost_per_unit
                if location:
                    existing_item.location = location
                existing_item.updated_at = datetime.utcnow()

                # Save to Firestore
                self.inventory_collection.document(inventory_id).update(
                    existing_item.to_dict()
                )

                return existing_item
            else:
                # Create new item
                new_item = InventoryItem(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id,
                    sku=sku,
                    quantity_on_hand=quantity,
                    quantity_reserved=0,
                    quantity_available=quantity,
                    cost_per_unit=cost_per_unit,
                    location=location,
                )

                # Save to Firestore
                self.inventory_collection.document(inventory_id).set(new_item.to_dict())

                return new_item

        except Exception as e:
            logger.error(f"Failed to create/update inventory {warehouse_id}/{sku}: {e}")
            raise

    def list_inventory(
        self,
        warehouse_id: str = None,
        sku: str = None,
        status: str = None,
        low_stock: bool = None,
        page: int = 1,
        limit: int = 50,
    ) -> List[InventoryItem]:
        """List inventory items with filtering"""
        try:
            query = self.inventory_collection

            # Apply filters
            if warehouse_id:
                query = query.where("warehouse_id", "==", warehouse_id)

            if sku:
                query = query.where("sku", "==", sku)

            if status:
                try:
                    status_enum = InventoryStatus(status)
                    query = query.where("status", "==", status_enum.value)
                except ValueError:
                    logger.warning(f"Invalid status filter: {status}")

            # Apply pagination
            offset = (page - 1) * limit
            query = (
                query.order_by("updated_at", direction="DESCENDING")
                .offset(offset)
                .limit(limit)
            )

            inventory_items = []
            for doc in query.stream():
                try:
                    item = InventoryItem.from_dict(doc.to_dict())

                    # Apply low stock filter
                    if low_stock is True and not item.is_low_stock:
                        continue
                    elif low_stock is False and item.is_low_stock:
                        continue

                    inventory_items.append(item)

                except Exception as e:
                    logger.warning(f"Failed to parse inventory document {doc.id}: {e}")

            return inventory_items

        except Exception as e:
            logger.error(f"Failed to list inventory: {e}")
            raise

    def adjust_inventory(
        self, inventory_id: str, new_quantity: int, reason: str, user_id: str
    ) -> Optional[InventoryItem]:
        """Adjust inventory quantity"""
        try:
            item = self.get_inventory_item(inventory_id)
            if not item:
                return None

            old_quantity = item.quantity_on_hand
            item.adjust_quantity(new_quantity, reason)

            # Save to Firestore
            self.inventory_collection.document(inventory_id).update(item.to_dict())

            # Record movement
            self._record_movement(
                warehouse_id=item.warehouse_id,
                sku=item.sku,
                movement_type="adjustment",
                quantity=new_quantity - old_quantity,
                reason=reason,
                user_id=user_id,
                reference_id=inventory_id,
            )

            logger.info(
                f"Inventory adjusted: {inventory_id} from {old_quantity} to {new_quantity}"
            )
            return item

        except Exception as e:
            logger.error(f"Failed to adjust inventory {inventory_id}: {e}")
            raise

    def reserve_inventory(
        self,
        inventory_id: str,
        quantity: int,
        order_id: str = None,
        user_id: str = None,
    ) -> bool:
        """Reserve inventory for order"""
        try:
            item = self.get_inventory_item(inventory_id)
            if not item:
                return False

            success = item.reserve_quantity(quantity)
            if success:
                # Save to Firestore
                self.inventory_collection.document(inventory_id).update(item.to_dict())

                # Record movement
                self._record_movement(
                    warehouse_id=item.warehouse_id,
                    sku=item.sku,
                    movement_type="reservation",
                    quantity=-quantity,
                    reason=f"Reserved for order {order_id}" if order_id else "Reserved",
                    user_id=user_id,
                    reference_id=order_id,
                )

                logger.info(f"Inventory reserved: {inventory_id} quantity {quantity}")

            return success

        except Exception as e:
            logger.error(f"Failed to reserve inventory {inventory_id}: {e}")
            raise

    def release_inventory(
        self, inventory_id: str, quantity: int, user_id: str = None
    ) -> bool:
        """Release reserved inventory"""
        try:
            item = self.get_inventory_item(inventory_id)
            if not item:
                return False

            item.release_quantity(quantity)

            # Save to Firestore
            self.inventory_collection.document(inventory_id).update(item.to_dict())

            # Record movement
            self._record_movement(
                warehouse_id=item.warehouse_id,
                sku=item.sku,
                movement_type="release",
                quantity=quantity,
                reason="Released reservation",
                user_id=user_id,
                reference_id=inventory_id,
            )

            logger.info(f"Inventory released: {inventory_id} quantity {quantity}")
            return True

        except Exception as e:
            logger.error(f"Failed to release inventory {inventory_id}: {e}")
            raise

    def get_low_stock_items(self, warehouse_id: str = None) -> List[InventoryItem]:
        """Get inventory items that are low in stock"""
        try:
            query = self.inventory_collection

            if warehouse_id:
                query = query.where("warehouse_id", "==", warehouse_id)

            # Get all items and filter for low stock (Firestore doesn't support complex queries)
            low_stock_items = []
            for doc in query.stream():
                try:
                    item = InventoryItem.from_dict(doc.to_dict())
                    if item.is_low_stock:
                        low_stock_items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse inventory document {doc.id}: {e}")

            return low_stock_items

        except Exception as e:
            logger.error(f"Failed to get low stock items: {e}")
            raise

    def find_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Find product and inventory by barcode"""
        try:
            # Find product by barcode
            product_query = self.products_collection.where("barcode", "==", barcode)

            for doc in product_query.stream():
                product = Product.from_dict(doc.to_dict())

                # Get inventory for this product across all warehouses
                inventory_query = self.inventory_collection.where(
                    "sku", "==", product.sku
                )
                inventory_items = []

                for inv_doc in inventory_query.stream():
                    try:
                        item = InventoryItem.from_dict(inv_doc.to_dict())
                        inventory_items.append(item.to_dict())
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse inventory document {inv_doc.id}: {e}"
                        )

                return {"product": product.to_dict(), "inventory": inventory_items}

            return None

        except Exception as e:
            logger.error(f"Failed to find by barcode {barcode}: {e}")
            raise

    def transfer_inventory(
        self,
        from_warehouse_id: str,
        to_warehouse_id: str,
        sku: str,
        quantity: int,
        notes: str = None,
        user_id: str = None,
    ) -> bool:
        """Transfer inventory between warehouses"""
        try:
            # Get source inventory
            source_item = self.get_inventory_by_warehouse_sku(from_warehouse_id, sku)
            if not source_item or source_item.quantity_available < quantity:
                return False

            # Get or create destination inventory
            dest_item = self.get_inventory_by_warehouse_sku(to_warehouse_id, sku)

            # Update source inventory
            source_item.quantity_on_hand -= quantity
            source_item.quantity_available = max(
                0, source_item.quantity_on_hand - source_item.quantity_reserved
            )
            source_item.updated_at = datetime.utcnow()

            # Update or create destination inventory
            if dest_item:
                dest_item.quantity_on_hand += quantity
                dest_item.quantity_available = max(
                    0, dest_item.quantity_on_hand - dest_item.quantity_reserved
                )
                dest_item.updated_at = datetime.utcnow()
            else:
                dest_item = InventoryItem(
                    inventory_id=f"{to_warehouse_id}_{sku}",
                    warehouse_id=to_warehouse_id,
                    sku=sku,
                    quantity_on_hand=quantity,
                    quantity_reserved=0,
                    quantity_available=quantity,
                )

            # Save both items
            self.inventory_collection.document(source_item.inventory_id).update(
                source_item.to_dict()
            )
            self.inventory_collection.document(dest_item.inventory_id).set(
                dest_item.to_dict()
            )

            # Record movements
            transfer_id = str(uuid.uuid4())

            self._record_movement(
                warehouse_id=from_warehouse_id,
                sku=sku,
                movement_type="transfer_out",
                quantity=-quantity,
                reason=f"Transfer to {to_warehouse_id}: {notes}"
                if notes
                else f"Transfer to {to_warehouse_id}",
                user_id=user_id,
                reference_id=transfer_id,
            )

            self._record_movement(
                warehouse_id=to_warehouse_id,
                sku=sku,
                movement_type="transfer_in",
                quantity=quantity,
                reason=f"Transfer from {from_warehouse_id}: {notes}"
                if notes
                else f"Transfer from {from_warehouse_id}",
                user_id=user_id,
                reference_id=transfer_id,
            )

            logger.info(
                f"Inventory transferred: {quantity} of {sku} from {from_warehouse_id} to {to_warehouse_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to transfer inventory: {e}")
            raise

    def _record_movement(
        self,
        warehouse_id: str,
        sku: str,
        movement_type: str,
        quantity: int,
        reason: str = None,
        user_id: str = None,
        reference_id: str = None,
    ):
        """Record inventory movement for audit trail"""
        try:
            movement_id = str(uuid.uuid4())

            movement_data = {
                "movement_id": movement_id,
                "warehouse_id": warehouse_id,
                "sku": sku,
                "movement_type": movement_type,
                "quantity": quantity,
                "reason": reason,
                "user_id": user_id,
                "reference_id": reference_id,
                "timestamp": datetime.utcnow().timestamp(),
            }

            self.movements_collection.document(movement_id).set(movement_data)

        except Exception as e:
            logger.warning(f"Failed to record inventory movement: {e}")
            # Don't raise exception as this is for audit only
