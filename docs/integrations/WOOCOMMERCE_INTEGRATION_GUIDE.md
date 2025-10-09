# WooCommerce Integration Guide

## Overview

The Logix WooCommerce integration enables seamless synchronization of orders, products, and inventory between your WooCommerce store and the Logix logistics platform. This integration supports both manual and automatic order syncing, real-time inventory updates, and bidirectional status updates.

## Features

### ✅ Core Capabilities
- **Automatic Order Sync**: Pull orders from WooCommerce automatically
- **Bidirectional Status Updates**: Update order status in both systems
- **Inventory Synchronization**: Keep product stock levels in sync
- **Webhook Support**: Real-time updates via WooCommerce webhooks
- **Multi-Store Support**: Connect multiple WooCommerce stores
- **Flexible Filtering**: Sync orders by status, date range, or other criteria

### 📊 Supported Data
- **Orders**: Full order details including line items, customer info, shipping address
- **Products**: SKU, name, stock levels
- **Customers**: Basic customer information
- **Order Status**: Bidirectional status mapping

## Setup Guide

### 1. Prerequisites

- WooCommerce store with REST API enabled
- WooCommerce 3.0 or higher
- WordPress with Pretty Permalinks enabled
- SSL certificate (recommended for production)

### 2. Generate WooCommerce API Keys

1. **Log in to WordPress Admin**
   - Navigate to your WordPress admin dashboard

2. **Go to WooCommerce Settings**
   - Click on `WooCommerce` → `Settings`

3. **Navigate to Advanced Tab**
   - Click on the `Advanced` tab
   - Click on `REST API`

4. **Create API Keys**
   - Click `Add key`
   - Fill in the details:
     - **Description**: `Logix Integration`
     - **User**: Select admin user
     - **Permissions**: `Read/Write`
   - Click `Generate API key`

5. **Copy Credentials**
   - **Consumer Key**: `ck_xxxxxxxxxxxxxxxxxxxxxx`
   - **Consumer Secret**: `cs_xxxxxxxxxxxxxxxxxxxxxx`
   - ⚠️ **Save these immediately** - the secret won't be shown again!

### 3. Configure Integration in Logix

#### Using API

```bash
POST https://api.logix.com/api/v1/woocommerce/integrations

Headers:
  Authorization: Bearer YOUR_JWT_TOKEN
  Content-Type: application/json

Body:
{
  "store_url": "https://your-store.com",
  "consumer_key": "ck_xxxxxxxxxxxxxxxxxxxxxx",
  "consumer_secret": "cs_xxxxxxxxxxxxxxxxxxxxxx",
  "integration_name": "My WooCommerce Store",
  "auto_sync": true
}
```

#### Response

```json
{
  "message": "WooCommerce integration created successfully",
  "integration": {
    "id": "integration_abc123",
    "user_id": "user_xyz789",
    "platform": "woocommerce",
    "store_url": "https://your-store.com",
    "integration_name": "My WooCommerce Store",
    "auto_sync": true,
    "status": "active",
    "created_at": "2025-10-09T10:00:00Z"
  }
}
```

## API Reference

### Create Integration

```http
POST /api/v1/woocommerce/integrations
```

**Request Body:**
```json
{
  "store_url": "https://your-store.com",
  "consumer_key": "ck_...",
  "consumer_secret": "cs_...",
  "integration_name": "My Store",
  "auto_sync": true
}
```

### List Integrations

```http
GET /api/v1/woocommerce/integrations
```

**Response:**
```json
{
  "integrations": [
    {
      "id": "integration_abc123",
      "platform": "woocommerce",
      "store_url": "https://your-store.com",
      "integration_name": "My Store",
      "status": "active",
      "last_sync": "2025-10-09T14:30:00Z"
    }
  ],
  "count": 1
}
```

### Sync Orders

```http
POST /api/v1/woocommerce/integrations/{integration_id}/sync
```

**Request Body (Optional):**
```json
{
  "status": "processing",
  "since": "2025-10-01T00:00:00Z",
  "limit": 100
}
```

**Response:**
```json
{
  "message": "Sync completed",
  "result": {
    "integration_id": "integration_abc123",
    "timestamp": "2025-10-09T15:00:00Z",
    "total_orders": 45,
    "synced": 45,
    "failed": 0,
    "errors": []
  }
}
```

