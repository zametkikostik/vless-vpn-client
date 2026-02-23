#!/usr/bin/env python3
"""
VLESS VPN SaaS - Backend API
Production-grade API for VPN management and billing.

© 2024 VPN Solutions Inc. All rights reserved.
"""

__version__ = "3.0.0-enterprise"

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import jwt
import hashlib
import uuid
import json

# =============================================================================
# Configuration
# =============================================================================

class Settings:
    """Application settings."""
    
    APP_NAME = "VLESS VPN SaaS API"
    APP_VERSION = "3.0.0-enterprise"
    DEBUG = False
    
    # Security
    SECRET_KEY = "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    
    # Database
    DATABASE_URL = "postgresql://user:password@localhost:5432/vpn_saas"
    
    # Redis
    REDIS_URL = "redis://localhost:6379"
    
    # Stripe
    STRIPE_SECRET_KEY = ""
    STRIPE_WEBHOOK_SECRET = ""
    
    # VPN
    VLESS_UUID_SECRET = "your-uuid-generation-secret"


settings = Settings()

# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise VPN SaaS API for user management, config generation, and billing",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# =============================================================================
# Database Models (SQLAlchemy)
# =============================================================================

# Note: In production, use proper SQLAlchemy models
# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()

# =============================================================================
# Pydantic Models
# =============================================================================

