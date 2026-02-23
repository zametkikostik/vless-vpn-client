# VLESS VPN SaaS - Quick Start Guide

## 🚀 Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (or Supabase account)
- Redis 7+ (optional, for caching)
- sing-box binary (for VPN engine)

---

## 1. Clone Repository

```bash
git clone https://github.com/zametkikostik/vless-vpn-client.git
cd vless-vpn-client
```

---

## 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install requirements
pip install -r requirements-saas.txt
```

---

## 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env  # or use your favorite editor
```

**Required variables:**
- `SECRET_KEY` - Generate with `openssl rand -hex 32`
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key

**Optional (for payments):**
- `STRIPE_SECRET_KEY` - Stripe API key
- `COINBASE_API_KEY` - Coinbase Commerce API key

---

## 4. Setup Database (Supabase)

### Option A: Using Supabase (Recommended)

1. Create account at https://supabase.com
2. Create new project
3. Go to SQL Editor and run:

```sql
-- Create tables
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  plan VARCHAR(20) DEFAULT 'free',
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  is_active BOOLEAN DEFAULT true
);

CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  plan VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL,
  current_period_start TIMESTAMP,
  current_period_end TIMESTAMP,
  cancel_at_period_end BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vpn_nodes (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  country VARCHAR(50) NOT NULL,
  city VARCHAR(100),
  host VARCHAR(255) NOT NULL,
  port INTEGER NOT NULL,
  protocol VARCHAR(20) DEFAULT 'vless',
  transport VARCHAR(20) DEFAULT 'reality',
  status VARCHAR(20) DEFAULT 'online',
  latency INTEGER DEFAULT 0,
  load DECIMAL(5,2) DEFAULT 0.0
);

CREATE TABLE vpn_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  vless_url TEXT NOT NULL,
  subscription_url TEXT,
  protocol VARCHAR(20),
  transport VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP
);

-- Insert default nodes
INSERT INTO vpn_nodes (id, name, country, city, host, port, status, latency) VALUES
  ('node-eu-1', 'Frankfurt-1', 'Germany', 'Frankfurt', 'de1.vpn.example.com', 443, 'online', 45),
  ('node-us-1', 'New York-1', 'USA', 'New York', 'us1.vpn.example.com', 443, 'online', 120),
  ('node-as-1', 'Singapore-1', 'Singapore', 'Singapore', 'sg1.vpn.example.com', 443, 'online', 85);
```

4. Get your credentials:
   - Settings → API → Project URL → `SUPABASE_URL`
   - Settings → API → anon/public key → `SUPABASE_KEY`

---

## 5. Run API Server

```bash
# Development mode (auto-reload)
uvicorn vless_vpn_api_v2:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn vless_vpn_api_v2:app --host 0.0.0.0 --port 8000 --workers 4
```

**API will be available at:** http://localhost:8000

**Documentation:** http://localhost:8000/api/docs

---

## 6. Test API

### Register New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Get User Info

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Generate VPN Config

```bash
curl -X POST http://localhost:8000/api/v1/configs/generate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"protocol": "vless", "transport": "reality"}'
```

---

## 7. Install sing-box (VPN Engine)

### Linux

```bash
# Download latest release
wget https://github.com/SagerNet/sing-box/releases/latest/download/sing-box-linux-amd64.tar.gz
tar -xzf sing-box-linux-amd64.tar.gz
sudo mv sing-box*/sing-box /usr/local/bin/
sudo chmod +x /usr/local/bin/sing-box

# Verify
sing-box version
```

### macOS

```bash
brew install sing-box
```

### Windows

```powershell
# Download from GitHub Releases
# https://github.com/SagerNet/sing-box/releases
```

---

## 8. Run VPN Engine

```bash
# Connect to VPN
python3 vpn_engine.py connect --server node-eu-1

# With kill switch
python3 vpn_engine.py connect --server node-eu-1 --kill-switch

# Check status
python3 vpn_engine.py status

# Disconnect
python3 vpn_engine.py disconnect
```

---

## 9. Docker Deployment (Optional)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token

### Users
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users/me/usage` - Get usage statistics

### Subscriptions
- `POST /api/v1/subscriptions` - Create subscription
- `GET /api/v1/subscriptions/me` - Get current subscription
- `POST /api/v1/subscriptions/cancel` - Cancel subscription

### VPN Nodes
- `GET /api/v1/nodes` - Get available nodes
- `GET /api/v1/nodes/{node_id}` - Get node details

### VPN Configs
- `POST /api/v1/configs/generate` - Generate VPN config
- `GET /api/v1/configs` - Get user configs

### Billing
- `POST /api/v1/billing/create-payment-intent` - Create Stripe payment
- `POST /api/v1/billing/crypto-charge` - Create crypto charge
- `POST /api/v1/billing/stripe-webhook` - Stripe webhook
- `POST /api/v1/billing/crypto-webhook` - Crypto webhook

---

## 🔧 Troubleshooting

### "sing-box not found"

Install sing-box binary (see step 7).

### "Supabase not configured"

Check your `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`.

### "JWT token invalid"

Make sure `SECRET_KEY` is set and matches between sessions.

### Database connection error

Verify PostgreSQL is running and `DATABASE_URL` is correct.

---

## 📖 Next Steps

1. **Configure Payments** - Set up Stripe and Coinbase Commerce
2. **Deploy to Production** - Use Docker or deploy to VPS
3. **Setup Monitoring** - Configure Sentry and logging
4. **Customize Branding** - Update app name, colors, logos
5. **Add More Nodes** - Deploy VPN nodes in different regions

---

## 🆘 Support

- **Documentation**: `/api/docs` (Swagger UI)
- **GitHub Issues**: https://github.com/zametkikostik/vless-vpn-client/issues
- **Email**: support@vpnsolutions.io

---

**Ready to launch! 🚀**
