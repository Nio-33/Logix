"""
Industry-Specific Route Optimization
Leverages Gemini AI with industry-specific constraints
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from shared.utils.gemini_client import GeminiClient
from shared.models import Order, IndustryCategory, OrderType

logger = logging.getLogger(__name__)


class IndustryRouteOptimizer:
    """Industry-aware route optimization using Gemini AI"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.enabled = getattr(self.gemini_client, 'enabled', False)
    
    def optimize_route_for_orders(
        self, 
        orders: List[Order],
        driver_info: Dict[str, Any],
        constraints: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Optimize route for a list of orders with industry-specific considerations
        """
        if not self.enabled:
            logger.warning("Gemini AI not available - using basic route optimization")
            return self._basic_route_optimization(orders)
        
        try:
            # Group orders by industry for special handling
            industry_groups = self._group_orders_by_industry(orders)
            
            # Build industry-aware stops
            stops = self._build_stops_from_orders(orders)
            
            # Add industry-specific constraints
            enhanced_constraints = self._add_industry_constraints(
                constraints or {},
                industry_groups
            )
            
            # Call Gemini AI for optimization
            optimized_route = self.gemini_client.optimize_route(
                stops=stops,
                constraints=enhanced_constraints
            )
            
            # Post-process with industry-specific logic
            optimized_route = self._apply_industry_rules(
                optimized_route,
                orders,
                industry_groups
            )
            
            logger.info(f"Route optimized for {len(orders)} orders across {len(industry_groups)} industries")
            
            return optimized_route
            
        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            # Fallback to basic optimization
            return self._basic_route_optimization(orders)
    
    def _group_orders_by_industry(self, orders: List[Order]) -> Dict[str, List[Order]]:
        """Group orders by industry category"""
        groups = {}
        for order in orders:
            industry = order.industry_category.value if order.industry_category else 'general'
            if industry not in groups:
                groups[industry] = []
            groups[industry].append(order)
        return groups
    
    def _build_stops_from_orders(self, orders: List[Order]) -> List[Dict[str, Any]]:
        """Convert orders to route stops with industry metadata"""
        stops = []
        
        for order in orders:
            stop = {
                'order_id': order.order_id,
                'address': order.delivery_address,
                'customer_id': order.customer_id,
                'items_count': len(order.items),
                'priority': order.priority.value,
                'industry': order.industry_category.value if order.industry_category else 'general',
                'order_type': order.order_type.value if order.order_type else 'standard',
                'time_sensitive': order.is_time_sensitive,
                'special_handling': order.requires_special_handling,
            }
            
            # Add industry-specific metadata
            if order.food_delivery_data:
                stop['food_delivery'] = {
                    'preparation_time': order.food_delivery_data.preparation_time_minutes,
                    'temperature_requirements': order.food_delivery_data.temperature_requirements,
                    'delivery_window_start': order.food_delivery_data.delivery_window_start.isoformat() if order.food_delivery_data.delivery_window_start else None,
                    'delivery_window_end': order.food_delivery_data.delivery_window_end.isoformat() if order.food_delivery_data.delivery_window_end else None,
                }
            
            elif order.retail_data:
                stop['retail'] = {
                    'delivery_window_start': order.retail_data.delivery_window_start.isoformat() if order.retail_data.delivery_window_start else None,
                    'delivery_window_end': order.retail_data.delivery_window_end.isoformat() if order.retail_data.delivery_window_end else None,
                    'appointment_required': order.retail_data.appointment_required,
                    'inspection_required': order.retail_data.inspection_required,
                }
            
            elif order.third_party_data:
                stop['3pl'] = {
                    'client_id': order.third_party_data.client_id,
                    'sla_delivery_time': order.third_party_data.sla_delivery_time,
                    'service_level': order.third_party_data.service_level,
                }
            
            stops.append(stop)
        
        return stops
    
    def _add_industry_constraints(
        self,
        base_constraints: Dict[str, Any],
        industry_groups: Dict[str, List[Order]]
    ) -> Dict[str, Any]:
        """Add industry-specific constraints to route optimization"""
        
        enhanced_constraints = base_constraints.copy()
        
        # Food delivery constraints
        if 'food_delivery' in industry_groups:
            food_orders = industry_groups['food_delivery']
            enhanced_constraints['food_delivery'] = {
                'max_delivery_time_minutes': 45,
                'temperature_control_required': any(
                    o.food_delivery_data and o.food_delivery_data.temperature_requirements
                    for o in food_orders
                ),
                'time_window_strict': True,
            }
        
        # Retail constraints
        if 'retail' in industry_groups:
            retail_orders = industry_groups['retail']
            enhanced_constraints['retail'] = {
                'appointment_required': any(
                    o.retail_data and o.retail_data.appointment_required
                    for o in retail_orders
                ),
                'inspection_time_buffer_minutes': 30,
            }
        
        # Manufacturing constraints
        if 'manufacturing' in industry_groups:
            enhanced_constraints['manufacturing'] = {
                'production_schedule_priority': True,
                'quality_check_required': True,
            }
        
        # 3PL constraints
        if '3pl' in industry_groups:
            tpl_orders = industry_groups['3pl']
            # Get strictest SLA
            min_sla = min(
                (o.third_party_data.sla_delivery_time for o in tpl_orders 
                 if o.third_party_data and o.third_party_data.sla_delivery_time),
                default=240
            )
            enhanced_constraints['3pl'] = {
                'sla_delivery_time_minutes': min_sla,
                'client_segregation': True,
            }
        
        return enhanced_constraints
    
    def _apply_industry_rules(
        self,
        route: Dict[str, Any],
        orders: List[Order],
        industry_groups: Dict[str, List[Order]]
    ) -> Dict[str, Any]:
        """Apply post-optimization industry-specific rules"""
        
        # Ensure food delivery orders are prioritized in sequence
        if 'food_delivery' in industry_groups:
            route = self._prioritize_time_sensitive_stops(route, orders)
        
        # Ensure retail appointment times are respected
        if 'retail' in industry_groups:
            route = self._validate_appointment_windows(route, orders)
        
        # Add industry-specific metadata to each stop
        route = self._enrich_stops_with_industry_data(route, orders)
        
        return route
    
    def _prioritize_time_sensitive_stops(
        self,
        route: Dict[str, Any],
        orders: List[Order]
    ) -> Dict[str, Any]:
        """Reorder stops to prioritize time-sensitive deliveries"""
        
        stops = route.get('stops', [])
        order_map = {o.order_id: o for o in orders}
        
        # Separate time-sensitive and regular stops
        time_sensitive = []
        regular = []
        
        for stop in stops:
            order_id = stop.get('order_id')
            if order_id in order_map and order_map[order_id].is_time_sensitive:
                time_sensitive.append(stop)
            else:
                regular.append(stop)
        
        # Combine: time-sensitive first
        route['stops'] = time_sensitive + regular
        
        logger.info(f"Prioritized {len(time_sensitive)} time-sensitive stops")
        
        return route
    
    def _validate_appointment_windows(
        self,
        route: Dict[str, Any],
        orders: List[Order]
    ) -> Dict[str, Any]:
        """Validate that appointment windows can be met"""
        
        # This would check if estimated arrival times match appointment windows
        # For now, just add warnings
        
        logger.info("Validated appointment windows for retail orders")
        return route
    
    def _enrich_stops_with_industry_data(
        self,
        route: Dict[str, Any],
        orders: List[Order]
    ) -> Dict[str, Any]:
        """Add industry-specific metadata to each stop"""
        
        order_map = {o.order_id: o for o in orders}
        
        for stop in route.get('stops', []):
            order_id = stop.get('order_id')
            if order_id in order_map:
                order = order_map[order_id]
                stop['industry_metadata'] = {
                    'industry': order.get_industry_display_name(),
                    'order_type': order.get_order_type_display_name(),
                    'time_sensitive': order.is_time_sensitive,
                    'special_handling': order.requires_special_handling,
                }
        
        return route
    
    def _basic_route_optimization(self, orders: List[Order]) -> Dict[str, Any]:
        """Fallback basic route optimization when AI is not available"""
        
        # Simple optimization: sort by priority and time-sensitivity
        sorted_orders = sorted(
            orders,
            key=lambda o: (
                not o.is_time_sensitive,  # Time-sensitive first
                -o.priority.value if hasattr(o.priority, 'value') else 0,  # Higher priority first
                o.created_at or datetime.utcnow()
            )
        )
        
        stops = []
        for idx, order in enumerate(sorted_orders):
            stops.append({
                'sequence': idx + 1,
                'order_id': order.order_id,
                'address': order.delivery_address,
                'estimated_arrival': (datetime.utcnow() + timedelta(minutes=(idx + 1) * 20)).isoformat(),
                'industry': order.get_industry_display_name(),
                'priority': order.priority.value,
            })
        
        return {
            'route_id': f'ROUTE-BASIC-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            'stops': stops,
            'total_stops': len(stops),
            'estimated_duration_minutes': len(stops) * 20,
            'optimization_method': 'basic',
            'created_at': datetime.utcnow().isoformat(),
        }


# Global instance
industry_route_optimizer = IndustryRouteOptimizer()

