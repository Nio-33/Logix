"""
Logix Platform - Main Application Entry Point
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from shared.middleware.auth import auth_middleware
from shared.middleware.logging import setup_logging
from shared.middleware.rate_limiting import setup_rate_limiting
from shared.utils.firebase_config import initialize_firebase

# Import service blueprints
from services.auth.routes import auth_bp
from services.inventory.routes import inventory_bp
from services.order.routes import order_bp
from services.route.routes import route_bp
from services.analytics.routes import analytics_bp

# Load environment variables
load_dotenv()


def create_app(config_name="development"):
    """
    Application factory pattern for creating Flask app instances
    """
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600)
    )
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 16777216))

    # CORS Configuration
    cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
    CORS(app, origins=cors_origins)

    # JWT Manager
    jwt = JWTManager(app)

    # Initialize middleware
    setup_logging(app)
    setup_rate_limiting(app)
    auth_middleware(app, jwt)

    # Initialize Firebase (skip in development if not configured)
    try:
        initialize_firebase()
    except Exception as e:
        if config_name == "development":
            app.logger.warning(f"Firebase initialization skipped in development: {e}")
        else:
            raise

    # Demo endpoints for dashboard (no authentication required)
    @app.route("/api/v1/analytics/kpis")
    def demo_kpis():
        """Demo KPIs for dashboard"""
        return (
            jsonify(
                {
                    "totalOrders": 1247,
                    "deliveriesToday": 23,
                    "avgDeliveryTime": "2.4h",
                    "customerRating": "4.8",
                }
            ),
            200,
        )

    @app.route("/api/v1/orders")
    def demo_orders():
        """Demo orders for dashboard"""
        return (
            jsonify(
                {
                    "orders": [
                        {
                            "order_id": "ORD-001",
                            "customer_name": "John Doe",
                            "status": "pending",
                            "total_amount": 156.99,
                            "created_at": "2025-09-26T10:00:00Z",
                        },
                        {
                            "order_id": "ORD-002",
                            "customer_name": "Jane Smith",
                            "status": "shipped",
                            "total_amount": 89.50,
                            "created_at": "2025-09-25T14:30:00Z",
                        },
                        {
                            "order_id": "ORD-003",
                            "customer_name": "Bob Johnson",
                            "status": "delivered",
                            "total_amount": 234.75,
                            "created_at": "2025-09-24T09:15:00Z",
                        },
                    ]
                }
            ),
            200,
        )

    @app.route("/api/v1/inventory")
    def demo_inventory():
        """Demo inventory for dashboard"""
        return (
            jsonify(
                {
                    "inventory": [
                        {
                            "inventory_id": "INV-001",
                            "sku": "PROD-001",
                            "product_name": "Widget A",
                            "warehouse_name": "Main Warehouse",
                            "quantity_available": 45,
                            "quantity_on_hand": 50,
                            "status": "available",
                        },
                        {
                            "inventory_id": "INV-002",
                            "sku": "PROD-002",
                            "product_name": "Widget B",
                            "warehouse_name": "Main Warehouse",
                            "quantity_available": 8,
                            "quantity_on_hand": 10,
                            "status": "low_stock",
                        },
                    ]
                }
            ),
            200,
        )

    @app.route("/api/v1/inventory/low-stock")
    def demo_low_stock():
        """Demo low stock items"""
        return (
            jsonify(
                {
                    "low_stock_items": [
                        {
                            "inventory_item": {
                                "inventory_id": "INV-002",
                                "sku": "PROD-002",
                                "product_name": "Widget B",
                                "quantity_available": 8,
                            },
                            "reorder_needed": True,
                        }
                    ]
                }
            ),
            200,
        )

    @app.route("/api/v1/notifications")
    def demo_notifications():
        """Demo notifications for dashboard"""
        return (
            jsonify(
                {
                    "notifications": [
                        {
                            "id": 1,
                            "message": "Low stock alert: 5 items below reorder point",
                            "time": "2 minutes ago",
                            "type": "warning",
                        },
                        {
                            "id": 2,
                            "message": "New order #12345 received",
                            "time": "5 minutes ago",
                            "type": "info",
                        },
                    ]
                }
            ),
            200,
        )

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(inventory_bp, url_prefix="/api/v1/inventory")
    app.register_blueprint(order_bp, url_prefix="/api/v1/orders")
    app.register_blueprint(route_bp, url_prefix="/api/v1/routes")
    app.register_blueprint(analytics_bp, url_prefix="/api/v1/analytics")

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint for load balancer"""
        return (
            jsonify(
                {"status": "healthy", "service": "logix-platform", "version": "1.0.0"}
            ),
            200,
        )

    # Serve admin dashboard
    @app.route("/")
    @app.route("/admin")
    def admin_dashboard():
        """Serve the admin dashboard"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "index.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"""
            <html>
            <head><title>Logix Platform</title></head>
            <body>
                <h1>🚚 Logix Platform</h1>
                <h2>AI-Powered Logistics Operations</h2>
                <p><strong>Backend API Status:</strong> ✅ Running</p>
                <p><strong>Version:</strong> 1.0.0</p>
                <p><strong>Environment:</strong> Development</p>
                
                <h3>Available API Endpoints:</h3>
                <ul>
                    <li><a href="/health" target="_blank">GET /health</a> - Health check</li>
                    <li><a href="/api/v1" target="_blank">GET /api/v1</a> - API information</li>
                    <li>POST /api/v1/auth/login - User authentication</li>
                    <li>GET /api/v1/inventory - Inventory management</li>
                    <li>GET /api/v1/orders - Order management</li>
                    <li>GET /api/v1/routes - Route optimization</li>
                    <li>GET /api/v1/analytics - Analytics & reporting</li>
                </ul>
                
                <h3>Features:</h3>
                <ul>
                    <li>✅ Multi-service architecture (Auth, Inventory, Orders, Routes, Analytics)</li>
                    <li>✅ Firebase integration (disabled in dev mode)</li>
                    <li>✅ Gemini AI integration (disabled without API key)</li>
                    <li>✅ JWT authentication with RBAC</li>
                    <li>✅ Rate limiting (disabled in dev mode)</li>
                    <li>✅ Comprehensive logging</li>
                </ul>
                
                <p><em>Error loading admin dashboard: {e}</em></p>
            </body>
            </html>
            """

    # Serve order management page
    @app.route("/admin/orders")
    def admin_orders():
        """Serve the admin order management page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "orders.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Orders</h1><p>Error loading orders page: {e}</p></body></html>"

    # Serve inventory management page
    @app.route("/admin/inventory")
    def admin_inventory():
        """Serve the admin inventory management page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "inventory.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Inventory</h1><p>Error loading inventory page: {e}</p></body></html>"

    # Serve routes management page
    @app.route("/admin/routes")
    def admin_routes():
        """Serve the admin routes management page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "routes.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Routes</h1><p>Error loading routes page: {e}</p></body></html>"

    # Serve analytics management page
    @app.route("/admin/analytics")
    def admin_analytics():
        """Serve the admin analytics management page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "analytics.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Analytics</h1><p>Error loading analytics page: {e}</p></body></html>"

    # Serve users management page
    @app.route("/admin/users")
    def admin_users():
        """Serve the admin users management page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "users.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Users</h1><p>Error loading users page: {e}</p></body></html>"

    # Serve settings page
    @app.route("/admin/settings")
    def admin_settings():
        """Serve the admin settings page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "settings.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Settings</h1><p>Error loading settings page: {e}</p></body></html>"

    # Serve profile page
    @app.route("/admin/profile")
    def admin_profile():
        """Serve the admin profile page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "profile.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Profile</h1><p>Error loading profile page: {e}</p></body></html>"

    # Authentication routes
    @app.route("/auth/login")
    def auth_login():
        """Serve the login page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "auth",
                "login.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Login</h1><p>Error loading login page: {e}</p></body></html>"

    @app.route("/auth/signup")
    def auth_signup():
        """Serve the sign up page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "auth",
                "signup.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Sign Up</h1><p>Error loading signup page: {e}</p></body></html>"

    @app.route("/auth/reset-password")
    def auth_reset_password():
        """Serve the password reset page"""
        try:
            import os

            frontend_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "auth",
                "reset-password.html",
            )
            with open(frontend_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<html><body><h1>Reset Password</h1><p>Error loading reset password page: {e}</p></body></html>"

    # Serve JavaScript files
    @app.route("/js/<path:filename>")
    def serve_js(filename):
        """Serve JavaScript files"""
        try:
            import os

            js_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "admin",
                "js",
                filename,
            )
            with open(js_path, "r") as f:
                return f.read(), 200, {"Content-Type": "application/javascript"}
        except Exception as e:
            return (
                f"// Error loading {filename}: {e}",
                404,
                {"Content-Type": "application/javascript"},
            )

    # Serve shared utility files
    @app.route("/shared/utils/<path:filename>")
    def serve_shared_utils(filename):
        """Serve shared utility files (JavaScript, CSS, etc.)"""
        try:
            import os

            utils_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "frontend",
                "shared",
                "utils",
                filename,
            )
            
            # Determine content type
            content_type = "application/javascript"
            if filename.endswith('.css'):
                content_type = "text/css"
            
            with open(utils_path, "r") as f:
                return f.read(), 200, {"Content-Type": content_type}
        except Exception as e:
            return (
                f"// Error loading {filename}: {e}",
                404,
                {"Content-Type": "application/javascript"},
            )

    # Serve favicon
    @app.route("/favicon.ico")
    def serve_favicon():
        """Serve favicon"""
        return "", 204  # No content response for favicon

    # Test chart page
    @app.route("/test-chart")
    def test_chart():
        """Test chart page"""
        try:
            import os

            test_path = os.path.join(
                os.path.dirname(__file__), "..", "tests", "frontend", "test_chart.html"
            )
            with open(test_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error loading test chart: {e}", 500

    # Simple chart test page
    @app.route("/simple-chart")
    def simple_chart():
        """Simple chart test page"""
        try:
            import os

            test_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "tests",
                "frontend",
                "simple_chart_test.html",
            )
            with open(test_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error loading simple chart test: {e}", 500

    # Minimal chart test page
    @app.route("/minimal-test")
    def minimal_test():
        """Minimal chart test page"""
        try:
            import os

            test_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "tests",
                "frontend",
                "minimal_test.html",
            )
            with open(test_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error loading minimal test: {e}", 500

    # API documentation endpoint
    @app.route("/api/v1")
    def api_info():
        """API information endpoint"""
        return (
            jsonify(
                {
                    "name": "Logix Platform API",
                    "version": "1.0.0",
                    "description": "AI-powered logistics operations management platform",
                    "endpoints": {
                        "auth": "/api/v1/auth",
                        "inventory": "/api/v1/inventory",
                        "orders": "/api/v1/orders",
                        "routes": "/api/v1/routes",
                        "analytics": "/api/v1/analytics",
                    },
                    "documentation": "/docs",
                }
            ),
            200,
        )

    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    app.run(host="0.0.0.0", port=port, debug=debug)
