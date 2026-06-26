"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ──────────────────────────────────────────────
# USER MODELS
# ──────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    role: str = Field(default="member", pattern="^(admin|manager|member)$")


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    created_at: Optional[str] = None


# ──────────────────────────────────────────────
# SITE MODELS
# ──────────────────────────────────────────────
class SiteCreate(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: int = 15
    address: Optional[str] = None
    created_by: Optional[str] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None
    address: Optional[str] = None


class SiteResponse(BaseModel):
    id: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = 15
    address: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    member_count: int = 0


# ──────────────────────────────────────────────
# SITE MEMBER MODELS
# ──────────────────────────────────────────────
class MemberAssign(BaseModel):
    user_id: str


class MemberResponse(BaseModel):
    site_id: str
    user_id: str
    assigned_at: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None


# ──────────────────────────────────────────────
# CHECK-IN MODEL
# ──────────────────────────────────────────────
class CheckInRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float


class CheckInResponse(BaseModel):
    success: bool
    message: str
    distance_meters: Optional[float] = None
    within_radius: bool = False