### Sync Product Stock

```http
POST /api/v1/woocommerce/integrations/{integration_id}/products/sync
```

**Request Body:**
```json
{
  "sku": "PROD-123",
  "quantity": 50
}
```

### Setup Webhooks

```http
POST /api/v1/woocommerce/integrations/{integration_id}/webhooks
```

**Request Body:**
```json
{
  "topics": [
    "order.created",
    "order.updated",
    "product.updated"
  ],
  "delivery_url": "https://api.logix.com/api/v1/woocommerce/webhooks/receive"
}
```

## Order Status Mapping

### WooCommerce → Logix

| WooCommerce Status | Logix Status |
|-------------------|--------------|
| pending | PENDING |
| processing | PROCESSING |
| on-hold | PENDING |
| completed | DELIVERED |
| cancelled | CANCELLED |
| refunded | RETURNED |
| failed | CANCELLED |

### Logix → WooCommerce

| Logix Status | WooCommerce Status |
|-------------|-------------------|
| PENDING | pending |
| CONFIRMED | processing |
| PROCESSING | processing |
| PICKED | processing |
| PACKED | processing |
| SHIPPED | processing |
| OUT_FOR_DELIVERY | processing |
| DELIVERED | completed |
| CANCELLED | cancelled |
| RETURNED | refunded |

## Webhook Configuration

### 1. Automatic Webhook Setup

Use the API to automatically create webhooks in your WooCommerce store:

```bash
POST /api/v1/woocommerce/integrations/{integration_id}/webhooks

{
  "topics": ["order.created", "order.updated", "product.updated"],
  "delivery_url": "https://api.logix.com/api/v1/woocommerce/webhooks/receive"
}
```

### 2. Manual Webhook Setup

If you prefer to set up webhooks manually in WooCommerce:

1. Go to `WooCommerce` → `Settings` → `Advanced` → `Webhooks`
2. Click `Add webhook`
3. Configure:
   - **Name**: `Logix - Order Created`
   - **Status**: `Active`
   - **Topic**: `Order created`
   - **Delivery URL**: `https://api.logix.com/api/v1/woocommerce/webhooks/receive`
   - **Secret**: (optional, for signature verification)
   - **API Version**: `WP REST API Integration v3`

4. Repeat for other events:
   - Order updated
   - Order deleted
   - Product updated

### 3. Webhook Events

Supported webhook topics:
- `order.created` - New order placed
- `order.updated` - Order status or details changed
- `order.deleted` - Order deleted/trashed
- `product.updated` - Product or stock level changed
- `product.created` - New product added
- `product.deleted` - Product deleted

## Data Flow

### Order Sync Flow

```
WooCommerce → Logix
1. Customer places order in WooCommerce
2. Webhook triggers or manual sync pulls order
3. Order is mapped to Logix format
4. Order created in Logix system
5. Fulfillment process begins
6. Status updates sync back to WooCommerce
```

### Inventory Sync Flow

```
Logix → WooCommerce
1. Inventory level changes in Logix
2. Stock update API call to WooCommerce
3. Product stock quantity updated in WooCommerce
4. Customers see real-time stock availability
```

## Best Practices

### 1. Security
- ✅ Always use HTTPS for your WooCommerce store
- ✅ Store API credentials securely (never commit to version control)
- ✅ Use webhook secrets for signature verification
- ✅ Regularly rotate API keys
- ✅ Limit API key permissions to Read/Write only

### 2. Performance
- ✅ Use webhooks for real-time updates instead of polling
- ✅ Sync orders incrementally (use `since` parameter)
- ✅ Limit batch sizes to 100 orders per request
- ✅ Implement retry logic with exponential backoff
- ✅ Monitor API rate limits

### 3. Data Management
- ✅ Sync orders at regular intervals (e.g., every 5-15 minutes)
- ✅ Keep order IDs prefixed (e.g., `WC-12345`) for easy identification
- ✅ Log all sync operations for debugging
- ✅ Handle duplicate orders gracefully
- ✅ Maintain audit trail of status changes

### 4. Error Handling
- ✅ Implement comprehensive error logging
- ✅ Set up alerts for sync failures
- ✅ Provide manual sync option as fallback
- ✅ Handle network timeouts gracefully
- ✅ Validate data before syncing

