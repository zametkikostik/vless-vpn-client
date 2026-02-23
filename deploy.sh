#!/bin/bash
# VLESS VPN SaaS - Production Deployment Script
# © 2024 VPN Solutions Inc.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env"
COMPOSE_FILE="docker-compose.yml"

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   VLESS VPN SaaS - Production Deployment              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Creating .env file...${NC}"
    cat > "$ENV_FILE" << EOF
# Database
DB_PASSWORD=$(openssl rand -base64 32)

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32)

# JWT Secret
SECRET_KEY=$(openssl rand -base64 48)

# VLESS Configuration
VLESS_UUID=$(uuidgen || cat /proc/sys/kernel/random/uuid)
XRAY_PRIVATE_KEY=$(openssl genpkey -algorithm X25519 -outform PEM | openssl pkey -text -noout | grep -A1 "priv:" | tail -1 | tr -d ' :')

# Stripe (optional)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Domain (for production)
DOMAIN_NAME=vpn.example.com
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
fi

# Load environment variables
source "$ENV_FILE"

# Step 1: Create directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p xray/certs
mkdir -p db/init
mkdir -p web/dist
mkdir -p logs

# Step 2: Generate SSL certificates (for production)
echo -e "${YELLOW}🔐 Generating SSL certificates...${NC}"
if [ ! -f "xray/certs/server.crt" ]; then
    openssl req -x509 -nodes -newkey ec:<(openssl ecparam -name prime256v1) \
        -keyout xray/certs/server.key \
        -out xray/certs/server.crt \
        -subj "/CN=vpn.example.com" \
        -days 3650
    echo -e "${GREEN}✅ SSL certificates generated${NC}"
fi

# Step 3: Initialize database
echo -e "${YELLOW}🗄️  Initializing database...${NC}"
cat > db/init.sql << 'EOF'
-- VLESS VPN SaaS Database Schema

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plan VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS vpn_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    node_id VARCHAR(50) NOT NULL,
    vless_url TEXT NOT NULL,
    protocol VARCHAR(20) DEFAULT 'vless',
    transport VARCHAR(20) DEFAULT 'reality',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vpn_nodes (
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
    load DECIMAL(5,2) DEFAULT 0.0,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255),
    plan VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    bytes_uploaded BIGINT DEFAULT 0,
    bytes_downloaded BIGINT DEFAULT 0,
    connections_count INTEGER DEFAULT 0,
    last_connection TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_vpn_configs_user_id ON vpn_configs(user_id);
CREATE INDEX idx_vpn_nodes_status ON vpn_nodes(status);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_usage_stats_user_id ON usage_stats(user_id);

-- Insert default nodes
INSERT INTO vpn_nodes (id, name, country, city, host, port, status, latency) VALUES
    ('node-eu-1', 'Frankfurt-1', 'Germany', 'Frankfurt', 'de1.vpn.example.com', 443, 'online', 45),
    ('node-eu-2', 'Amsterdam-1', 'Netherlands', 'Amsterdam', 'nl1.vpn.example.com', 443, 'online', 38),
    ('node-us-1', 'New York-1', 'USA', 'New York', 'us1.vpn.example.com', 443, 'online', 120),
    ('node-us-2', 'Los Angeles-1', 'USA', 'Los Angeles', 'us2.vpn.example.com', 443, 'online', 150),
    ('node-as-1', 'Singapore-1', 'Singapore', 'Singapore', 'sg1.vpn.example.com', 443, 'online', 85),
    ('node-as-2', 'Tokyo-1', 'Japan', 'Tokyo', 'jp1.vpn.example.com', 443, 'online', 95);
EOF

echo -e "${GREEN}✅ Database schema created${NC}"

# Step 4: Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "${YELLOW}🏥 Checking service health...${NC}"
docker-compose ps

# Test API
echo -e "${YELLOW}🧪 Testing API...${NC}"
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    exit 1
fi

# Success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Deployment Successful!                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📊 ${YELLOW}Service Status:${NC}"
echo "   - API:      http://localhost:8000"
echo "   - Web:      http://localhost"
echo "   - Postgres: localhost:5432"
echo "   - Redis:    localhost:6379"
echo ""
echo -e "📖 ${YELLOW}API Documentation:${NC}"
echo "   - Swagger:  http://localhost:8000/api/docs"
echo "   - ReDoc:    http://localhost:8000/api/redoc"
echo ""
echo -e "🔑 ${YELLOW}Important Files:${NC}"
echo "   - .env              (Environment variables - KEEP SECURE)"
echo "   - xray/certs/       (SSL certificates)"
echo "   - db/init.sql       (Database schema)"
echo ""
echo -e "🛠️  ${YELLOW}Useful Commands:${NC}"
echo "   docker-compose logs -f     # View logs"
echo "   docker-compose stop        # Stop services"
echo "   docker-compose restart     # Restart services"
echo "   docker-compose down        # Stop and remove containers"
echo ""
