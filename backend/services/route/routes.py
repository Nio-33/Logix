"""
Route Management Service Routes with AI Integration
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from shared.middleware.auth import require_auth, require_roles
from shared.middleware.rate_limiting import api_rate_limit
from shared.models.user import UserRole
from .service import RouteService

logger = logging.getLogger(__name__)
route_bp = Blueprint("route", __name__)
route_service = RouteService()


@route_bp.route("/", methods=["POST"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def create_route():
    """
    Create new optimized route with AI
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["driver_id", "stops"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        if not data["stops"]:
            return jsonify({"error": "Route must have at least one stop"}), 400

        route = route_service.create_route(data)

        return (
            jsonify(
                {
                    "message": "Route created and optimized successfully",
                    "route": route.to_dict(),
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Create route error: {e}")
        return jsonify({"error": "Failed to create route"}), 500


@route_bp.route("/<route_id>", methods=["GET"])
@require_auth()
@api_rate_limit
def get_route(route_id):
    """
    Get route by ID
    """
    try:
        route = route_service.get_route(route_id)

        if not route:
            return jsonify({"error": "Route not found"}), 404

        # Check user permissions
        user_role = getattr(request, "user_role", None)
        if user_role == UserRole.DRIVER.value and route.driver_id != request.user_id:
            return jsonify({"error": "Access denied"}), 403

        return jsonify({"route": route.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get route error: {e}")
        return jsonify({"error": "Failed to get route"}), 500


@route_bp.route("/<route_id>/status", methods=["PUT"])
@require_auth()
@api_rate_limit
def update_route_status(route_id):
    """
    Update route status
    """
    try:
        data = request.get_json()

        if "status" not in data:
            return jsonify({"error": "status is required"}), 400

        new_status = data["status"]

        # Check permissions
        route = route_service.get_route(route_id)
        if not route:
            return jsonify({"error": "Route not found"}), 404

        user_role = getattr(request, "user_role", None)
        if user_role == UserRole.DRIVER.value and route.driver_id != request.user_id:
            return jsonify({"error": "Access denied"}), 403

        updated_route = route_service.update_route_status(
            route_id, new_status, request.user_id
        )

        return (
            jsonify(
                {
                    "message": "Route status updated successfully",
                    "route": {
                        "route_id": updated_route.route_id,
                        "status": updated_route.status.value,
                        "updated_at": updated_route.updated_at.isoformat(),
                    },
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Update route status error: {e}")
        return jsonify({"error": "Failed to update route status"}), 500


@route_bp.route("/<route_id>/stops/<stop_id>/status", methods=["PUT"])
@require_auth()
@api_rate_limit
def update_stop_status(route_id, stop_id):
    """
    Update stop status with delivery proof
    """
    try:
        data = request.get_json()

        if "status" not in data:
            return jsonify({"error": "status is required"}), 400

        new_status = data["status"]
        delivery_proof = data.get("delivery_proof")

        # Check permissions
        route = route_service.get_route(route_id)
        if not route:
            return jsonify({"error": "Route not found"}), 404

        user_role = getattr(request, "user_role", None)
        if user_role == UserRole.DRIVER.value and route.driver_id != request.user_id:
            return jsonify({"error": "Access denied"}), 403

        updated_route = route_service.update_stop_status(
            route_id, stop_id, new_status, delivery_proof
        )

        if not updated_route:
            return jsonify({"error": "Stop not found"}), 404

        return (
            jsonify(
                {
                    "message": "Stop status updated successfully",
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "status": new_status,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Update stop status error: {e}")
        return jsonify({"error": "Failed to update stop status"}), 500


@route_bp.route("/driver/<driver_id>", methods=["GET"])
@require_auth()
@api_rate_limit
def get_driver_routes(driver_id):
    """
    Get routes for a specific driver
    """
    try:
        # Check permissions
        user_role = getattr(request, "user_role", None)
        if user_role == UserRole.DRIVER.value and driver_id != request.user_id:
            return jsonify({"error": "Access denied"}), 403

        status = request.args.get("status")
        date_str = request.args.get("date")

        date_filter = None
        if date_str:
            date_filter = datetime.fromisoformat(date_str)

        routes = route_service.get_driver_routes(
            driver_id, status=status, date=date_filter
        )

        payload = {
            "routes": [route.to_dict() for route in routes],
            "driver_id": driver_id,
            "count": len(routes),
        }
        return jsonify(payload), 200

    except Exception as e:
        logger.error(f"Get driver routes error: {e}")
        return jsonify({"error": "Failed to get driver routes"}), 500


@route_bp.route("/<route_id>/optimize", methods=["POST"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def optimize_route(route_id):
    """
    Re-optimize existing route using AI
    """
    try:
        data = request.get_json() or {}
        constraints = data.get("constraints")

        optimized_route = route_service.optimize_existing_route(
            route_id, constraints=constraints
        )

        if not optimized_route:
            return jsonify({"error": "Route not found or cannot be optimized"}), 404

        return jsonify({"message": "Route optimized successfully", "route": optimized_route.to_dict()}), 200

    except Exception as e:
        logger.error(f"Optimize route error: {e}")
        return jsonify({"error": "Failed to optimize route"}), 500


@route_bp.route("/<route_id>/analytics", methods=["GET"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.DRIVER)
@api_rate_limit
def get_route_analytics(route_id):
    """
    Get route performance analytics
    """
    try:
        route = route_service.get_route(route_id)
        if not route:
            return jsonify({"error": "Route not found"}), 404

        # Check permissions for drivers
        user_role = getattr(request, "user_role", None)
        if user_role == UserRole.DRIVER.value and route.driver_id != request.user_id:
            return jsonify({"error": "Access denied"}), 403

        analytics = route_service.get_route_analytics(route_id)

        return jsonify({"analytics": analytics}), 200

    except Exception as e:
        logger.error(f"Get route analytics error: {e}")
        return jsonify({"error": "Failed to get route analytics"}), 500


@route_bp.route("/active", methods=["GET"])
@require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)
@api_rate_limit
def get_active_routes():
    """
    Get all active routes for monitoring
    """
    try:
        from shared.utils.firebase_config import get_firestore_client

        db = get_firestore_client()
        routes_collection = db.collection("routes")

        # Query active routes
        query = routes_collection.where("status", "==", "active")

        active_routes = []
        for doc in query.stream():
            try:
                from shared.models.route import Route

                route = Route.from_dict(doc.to_dict())
                active_routes.append(route.to_dict())
            except Exception as e:
                logger.warning(f"Failed to parse route document {doc.id}: {e}")

        return (
            jsonify({"active_routes": active_routes, "count": len(active_routes)}),
            200,
        )

    except Exception as e:
        logger.error(f"Get active routes error: {e}")
        return jsonify({"error": "Failed to get active routes"}), 500


@route_bp.route("/chatbot", methods=["POST"])
@require_auth()
@api_rate_limit
def chatbot_support():
    """
    AI chatbot for route and delivery support
    """
    try:
        data = request.get_json()

        if "message" not in data:
            return jsonify({"error": "message is required"}), 400

        user_message = data["message"]
        context = {
            "user_id": request.user_id,
            "user_role": getattr(request, "user_role", None),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add route context if provided
        route_id = data.get("route_id")
        if route_id:
            route = route_service.get_route(route_id)
            if route:
                context["route"] = {
                    "route_id": route.route_id,
                    "status": route.status.value,
                    "stops_count": len(route.stops),
                    "driver_id": route.driver_id,
                }

        # Get AI response
        from shared.utils.gemini_client import GeminiClient

        gemini_client = GeminiClient()

        response = gemini_client.chatbot_response(user_message, context)

        payload = {"response": response, "timestamp": datetime.utcnow().isoformat()}
        return jsonify(payload), 200

    except Exception as e:
        logger.error(f"Chatbot support error: {e}")
        msg = (
            "I'm sorry, I'm having trouble processing your request right now. "
            "Please try again or contact our support team."
        )
        return jsonify({"response": msg, "error": True}), 500


@route_bp.route("/<route_id>/delivery-proof/<stop_id>", methods=["POST"])
@require_auth()
@api_rate_limit
def upload_delivery_proof(route_id, stop_id):
    """
    Upload and analyze delivery proof image
    """
    try:
        # Check route and stop exist
        route = route_service.get_route(route_id)
        if not route:
            return jsonify({"error": "Route not found"}), 404

        # Check permissions
        user_role = getattr(request, "user_role", None)
        if user_role == UserRole.DRIVER.value and route.driver_id != request.user_id:
            return jsonify({"error": "Access denied"}), 403

        # Get uploaded file
        if "image" not in request.files:
            return jsonify({"error": "Image file is required"}), 400

        image_file = request.files["image"]
        if image_file.filename == "":
            return jsonify({"error": "No image file selected"}), 400

        # Read image data
        image_data = image_file.read()

        # Analyze image with AI
        from shared.utils.gemini_client import GeminiClient

        gemini_client = GeminiClient()

        context = f"Route {route_id}, Stop {stop_id}"
        analysis = gemini_client.analyze_delivery_image(image_data, context)

        # TODO: Save image to Cloud Storage and get URL
        image_url = (
            f"gs://logix-delivery-proofs/{route_id}/{stop_id}/{image_file.filename}"
        )

        # Update stop with delivery proof
        delivery_proof = {
            "photo_url": image_url,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat(),
        }

        route_service.update_stop_status(route_id, stop_id, "completed", delivery_proof)

        return (
            jsonify(
                {
                    "message": "Delivery proof uploaded and analyzed successfully",
                    "analysis": analysis,
                    "image_url": image_url,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Upload delivery proof error: {e}")
        return jsonify({"error": "Failed to upload delivery proof"}), 500