## Troubleshooting

### Common Issues

#### 1. Connection Failed

**Problem**: Cannot connect to WooCommerce store

**Solutions**:
- Verify store URL is correct (include `https://`)
- Check if REST API is enabled in WooCommerce
- Ensure Pretty Permalinks are enabled in WordPress
- Verify API keys are correct and have Read/Write permissions
- Check SSL certificate is valid

#### 2. Authentication Failed

**Problem**: 401 Unauthorized error

**Solutions**:
- Regenerate API keys in WooCommerce
- Verify Consumer Key and Secret are correctly copied
- Check API key hasn't been deleted or revoked
- Ensure API version is compatible (v3 recommended)

#### 3. Orders Not Syncing

**Problem**: Orders not appearing in Logix

**Solutions**:
- Check sync logs for errors
- Verify order status filter settings
- Ensure date range parameters are correct
- Check webhook delivery status in WooCommerce
- Test connection using test endpoint

#### 4. Stock Not Updating

**Problem**: Stock levels not syncing to WooCommerce

**Solutions**:
- Verify SKU matches exactly between systems
- Check if product exists in WooCommerce
- Ensure stock management is enabled for product
- Review API response for error messages
- Check WooCommerce product variations

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs at: `/var/log/logix/woocommerce.log`

## Code Examples

### Python Example: Create Integration

```python
import requests

# Your Logix API credentials
LOGIX_API_URL = "https://api.logix.com"
JWT_TOKEN = "your_jwt_token_here"

# WooCommerce credentials
woo_data = {
    "store_url": "https://your-store.com",
    "consumer_key": "ck_xxxxxxxxxxxxxxxxxx",
    "consumer_secret": "cs_xxxxxxxxxxxxxxxxxx",
    "integration_name": "My WooCommerce Store",
    "auto_sync": True
}

# Create integration
response = requests.post(
    f"{LOGIX_API_URL}/api/v1/woocommerce/integrations",
    headers={
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    },
    json=woo_data
)

if response.status_code == 201:
    integration = response.json()["integration"]
    print(f"Integration created: {integration['id']}")
else:
    print(f"Error: {response.json()}")
```

### Python Example: Manual Sync

```python
# Sync orders from last 7 days
from datetime import datetime, timedelta

integration_id = "your_integration_id"
since_date = (datetime.now() - timedelta(days=7)).isoformat()

response = requests.post(
    f"{LOGIX_API_URL}/api/v1/woocommerce/integrations/{integration_id}/sync",
    headers={
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "status": "processing",
        "since": since_date,
        "limit": 100
    }
)

result = response.json()
print(f"Synced {result['result']['synced']} orders")
```

### JavaScript Example: Sync Orders

```javascript
const axios = require('axios');

const LOGIX_API_URL = 'https://api.logix.com';
const JWT_TOKEN = 'your_jwt_token_here';
const INTEGRATION_ID = 'your_integration_id';

async function syncOrders() {
  try {
    const response = await axios.post(
      `${LOGIX_API_URL}/api/v1/woocommerce/integrations/${INTEGRATION_ID}/sync`,
      {
        status: 'processing',
        limit: 50
      },
      {
        headers: {
          'Authorization': `Bearer ${JWT_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );

    console.log('Sync result:', response.data);
  } catch (error) {
    console.error('Sync failed:', error.response.data);
  }
}

syncOrders();
```

## Advanced Configuration

### Custom Order Mapping

You can customize how WooCommerce orders are mapped to Logix by modifying the mapping logic in `backend/services/integrations/woocommerce/service.py`.

### Scheduled Syncing

Set up a cron job for automatic syncing:

```bash
# Sync orders every 15 minutes
*/15 * * * * curl -X POST https://api.logix.com/api/v1/woocommerce/integrations/{id}/sync \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Multi-Warehouse Support

For multi-warehouse setups, you can route orders to specific warehouses based on:
- Customer location
- Product availability
- Custom business rules

## Support

For additional help:
- 📧 Email: support@logix.com
- 📚 Documentation: https://docs.logix.com
- 💬 Community: https://community.logix.com
- 🐛 Issues: https://github.com/logix/logix/issues

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-09 | Initial release with order and inventory sync |

## License

This integration is part of the Logix platform and is subject to the Logix Terms of Service.

