from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import secrets
from config import (
    GITHUB_CLIENT_ID, 
    GITHUB_CLIENT_SECRET, 
    GITHUB_AUTHORIZE_URL, 
    GITHUB_TOKEN_URL, 
    GITHUB_USER_URL, 
    RAILWAY_PUBLIC_URL,
    sessions
)

async def get_current_user(request: Request):
    """Get the current user from the session."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[session_id]

async def github_auth():
    """Redirect to GitHub OAuth page."""
    state = secrets.token_urlsafe(16)
    scopes = "repo admin:repo_hook admin:org admin:public_key admin:org_hook user workflow"
    return RedirectResponse(
        f"{GITHUB_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={RAILWAY_PUBLIC_URL}/auth/callback"
        f"&state={state}&scope={scopes}"
    )

async def github_callback(code: str, state: str):
    """Handle GitHub OAuth callback."""
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        # Get user info using the token in the Authorization header
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"token {access_token}"},
        )
        user_data = user_response.json()
        
        # Store raw access token in user data (without 'token ' prefix)
        user_data['access_token'] = access_token

        # Create session
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = user_data

        # Redirect to home page with session cookie
        response = RedirectResponse(url="/")
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response

async def logout():
    """Logout the user."""
    response = RedirectResponse(url="/")
    response.delete_cookie("session_id")
    return response 