#!/usr/bin/env python3
"""
VLESS VPN SaaS - Backend API v2
Production API with Supabase, Stripe, and Crypto billing.

© 2024 VPN Solutions Inc. All rights reserved.
"""

__version__ = "3.0.0-saas-day4"

from fastapi import FastAPI, Depends, HTTPException, status, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from datetime import datetime, timedelta
from typing import Optional, List, Any
from enum import Enum
import jwt
import hashlib
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

class Settings:
    """Application settings."""
    
    APP_NAME = "VLESS VPN SaaS API"
    APP_VERSION = "3.0.0-saas"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_ID_BASIC = os.getenv("STRIPE_PRICE_ID_BASIC", "")
    STRIPE_PRICE_ID_PRO = os.getenv("STRIPE_PRICE_ID_PRO", "")
    STRIPE_PRICE_ID_ENTERPRISE = os.getenv("STRIPE_PRICE_ID_ENTERPRISE", "")
    
    # Coinbase Commerce
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY", "")
    COINBASE_WEBHOOK_SECRET = os.getenv("COINBASE_WEBHOOK_SECRET", "")
    
    # VPN
    VLESS_SECRET = os.getenv("VLESS_SECRET", "vless-secret-key")


settings = Settings()

# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production VPN SaaS API with billing and subscription management",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# =============================================================================
# Supabase Client
# =============================================================================

try:
    from supabase import create_client, Client
    supabase: Optional[Client] = None
    
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print("✓ Supabase connected")
    else:
        print("⚠ Supabase not configured, using mock mode")
except ImportError:
    supabase = None
    print("⚠ Supabase client not installed, using mock mode")

# =============================================================================
# Pydantic Models
# =============================================================================

class PlanType(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentMethod(str, Enum):
    STRIPE = "stripe"
    CRYPTO = "crypto"
    PAYPAL = "paypal"


class CryptoCurrency(str, Enum):
    USDT = "USDT"
    BTC = "BTC"
    ETH = "ETH"
    DAI = "DAI"


# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


# User Models
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    plan: PlanType
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    has_subscription: bool


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


# Subscription Models
class SubscriptionCreate(BaseModel):
    plan: PlanType
    payment_method: PaymentMethod
    crypto_currency: Optional[CryptoCurrency] = None
    months: int = 1


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan: PlanType
    status: str
    payment_method: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime


class SubscriptionCancel(BaseModel):
    reason: Optional[str] = None


# Node Models
class VPNNodeResponse(BaseModel):
    id: str
    name: str
    country: str
    city: str
    host: str
    port: int
    protocol: str
    transport: str
    status: str
    latency: int
    load: float


class ConfigGenerate(BaseModel):
    node_id: Optional[str] = None
    protocol: str = "vless"
    transport: str = "reality"


class VPNConfigResponse(BaseModel):
    id: str
    user_id: str
    vless_url: str
    subscription_url: str
    protocol: str
    transport: str
    created_at: datetime
    expires_at: datetime


# Billing Models
class InvoiceResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None


class PaymentIntent(BaseModel):
    amount: float
    currency: str = "usd"
    plan: PlanType


class CryptoPayment(BaseModel):
    amount: float
    currency: CryptoCurrency
    plan: PlanType


# Usage Models
class UsageStats(BaseModel):
    user_id: str
    bytes_uploaded: int
    bytes_downloaded: int
    connections_count: int
    last_connection: Optional[datetime]
    period_start: datetime
    period_end: datetime


# =============================================================================
# Helper Functions
# =============================================================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256 (use Argon2 in production with Supabase Auth)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


def generate_vless_uuid(user_id: str, node_id: str) -> str:
    """Generate deterministic UUID for VLESS config."""
    seed = f"{user_id}:{node_id}:{settings.VLESS_SECRET}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))


def generate_vless_url(user_id: str, node: dict, vless_uuid: str) -> str:
    """Generate VLESS URL configuration."""
    sni = node.get('server_name', node['host'])
    public_key = node.get('public_key', '')
    short_id = node.get('short_id', '')
    
    url = (
        f"vless://{vless_uuid}@{node['host']}:{node['port']}"
        f"?encryption=none"
        f"&security=reality"
        f"&type=tcp"
        f"&fp=chrome"
        f"&sni={sni}"
        f"&pbk={public_key}"
        f"&sid={short_id}"
        f"#{node['name']}"
    )
    
    return url


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {"user_id": user_id, "token_payload": payload}
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


# Mock database (replace with Supabase in production)
MOCK_USERS = {}
MOCK_NODES = {
    "node-eu-1": {
        "id": "node-eu-1",
        "name": "Frankfurt-1",
        "country": "Germany",
        "city": "Frankfurt",
        "host": "de1.vpn.example.com",
        "port": 443,
        "protocol": "vless",
        "transport": "reality",
        "status": "online",
        "latency": 45,
        "load": 0.3,
        "server_name": "example.com",
        "public_key": "test-public-key",
        "short_id": "1234"
    },
    "node-us-1": {
        "id": "node-us-1",
        "name": "New York-1",
        "country": "USA",
        "city": "New York",
        "host": "us1.vpn.example.com",
        "port": 443,
        "protocol": "vless",
        "transport": "reality",
        "status": "online",
        "latency": 120,
        "load": 0.5
    },
    "node-as-1": {
        "id": "node-as-1",
        "name": "Singapore-1",
        "country": "Singapore",
        "city": "Singapore",
        "host": "sg1.vpn.example.com",
        "port": 443,
        "protocol": "vless",
        "transport": "reality",
        "status": "online",
        "latency": 85,
        "load": 0.2
    }
}
MOCK_SUBSCRIPTIONS = {}
MOCK_CONFIGS = {}


# =============================================================================
# API Routes - Health & Root
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs",
        "health": "/api/health"
    }


