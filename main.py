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
import asyncio  # Add asyncio for sleep

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
TEMPLATE_OWNER = "cdonel707"
TEMPLATE_REPO = "sdk-starter"

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Session management
sessions = {}

async def create_repo_from_template(access_token: str, company_name: str, spec_file_name: str, spec_content: str) -> tuple[str, Github, str, str]:
    """Create a new repository from the template and delete existing spec."""
    try:
        g = Github(access_token)
        auth_user = g.get_user()
        print(f"Authenticated as user: {auth_user.login}")
        
        # Get the template repository
        template_repo = g.get_repo(f"{TEMPLATE_OWNER}/{TEMPLATE_REPO}")
        print(f"Template repo: {template_repo.full_name}, Is template: {template_repo.is_template}")
        
        # Create a new repository from the template
        repo_name = f"{company_name}-config"
        repo_description = f"SDK configuration for {company_name}"
        
        try:
            # Create repository from template using the correct method
            new_repo = auth_user.create_repo_from_template(
                name=repo_name,
                description=repo_description,
                private=False,
                repo=template_repo
            )

            async def verify_file_deleted(repo, file_path: str, max_retries: int = 3) -> bool:
                """Verify a file is deleted with retries."""
                for i in range(max_retries):
                    try:
                        repo.get_contents(file_path)
                        if i < max_retries - 1:  # Don't sleep on last attempt
                            await asyncio.sleep(1)  # Wait a second before retrying
                        continue  # File still exists
                    except GithubException as e:
                        if e.status == 404:  # File is gone
                            return True
                        raise  # Other error
                return False  # File still exists after all retries

            # Try to delete the existing OpenAPI spec file (trying both .yaml and .yml extensions)
            deleted = False
            max_retries = 3
            
            async def find_spec_file(repo, file_path: str) -> tuple[bool, any]:
                """Try to find a file with retries."""
                for attempt in range(max_retries):
                    try:
                        print(f"Attempt {attempt + 1}/{max_retries} to find {file_path}")
                        contents = repo.get_contents(file_path)
                        return True, contents
                    except GithubException as e:
                        if e.status != 404:  # Only retry on 404
                            raise
                        if attempt < max_retries - 1:
                            print(f"File not found, waiting before retry...")
                            await asyncio.sleep(2)  # Wait 2 seconds between attempts
                return False, None

            for file_path in ["fern/openapi.yaml", "fern/openapi.yml"]:
                try:
                    found, contents = await find_spec_file(new_repo, file_path)
                    if not found:
                        print(f"File {file_path} not found after {max_retries} attempts")
                        continue

                    # Handle if contents is a list (directory)
                    if isinstance(contents, list):
                        print(f"Warning: {file_path} is a directory containing {len(contents)} items")
                        continue
                        
                    print(f"Found file {file_path} with SHA: {contents.sha}")
                    
                    print(f"Attempting to delete {file_path}")
                    new_repo.delete_file(
                        path=contents.path,
                        message="Remove default OpenAPI spec",
                        sha=contents.sha
                    )
                    print(f"Delete API call completed for {file_path}")
                    
                    # Wait and verify deletion
                    if await verify_file_deleted(new_repo, file_path):
                        print(f"Verified deletion of {file_path}")
                        deleted = True
                        break  # Exit loop after successful deletion and verification
                    else:
                        print(f"Warning: {file_path} deletion could not be verified")
                except GithubException as e:
                    if e.status != 404:  # Only raise if error is not "file not found"
                        print(f"GitHub error for {file_path}: Status {e.status}, Data: {e.data}")
                        raise
                    print(f"Unexpected error for {file_path}")

            if not deleted:
                print("Warning: Could not find original spec file to delete")

            # Add a longer delay before creating the new file
            await asyncio.sleep(5)  # Wait 5 seconds before creating new file

            # Create the new spec file
            try:
                new_repo.create_file(
                    path=f"fern/{spec_file_name}",
                    message="Add OpenAPI specification",
                    content=spec_content,
                )
                print(f"Created new spec file: fern/{spec_file_name}")
            except GithubException as e:
                raise HTTPException(status_code=500, detail=f"Failed to create spec file: {str(e)}")

            # Update generators.yml with correct repository names and spec file
            try:
                generators_yml = new_repo.get_contents("fern/generators.yml")
                current_content = generators_yml.decoded_content.decode('utf-8')
                
                # Replace the commented repository lines with uncommented versions using the company name
                # and update the OpenAPI spec filename
                updated_content = current_content.replace(
                    '    - openapi: openapi.yaml',
                    f'    - openapi: {spec_file_name}'
                ).replace(
                    '          # github:\n          #   repository: fern-demo/starter-python-sdk',
                    f'        github:\n          repository: {company_name}-python-sdk'
                ).replace(
                    '          # github:\n          #   repository: fern-demo/starter-typescript-sdk',
                    f'        github:\n          repository: {company_name}-typescript-sdk'
                )
                
                new_repo.update_file(
                    path="fern/generators.yml",
                    message="Update SDK repository names and spec filename",
                    content=updated_content,
                    sha=generators_yml.sha
                )
                print("Updated generators.yml with SDK repository names and spec filename")
            except GithubException as e:
                print(f"Warning: Failed to update generators.yml: {str(e)}")
                # Don't raise an exception here as the main functionality succeeded

            # Create SDK repositories and install Fern API app
            try:
                # Create Python SDK repository
                python_repo_name = f"{company_name}-python-sdk"
                print(f"Creating Python SDK repository: {python_repo_name}")
                python_repo = auth_user.create_repo(
                    name=python_repo_name,
                    description=f"Python SDK for {company_name} API",
                    private=False,
                    auto_init=True  # Initialize with README
                )
                print(f"Created Python SDK repository: {python_repo_name}")

                # Create TypeScript SDK repository
                typescript_repo_name = f"{company_name}-typescript-sdk"
                print(f"Creating TypeScript SDK repository: {typescript_repo_name}")
                typescript_repo = auth_user.create_repo(
                    name=typescript_repo_name,
                    description=f"TypeScript SDK for {company_name} API",
                    private=False,
                    auto_init=True  # Initialize with README
                )
                print(f"Created TypeScript SDK repository: {typescript_repo_name}")

                # Install Fern API app in all repositories
                fern_app_url = "https://github.com/apps/fern-api/installations/new"
                repos_to_install = [
                    new_repo.full_name,  # Config repo
                    f"{auth_user.login}/{python_repo_name}",  # Python SDK repo
                    f"{auth_user.login}/{typescript_repo_name}"  # TypeScript SDK repo
                ]
                
                installation_url = f"{fern_app_url}?repository_ids={','.join([str(repo.id) for repo in [new_repo, python_repo, typescript_repo]])}"
                print(f"Installing Fern API app in repositories...")
                
                # Return the installation URL to the user
                return new_repo.html_url, g, new_repo.full_name, installation_url

            except GithubException as e:
                print(f"Warning: Failed to create SDK repositories: {str(e)}")
                # Don't raise an exception as the main config repo was created successfully
                return new_repo.html_url, g, new_repo.full_name, None
            
        except GithubException as e:
            print(f"Detailed GitHub error: Status {e.status}, Data: {e.data}")
            raise
            
    except GithubException as e:
        if e.status == 422:  # Repository already exists
            raise ValueError(f"A repository named '{repo_name}' already exists.")
        elif e.status == 403:  # Permission denied
            raise ValueError(f"Permission denied. GitHub says: {e.data.get('message', 'No message provided')}")
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
    scopes = "repo admin:repo_hook admin:org admin:public_key admin:org_hook user workflow"  # Request comprehensive permissions for testing
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

        # Create repository from template and get Github instance
        repo_url, g, repo_full_name, installation_url = await create_repo_from_template(
            user['access_token'], 
            company_name,
            openapi_spec.filename,
            content.decode('utf-8')
        )
        
        # Get the newly created repository
        new_repo = g.get_repo(repo_full_name)
        
        return HTMLResponse(f"""
            <div class="container">
                <h1>Success!</h1>
                <p class="success">Setup completed for {company_name}</p>
                <h2>Created Repositories:</h2>
                <ul>
                    <li>Configuration: <a href="{repo_url}" target="_blank">{repo_url}</a></li>
                    <li>Python SDK: <a href="https://github.com/{user['login']}/{company_name}-python-sdk" target="_blank">{company_name}-python-sdk</a></li>
                    <li>TypeScript SDK: <a href="https://github.com/{user['login']}/{company_name}-typescript-sdk" target="_blank">{company_name}-typescript-sdk</a></li>
                </ul>
                <p>OpenAPI spec uploaded as fern/{openapi_spec.filename}</p>
                
                <div style="margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 8px;">
                    <h2>Final Step: Install Fern API</h2>
                    <p>To enable automatic SDK generation, please install the Fern API GitHub App:</p>
                    <ol style="text-align: left;">
                        <li>Click the button below to open the installation page</li>
                        <li>Review the repository access</li>
                        <li>Click "Install" to complete the setup</li>
                    </ol>
                    <a href="{installation_url}" target="_blank" style="display: inline-block; margin-top: 1rem; padding: 0.75rem 1.5rem; background-color: #2ea44f; color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Install Fern API
                    </a>
                </div>
                
                <a href="/" style="display: inline-block; margin-top: 2rem;">Create Another SDK</a>
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
                <p class="error">An unexpected error occurred: {str(e)}</p>
                <a href="/">Try again</a>
            </div>
        """) 