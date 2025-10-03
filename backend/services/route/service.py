"""
Route Management Service with AI Optimization
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from shared.utils.firebase_config import get_firestore_client
from shared.utils.gemini_client import GeminiClient
from shared.models.route import Route, RouteStop, DeliveryProof

logger = logging.getLogger(__name__)


class RouteService:
    """Route management and optimization service"""

    def __init__(self):
        self.db = get_firestore_client()
        if self.db:
            self.routes_collection = self.db.collection("routes")
        else:
            self.routes_collection = None
        self.gemini_client = GeminiClient()

    def create_route(self, route_data: Dict[str, Any]) -> Route:
        """
        Create new route with AI optimization
        """
        try:
            route_id = str(uuid.uuid4())

            # Extract stops for optimization
            stops_data = route_data.get("stops", [])

            # Optimize route using Gemini AI
            optimized_route = self._optimize_route_with_ai(
                stops_data, route_data.get("constraints")
            )

            # Create route stops
            stops = []
            for i, stop_data in enumerate(
                optimized_route.get("optimized_sequence", stops_data)
            ):
                stop = RouteStop(
                    stop_id=str(uuid.uuid4()),
                    order_id=stop_data["order_id"],
                    sequence=i + 1,
                    address=stop_data["address"],
                    latitude=stop_data.get("latitude"),
                    longitude=stop_data.get("longitude"),
                    planned_arrival=self._calculate_planned_arrival(i, optimized_route),
                    status="pending",
                )
                stops.append(stop)

            # Create route
            route = Route(
                route_id=route_id,
                driver_id=route_data["driver_id"],
                vehicle_id=route_data.get("vehicle_id"),
                status="planned",
                planned_start_time=route_data.get(
                    "planned_start_time", datetime.utcnow()
                ),
                planned_end_time=route_data.get("planned_end_time"),
                total_distance=optimized_route.get("total_distance_km", 0),
                estimated_duration=optimized_route.get("total_time_minutes", 0),
                fuel_estimate=optimized_route.get("fuel_estimate_liters", 0),
                stops=stops,
            )

            # Save to Firestore
            self.routes_collection.document(route_id).set(route.to_dict())

            logger.info(f"Route created with AI optimization: {route_id}")
            return route

        except Exception as e:
            logger.error(f"Failed to create route: {e}")
            raise

    def get_route(self, route_id: str) -> Optional[Route]:
        """Get route by ID"""
        try:
            route_doc = self.routes_collection.document(route_id).get()

            if route_doc.exists:
                return Route.from_dict(route_doc.to_dict())

            return None

        except Exception as e:
            logger.error(f"Failed to get route {route_id}: {e}")
            raise

    def update_route_status(
        self, route_id: str, new_status: str, user_id: str
    ) -> Optional[Route]:
        """Update route status"""
        try:
            route = self.get_route(route_id)
            if not route:
                return None

            old_status = route.status
            route.status = new_status
            route.updated_at = datetime.utcnow()

            # Set timestamps based on status
            if new_status == "active" and not route.actual_start_time:
                route.actual_start_time = datetime.utcnow()
            elif new_status == "completed" and not route.actual_end_time:
                route.actual_end_time = datetime.utcnow()
                route.actual_duration = int(
                    (route.actual_end_time - route.actual_start_time).total_seconds()
                    / 60
                )

            # Save to Firestore
            self.routes_collection.document(route_id).update(route.to_dict())

            logger.info(
                f"Route {route_id} status updated from {old_status} to {new_status}"
            )
            return route

        except Exception as e:
            logger.error(f"Failed to update route status: {e}")
            raise

    def update_stop_status(
        self,
        route_id: str,
        stop_id: str,
        new_status: str,
        delivery_proof: Dict[str, Any] = None,
    ) -> Optional[Route]:
        """Update stop status with delivery proof"""
        try:
            route = self.get_route(route_id)
            if not route:
                return None

            # Find and update the stop
            for stop in route.stops:
                if stop.stop_id == stop_id:
                    stop.status = new_status

                    if new_status == "arrived":
                        stop.actual_arrival = datetime.utcnow()
                    elif new_status == "completed":
                        if delivery_proof:
                            stop.delivery_proof = DeliveryProof(
                                photo_url=delivery_proof.get("photo_url"),
                                signature_url=delivery_proof.get("signature_url"),
                                notes=delivery_proof.get("notes"),
                                recipient_name=delivery_proof.get("recipient_name"),
                                timestamp=datetime.utcnow(),
                            )
                    elif new_status == "failed":
                        stop.attempt_count += 1
                        stop.notes = (
                            delivery_proof.get("failure_reason", "")
                            if delivery_proof
                            else ""
                        )

                    break

            route.updated_at = datetime.utcnow()

            # Save to Firestore
            self.routes_collection.document(route_id).update(route.to_dict())

            return route

        except Exception as e:
            logger.error(f"Failed to update stop status: {e}")
            raise

    def get_driver_routes(
        self, driver_id: str, status: str = None, date: datetime = None
    ) -> List[Route]:
        """Get routes for a specific driver"""
        try:
            query = self.routes_collection.where("driver_id", "==", driver_id)

            if status:
                query = query.where("status", "==", status)

            if date:
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)

                query = query.where(
                    "planned_start_time", ">=", start_of_day.timestamp()
                )
                query = query.where("planned_start_time", "<", end_of_day.timestamp())

            routes = []
            for doc in query.stream():
                try:
                    route = Route.from_dict(doc.to_dict())
                    routes.append(route)
                except Exception as e:
                    logger.warning(f"Failed to parse route document {doc.id}: {e}")

            return routes

        except Exception as e:
            logger.error(f"Failed to get driver routes: {e}")
            raise

    def optimize_existing_route(
        self, route_id: str, constraints: Dict[str, Any] = None
    ) -> Optional[Route]:
        """Re-optimize existing route using AI"""
        try:
            route = self.get_route(route_id)
            if not route or route.status != "planned":
                return None

            # Prepare stops data for optimization
            stops_data = []
            for stop in route.stops:
                stops_data.append(
                    {
                        "id": stop.stop_id,
                        "order_id": stop.order_id,
                        "address": stop.address,
                        "latitude": stop.latitude,
                        "longitude": stop.longitude,
                    }
                )

            # Re-optimize with AI
            optimized_route = self._optimize_route_with_ai(stops_data, constraints)

            # Update route with new optimization
            route.total_distance = optimized_route.get(
                "total_distance_km", route.total_distance
            )
            route.estimated_duration = optimized_route.get(
                "total_time_minutes", route.estimated_duration
            )
            route.fuel_estimate = optimized_route.get(
                "fuel_estimate_liters", route.fuel_estimate
            )

            # Reorder stops based on optimization
            optimized_sequence = optimized_route.get("optimized_sequence", [])
            if optimized_sequence:
                stop_map = {stop.stop_id: stop for stop in route.stops}
                route.stops = []

                for i, stop_id in enumerate(optimized_sequence):
                    if stop_id in stop_map:
                        stop = stop_map[stop_id]
                        stop.sequence = i + 1
                        stop.planned_arrival = self._calculate_planned_arrival(
                            i, optimized_route
                        )
                        route.stops.append(stop)

            route.updated_at = datetime.utcnow()

            # Save to Firestore
            self.routes_collection.document(route_id).update(route.to_dict())

            logger.info(f"Route {route_id} re-optimized with AI")
            return route

        except Exception as e:
            logger.error(f"Failed to optimize existing route: {e}")
            raise

    def get_route_analytics(self, route_id: str) -> Dict[str, Any]:
        """Get analytics for a completed route"""
        try:
            route = self.get_route(route_id)
            if not route:
                return {}

            # Calculate performance metrics
            analytics = {
                "route_id": route_id,
                "planned_vs_actual_time": {},
                "planned_vs_actual_distance": {},
                "delivery_success_rate": 0,
                "on_time_percentage": 0,
                "fuel_efficiency": {},
                "stops_completed": 0,
                "stops_failed": 0,
            }

            # Time analysis
            if route.actual_duration and route.estimated_duration:
                analytics["planned_vs_actual_time"] = {
                    "planned_minutes": route.estimated_duration,
                    "actual_minutes": route.actual_duration,
                    "variance_minutes": route.actual_duration
                    - route.estimated_duration,
                    "variance_percentage": (
                        (route.actual_duration - route.estimated_duration)
                        / route.estimated_duration
                    )
                    * 100,
                }

            # Stop analysis
            completed_stops = len(
                [stop for stop in route.stops if stop.status == "completed"]
            )
            failed_stops = len(
                [stop for stop in route.stops if stop.status == "failed"]
            )
            total_stops = len(route.stops)

            analytics["stops_completed"] = completed_stops
            analytics["stops_failed"] = failed_stops
            analytics["delivery_success_rate"] = (
                (completed_stops / total_stops) * 100 if total_stops > 0 else 0
            )

            # On-time analysis
            on_time_stops = 0
            for stop in route.stops:
                if stop.actual_arrival and stop.planned_arrival:
                    if stop.actual_arrival <= stop.planned_arrival + timedelta(
                        minutes=15
                    ):  # 15 min tolerance
                        on_time_stops += 1

            analytics["on_time_percentage"] = (
                (on_time_stops / total_stops) * 100 if total_stops > 0 else 0
            )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get route analytics: {e}")
            raise

    def _optimize_route_with_ai(
        self, stops_data: List[Dict[str, Any]], constraints: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Use Gemini AI to optimize route"""
        try:
            return self.gemini_client.optimize_route(stops_data, constraints)
        except Exception as e:
            logger.warning(f"AI route optimization failed, using fallback: {e}")
            # Fallback to simple optimization
            return {
                "optimized_sequence": [
                    stop.get("id", i) for i, stop in enumerate(stops_data)
                ],
                "total_distance_km": 50,  # Default estimate
                "total_time_minutes": len(stops_data) * 30,  # 30 min per stop
                "fuel_estimate_liters": 10,
                "recommendations": [
                    "AI optimization unavailable, using default routing"
                ],
            }

    def _calculate_planned_arrival(
        self, stop_index: int, optimized_route: Dict[str, Any]
    ) -> datetime:
        """Calculate planned arrival time for a stop"""
        base_time = datetime.utcnow() + timedelta(hours=1)  # Start in 1 hour

        # Add travel time based on stop sequence
        travel_time_per_stop = optimized_route.get("total_time_minutes", 0) / max(
            1, len(optimized_route.get("optimized_sequence", []))
        )

        arrival_time = base_time + timedelta(minutes=stop_index * travel_time_per_stop)

        return arrival_time
