# 🚚 Logix Platform

**AI-Powered Logistics Operations Management Platform**

A comprehensive, cloud-native logistics platform designed for mid-market logistics companies. Built with modern web technologies and AI-powered automation to streamline supply chain operations.

## ✨ Features

### 🎯 Core Platform
- **Multi-Role User Management**: 5 distinct user types with role-based access control
- **Real-Time Inventory Tracking**: Multi-warehouse support with barcode scanning
- **Order Processing**: Complete order lifecycle management
- **AI-Powered Route Optimization**: Google Gemini integration for intelligent automation
- **Progressive Web Apps**: Mobile-optimized interfaces for drivers and warehouse staff

### 🏗️ Architecture
- **Backend**: Flask microservices with JWT authentication
- **Database**: Firebase Firestore for real-time data
- **AI Integration**: Google Gemini API for intelligent automation
- **Frontend**: Modern HTML5 + Tailwind CSS + Alpine.js
- **Infrastructure**: Docker + Google Cloud Run deployment ready

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+ (for frontend development)
- Docker (optional, for containerized deployment)

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd Logix
   chmod +x scripts/dev-setup.sh
   ./scripts/dev-setup.sh
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start development server**:
   ```bash
   source venv/bin/activate
   python backend/app.py
   ```

4. **Access the application**:
   - **Main Dashboard**: http://localhost:5002/
   - **API Health**: http://localhost:5002/health
   - **API Docs**: http://localhost:5002/api/v1

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the application
# Main Dashboard: http://localhost:5000/
```

## 📁 Project Structure

```
Logix/
├── backend/                 # Flask backend services
│   ├── services/           # Microservices (auth, inventory, orders, routes, analytics)
│   ├── shared/             # Shared utilities and models
│   └── app.py             # Main application entry point
├── frontend/               # Frontend applications
│   ├── admin/             # Admin dashboard
│   ├── customer/          # Customer portal
│   ├── driver/            # Driver mobile app
│   └── warehouse/         # Warehouse management
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── frontend/          # Frontend tests
├── infrastructure/        # Deployment configurations
│   ├── gcp/              # Google Cloud Platform
│   └── terraform/        # Infrastructure as Code
├── scripts/              # Development and deployment scripts
└── docs/                 # Documentation
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=backend --cov-report=html

# Run specific test types
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/   # Integration tests only
```

## 🔧 Development

### Code Quality
- **Linting**: `flake8 backend/`
- **Formatting**: `black backend/`
- **Type Checking**: `mypy backend/`

### API Documentation
- **Health Check**: `GET /health`
- **API Info**: `GET /api/v1`
- **Authentication**: `POST /api/v1/auth/login`

## 🌐 Deployment

### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --config infrastructure/gcp/cloudbuild.yaml
gcloud run deploy logix-platform --image gcr.io/PROJECT_ID/logix-platform
```

### Docker
```bash
# Build image
docker build -t logix-platform .

# Run container
docker run -p 5002:8080 logix-platform
```

## 📊 User Roles

1. **Super Admin**: Full system access and user management
2. **Operations Manager**: Order and inventory management
3. **Warehouse Staff**: Inventory and order fulfillment
4. **Driver**: Delivery management and route optimization
5. **Customer**: Order tracking and self-service

## 🔐 Security

- **Authentication**: Firebase Auth + JWT tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Protection**: End-to-end encryption
- **Rate Limiting**: API protection against abuse
- **CORS**: Configurable cross-origin resource sharing

## 📈 Monitoring

- **Health Checks**: Built-in health monitoring
- **Logging**: Comprehensive application logging
- **Metrics**: Performance and usage analytics
- **Alerts**: Real-time notification system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check the `docs/` directory
- **Issues**: Create a GitHub issue
- **Email**: support@logix-platform.com

---

**Built with ❤️ for the logistics industry**
