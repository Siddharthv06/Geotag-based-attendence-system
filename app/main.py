"""
FastAPI Backend - Site Management System
Works with LOCAL SQLite database - no setup needed!
"""
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional

from app import database as db
from app.models import (
    UserCreate, UserResponse,
    SiteCreate, SiteUpdate, SiteResponse,
    MemberAssign, MemberResponse,
    CheckInRequest, CheckInResponse,
)
from app.utils import is_within_radius

app = FastAPI(
    title="Site Management API",
    description="Backend for location-based site management app",
    version="1.0.0",
)

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ──────────────────────────────────────────────────────
# STARTUP - Initialize local database
# ──────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    db.init_db()


# ──────────────────────────────────────────────────────
# FRONTEND - Serve the HTML app
# ──────────────────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "healthy", "database": "local SQLite"}


# ──────────────────────────────────────────────────────
# USER ROUTES
# ──────────────────────────────────────────────────────
@app.get("/api/users", response_model=list[UserResponse])
def list_users(role: Optional[str] = Query(None)):
    """List all users, optionally filter by role."""
    return db.get_all_users(role=role)


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    """Get a single user by ID."""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    """Create a new user."""
    result = db.create_user(user.model_dump())
    return result


@app.delete("/api/users/{user_id}")
def delete_user(user_id: str):
    """Delete a user."""
    db.delete_user(user_id)
    return {"success": True, "message": "User deleted"}


# ──────────────────────────────────────────────────────
# SITE ROUTES
# ──────────────────────────────────────────────────────
@app.get("/api/sites", response_model=list[SiteResponse])
def list_sites(created_by: Optional[str] = Query(None)):
    """List all sites with member count."""
    return db.get_all_sites(created_by=created_by)


@app.get("/api/sites/{site_id}", response_model=SiteResponse)
def get_site(site_id: str):
    """Get a single site by ID with member count."""
    site = db.get_site_by_id(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@app.post("/api/sites", response_model=SiteResponse, status_code=201)
def create_site(site: SiteCreate):
    """Create a new site with optional GPS coordinates."""
    data = site.model_dump(exclude_none=True)
    result = db.create_site(data)
    return result


@app.patch("/api/sites/{site_id}", response_model=SiteResponse)
def update_site(site_id: str, site: SiteUpdate):
    """Update a site's details."""
    data = {k: v for k, v in site.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = db.update_site(site_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Site not found")
    return result


@app.delete("/api/sites/{site_id}")
def delete_site(site_id: str):
    """Delete a site and its member assignments."""
    db.delete_site(site_id)
    return {"success": True, "message": "Site deleted"}


# ──────────────────────────────────────────────────────
# SITE MEMBER ROUTES
# ──────────────────────────────────────────────────────
@app.get("/api/sites/{site_id}/members", response_model=list[MemberResponse])
def list_site_members(site_id: str):
    """Get all members assigned to a site."""
    return db.get_site_members(site_id)


@app.post("/api/sites/{site_id}/members", response_model=MemberResponse, status_code=201)
def assign_member(site_id: str, member: MemberAssign):
    """Assign a user to a site."""
    # Check if site exists
    site = db.get_site_by_id(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Check if user exists
    user = db.get_user_by_id(member.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Assign
    result = db.assign_member(site_id, member.user_id)
    return result


@app.delete("/api/sites/{site_id}/members/{user_id}")
def remove_member(site_id: str, user_id: str):
    """Remove a user from a site."""
    db.remove_member(site_id, user_id)
    return {"success": True, "message": "Member removed from site"}


# ──────────────────────────────────────────────────────
# AVAILABLE USERS (for team assignment picker)
# ──────────────────────────────────────────────────────
@app.get("/api/sites/{site_id}/available-members", response_model=list[UserResponse])
def available_members(site_id: str):
    """Get users NOT yet assigned to this site (for the member picker UI)."""
    return db.get_available_members(site_id)


# ──────────────────────────────────────────────────────
# CHECK-IN (GPS PUNCH-IN VALIDATION)
# ──────────────────────────────────────────────────────
@app.post("/api/sites/{site_id}/check-in", response_model=CheckInResponse)
def check_in(site_id: str, req: CheckInRequest):
    """
    Validate if a user's GPS position is within the site's punch-in radius.
    Returns distance and whether they're within the allowed zone.
    """
    site = db.get_site_by_id(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    if site.get("latitude") is None or site.get("longitude") is None:
        raise HTTPException(status_code=400, detail="Site has no GPS coordinates set")

    within, dist = is_within_radius(
        req.latitude, req.longitude,
        site["latitude"], site["longitude"],
        site.get("radius_meters", 15),
    )

    return {
        "success": within,
        "message": "Check-in successful!" if within else f"Too far from site ({dist}m away, radius is {site.get('radius_meters', 15)}m)",
        "distance_meters": dist,
        "within_radius": within,
    }


# ──────────────────────────────────────────────────────
# ENTRYPOINT
# ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
