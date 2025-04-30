from fastapi import FastAPI, Form, UploadFile, File, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import yaml
from pathlib import Path
import httpx
from dotenv import load_dotenv
from jose import jwt
import secrets
from github import Github
from github.GithubException import GithubException

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
RAILWAY_PUBLIC_URL = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"

# GitHub Template Configuration
TEMPLATE_OWNER = "fern-api"
TEMPLATE_REPO = "sdk-starter"

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Session management
sessions = {}

async def create_repo_from_template(access_token: str, company_name: str) -> str:
    """Create a new repository from the template."""
    try:
        g = Github(access_token)
        auth_user = g.get_user()
        
        # Get the template repository
        template_repo = g.get_repo(f"{TEMPLATE_OWNER}/{TEMPLATE_REPO}")
        
        # Create a new repository from the template
        repo_name = f"{company_name}-config"
        repo_description = f"SDK configuration for {company_name}"
        
        # Create repository from template using the correct method
        new_repo = template_repo.create_repository_from_template(
            name=repo_name,
            description=repo_description,
            private=False,
            owner=auth_user.login
        )
        
        return new_repo.html_url
    except GithubException as e:
        if e.status == 422:  # Repository already exists
            raise ValueError(f"A repository named '{repo_name}' already exists.")
        elif e.status == 403:  # Permission denied
            raise ValueError("Permission denied. Please ensure you have granted the necessary repository permissions.")
        elif e.status == 404:  # Template not found
            raise ValueError("Template repository not found. Please check the template exists and you have access to it.")
        raise ValueError(f"GitHub API error ({e.status}): {e.data.get('message', str(e))}")
    except Exception as e:
        raise ValueError(f"Failed to create repository: {str(e)}")

def validate_openapi(content: bytes, file_extension: str) -> dict:
    """Validate and parse OpenAPI content based on file extension."""
    try:
        if file_extension in ['.json']:
            return json.loads(content)
        elif file_extension in ['.yaml', '.yml']:
            return yaml.safe_load(content)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ValueError(f"Invalid {file_extension[1:].upper()} file: {str(e)}")

async def get_current_user(request: Request):
    """Get the current user from the session."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[session_id]

@app.get("/auth/github")
async def github_auth():
    """Redirect to GitHub OAuth page."""
    state = secrets.token_urlsafe(16)
    scopes = "repo workflow"  # Add necessary scopes
    return RedirectResponse(
        f"{GITHUB_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={RAILWAY_PUBLIC_URL}/auth/callback"
        f"&state={state}&scope={scopes}"
    )

@app.get("/auth/callback")
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

        # Get user info
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_response.json()
        
        # Store access token in user data
        user_data['access_token'] = access_token

        # Create session
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = user_data

        # Redirect to home page with session cookie
        response = RedirectResponse(url="/")
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Show the form or login page."""
    try:
        user = await get_current_user(request)
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>SDK Setup</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background-color: #f0f0f0;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        width: 80%;
                        max-width: 600px;
                    }}
                    h1 {{
                        color: #333;
                        margin-bottom: 2rem;
                    }}
                    .form-group {{
                        margin-bottom: 1rem;
                        text-align: left;
                    }}
                    label {{
                        display: block;
                        margin-bottom: 0.5rem;
                        color: #555;
                    }}
                    input[type="text"],
                    input[type="file"] {{
                        width: 100%;
                        padding: 0.5rem;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        box-sizing: border-box;
                    }}
                    button {{
                        background-color: #4CAF50;
                        color: white;
                        padding: 0.5rem 1rem;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 1rem;
                        margin-top: 1rem;
                    }}
                    button:hover {{
                        background-color: #45a049;
                    }}
                    .error {{
                        color: red;
                        margin-top: 1rem;
                    }}
                    .success {{
                        color: green;
                        margin-top: 1rem;
                    }}
                    .file-info {{
                        font-size: 0.9rem;
                        color: #666;
                        margin-top: 0.5rem;
                    }}
                    .user-info {{
                        text-align: right;
                        margin-bottom: 1rem;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="user-info">
                        Logged in as: {user['login']}
                        <a href="/logout" style="margin-left: 1rem; color: #666;">Logout</a>
                    </div>
                    <h1>SDK Setup</h1>
                    <form action="/submit" method="post" enctype="multipart/form-data">
                        <div class="form-group">
                            <label for="company_name">Company Name:</label>
                            <input type="text" id="company_name" name="company_name" required>
                        </div>
                        <div class="form-group">
                            <label for="openapi_spec">OpenAPI Specification:</label>
                            <input type="file" id="openapi_spec" name="openapi_spec" accept=".json,.yaml,.yml" required>
                            <div class="file-info">Supported formats: JSON (.json), YAML (.yaml, .yml)</div>
                        </div>
                        <button type="submit">Submit</button>
                    </form>
                </div>
            </body>
        </html>
        """
        return html_content
    except HTTPException:
        return """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Login Required</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background-color: #f0f0f0;
                    }
                    .container {
                        text-align: center;
                        padding: 2rem;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        width: 80%;
                        max-width: 600px;
                    }
                    h1 {
                        color: #333;
                        margin-bottom: 2rem;
                    }
                    button {
                        background-color: #24292e;
                        color: white;
                        padding: 0.5rem 1rem;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 1rem;
                    }
                    button:hover {
                        background-color: #1b1f23;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Login Required</h1>
                    <p>Please log in with GitHub to continue.</p>
                    <a href="/auth/github">
                        <button>Login with GitHub</button>
                    </a>
                </div>
            </body>
        </html>
        """

@app.get("/logout")
async def logout():
    """Logout the user."""
    response = RedirectResponse(url="/")
    response.delete_cookie("session_id")
    return response

@app.post("/submit")
async def handle_submission(
    request: Request,
    company_name: str = Form(...),
    openapi_spec: UploadFile = File(...)
):
    """Handle form submission."""
    try:
        # Check authentication
        user = await get_current_user(request)
        
        # Get file extension
        file_extension = Path(openapi_spec.filename).suffix.lower()
        if file_extension not in ['.json', '.yaml', '.yml']:
            raise ValueError("Unsupported file type. Please upload a JSON or YAML file.")

        # Read and validate the file
        content = await openapi_spec.read()
        spec_data = validate_openapi(content, file_extension)

        # Create repository from template
        repo_url = await create_repo_from_template(user['access_token'], company_name)

        # Save the file with appropriate extension
        file_path = f"uploads/{company_name}_openapi{file_extension}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        return HTMLResponse(f"""
            <div class="container">
                <h1>Success!</h1>
                <p class="success">Setup completed for {company_name}</p>
                <p>Repository created: <a href="{repo_url}" target="_blank">{repo_url}</a></p>
                <p>OpenAPI spec saved successfully as {file_extension.upper()}.</p>
                <a href="/">Submit another</a>
            </div>
        """)
    except ValueError as e:
        return HTMLResponse(f"""
            <div class="container">
                <h1>Error</h1>
                <p class="error">{str(e)}</p>
                <a href="/">Try again</a>
            </div>
        """)
    except Exception as e:
        return HTMLResponse(f"""
            <div class="container">
                <h1>Error</h1>
                <p class="error">An error occurred: {str(e)}</p>
                <a href="/">Try again</a>
            </div>
        """) 