@app.get("/api/health")
async def health_check():
    """API health check endpoint."""
    supabase_status = "connected" if supabase else "not configured"
    
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "supabase": supabase_status
    }


# =============================================================================
# API Routes - Authentication
# =============================================================================

@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserRegister):
    """Register new user."""
    # Check if user exists
    for user in MOCK_USERS.values():
        if user["email"] == user_data.email or user["username"] == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
    
    # Create user
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "password_hash": hash_password(user_data.password),
        "plan": PlanType.FREE,
        "created_at": datetime.utcnow(),
        "expires_at": None,
        "is_active": True,
        "has_subscription": False
    }
    
    MOCK_USERS[user_id] = user
    
    # Create free subscription
    MOCK_SUBSCRIPTIONS[user_id] = {
        "id": f"sub_{user_id[:8]}",
        "user_id": user_id,
        "plan": PlanType.FREE,
        "status": "active",
        "payment_method": "none",
        "current_period_start": datetime.utcnow(),
        "current_period_end": datetime.utcnow() + timedelta(days=30),
        "cancel_at_period_end": False,
        "created_at": datetime.utcnow()
    }
    
    return UserResponse(**user)


@app.post("/api/v1/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access tokens."""
    # Find user
    user = None
    for u in MOCK_USERS.values():
        if u["email"] == credentials.email:
            user = u
            break
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user["id"]})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token."""
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id: str = payload.get("sub")
        if user_id not in MOCK_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# =============================================================================
# API Routes - Users
# =============================================================================

@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    user = MOCK_USERS.get(current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)


@app.get("/api/v1/users/me/usage", response_model=UsageStats)
async def get_user_usage(current_user: dict = Depends(get_current_user)):
    """Get current user usage statistics."""
    # Mock usage data
    return UsageStats(
        user_id=current_user["user_id"],
        bytes_uploaded=1024 * 1024 * 500,  # 500 MB
        bytes_downloaded=1024 * 1024 * 1024 * 2,  # 2 GB
        connections_count=42,
        last_connection=datetime.utcnow(),
        period_start=datetime.utcnow() - timedelta(days=30),
        period_end=datetime.utcnow()
    )


# =============================================================================
# API Routes - Subscriptions
# =============================================================================

@app.post("/api/v1/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new subscription."""
    user_id = current_user["user_id"]
    
    # Calculate pricing
    base_prices = {
        "free": 0,
        "basic": 4.99,
        "pro": 9.99,
        "enterprise": 29.99
    }
    
    amount = base_prices.get(subscription_data.plan.value, 0) * subscription_data.months
    
    # In production: Create Stripe Checkout Session or Coinbase Charge
    # For now, activate subscription immediately
    subscription = {
        "id": f"sub_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "plan": subscription_data.plan,
        "status": "active",
        "payment_method": subscription_data.payment_method.value,
        "current_period_start": datetime.utcnow(),
        "current_period_end": datetime.utcnow() + timedelta(days=30 * subscription_data.months),
        "cancel_at_period_end": False,
        "created_at": datetime.utcnow()
    }
    
    MOCK_SUBSCRIPTIONS[user_id] = subscription
    
    # Update user plan
    if user_id in MOCK_USERS:
        MOCK_USERS[user_id]["plan"] = subscription_data.plan
        MOCK_USERS[user_id]["has_subscription"] = subscription_data.plan != "free"
    
    return SubscriptionResponse(**subscription)


