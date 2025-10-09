"""
Intelligent Automation for Order Routing and Driver Assignment
Uses AI and business rules to automatically route orders and assign drivers
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from shared.models import Order, IndustryCategory, OrderType
from shared.utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)


class IntelligentOrderRouter:
    """Automatically route orders to optimal warehouses"""
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def auto_route_order(self, order: Order) -> Dict[str, Any]:
        """
        Automatically determine the best warehouse for an order
        based on industry-specific rules
        """
        try:
            # Get available warehouses
            warehouses = self._get_available_warehouses()
            
            # Apply industry-specific routing logic
            if order.industry_category == IndustryCategory.ECOMMERCE:
                best_warehouse = self._route_ecommerce_order(order, warehouses)
            
            elif order.industry_category == IndustryCategory.RETAIL:
                best_warehouse = self._route_retail_order(order, warehouses)
            
            elif order.industry_category == IndustryCategory.FOOD_DELIVERY:
                best_warehouse = self._route_food_delivery_order(order, warehouses)
            
            elif order.industry_category == IndustryCategory.MANUFACTURING:
                best_warehouse = self._route_manufacturing_order(order, warehouses)
            
            elif order.industry_category == IndustryCategory.THIRD_PARTY_LOGISTICS:
                best_warehouse = self._route_3pl_order(order, warehouses)
            
            else:
                # Default routing: closest warehouse with inventory
                best_warehouse = self._route_default(order, warehouses)
            
            logger.info(
                f"Order {order.order_id} auto-routed to warehouse {best_warehouse['warehouse_id']} "
                f"({order.get_industry_display_name()})"
            )
            
            return {
                'warehouse_id': best_warehouse['warehouse_id'],
                'warehouse_name': best_warehouse['name'],
                'routing_reason': best_warehouse.get('reason', 'Optimal warehouse selected'),
                'estimated_fulfillment_time': best_warehouse.get('fulfillment_time', 60),
            }
            
        except Exception as e:
            logger.error(f"Auto-routing failed for order {order.order_id}: {e}")
            return {
                'warehouse_id': None,
                'routing_reason': 'Manual routing required',
            }
    
    def _get_available_warehouses(self) -> List[Dict[str, Any]]:
        """Get list of available warehouses"""
        # In production, this would query Firestore
        # For now, return sample warehouses
        return [
            {
                'warehouse_id': 'WH-001',
                'name': 'Main Distribution Center',
                'location': {'city': 'Los Angeles', 'state': 'CA'},
                'capabilities': ['ecommerce', 'retail', '3pl'],
                'operating_hours': '24/7',
            },
            {
                'warehouse_id': 'WH-002',
                'name': 'Food Hub',
                'location': {'city': 'San Francisco', 'state': 'CA'},
                'capabilities': ['food_delivery'],
                'operating_hours': '6am-10pm',
                'temperature_controlled': True,
            },
            {
                'warehouse_id': 'WH-003',
                'name': 'Manufacturing Facility',
                'location': {'city': 'San Jose', 'state': 'CA'},
                'capabilities': ['manufacturing'],
                'operating_hours': 'Mon-Fri 8am-6pm',
            },
        ]
    
    def _route_ecommerce_order(self, order: Order, warehouses: List[Dict]) -> Dict:
        """Route e-commerce order to warehouse with inventory and fastest shipping"""
        # Priority: Inventory availability > Distance > Operating hours
        ecommerce_warehouses = [w for w in warehouses if 'ecommerce' in w.get('capabilities', [])]
        
        if ecommerce_warehouses:
            best = ecommerce_warehouses[0]
            best['reason'] = 'Fastest e-commerce fulfillment'
            best['fulfillment_time'] = 45
            return best
        
        return warehouses[0] if warehouses else {'warehouse_id': 'MANUAL', 'name': 'Manual Assignment'}
    
    def _route_retail_order(self, order: Order, warehouses: List[Dict]) -> Dict:
        """Route retail order considering compliance and inspection requirements"""
        retail_warehouses = [w for w in warehouses if 'retail' in w.get('capabilities', [])]
        
        if retail_warehouses:
            best = retail_warehouses[0]
            best['reason'] = 'Retail compliance and inspection capabilities'
            best['fulfillment_time'] = 240
            return best
        
        return warehouses[0] if warehouses else {'warehouse_id': 'MANUAL', 'name': 'Manual Assignment'}
    
    def _route_food_delivery_order(self, order: Order, warehouses: List[Dict]) -> Dict:
        """Route food delivery order to nearest temperature-controlled facility"""
        food_warehouses = [w for w in warehouses if 'food_delivery' in w.get('capabilities', [])]
        
        if food_warehouses:
            best = food_warehouses[0]
            best['reason'] = 'Temperature-controlled facility with fast delivery'
            best['fulfillment_time'] = 35
            return best
        
        return warehouses[0] if warehouses else {'warehouse_id': 'MANUAL', 'name': 'Manual Assignment'}
    
    def _route_manufacturing_order(self, order: Order, warehouses: List[Dict]) -> Dict:
        """Route manufacturing order to production facility"""
        mfg_warehouses = [w for w in warehouses if 'manufacturing' in w.get('capabilities', [])]
        
        if mfg_warehouses:
            best = mfg_warehouses[0]
            best['reason'] = 'Production facility with QC capabilities'
            best['fulfillment_time'] = 1440
            return best
        
        return warehouses[0] if warehouses else {'warehouse_id': 'MANUAL', 'name': 'Manual Assignment'}
    
    def _route_3pl_order(self, order: Order, warehouses: List[Dict]) -> Dict:
        """Route 3PL order to client-designated facility"""
        # For 3PL, use client's designated fulfillment center
        if order.third_party_data and order.third_party_data.fulfillment_center:
            return {
                'warehouse_id': order.third_party_data.fulfillment_center,
                'name': f'Client Fulfillment Center ({order.third_party_data.client_name})',
                'reason': 'Client-designated facility',
                'fulfillment_time': order.third_party_data.sla_delivery_time or 240,
            }
        
        tpl_warehouses = [w for w in warehouses if '3pl' in w.get('capabilities', [])]
        if tpl_warehouses:
            return tpl_warehouses[0]
        
        return warehouses[0] if warehouses else {'warehouse_id': 'MANUAL', 'name': 'Manual Assignment'}
    
    def _route_default(self, order: Order, warehouses: List[Dict]) -> Dict:
        """Default routing logic"""
        if warehouses:
            best = warehouses[0]
            best['reason'] = 'Default warehouse assignment'
            best['fulfillment_time'] = 60
            return best
        
        return {'warehouse_id': 'MANUAL', 'name': 'Manual Assignment'}


class IntelligentDriverAssigner:
    """Automatically assign drivers to orders based on availability and suitability"""
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def auto_assign_driver(
        self,
        order: Order,
        warehouse_id: str,
        available_drivers: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Automatically assign the best driver for an order
        """
        try:
            if not available_drivers:
                available_drivers = self._get_available_drivers(warehouse_id)
            
            if not available_drivers:
                logger.warning(f"No available drivers for order {order.order_id}")
                return {
                    'driver_id': None,
                    'assignment_reason': 'No drivers available',
                }
            
            # Apply industry-specific driver selection
            if order.industry_category == IndustryCategory.FOOD_DELIVERY:
                best_driver = self._select_food_delivery_driver(order, available_drivers)
            
            elif order.industry_category == IndustryCategory.RETAIL:
                best_driver = self._select_retail_driver(order, available_drivers)
            
            elif order.industry_category == IndustryCategory.MANUFACTURING:
                best_driver = self._select_manufacturing_driver(order, available_drivers)
            
            else:
                best_driver = self._select_default_driver(order, available_drivers)
            
            logger.info(
                f"Order {order.order_id} auto-assigned to driver {best_driver['driver_id']} "
                f"({order.get_industry_display_name()})"
            )
            
            return best_driver
            
        except Exception as e:
            logger.error(f"Auto-assignment failed for order {order.order_id}: {e}")
            return {
                'driver_id': None,
                'assignment_reason': 'Manual assignment required',
            }
    
    def _get_available_drivers(self, warehouse_id: str) -> List[Dict[str, Any]]:
        """Get available drivers for a warehouse"""
        # In production, this would query Firestore/real-time data
        # For now, return sample drivers
        return [
            {
                'driver_id': 'DRV-001',
                'name': 'John Doe',
                'vehicle_type': 'van',
                'certifications': ['food_safety', 'hazmat'],
                'current_load': 3,
                'max_load': 15,
                'rating': 4.8,
                'specializations': ['food_delivery', 'ecommerce'],
            },
            {
                'driver_id': 'DRV-002',
                'name': 'Jane Smith',
                'vehicle_type': 'truck',
                'certifications': ['forklift', 'hazmat'],
                'current_load': 5,
                'max_load': 25,
                'rating': 4.9,
                'specializations': ['retail', 'manufacturing'],
            },
        ]
    
    def _select_food_delivery_driver(self, order: Order, drivers: List[Dict]) -> Dict:
        """Select best driver for food delivery"""
        # Prefer drivers with food safety certification
        food_certified = [
            d for d in drivers 
            if 'food_safety' in d.get('certifications', []) or 'food_delivery' in d.get('specializations', [])
        ]
        
        if food_certified:
            # Select driver with lowest current load
            best = min(food_certified, key=lambda d: d.get('current_load', 0))
            return {
                'driver_id': best['driver_id'],
                'driver_name': best['name'],
                'assignment_reason': 'Food safety certified, lowest current load',
                'estimated_pickup_time': 10,  # minutes
            }
        
        # Fallback to any available driver
        if drivers:
            best = min(drivers, key=lambda d: d.get('current_load', 0))
            return {
                'driver_id': best['driver_id'],
                'driver_name': best['name'],
                'assignment_reason': 'Available driver with capacity',
                'estimated_pickup_time': 10,
            }
        
        return {'driver_id': None, 'assignment_reason': 'No suitable drivers'}
    
    def _select_retail_driver(self, order: Order, drivers: List[Dict]) -> Dict:
        """Select best driver for retail delivery"""
        # Prefer drivers with trucks for larger retail orders
        truck_drivers = [d for d in drivers if d.get('vehicle_type') == 'truck']
        
        # Check if hazmat certification needed
        needs_hazmat = (
            order.retail_data and 
            order.retail_data.hazmat_classification is not None
        )
        
        if needs_hazmat:
            hazmat_drivers = [d for d in drivers if 'hazmat' in d.get('certifications', [])]
            if hazmat_drivers:
                best = min(hazmat_drivers, key=lambda d: d.get('current_load', 0))
                return {
                    'driver_id': best['driver_id'],
                    'driver_name': best['name'],
                    'assignment_reason': 'Hazmat certified for retail delivery',
                    'estimated_pickup_time': 30,
                }
        
        if truck_drivers:
            best = min(truck_drivers, key=lambda d: d.get('current_load', 0))
            return {
                'driver_id': best['driver_id'],
                'driver_name': best['name'],
                'assignment_reason': 'Truck driver for retail delivery',
                'estimated_pickup_time': 30,
            }
        
        # Fallback
        if drivers:
            best = min(drivers, key=lambda d: d.get('current_load', 0))
            return {
                'driver_id': best['driver_id'],
                'driver_name': best['name'],
                'assignment_reason': 'Available driver',
                'estimated_pickup_time': 30,
            }
        
        return {'driver_id': None, 'assignment_reason': 'No suitable drivers'}
    
    def _select_manufacturing_driver(self, order: Order, drivers: List[Dict]) -> Dict:
        """Select best driver for manufacturing delivery"""
        # Manufacturing often requires specialized vehicles
        mfg_drivers = [d for d in drivers if 'manufacturing' in d.get('specializations', [])]
        
        if mfg_drivers:
            best = min(mfg_drivers, key=lambda d: d.get('current_load', 0))
            return {
                'driver_id': best['driver_id'],
                'driver_name': best['name'],
                'assignment_reason': 'Manufacturing logistics specialist',
                'estimated_pickup_time': 60,
            }
        
        # Fallback to truck drivers
        truck_drivers = [d for d in drivers if d.get('vehicle_type') == 'truck']
        if truck_drivers:
            best = min(truck_drivers, key=lambda d: d.get('current_load', 0))
            return {
                'driver_id': best['driver_id'],
                'driver_name': best['name'],
                'assignment_reason': 'Available truck driver',
                'estimated_pickup_time': 60,
            }
        
        return {'driver_id': None, 'assignment_reason': 'No suitable drivers'}
    
    def _select_default_driver(self, order: Order, drivers: List[Dict]) -> Dict:
        """Default driver selection based on load and rating"""
        if not drivers:
            return {'driver_id': None, 'assignment_reason': 'No drivers available'}
        
        # Select driver with best combination of low load and high rating
        def score_driver(driver):
            load_score = 1 - (driver.get('current_load', 0) / driver.get('max_load', 10))
            rating_score = driver.get('rating', 4.0) / 5.0
            return (load_score * 0.6) + (rating_score * 0.4)
        
        best = max(drivers, key=score_driver)
        
        return {
            'driver_id': best['driver_id'],
            'driver_name': best['name'],
            'assignment_reason': f'Best available (Rating: {best.get("rating", 0)}, Load: {best.get("current_load", 0)}/{best.get("max_load", 0)})',
            'estimated_pickup_time': 20,
        }


