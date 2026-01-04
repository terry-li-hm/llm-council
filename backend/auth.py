"""GitHub OAuth authentication for LLM Council."""

import secrets
import time
import hashlib
import hmac
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse
import httpx

from .config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_ALLOWED_USERS,
    SESSION_SECRET,
    FRONTEND_URL,
    logger,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Auth is enabled only if GitHub credentials are configured
auth_enabled = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)

# In-memory session store (for production, use Redis or database)
# Format: {session_token: {"username": str, "expires": float}}
sessions: dict[str, dict] = {}

# Session duration: 7 days
SESSION_DURATION = 7 * 24 * 60 * 60


def create_session_token(username: str) -> str:
    """Create a signed session token for a user."""
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "username": username,
        "expires": time.time() + SESSION_DURATION,
    }
    return token


def validate_session_token(token: str) -> Optional[str]:
    """Validate a session token and return the username if valid."""
    if not token or token not in sessions:
        return None
    session = sessions[token]
    if time.time() > session["expires"]:
        del sessions[token]
        return None
    return session["username"]


def get_session_token(request: Request) -> Optional[str]:
    """Extract session token from cookie or Authorization header."""
    # Try cookie first
    token = request.cookies.get("session")
    if token:
        return token
    # Fall back to Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def verify_auth(request: Request) -> Optional[str]:
    """Verify authentication. Returns username if authenticated, None if auth disabled."""
    if not auth_enabled:
        return None  # Auth disabled, allow all

    token = get_session_token(request)
    username = validate_session_token(token)

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return username


@router.get("/status")
async def auth_status(request: Request):
    """Check authentication status."""
    if not auth_enabled:
        return {"authenticated": True, "auth_enabled": False, "username": None}

    token = get_session_token(request)
    username = validate_session_token(token)

    return {
        "authenticated": username is not None,
        "auth_enabled": True,
        "username": username,
    }


@router.get("/login")
async def login():
    """Redirect to GitHub OAuth login."""
    if not auth_enabled:
        raise HTTPException(status_code=400, detail="Authentication not configured")

    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(16)

    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=read:user"
        f"&state={state}"
    )

    response = RedirectResponse(url=github_auth_url)
    # Store state in cookie for validation
    response.set_cookie("oauth_state", state, httponly=True, max_age=300)
    return response


@router.get("/callback")
async def oauth_callback(code: str, state: str, request: Request):
    """Handle GitHub OAuth callback."""
    if not auth_enabled:
        raise HTTPException(status_code=400, detail="Authentication not configured")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error(f"GitHub token exchange failed: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to authenticate with GitHub")

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            logger.error(f"No access token in response: {token_data}")
            raise HTTPException(status_code=400, detail="Failed to get access token")

        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        if user_response.status_code != 200:
            logger.error(f"GitHub user info failed: {user_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user_data = user_response.json()
        username = user_data.get("login")

        if not username:
            raise HTTPException(status_code=400, detail="Failed to get username")

        # Check if user is allowed
        if GITHUB_ALLOWED_USERS and username not in GITHUB_ALLOWED_USERS:
            logger.warning(f"User {username} not in allowed users list")
            raise HTTPException(status_code=403, detail="User not authorized")

        logger.info(f"User {username} authenticated successfully")

        # Create session
        session_token = create_session_token(username)

        # Redirect to frontend with session cookie
        response = RedirectResponse(url=FRONTEND_URL)
        response.set_cookie(
            "session",
            session_token,
            httponly=True,
            secure=True,  # Only send over HTTPS in production
            samesite="lax",
            max_age=SESSION_DURATION,
        )
        # Clear the oauth_state cookie
        response.delete_cookie("oauth_state")

        return response


@router.post("/logout")
async def logout(request: Request):
    """Log out the current user."""
    token = get_session_token(request)
    if token and token in sessions:
        del sessions[token]

    response = Response(content='{"status": "logged out"}', media_type="application/json")
    response.delete_cookie("session")
    return response
