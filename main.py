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
import shutil
import subprocess
import random  # Add import for random number generation

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()  # Trigger Railway redeploy

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
                private=True,
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
                
                # Replace the commented repository lines with uncommented versions using the company name,
                # update the OpenAPI spec filename, and update package names
                updated_content = current_content.replace(
                    '    - openapi: openapi.yaml',
                    f'    - openapi: {spec_file_name}'
                ).replace(
                    '          # github:\n          #   repository: fern-demo/starter-python-sdk',
                    f'        github:\n          repository: {auth_user.login}/{company_name}-python-sdk'
                ).replace(
                    '          # github:\n          #   repository: fern-demo/starter-typescript-sdk',
                    f'        github:\n          repository: {auth_user.login}/{company_name}-typescript-sdk'
                ).replace(
                    'package-name: startersdk',
                    f'package-name: {company_name.lower()}-sdk'
                ).replace(
                    'pypi-package-name: startersdk',
                    f'pypi-package-name: {company_name.lower()}-sdk'
                ).replace(
                    'npm-package-name: startersdk',
                    f'npm-package-name: {company_name.lower()}-sdk'
                )
                
                new_repo.update_file(
                    path="fern/generators.yml",
                    message="Update SDK repository names and spec filename",
                    content=updated_content,
                    sha=generators_yml.sha
                )
                print("Updated generators.yml with SDK repository names and spec filename")

                # Update fern.config.json with the company name
                try:
                    fern_config = new_repo.get_contents("fern/fern.config.json")
                    config_content = json.loads(fern_config.decoded_content.decode('utf-8'))
                    
                    # Update the organization name - remove spaces and special characters, convert to lowercase
                    # and add random 6 digits at the end
                    base_name = ''.join(c.lower() for c in company_name if c.isalnum())
                    random_digits = str(random.randint(100000, 999999))
                    org_name = f"{base_name}{random_digits}"
                    config_content['organization'] = org_name
                    
                    # Convert back to JSON string with proper formatting
                    updated_config = json.dumps(config_content, indent=2)
                    
                    new_repo.update_file(
                        path="fern/fern.config.json",
                        message="Update organization name in fern.config.json",
                        content=updated_config,
                        sha=fern_config.sha
                    )
                    print(f"Updated fern.config.json with organization name: {org_name}")
                except GithubException as e:
                    print(f"Warning: Failed to update fern.config.json: {str(e)}")
                    # Don't raise an exception here as the main functionality succeeded

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
                    private=True,
                    auto_init=True  # Initialize with README
                )
                print(f"Created Python SDK repository: {python_repo_name}")

                # Create TypeScript SDK repository
                typescript_repo_name = f"{company_name}-typescript-sdk"
                print(f"Creating TypeScript SDK repository: {typescript_repo_name}")
                typescript_repo = auth_user.create_repo(
                    name=typescript_repo_name,
                    description=f"TypeScript SDK for {company_name} API",
                    private=True,
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
        avatar_url = user.get('avatar_url', f'https://github.com/identicons/{user["login"]}')
        user_login = user['login']
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>SDK Setup</title>
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}

                    body {{
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                        min-height: 100vh;
                        background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%);
                        color: #1f2937;
                        line-height: 1.5;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        padding: 2rem;
                    }}

                    .container {{
                        background: white;
                        border-radius: 16px;
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                        width: 100%;
                        max-width: 640px;
                        padding: 2.5rem;
                        transition: transform 0.2s ease;
                    }}

                    .container:hover {{
                        transform: translateY(-2px);
                    }}

                    h1 {{
                        font-size: 2rem;
                        font-weight: 600;
                        color: #111827;
                        margin-bottom: 2rem;
                        text-align: center;
                    }}

                    .form-group {{
                        margin-bottom: 1.5rem;
                    }}

                    label {{
                        display: block;
                        font-weight: 500;
                        margin-bottom: 0.5rem;
                        color: #374151;
                        font-size: 0.95rem;
                    }}

                    input[type="text"] {{
                        width: 100%;
                        padding: 0.75rem 1rem;
                        border: 1px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 1rem;
                        transition: all 0.2s ease;
                        background: #f9fafb;
                    }}

                    input[type="text"]:focus {{
                        outline: none;
                        border-color: #2563eb;
                        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                        background: white;
                    }}

                    input[type="file"] {{
                        width: 100%;
                        padding: 0.75rem;
                        border: 2px dashed #d1d5db;
                        border-radius: 8px;
                        font-size: 0.95rem;
                        cursor: pointer;
                        transition: all 0.2s ease;
                    }}

                    input[type="file"]:hover {{
                        border-color: #2563eb;
                        background: rgba(37, 99, 235, 0.05);
                    }}

                    textarea {{
                        width: 100%;
                        padding: 0.75rem 1rem;
                        border: 1px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 1rem;
                        transition: all 0.2s ease;
                        background: #f9fafb;
                        min-height: 100px;
                        resize: vertical;
                        font-family: inherit;
                    }}

                    textarea:focus {{
                        outline: none;
                        border-color: #2563eb;
                        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                        background: white;
                    }}

                    .file-info {{
                        font-size: 0.875rem;
                        color: #6b7280;
                        margin-top: 0.5rem;
                        padding-left: 0.5rem;
                    }}

                    button {{
                        width: 100%;
                        padding: 0.875rem 1.5rem;
                        background: #2563eb;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 1rem;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        margin-top: 1rem;
                    }}

                    button:hover {{
                        background: #1d4ed8;
                        transform: translateY(-1px);
                    }}

                    button:active {{
                        transform: translateY(0);
                    }}

                    #repository_dropdown {{
                        display: none;
                        position: absolute;
                        z-index: 1000;
                        width: 100%;
                        max-height: 200px;
                        overflow-y: auto;
                        background: white;
                        border: 1px solid #d1d5db;
                        border-radius: 8px;
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    }}

                    .repo-item {{
                        padding: 0.75rem;
                        cursor: pointer;
                        border-bottom: 1px solid #f3f4f6;
                    }}

                    .repo-item:hover {{
                        background: #f9fafb;
                    }}

                    .repo-tag {{
                        background: #dbeafe;
                        color: #1e40af;
                        padding: 0.25rem 0.75rem;
                        border-radius: 1rem;
                        font-size: 0.875rem;
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        margin: 0.25rem;
                    }}

                    .repo-tag button {{
                        background: none;
                        border: none;
                        color: #1e40af;
                        cursor: pointer;
                        padding: 0;
                        font-size: 1rem;
                        width: auto;
                        margin: 0;
                    }}

                    .user-info {{
                        display: flex;
                        align-items: center;
                        justify-content: flex-end;
                        margin-bottom: 2rem;
                        padding-bottom: 1rem;
                        border-bottom: 1px solid #e5e7eb;
                    }}

                    .user-info a {{
                        color: #4b5563;
                        text-decoration: none;
                        font-size: 0.95rem;
                        padding: 0.5rem 1rem;
                        border-radius: 6px;
                        transition: all 0.2s ease;
                        margin-left: 1rem;
                    }}

                    .user-info a:hover {{
                        background: #f3f4f6;
                        color: #111827;
                    }}

                    .user-avatar {{
                        width: 32px;
                        height: 32px;
                        border-radius: 50%;
                        margin-right: 0.75rem;
                    }}

                    .user-name {{
                        font-weight: 500;
                        color: #374151;
                    }}

                    @media (max-width: 640px) {{
                        body {{
                            padding: 1rem;
                        }}

                        .container {{
                            padding: 1.5rem;
                        }}

                        h1 {{
                            font-size: 1.75rem;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="user-info">
                        <img src="{avatar_url}" alt="Avatar" class="user-avatar">
                        <span class="user-name">{user_login}</span>
                        <a href="/logout">Logout</a>
                    </div>
                    <h1>SDK Setup</h1>
                    <form action="/submit" method="post" enctype="multipart/form-data">
                        <div class="form-group">
                            <label for="company_name">Company Name</label>
                            <input 
                                type="text" 
                                id="company_name" 
                                name="company_name" 
                                placeholder="Enter your company name"
                                required
                            >
                        </div>
                        <div class="form-group">
                            <label for="openapi_spec">OpenAPI Specification</label>
                            <input 
                                type="file" 
                                id="openapi_spec" 
                                name="openapi_spec" 
                                accept=".json,.yaml,.yml" 
                                required
                            >
                            <div class="file-info">
                                Supported formats: JSON (.json), YAML (.yaml, .yml)
                            </div>
                        </div>
                        <button type="submit">Generate SDK</button>
                    </form>
                    
                    <!-- Repository Access Management Section -->
                    <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e5e7eb;">
                        <h1 style="font-size: 1.5rem; margin-bottom: 1.5rem;">Repository Access Management</h1>
                        <form id="accessForm" style="margin-bottom: 2rem;">
                            <div class="form-group">
                                <label for="repository_select">Select Repositories</label>
                                <div style="position: relative;">
                                    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                                        <input 
                                            type="text" 
                                            id="repository_search" 
                                            placeholder="Search repositories..."
                                            style="flex: 1; margin-bottom: 0;"
                                        >
                                        <button 
                                            type="button" 
                                            id="refresh_repos" 
                                            onclick="refreshRepositories()"
                                            style="width: auto; padding: 0.75rem; background: #6b7280; margin: 0;"
                                            title="Refresh repositories list"
                                        >
                                            ↻
                                        </button>
                                    </div>
                                    <div id="repository_dropdown"></div>
                                </div>
                                <div id="selected_repos" style="margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="github_usernames">GitHub Usernames or Emails</label>
                                <div id="username_input_container" class="username-input-container">
                                    <input 
                                        type="text" 
                                        id="github_usernames" 
                                        name="github_usernames" 
                                        placeholder="Type usernames or emails and press space..."
                                        autocomplete="off"
                                        class="username-input"
                                    >
                                </div>
                                <div class="file-info">
                                    Type usernames/emails and press space to add them as tags. Users will be added with "Maintain" permissions.
                                </div>
                            </div>
                            <button type="button" onclick="addRepoAccess()" style="background: #059669;">
                                Add Repository Access
                            </button>
                        </form>
                        <div id="accessResults" style="margin-top: 1rem;">
                        </div>
                    </div>
                </div>
                
                <script>
                let userRepositories = [];
                let selectedRepositories = [];
                let repositoriesLoaded = false;
                let isLoadingRepositories = false;

                // Initialize everything when DOM is ready
                document.addEventListener('DOMContentLoaded', function() {{
                    initializeRepositorySearch();
                    initializeUsernameParser();
                }});

                // Also ensure repositories are loaded when page becomes visible
                document.addEventListener('visibilitychange', function() {{
                    if (!document.hidden && !repositoriesLoaded && !isLoadingRepositories) {{
                        console.log('Page became visible, loading repositories...');
                        loadUserRepositories();
                    }}
                }});

                // Force refresh on window focus as well
                window.addEventListener('focus', function() {{
                    if (!repositoriesLoaded && !isLoadingRepositories) {{
                        console.log('Window focused, loading repositories...');
                        loadUserRepositories();
                    }}
                }});

                let usernamePills = [];

                function initializeUsernameParser() {{
                    const usernameInput = document.getElementById('github_usernames');
                    const container = document.getElementById('username_input_container');
                    
                    if (!usernameInput || !container) return;
                    
                    // Handle input events
                    usernameInput.addEventListener('keydown', handleUsernameKeydown);
                    usernameInput.addEventListener('input', handleUsernameInput);
                    usernameInput.addEventListener('paste', handleUsernamePaste);
                    
                    // Make container clickable to focus input
                    container.addEventListener('click', function(e) {{
                        if (!e.target.closest('.username-pill')) {{
                            usernameInput.focus();
                        }}
                    }});
                    
                    // Initialize display
                    updateInputDisplay();
                }}

                function handleUsernameKeydown(e) {{
                    const input = e.target;
                    const cursorPos = input.selectionStart;
                    const value = input.value;
                    
                    // Handle space, comma, semicolon, or enter to create pill
                    if ((e.key === ' ' || e.key === ',' || e.key === ';' || e.key === 'Enter')) {{
                        const beforeCursor = value.substring(0, cursorPos);
                        const afterCursor = value.substring(cursorPos);
                        
                        // Find the current word being typed
                        const wordStart = Math.max(0, beforeCursor.lastIndexOf(' ') + 1);
                        const currentWord = beforeCursor.substring(wordStart).trim();
                        
                        if (currentWord) {{
                            e.preventDefault();
                            addUsernamePill(currentWord);
                            
                            // Update input value
                            const newValue = value.substring(0, wordStart) + value.substring(cursorPos);
                            input.value = newValue.trim();
                            updateInputDisplay();
                            return;
                        }}
                    }}
                    
                    // Handle backspace to remove last pill when at start or after space
                    if (e.key === 'Backspace' && cursorPos === 0 && usernamePills.length > 0) {{
                        e.preventDefault();
                        removeUsernamePill(usernamePills.length - 1);
                        return;
                    }}
                }}

                function handleUsernameInput(e) {{
                    updateInputDisplay();
                }}

                function handleUsernamePaste(e) {{
                    setTimeout(() => {{
                        const input = e.target;
                        const value = input.value;
                        const tokens = value.split(/[\\s,;\\n\\r\\t]+/).filter(t => t.trim());
                        
                        if (tokens.length > 1) {{
                            e.preventDefault();
                            // Add all tokens as pills
                            tokens.forEach(token => {{
                                if (token.trim()) {{
                                    addUsernamePill(token.trim());
                                }}
                            }});
                            input.value = '';
                            updateInputDisplay();
                        }}
                    }}, 10);
                }}

                function addUsernamePill(input) {{
                    const trimmedInput = input.trim();
                    if (!trimmedInput) return;
                    
                    // Extract username from email if it's an email
                    let username = trimmedInput;
                    let isEmail = false;
                    
                    if (trimmedInput.includes('@')) {{
                        username = trimmedInput.split('@')[0];
                        isEmail = true;
                    }}
                    
                    // Validate GitHub username
                    if (!isValidGitHubUsername(username)) {{
                        console.log('Invalid GitHub username:', username);
                        return;
                    }}
                    
                    // Check for duplicates
                    if (usernamePills.some(pill => pill.username.toLowerCase() === username.toLowerCase())) {{
                        console.log('Duplicate username:', username);
                        return;
                    }}
                    
                    // Add to pills array
                    const pill = {{
                        original: trimmedInput,
                        username: username,
                        isEmail: isEmail
                    }};
                    
                    usernamePills.push(pill);
                    updateInputDisplay();
                }}

                function removeUsernamePill(index) {{
                    if (index >= 0 && index < usernamePills.length) {{
                        usernamePills.splice(index, 1);
                        updateInputDisplay();
                    }}
                }}

                function updateInputDisplay() {{
                    const container = document.getElementById('username_input_container');
                    const input = document.getElementById('github_usernames');
                    
                    if (!container || !input) return;
                    
                    // Remove existing pills
                    const existingPills = container.querySelectorAll('.username-pill');
                    existingPills.forEach(pill => pill.remove());
                    
                    // Create and insert pills before the input
                    usernamePills.forEach((pill, index) => {{
                        const displayText = pill.isEmail ? `${{pill.username}}` : pill.username;
                        const emailClass = pill.isEmail ? ' email' : '';
                        const tooltip = pill.isEmail ? `Extracted from email: ${{pill.original}}` : `GitHub username: ${{pill.username}}`;
                        
                        const pillElement = document.createElement('div');
                        pillElement.className = `username-pill${{emailClass}}`;
                        pillElement.title = tooltip;
                        pillElement.innerHTML = `
                            <span class="pill-text">${{displayText}}</span>
                            <button class="remove-btn" onclick="removeUsernamePill(${{index}})" type="button">×</button>
                        `;
                        
                        container.insertBefore(pillElement, input);
                    }});
                    
                    // Update placeholder
                    input.placeholder = usernamePills.length > 0 
                        ? 'Add more users...' 
                        : 'Type usernames or emails and press space...';
                }}

                function isValidGitHubUsername(username) {{
                    // GitHub username rules:
                    // - May only contain alphanumeric characters or single hyphens
                    // - Cannot begin or end with a hyphen
                    // - Maximum 39 characters
                    const githubUsernameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{{0,37}}[a-zA-Z0-9])?$/;
                    return githubUsernameRegex.test(username);
                }}

                function getUsernamesForSubmission() {{
                    return usernamePills.map(pill => pill.username);
                }}

                async function initializeRepositorySearch() {{
                    const searchInput = document.getElementById('repository_search');
                    if (!searchInput) return;
                    
                    // Set up search input event listener
                    searchInput.addEventListener('input', function(e) {{
                        console.log('Search input changed:', e.target.value);
                        handleRepositorySearch(e);
                    }});
                    
                    // Add focus event to load repositories if not already loaded
                    searchInput.addEventListener('focus', function() {{
                        console.log('Search input focused, checking repositories...');
                        if (!repositoriesLoaded && !isLoadingRepositories) {{
                            loadUserRepositories();
                        }}
                    }});
                    
                    // Load repositories immediately
                    await loadUserRepositories();
                }}

                async function loadUserRepositories(retryCount = 3) {{
                    if (isLoadingRepositories) {{
                        console.log('Already loading repositories, skipping...');
                        return;
                    }}
                    
                    isLoadingRepositories = true;
                    const searchInput = document.getElementById('repository_search');
                    
                    // Show loading state
                    if (searchInput) {{
                        const originalPlaceholder = searchInput.placeholder;
                        searchInput.placeholder = 'Loading repositories...';
                        searchInput.disabled = true;
                    }}
                    
                    for (let attempt = 1; attempt <= retryCount; attempt++) {{
                        try {{
                            console.log(`Loading repositories... (attempt ${{attempt}}/${{retryCount}})`);
                            const response = await fetch('/api/repositories', {{
                                method: 'GET',
                                headers: {{
                                    'Cache-Control': 'no-cache'
                                }}
                            }});
                            
                            if (!response.ok) {{
                                throw new Error(`HTTP error! status: ${{response.status}}`);
                            }}
                            
                            const repos = await response.json();
                            userRepositories = repos;
                            repositoriesLoaded = true;
                            console.log('Successfully loaded repositories:', repos.length, repos);
                            
                            // Update UI to ready state
                            if (searchInput) {{
                                searchInput.disabled = false;
                                if (repos.length === 0) {{
                                    searchInput.placeholder = 'No repositories found with admin access';
                                }} else {{
                                    searchInput.placeholder = 'Search repositories...';
                                }}
                            }}
                            
                            isLoadingRepositories = false;
                            return; // Success, exit retry loop
                            
                        }} catch (error) {{
                            console.error(`Failed to load repositories (attempt ${{attempt}}):`, error);
                            
                            if (attempt === retryCount) {{
                                // Final attempt failed
                                if (searchInput) {{
                                    searchInput.placeholder = 'Error loading repositories - click to retry';
                                    searchInput.disabled = false;
                                    searchInput.style.cursor = 'pointer';
                                    
                                    // Add click handler to retry
                                    const retryHandler = function() {{
                                        console.log('Retrying repository load...');
                                        searchInput.removeEventListener('click', retryHandler);
                                        searchInput.style.cursor = '';
                                        repositoriesLoaded = false;
                                        isLoadingRepositories = false;
                                        loadUserRepositories();
                                    }};
                                    searchInput.addEventListener('click', retryHandler);
                                }}
                            }} else {{
                                // Wait before retry (exponential backoff)
                                await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                            }}
                        }}
                    }}
                    
                    isLoadingRepositories = false;
                }}

                function refreshRepositories() {{
                    console.log('Manually refreshing repositories...');
                    repositoriesLoaded = false;
                    isLoadingRepositories = false;
                    userRepositories = [];
                    
                    // Clear search and dropdown
                    const searchInput = document.getElementById('repository_search');
                    const dropdown = document.getElementById('repository_dropdown');
                    
                    if (searchInput) {{
                        searchInput.value = '';
                    }}
                    if (dropdown) {{
                        dropdown.style.display = 'none';
                    }}
                    
                    // Reload repositories
                    loadUserRepositories();
                }}

                function handleRepositorySearch(e) {{
                    const searchTerm = e.target.value.toLowerCase();
                    const dropdown = document.getElementById('repository_dropdown');
                    
                    console.log('Searching for:', searchTerm, 'Total repos:', userRepositories.length, 'Loaded:', repositoriesLoaded);
                    
                    // If repositories aren't loaded yet, try to load them
                    if (!repositoriesLoaded && !isLoadingRepositories) {{
                        console.log('Repositories not loaded, loading now...');
                        loadUserRepositories();
                        dropdown.innerHTML = '<div class="repo-item" style="color: #6b7280; font-style: italic;">Loading repositories...</div>';
                        dropdown.style.display = 'block';
                        return;
                    }}
                    
                    if (isLoadingRepositories) {{
                        dropdown.innerHTML = '<div class="repo-item" style="color: #6b7280; font-style: italic;">Loading repositories...</div>';
                        dropdown.style.display = 'block';
                        return;
                    }}
                    
                    if (searchTerm.length === 0) {{
                        dropdown.style.display = 'none';
                        return;
                    }}

                    const filteredRepos = userRepositories.filter(repo => {{
                        const nameMatch = repo.name.toLowerCase().includes(searchTerm);
                        const notSelected = !selectedRepositories.some(selected => selected.id === repo.id);
                        console.log(`Repo ${{repo.name}}: nameMatch=${{nameMatch}}, notSelected=${{notSelected}}`);
                        return nameMatch && notSelected;
                    }});

                    console.log('Filtered repos:', filteredRepos.length, filteredRepos);

                    if (filteredRepos.length === 0) {{
                        const message = userRepositories.length === 0 
                            ? 'No repositories available' 
                            : 'No matching repositories found';
                        dropdown.innerHTML = `<div class="repo-item" style="color: #6b7280; font-style: italic;">${{message}}</div>`;
                        dropdown.style.display = 'block';
                        return;
                    }}

                    dropdown.innerHTML = filteredRepos.map(repo => 
                        `<div class="repo-item" onclick="selectRepository(${{repo.id}})" data-repo-id="${{repo.id}}">
                            <strong>${{repo.name}}</strong>
                            <div style="font-size: 0.875rem; color: #6b7280;">${{repo.description || 'No description'}}</div>
                        </div>`
                    ).join('');
                    
                    dropdown.style.display = 'block';
                }}

                function selectRepository(repoId) {{
                    console.log('Selecting repository:', repoId);
                    const repo = userRepositories.find(r => r.id === repoId);
                    if (repo && !selectedRepositories.some(selected => selected.id === repoId)) {{
                        selectedRepositories.push(repo);
                        updateSelectedReposDisplay();
                        document.getElementById('repository_search').value = '';
                        document.getElementById('repository_dropdown').style.display = 'none';
                        console.log('Selected repositories:', selectedRepositories);
                    }} else {{
                        console.log('Repository not found or already selected');
                    }}
                }}

                function removeRepository(repoId) {{
                    console.log('Removing repository:', repoId);
                    selectedRepositories = selectedRepositories.filter(repo => repo.id !== repoId);
                    updateSelectedReposDisplay();
                }}

                function updateSelectedReposDisplay() {{
                    const container = document.getElementById('selected_repos');
                    container.innerHTML = selectedRepositories.map(repo => 
                        `<span class="repo-tag">
                            ${{repo.name}}
                            <button onclick="removeRepository(${{repo.id}})" type="button">×</button>
                        </span>`
                    ).join('');
                    
                    console.log('Updated selected repos display:', selectedRepositories.length);
                }}

                document.addEventListener('click', function(e) {{
                    if (!e.target.closest('#repository_search') && !e.target.closest('#repository_dropdown')) {{
                        document.getElementById('repository_dropdown').style.display = 'none';
                    }}
                }});

                async function addRepoAccess() {{
                    const resultsDiv = document.getElementById('accessResults');
                    
                    if (selectedRepositories.length === 0) {{
                        resultsDiv.innerHTML = '<div style="color: #dc2626; background: #fef2f2; padding: 1rem; border-radius: 8px; border: 1px solid #fecaca;">Please select at least one repository.</div>';
                        return;
                    }}
                    
                    // Get usernames from pills
                    const usernames = getUsernamesForSubmission();
                    
                    if (usernames.length === 0) {{
                        resultsDiv.innerHTML = '<div style="color: #dc2626; background: #fef2f2; padding: 1rem; border-radius: 8px; border: 1px solid #fecaca;">Please add at least one GitHub username or email.</div>';
                        return;
                    }}
                    
                    console.log('Adding repo access:', selectedRepositories.length, 'repos for users:', usernames);

                    resultsDiv.innerHTML = '<div style="color: #2563eb; background: #eff6ff; padding: 1rem; border-radius: 8px; border: 1px solid #bfdbfe;">Processing...</div>';

                    try {{
                        const response = await fetch('/api/add-repo-access', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                repositories: selectedRepositories.map(repo => repo.full_name),
                                usernames: usernames
                            }})
                        }});

                        if (!response.ok) {{
                            throw new Error(`HTTP error! status: ${{response.status}}`);
                        }}

                        const result = await response.json();
                        displayAccessResults(result);
                    }} catch (error) {{
                        console.error('Error adding repo access:', error);
                        resultsDiv.innerHTML = '<div style="color: #dc2626; background: #fef2f2; padding: 1rem; border-radius: 8px; border: 1px solid #fecaca;">An error occurred. Please try again. Check console for details.</div>';
                    }}
                }}

                function displayAccessResults(results) {{
                    const resultsDiv = document.getElementById('accessResults');
                    let html = '<div style="margin-top: 1rem;">';
                    
                    results.forEach(result => {{
                        const isSuccess = result.success;
                        const bgColor = isSuccess ? '#f0fdf4' : '#fef2f2';
                        const borderColor = isSuccess ? '#86efac' : '#fecaca';
                        const textColor = isSuccess ? '#15803d' : '#dc2626';
                        const icon = isSuccess ? '✓' : '✗';
                        
                        html += `<div style="background: ${{bgColor}}; border: 1px solid ${{borderColor}}; color: ${{textColor}}; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem;">
                            <strong>${{icon}} ${{result.repository}}</strong> - ${{result.username}}: ${{result.message}}
                        </div>`;
                    }});
                    
                    html += '</div>';
                    resultsDiv.innerHTML = html;
                    
                    if (results.some(r => r.success)) {{
                        setTimeout(() => {{
                            // Clear username pills
                            usernamePills = [];
                            document.getElementById('github_usernames').value = '';
                            updateInputDisplay();
                            
                            // Clear selected repositories
                            selectedRepositories = [];
                            updateSelectedReposDisplay();
                        }}, 3000);
                    }}
                }}
                </script>
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
            <!DOCTYPE html>
            <html>
                <head>
                    <title>SDK Setup - Success</title>
                    <link rel="preconnect" href="https://fonts.googleapis.com">
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
                    <style>
                        * {{
                            margin: 0;
                            padding: 0;
                            box-sizing: border-box;
                        }}

                        body {{
                            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                            min-height: 100vh;
                            background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%);
                            color: #1f2937;
                            line-height: 1.5;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            padding: 2rem;
                        }}

                        .container {{
                            background: white;
                            border-radius: 16px;
                            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                            width: 100%;
                            max-width: 720px;
                            padding: 2.5rem;
                        }}

                        h1, h2 {{
                            color: #111827;
                            margin-bottom: 1.5rem;
                        }}

                        h1 {{
                            font-size: 2rem;
                            font-weight: 600;
                            display: flex;
                            align-items: center;
                            gap: 0.75rem;
                        }}

                        h2 {{
                            font-size: 1.25rem;
                            font-weight: 600;
                            margin-top: 2rem;
                        }}

                        .success-icon {{
                            width: 32px;
                            height: 32px;
                            background: #22c55e;
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 1.25rem;
                        }}

                        .success-message {{
                            color: #15803d;
                            background: #f0fdf4;
                            padding: 1rem;
                            border-radius: 8px;
                            margin-bottom: 2rem;
                            border: 1px solid #86efac;
                        }}

                        .repo-list {{
                            list-style: none;
                            margin: 1rem 0;
                        }}

                        .repo-list li {{
                            padding: 1rem;
                            background: #f8fafc;
                            border: 1px solid #e2e8f0;
                            border-radius: 8px;
                            margin-bottom: 0.75rem;
                        }}

                        .repo-list li:hover {{
                            border-color: #94a3b8;
                        }}

                        .repo-list a {{
                            color: #2563eb;
                            text-decoration: none;
                            font-weight: 500;
                        }}

                        .repo-list a:hover {{
                            text-decoration: underline;
                        }}

                        .step-container {{
                            background: #f8fafc;
                            border: 1px solid #e2e8f0;
                            border-radius: 12px;
                            padding: 1.5rem;
                            margin: 1.5rem 0;
                        }}

                        .step-number {{
                            display: inline-block;
                            width: 24px;
                            height: 24px;
                            background: #2563eb;
                            color: white;
                            border-radius: 50%;
                            text-align: center;
                            line-height: 24px;
                            font-size: 0.875rem;
                            margin-right: 0.75rem;
                        }}

                        ol {{
                            list-style: none;
                            margin: 1rem 0;
                            padding-left: 1rem;
                        }}

                        ol li {{
                            margin-bottom: 0.5rem;
                            color: #4b5563;
                        }}

                        button {{
                            background: #2563eb;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 0.875rem 1.5rem;
                            font-size: 1rem;
                            font-weight: 500;
                            cursor: pointer;
                            transition: all 0.2s ease;
                            display: inline-flex;
                            align-items: center;
                            gap: 0.5rem;
                        }}

                        button:hover {{
                            background: #1d4ed8;
                            transform: translateY(-1px);
                        }}

                        button:active {{
                            transform: translateY(0);
                        }}

                        #refresh_repos:hover {{
                            background: #4b5563 !important;
                            transform: rotate(180deg);
                            transition: all 0.3s ease;
                        }}

                        .status-message {{
                            margin-top: 1rem;
                            padding: 1rem;
                            border-radius: 8px;
                            background: #f0fdf4;
                            border: 1px solid #86efac;
                            color: #15803d;
                            display: none;
                        }}

                        .home-link {{
                            display: inline-block;
                            margin-top: 2rem;
                            color: #4b5563;
                            text-decoration: none;
                            padding: 0.5rem 1rem;
                            border-radius: 6px;
                            transition: all 0.2s ease;
                        }}

                                            .home-link:hover {{
                        background: #f3f4f6;
                        color: #111827;
                    }}



                    .username-input-container {{
                        position: relative;
                        display: flex;
                        flex-wrap: wrap;
                        align-items: center;
                        gap: 0.25rem;
                        border: 2px solid #e1e5e9;
                        border-radius: 8px;
                        background: white;
                        min-height: 44px;
                        padding: 0.5rem 0.75rem;
                        cursor: text;
                        transition: all 0.15s ease;
                        font-family: 'Slack-Lato', 'Lato', sans-serif;
                    }}

                    .username-input-container:focus-within {{
                        border-color: #1264a3;
                        box-shadow: 0 0 0 1px #1264a3;
                    }}

                    .username-input {{
                        border: none;
                        outline: none;
                        background: transparent;
                        flex: 1;
                        min-width: 120px;
                        font-size: 15px;
                        padding: 0;
                        font-family: inherit;
                        color: #1d1c1d;
                    }}

                    .username-input::placeholder {{
                        color: #616061;
                        font-weight: 400;
                    }}

                    .username-pill {{
                        display: inline-flex;
                        align-items: center;
                        gap: 0.25rem;
                        background: #1264a3;
                        color: white;
                        padding: 0.125rem 0.25rem 0.125rem 0.5rem;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: 700;
                        line-height: 1.2;
                        cursor: default;
                        max-width: 200px;
                        font-family: inherit;
                        flex-shrink: 0;
                    }}

                    .username-pill.email {{
                        background: #e01e5a;
                    }}

                    .username-pill:hover {{
                        opacity: 0.9;
                    }}

                    .username-pill .pill-text {{
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        max-width: 150px;
                    }}

                    .username-pill .remove-btn {{
                        background: transparent;
                        border: none;
                        border-radius: 2px;
                        width: 16px;
                        height: 16px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        font-size: 14px;
                        font-weight: bold;
                        color: white;
                        transition: background-color 0.15s ease;
                        margin-left: 0.125rem;
                    }}

                    .username-pill .remove-btn:hover {{
                        background: rgba(255, 255, 255, 0.2);
                    }}

                    .username-pill .remove-btn:active {{
                        background: rgba(255, 255, 255, 0.3);
                    }}

                    @media (max-width: 640px) {{
                            body {{
                                padding: 1rem;
                            }}

                            .container {{
                                padding: 1.5rem;
                            }}

                            h1 {{
                                font-size: 1.75rem;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>
                            <span class="success-icon">✓</span>
                            Setup Complete
                        </h1>
                        <p class="success-message">Successfully set up SDK configuration for {company_name}</p>
                        
                        <h2>Created Repositories</h2>
                        <ul class="repo-list">
                            <li>
                                <strong>Configuration:</strong><br>
                                <a href="{repo_url}" target="_blank">{repo_url}</a>
                            </li>
                            <li>
                                <strong>Python SDK:</strong><br>
                                <a href="https://github.com/{user['login']}/{company_name}-python-sdk" target="_blank">
                                    github.com/{user['login']}/{company_name}-python-sdk
                                </a>
                            </li>
                            <li>
                                <strong>TypeScript SDK:</strong><br>
                                <a href="https://github.com/{user['login']}/{company_name}-typescript-sdk" target="_blank">
                                    github.com/{user['login']}/{company_name}-typescript-sdk
                                </a>
                            </li>
                        </ul>
                        
                        <div class="step-container">
                            <h2><span class="step-number">1</span>Install Fern API</h2>
                            <p>To enable automatic SDK generation, please install the Fern API GitHub App:</p>
                            <ol>
                                <li>Click the button below to open the installation page</li>
                                <li>Review the repository access</li>
                                <li>Click "Install" to complete the setup</li>
                            </ol>
                            <a href="{installation_url}" target="_blank">
                                <button>
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M12 5v14M5 12h14"/>
                                    </svg>
                                    Install Fern API
                                </button>
                            </a>
                        </div>

                        <div class="step-container">
                            <h2><span class="step-number">2</span>Setup Local Environment</h2>
                            <p>This will prepare your local environment with:</p>
                            <ol>
                                <li>Clone the configuration repository</li>
                                <li>Install Fern CLI</li>
                                <li>Run initial setup and login</li>
                            </ol>
                            <button onclick="setupLocalEnv('{company_name}', '{user['login']}')">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M8 13v-1h8v1M12 12v7m-4-3l4 3 4-3"/>
                                </svg>
                                Setup Local Environment
                            </button>
                            <div id="setupStatus"></div>
                        </div>

                        <div class="step-container">
                            <h2><span class="step-number">3</span>Generate SDKs</h2>
                            <p>After completing Fern authentication in your terminal, generate your SDKs:</p>
                            <button onclick="generateSDKs('{company_name}', '{user['login']}')">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 4v16m-8-8h16"/>
                                </svg>
                                Generate SDKs
                            </button>
                            <div id="generateStatus"></div>
                        </div>
                        
                        <a href="/" class="home-link">← Create Another SDK</a>

                        <script>
                        function copyToClipboard(text) {{
                            const textarea = document.createElement('textarea');
                            textarea.value = text;
                            document.body.appendChild(textarea);
                            textarea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textarea);
                        }}

                        function setupLocalEnv(companyName, username) {{
                            const setupCmd = `cd /tmp && \\
git clone https://github.com/${{username}}/${{companyName}}-config.git && \\
npm install -g fern-api && \\
cd ${{companyName}}-config && \\
fern upgrade && \\
fern login`;
                            
                            copyToClipboard(setupCmd);
                            document.getElementById('setupStatus').innerHTML = `
                                <div class="status-message" style="display: block;">
                                    <strong>✓ Command copied to clipboard!</strong><br>
                                    Please paste and run the command in your terminal.
                                </div>
                            `;
                        }}

                        function generateSDKs(companyName, username) {{
                            const generateCmd = `cd /tmp/${{companyName}}-config && \\
fern generate --group python-sdk && \\
fern generate --group ts-sdk`;
                            
                            copyToClipboard(generateCmd);
                            document.getElementById('generateStatus').innerHTML = `
                                <div class="status-message" style="display: block;">
                                    <strong>✓ Command copied to clipboard!</strong><br>
                                    Please paste and run the command in your terminal.
                                </div>
                            `;
                        }}
                        </script>
                    </div>
                </body>
            </html>
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

@app.post("/setup-fern")
async def setup_fern(request: Request, data: dict):
    """Setup Fern CLI and initiate authentication."""
    try:
        # Check authentication
        user = await get_current_user(request)
        company_name = data.get('company_name')
        if not company_name:
            raise HTTPException(status_code=400, detail="Company name is required")

        # Create a temporary directory for the repository
        repo_dir = f"/tmp/{company_name}-config"
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)  # Clean up any existing directory
        os.makedirs(repo_dir)

        try:
            # Install Fern CLI globally
            subprocess.run(['npm', 'install', '-g', 'fern-api'], check=True)
            
            # Clone the repository
            repo_url = f"https://github.com/{user['login']}/{company_name}-config.git"
            subprocess.run(['git', 'clone', repo_url, repo_dir], check=True)
            
            # Change to repository directory and run fern upgrade
            os.chdir(repo_dir)
            subprocess.run(['fern', 'upgrade'], check=True)
            
            # Start fern login process
            process = subprocess.Popen(['fern', 'login'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
            
            # Store the process information for later use
            request.session['fern_process'] = process
            request.session['repo_dir'] = repo_dir
            
            return {"status": "success", "message": "Fern CLI setup initiated"}
            
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, 
                              detail=f"Command failed: {e.cmd}. Output: {e.output}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-sdks")
async def generate_sdks(request: Request, data: dict):
    """Generate SDKs using Fern CLI."""
    try:
        # Check authentication
        user = await get_current_user(request)
        company_name = data.get('company_name')
        if not company_name:
            raise HTTPException(status_code=400, detail="Company name is required")

        # Get the repository directory from session
        repo_dir = request.session.get('repo_dir')
        if not repo_dir:
            raise HTTPException(status_code=400, detail="Fern setup not completed")

        # Change to repository directory
        os.chdir(repo_dir)

        # Generate TypeScript SDK
        subprocess.run(['fern', 'generate', '--group', 'ts-sdk'], check=True)
        
        # Generate Python SDK
        subprocess.run(['fern', 'generate', '--group', 'python-sdk'], check=True)

        # Clean up
        shutil.rmtree(repo_dir)
        
        return {"status": "success", "message": "SDKs generated successfully"}
            
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, 
                          detail=f"Command failed: {e.cmd}. Output: {e.output}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/repositories")
async def get_repositories(request: Request):
    """Get user's repositories where they have admin access."""
    try:
        user = await get_current_user(request)
        g = Github(user['access_token'])
        
        print(f"Fetching repositories for user: {user['login']}")
        
        # Get repositories where user has admin access
        repositories = []
        auth_user = g.get_user()
        
        for repo in auth_user.get_repos():
            try:
                # Check if user has admin permissions
                if repo.permissions and repo.permissions.admin:
                    repositories.append({
                        'id': repo.id,
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'description': repo.description,
                        'private': repo.private,
                        'permissions': {
                            'admin': repo.permissions.admin,
                            'maintain': repo.permissions.maintain if hasattr(repo.permissions, 'maintain') else False,
                            'push': repo.permissions.push,
                            'pull': repo.permissions.pull
                        }
                    })
            except Exception as repo_error:
                print(f"Error processing repo {repo.name}: {str(repo_error)}")
                continue
        
        print(f"Found {len(repositories)} repositories with admin access")
        return repositories
        
    except Exception as e:
        print(f"Error fetching repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")

@app.post("/api/add-repo-access")
async def add_repo_access(request: Request):
    """Add users to repositories with maintain permissions."""
    try:
        user = await get_current_user(request)
        data = await request.json()
        repositories = data.get('repositories', [])
        usernames = data.get('usernames', [])
        
        g = Github(user['access_token'])
        results = []
        
        for repo_name in repositories:
            repo = g.get_repo(repo_name)
            for username in usernames:
                try:
                    repo.add_to_collaborators(username, permission='maintain')
                    results.append({
                        'repository': repo_name,
                        'username': username,
                        'success': True,
                        'message': 'Successfully added as maintainer'
                    })
                except Exception as e:
                    results.append({
                        'repository': repo_name,
                        'username': username,
                        'success': False,
                        'message': str(e)
                    })
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 