class IntelligentAutomationService:
    """
    Orchestrates intelligent automation for order processing
    Combines routing, driver assignment, and workflow automation
    """
    
    def __init__(self):
        self.order_router = IntelligentOrderRouter()
        self.driver_assigner = IntelligentDriverAssigner()
    
    def process_new_order(self, order: Order) -> Dict[str, Any]:
        """
        Automatically process a new order:
        1. Route to optimal warehouse
        2. Assign suitable driver
        3. Set initial workflow status
        4. Calculate estimated delivery time
        """
        try:
            result = {
                'order_id': order.order_id,
                'industry': order.get_industry_display_name(),
                'automation_steps': [],
            }
            
            # Step 1: Auto-route to warehouse
            routing_result = self.order_router.auto_route_order(order)
            result['warehouse'] = routing_result
            result['automation_steps'].append({
                'step': 'warehouse_routing',
                'status': 'completed',
                'result': routing_result['routing_reason'],
            })
            
            # Step 2: Auto-assign driver (if warehouse assigned)
            if routing_result.get('warehouse_id'):
                assignment_result = self.driver_assigner.auto_assign_driver(
                    order,
                    routing_result['warehouse_id']
                )
                result['driver'] = assignment_result
                result['automation_steps'].append({
                    'step': 'driver_assignment',
                    'status': 'completed',
                    'result': assignment_result['assignment_reason'],
                })
            
            # Step 3: Calculate automation success rate
            successful_steps = len([s for s in result['automation_steps'] if s['status'] == 'completed'])
            total_steps = len(result['automation_steps'])
            result['automation_rate'] = (successful_steps / total_steps * 100) if total_steps > 0 else 0
            
            logger.info(
                f"Order {order.order_id} automated: {successful_steps}/{total_steps} steps "
                f"({result['automation_rate']:.0f}%)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Automation processing failed for order {order.order_id}: {e}")
            return {
                'order_id': order.order_id,
                'automation_steps': [],
                'automation_rate': 0,
                'error': str(e),
            }


# Global instances
intelligent_order_router = IntelligentOrderRouter()
intelligent_driver_assigner = IntelligentDriverAssigner()
intelligent_automation_service = IntelligentAutomationService()

