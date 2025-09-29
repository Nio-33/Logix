"""
Inventory Service Routes
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from shared.middleware.auth import require_auth, require_roles
from shared.middleware.rate_limiting import api_rate_limit
from shared.models.user import UserRole
from .service import InventoryService

logger = logging.getLogger(__name__)
inventory_bp = Blueprint('inventory', __name__)
inventory_service = InventoryService()

@inventory_bp.route('/products', methods=['GET'])
@require_auth()
@api_rate_limit
def list_products():
    """
    List products with pagination and filtering
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search')
        
        products = inventory_service.list_products(
            page=page,
            limit=limit,
            category=category,
            status=status,
            search=search
        )
        
        return jsonify({
            'products': [product.to_dict() for product in products],
            'page': page,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"List products error: {e}")
        return jsonify({'error': 'Failed to list products'}), 500

@inventory_bp.route('/products/<sku>', methods=['GET'])
@require_auth()
@api_rate_limit
def get_product(sku):
    """
    Get product by SKU
    """
    try:
        product = inventory_service.get_product(sku)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get product error: {e}")
        return jsonify({'error': 'Failed to get product'}), 500

@inventory_bp.route('/products', methods=['POST'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def create_product():
    """
    Create new product
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sku', 'name', 'description', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        product = inventory_service.create_product(data)
        
        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Create product error: {e}")
        return jsonify({'error': 'Failed to create product'}), 500

@inventory_bp.route('/products/<sku>', methods=['PUT'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def update_product(sku):
    """
    Update existing product
    """
    try:
        data = request.get_json()
        
        product = inventory_service.update_product(sku, data)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update product error: {e}")
        return jsonify({'error': 'Failed to update product'}), 500

@inventory_bp.route('/warehouses', methods=['GET'])
@require_auth()
@api_rate_limit
def list_warehouses():
    """
    List warehouses
    """
    try:
        warehouses = inventory_service.list_warehouses()
        
        return jsonify({
            'warehouses': [warehouse.to_dict() for warehouse in warehouses]
        }), 200
        
    except Exception as e:
        logger.error(f"List warehouses error: {e}")
        return jsonify({'error': 'Failed to list warehouses'}), 500

@inventory_bp.route('/warehouses', methods=['POST'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def create_warehouse():
    """
    Create new warehouse
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['warehouse_id', 'name', 'address', 'city', 'state', 'zip_code', 'country']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        warehouse = inventory_service.create_warehouse(data)
        
        return jsonify({
            'message': 'Warehouse created successfully',
            'warehouse': warehouse.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Create warehouse error: {e}")
        return jsonify({'error': 'Failed to create warehouse'}), 500

@inventory_bp.route('/inventory', methods=['GET'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def list_inventory():
    """
    List inventory items with filtering
    """
    try:
        warehouse_id = request.args.get('warehouse_id')
        sku = request.args.get('sku')
        status = request.args.get('status')
        low_stock = request.args.get('low_stock', type=bool)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        inventory_items = inventory_service.list_inventory(
            warehouse_id=warehouse_id,
            sku=sku,
            status=status,
            low_stock=low_stock,
            page=page,
            limit=limit
        )
        
        return jsonify({
            'inventory': [item.to_dict() for item in inventory_items],
            'page': page,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"List inventory error: {e}")
        return jsonify({'error': 'Failed to list inventory'}), 500

@inventory_bp.route('/inventory/<inventory_id>', methods=['GET'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def get_inventory_item(inventory_id):
    """
    Get specific inventory item
    """
    try:
        item = inventory_service.get_inventory_item(inventory_id)
        
        if not item:
            return jsonify({'error': 'Inventory item not found'}), 404
        
        return jsonify({
            'inventory_item': item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get inventory item error: {e}")
        return jsonify({'error': 'Failed to get inventory item'}), 500

@inventory_bp.route('/inventory/<inventory_id>/adjust', methods=['POST'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def adjust_inventory(inventory_id):
    """
    Adjust inventory quantity
    """
    try:
        data = request.get_json()
        
        if 'new_quantity' not in data:
            return jsonify({'error': 'new_quantity is required'}), 400
        
        new_quantity = data['new_quantity']
        reason = data.get('reason', 'Manual adjustment')
        
        if new_quantity < 0:
            return jsonify({'error': 'Quantity cannot be negative'}), 400
        
        updated_item = inventory_service.adjust_inventory(
            inventory_id, 
            new_quantity, 
            reason,
            request.user_id
        )
        
        if not updated_item:
            return jsonify({'error': 'Inventory item not found'}), 404
        
        return jsonify({
            'message': 'Inventory adjusted successfully',
            'inventory_item': updated_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Adjust inventory error: {e}")
        return jsonify({'error': 'Failed to adjust inventory'}), 500

@inventory_bp.route('/inventory/<inventory_id>/reserve', methods=['POST'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def reserve_inventory(inventory_id):
    """
    Reserve inventory for order
    """
    try:
        data = request.get_json()
        
        if 'quantity' not in data:
            return jsonify({'error': 'quantity is required'}), 400
        
        quantity = data['quantity']
        order_id = data.get('order_id')
        
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
        
        success = inventory_service.reserve_inventory(
            inventory_id, 
            quantity, 
            order_id,
            request.user_id
        )
        
        if not success:
            return jsonify({'error': 'Insufficient inventory or item not found'}), 400
        
        return jsonify({
            'message': 'Inventory reserved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Reserve inventory error: {e}")
        return jsonify({'error': 'Failed to reserve inventory'}), 500

@inventory_bp.route('/inventory/<inventory_id>/release', methods=['POST'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def release_inventory(inventory_id):
    """
    Release reserved inventory
    """
    try:
        data = request.get_json()
        
        if 'quantity' not in data:
            return jsonify({'error': 'quantity is required'}), 400
        
        quantity = data['quantity']
        
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
        
        success = inventory_service.release_inventory(
            inventory_id, 
            quantity,
            request.user_id
        )
        
        if not success:
            return jsonify({'error': 'Inventory item not found'}), 404
        
        return jsonify({
            'message': 'Inventory released successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Release inventory error: {e}")
        return jsonify({'error': 'Failed to release inventory'}), 500

@inventory_bp.route('/inventory/low-stock', methods=['GET'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def get_low_stock_items():
    """
    Get inventory items that are low in stock
    """
    try:
        warehouse_id = request.args.get('warehouse_id')
        
        low_stock_items = inventory_service.get_low_stock_items(warehouse_id)
        
        return jsonify({
            'low_stock_items': [
                {
                    'inventory_item': item.to_dict(),
                    'reorder_needed': True
                }
                for item in low_stock_items
            ],
            'count': len(low_stock_items)
        }), 200
        
    except Exception as e:
        logger.error(f"Get low stock items error: {e}")
        return jsonify({'error': 'Failed to get low stock items'}), 500

@inventory_bp.route('/inventory/barcode/<barcode>', methods=['GET'])
@require_auth()
@api_rate_limit
def find_by_barcode(barcode):
    """
    Find product and inventory by barcode
    """
    try:
        result = inventory_service.find_by_barcode(barcode)
        
        if not result:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Find by barcode error: {e}")
        return jsonify({'error': 'Failed to find product'}), 500

@inventory_bp.route('/inventory/transfer', methods=['POST'])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.WAREHOUSE_STAFF)
@api_rate_limit
def transfer_inventory():
    """
    Transfer inventory between warehouses
    """
    try:
        data = request.get_json()
        
        required_fields = ['from_warehouse_id', 'to_warehouse_id', 'sku', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        from_warehouse_id = data['from_warehouse_id']
        to_warehouse_id = data['to_warehouse_id']
        sku = data['sku']
        quantity = data['quantity']
        notes = data.get('notes')
        
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
        
        if from_warehouse_id == to_warehouse_id:
            return jsonify({'error': 'Source and destination warehouses must be different'}), 400
        
        success = inventory_service.transfer_inventory(
            from_warehouse_id,
            to_warehouse_id,
            sku,
            quantity,
            notes,
            request.user_id
        )
        
        if not success:
            return jsonify({'error': 'Transfer failed - insufficient inventory or invalid warehouses'}), 400
        
        return jsonify({
            'message': 'Inventory transferred successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Transfer inventory error: {e}")
        return jsonify({'error': 'Failed to transfer inventory'}), 500