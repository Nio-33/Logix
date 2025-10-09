# WooCommerce Integration - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you connect your WooCommerce store to Logix and start synchronizing orders.

## Step 1: Get Your WooCommerce API Keys (2 minutes)

1. **Log in to WordPress Admin**
   ```
   https://your-store.com/wp-admin
   ```

2. **Navigate to WooCommerce REST API**
   - WooCommerce → Settings → Advanced → REST API

3. **Create New Key**
   - Click "Add key"
   - Description: `Logix Integration`
   - User: (Select your admin user)
   - Permissions: `Read/Write`
   - Click "Generate API key"

4. **Copy Your Credentials**
   ```
   Consumer Key:    ck_xxxxxxxxxxxxxxxxxxxxx
   Consumer Secret: cs_xxxxxxxxxxxxxxxxxxxxx
   ```
   ⚠️ **Save these now!** You won't see the secret again.

## Step 2: Connect to Logix (1 minute)

### Option A: Using the API

```bash
curl -X POST https://api.logix.com/api/v1/woocommerce/integrations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "store_url": "https://your-store.com",
    "consumer_key": "ck_xxxxxxxxxxxxxxxxxxxxx",
    "consumer_secret": "cs_xxxxxxxxxxxxxxxxxxxxx",
    "integration_name": "My Store",
    "auto_sync": true
  }'
```

### Option B: Using Python

```python
import requests

response = requests.post(
    "https://api.logix.com/api/v1/woocommerce/integrations",
    headers={
        "Authorization": "Bearer YOUR_JWT_TOKEN",
        "Content-Type": "application/json"
    },
    json={
        "store_url": "https://your-store.com",
        "consumer_key": "ck_xxxxxxxxxxxxxxxxxxxxx",
        "consumer_secret": "cs_xxxxxxxxxxxxxxxxxxxxx",
        "integration_name": "My Store",
        "auto_sync": True
    }
)

print(response.json())
```

### Expected Response

```json
{
  "message": "WooCommerce integration created successfully",
  "integration": {
    "id": "integration_abc123",
    "store_url": "https://your-store.com",
    "status": "active"
  }
}
```

## Step 3: Sync Your Orders (1 minute)

```bash
# Replace {integration_id} with your actual integration ID
curl -X POST https://api.logix.com/api/v1/woocommerce/integrations/{integration_id}/sync \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Expected Response

```json
{
  "message": "Sync completed",
  "result": {
    "total_orders": 25,
    "synced": 25,
    "failed": 0
  }
}
```

## Step 4: Set Up Real-Time Webhooks (1 minute)

### Automatic Setup

```bash
curl -X POST https://api.logix.com/api/v1/woocommerce/integrations/{integration_id}/webhooks \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["order.created", "order.updated"],
    "delivery_url": "https://api.logix.com/api/v1/woocommerce/webhooks/receive"
  }'
```

### Manual Setup (Alternative)

1. In WordPress Admin: WooCommerce → Settings → Advanced → Webhooks
2. Click "Add webhook"
3. Configure:
   - Name: `Logix - Order Created`
   - Status: `Active`
   - Topic: `Order created`
   - Delivery URL: `https://api.logix.com/api/v1/woocommerce/webhooks/receive`
   - API Version: `WP REST API Integration v3`
4. Save webhook

## 🎉 You're Done!

Your WooCommerce store is now connected to Logix!

### What Happens Next?

1. **New orders** in WooCommerce automatically appear in Logix
2. **Order statuses** sync between both platforms
3. **Inventory levels** stay synchronized
4. **Fulfillment** can be managed from Logix dashboard

## 📊 View Your Orders

Access your synced orders at:
```
https://app.logix.com/admin/orders
```

Filter by source to see only WooCommerce orders:
```
Source: woocommerce
```

## 🔄 Sync Options

### Sync Specific Status

```bash
# Only sync processing orders
curl -X POST .../sync \
  -d '{"status": "processing"}'
```

### Sync Recent Orders

```bash
# Sync orders from last 7 days
curl -X POST .../sync \
  -d '{"since": "2025-10-02T00:00:00Z"}'
```

### Limit Results

```bash
# Sync maximum 50 orders
curl -X POST .../sync \
  -d '{"limit": 50}'
```

## 🛠️ Quick Troubleshooting

### ❌ "Connection failed"
- Check store URL includes `https://`
- Verify WooCommerce REST API is enabled
- Ensure Pretty Permalinks are active

### ❌ "Authentication failed"
- Regenerate API keys in WooCommerce
- Double-check you copied the full key

### ❌ "Orders not syncing"
- Check webhook delivery in WooCommerce
- Verify order status filter
- Test connection: `GET /integrations/{id}/test`

## 📚 Next Steps

- [Full Integration Guide](./WOOCOMMERCE_INTEGRATION_GUIDE.md)
- [API Reference](./WOOCOMMERCE_API_REFERENCE.md)
- [Advanced Configuration](./WOOCOMMERCE_ADVANCED.md)

## 💡 Pro Tips

1. **Webhook vs Polling**: Webhooks provide real-time updates. Use them for production.
2. **Initial Sync**: Start with a small date range, then expand.
3. **Monitor**: Check sync logs regularly for any errors.
4. **Testing**: Test with a few orders before full rollout.

## 🆘 Need Help?

- 📧 support@logix.com
- 📚 docs.logix.com/woocommerce
- 💬 community.logix.com

---

**Estimated Setup Time**: ⏱️ 5 minutes
**Difficulty**: 🟢 Easy
**Prerequisites**: WooCommerce 3.0+, WordPress with Pretty Permalinks