@app.get("/api/v1/subscriptions/me", response_model=SubscriptionResponse)
async def get_user_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user subscription."""
    subscription = MOCK_SUBSCRIPTIONS.get(current_user["user_id"])
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return SubscriptionResponse(**subscription)


@app.post("/api/v1/subscriptions/cancel", response_model=dict)
async def cancel_subscription(
    cancel_data: SubscriptionCancel,
    current_user: dict = Depends(get_current_user)
):
    """Cancel user subscription."""
    subscription = MOCK_SUBSCRIPTIONS.get(current_user["user_id"])
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    subscription["cancel_at_period_end"] = True
    
    return {
        "message": "Subscription will be cancelled at period end",
        "cancelled_at": datetime.utcnow().isoformat()
    }


# =============================================================================
# API Routes - VPN Nodes
# =============================================================================

@app.get("/api/v1/nodes", response_model=List[VPNNodeResponse])
async def get_available_nodes(current_user: dict = Depends(get_current_user)):
    """Get all available VPN nodes."""
    user = MOCK_USERS.get(current_user["user_id"])
    
    # Filter nodes based on user plan
    plan_limits = {
        "free": 1,
        "basic": 5,
        "pro": 20,
        "enterprise": 999
    }
    
    limit = plan_limits.get(user["plan"] if user else "free", 1)
    nodes = [n for n in MOCK_NODES.values() if n["status"] == "online"][:limit]
    
    return [VPNNodeResponse(**node) for node in nodes]


@app.get("/api/v1/nodes/{node_id}", response_model=VPNNodeResponse)
async def get_node(
    node_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific VPN node information."""
    node = MOCK_NODES.get(node_id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    return VPNNodeResponse(**node)


# =============================================================================
# API Routes - VPN Configs
# =============================================================================

@app.post("/api/v1/configs/generate", response_model=VPNConfigResponse)
async def generate_config(
    config_data: ConfigGenerate,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Generate new VPN config for user."""
    user_id = current_user["user_id"]
    
    # Select node
    if config_data.node_id:
        if config_data.node_id not in MOCK_NODES:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        node = MOCK_NODES[config_data.node_id]
    else:
        # Auto-select best node (lowest latency)
        online_nodes = [n for n in MOCK_NODES.values() if n["status"] == "online"]
        if not online_nodes:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No online nodes available"
            )
        node = min(online_nodes, key=lambda n: n["latency"])
    
    # Generate VLESS UUID
    vless_uuid = generate_vless_uuid(user_id, node["id"])
    
    # Generate VLESS URL
    vless_url = generate_vless_url(user_id, node, vless_uuid)
    
    # Generate subscription URL
    subscription_token = hashlib.sha256(f"{user_id}:{settings.SECRET_KEY}".encode()).hexdigest()[:16]
    subscription_url = f"https://api.vpn-saas.io/api/v1/subscribe/{subscription_token}"
    
    # Store config
    config_id = str(uuid.uuid4())
    config = {
        "id": config_id,
        "user_id": user_id,
        "vless_url": vless_url,
        "subscription_url": subscription_url,
        "protocol": config_data.protocol,
        "transport": config_data.transport,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=30)
    }
    
    MOCK_CONFIGS[config_id] = config
    
    return VPNConfigResponse(**config)


@app.get("/api/v1/configs", response_model=List[VPNConfigResponse])
async def get_user_configs(current_user: dict = Depends(get_current_user)):
    """Get all VPN configs for current user."""
    user_configs = [c for c in MOCK_CONFIGS.values() if c["user_id"] == current_user["user_id"]]
    return [VPNConfigResponse(**c) for c in user_configs]


# =============================================================================
# API Routes - Billing (Stripe Placeholder)
# =============================================================================

@app.post("/api/v1/billing/create-payment-intent")
async def create_payment_intent(
    payment: PaymentIntent,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe payment intent."""
    # In production: Use Stripe SDK to create PaymentIntent
    # stripe.PaymentIntent.create(amount=payment.amount, currency=payment.currency, ...)
    
    return {
        "client_secret": "pi_xxx_secret_xxx",
        "amount": payment.amount,
        "currency": payment.currency,
        "plan": payment.plan.value
    }


@app.post("/api/v1/billing/stripe-webhook")
async def stripe_webhook(request: dict):
    """Handle Stripe webhooks."""
    # In production: Verify webhook signature and handle events
    # stripe.Webhook.construct_event(...)
    
    # Handle events:
    # - checkout.session.completed
    # - invoice.paid
    # - customer.subscription.deleted
    
    return {"status": "ok"}


# =============================================================================
# API Routes - Billing (Crypto Placeholder)
# =============================================================================

@app.post("/api/v1/billing/crypto-charge")
async def create_crypto_charge(
    crypto_payment: CryptoPayment,
    current_user: dict = Depends(get_current_user)
):
    """Create Coinbase Commerce charge."""
    # In production: Use Coinbase Commerce API
    # coinbase.charge.create(name="VPN Subscription", amounts={...})
    
    return {
        "charge_id": "charge_xxx",
        "amount": crypto_payment.amount,
        "currency": crypto_payment.currency.value,
        "plan": crypto_payment.plan.value,
        "payment_address": "0x...",
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }


@app.post("/api/v1/billing/crypto-webhook")
async def crypto_webhook(request: dict):
    """Handle Coinbase Commerce webhooks."""
    # In production: Verify webhook signature and handle events
    # - charge:confirmed
    # - charge:failed
    
    return {"status": "ok"}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "vless_vpn_api_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