class PlanType(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserBase(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User registration model."""
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    plan: PlanType
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VPNConfig(BaseModel):
    """VPN configuration response."""
    id: str
    user_id: str
    node_id: str
    vless_url: str
    protocol: str
    transport: str
    created_at: datetime
    expires_at: datetime


class VPNNode(BaseModel):
    """VPN node information."""
    id: str
    name: str
    country: str
    city: str
    host: str
    port: int
    protocol: str = "vless"
    transport: str = "reality"
    status: str = "online"
    latency: int = 0
    load: float = 0.0


class Subscription(BaseModel):
    """Subscription information."""
    id: str
    user_id: str
    plan: PlanType
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False


class UsageStats(BaseModel):
    """User usage statistics."""
    user_id: str
    bytes_uploaded: int = 0
    bytes_downloaded: int = 0
    connections_count: int = 0
    last_connection: Optional[datetime] = None


# =============================================================================
# Helper Functions
# =============================================================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256 (use Argon2 in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


def generate_uuid() -> str:
    """Generate unique UUID for VLESS config."""
    return str(uuid.uuid4())


def generate_vless_config(user_id: str, node: VPNNode) -> str:
    """Generate VLESS URL configuration."""
    uuid = generate_uuid()
    
    # VLESS URL format
    # vless://uuid@host:port?encryption=none&security=reality&sni=xxx&pbk=xxx&sid=xxx#name
    
    config = (
        f"vless://{uuid}@{node.host}:{node.port}"
        f"?encryption=none"
        f"&security={node.protocol}"
        f"&type={node.transport}"
        f"&fp=chrome"
        f"&sni={node.host}"
        f"#VPN-{node.country}-{node.city}"
    )
    
    return config


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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


# =============================================================================
# Mock Database (Replace with real DB in production)
# =============================================================================

USERS_DB = {}
NODES_DB = {
    "node-eu-1": VPNNode(
        id="node-eu-1",
        name="Frankfurt-1",
        country="Germany",
        city="Frankfurt",
        host="de1.vpn.example.com",
        port=443,
        status="online",
        latency=45
    ),
    "node-us-1": VPNNode(
        id="node-us-1",
        name="New York-1",
        country="USA",
        city="New York",
        host="us1.vpn.example.com",
        port=443,
        status="online",
        latency=120
    ),
    "node-as-1": VPNNode(
        id="node-as-1",
        name="Singapore-1",
        country="Singapore",
        city="Singapore",
        host="sg1.vpn.example.com",
        port=443,
        status="online",
        latency=85
    ),
}
CONFIGS_DB = {}


# =============================================================================
# API Routes - Authentication
# =============================================================================

@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate):
    """Register new user."""
    # Check if user exists
    for user in USERS_DB.values():
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
        "is_active": True
    }
    
    USERS_DB[user_id] = user
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        plan=user["plan"],
        created_at=user["created_at"],
        expires_at=user["expires_at"],
        is_active=user["is_active"]
    )


@app.post("/api/v1/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access tokens."""
    # Find user
    user = None
    for u in USERS_DB.values():
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
    access_token = create_access_token(data={"sub": user["id"]})
    refresh_token = create_refresh_token(data={"sub": user["id"]})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id not in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token
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
    user = USERS_DB.get(current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        plan=user["plan"],
        created_at=user["created_at"],
        expires_at=user["expires_at"],
        is_active=user["is_active"]
    )


@app.get("/api/v1/users/me/usage", response_model=UsageStats)
async def get_user_usage(current_user: dict = Depends(get_current_user)):
    """Get current user usage statistics."""
    # Mock usage data
    return UsageStats(
        user_id=current_user["user_id"],
        bytes_uploaded=1024 * 1024 * 500,  # 500 MB
        bytes_downloaded=1024 * 1024 * 1024 * 2,  # 2 GB
        connections_count=42,
        last_connection=datetime.utcnow()
    )


# =============================================================================
# API Routes - VPN Configs
# =============================================================================

@app.get("/api/v1/configs", response_model=List[VPNConfig])
async def get_user_configs(current_user: dict = Depends(get_current_user)):
    """Get all VPN configs for current user."""
    user_configs = [c for c in CONFIGS_DB.values() if c["user_id"] == current_user["user_id"]]
    return [VPNConfig(**c) for c in user_configs]


@app.post("/api/v1/configs/generate", response_model=VPNConfig)
async def generate_config(
    node_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate new VPN config for user."""
    # Select node
    if node_id:
        if node_id not in NODES_DB:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        node = NODES_DB[node_id]
    else:
        # Auto-select best node (lowest latency)
        online_nodes = [n for n in NODES_DB.values() if n.status == "online"]
        if not online_nodes:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No online nodes available"
            )
        node = min(online_nodes, key=lambda n: n.latency)
    
    # Generate config
    config_id = str(uuid.uuid4())
    vless_url = generate_vless_config(current_user["user_id"], node)
    
    config = {
        "id": config_id,
        "user_id": current_user["user_id"],
        "node_id": node.id,
        "vless_url": vless_url,
        "protocol": node.protocol,
        "transport": node.transport,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=30)
    }
    
    CONFIGS_DB[config_id] = config
    
    return VPNConfig(**config)


@app.get("/api/v1/configs/{config_id}", response_model=VPNConfig)
async def get_config(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific VPN config."""
    config = CONFIGS_DB.get(config_id)
    
    if not config or config["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )
    
    return VPNConfig(**config)


@app.delete("/api/v1/configs/{config_id}")
async def delete_config(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete VPN config."""
    if config_id not in CONFIGS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )
    
    del CONFIGS_DB[config_id]
    return {"message": "Config deleted successfully"}


# =============================================================================
# API Routes - Nodes
# =============================================================================

@app.get("/api/v1/nodes", response_model=List[VPNNode])
async def get_available_nodes(current_user: dict = Depends(get_current_user)):
    """Get all available VPN nodes."""
    user = USERS_DB.get(current_user["user_id"])
    
    # Filter nodes based on user plan
    if user["plan"] == PlanType.FREE:
        # Free users get limited nodes
        nodes = list(NODES_DB.values())[:1]
    else:
        nodes = [n for n in NODES_DB.values() if n.status == "online"]
    
    return nodes


@app.get("/api/v1/nodes/{node_id}", response_model=VPNNode)
async def get_node(
    node_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific VPN node information."""
    node = NODES_DB.get(node_id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    return node


# =============================================================================
# API Routes - Health Check
# =============================================================================

@app.get("/api/health")
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/health"
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "vless_vpn_api:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
