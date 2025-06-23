from fastapi import APIRouter, Form, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse
from auth import get_current_user, github_auth, github_callback, logout
from github_operations import create_repo_from_template
from utils import validate_openapi, get_file_extension
from templates import get_login_template, get_main_template, get_success_template
import os
import shutil
import subprocess

router = APIRouter()

@router.get("/auth/github")
async def auth_github():
    """Redirect to GitHub OAuth page."""
    return await github_auth()

@router.get("/auth/callback")
async def auth_callback(code: str, state: str):
    """Handle GitHub OAuth callback."""
    return await github_callback(code, state)

@router.get("/logout")
async def logout_user():
    """Logout the user."""
    return await logout()

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Show the form or login page."""
    try:
        user = await get_current_user(request)
        avatar_url = user.get('avatar_url', f'https://github.com/identicons/{user["login"]}')
        user_login = user['login']
        
        # Return the main template with the full HTML
        return HTMLResponse(get_main_template(user_login, avatar_url))
        
    except HTTPException:
        return HTMLResponse(get_login_template())

@router.post("/submit")
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
        file_extension = get_file_extension(openapi_spec.filename)
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
        
        return HTMLResponse(get_success_template(
            company_name, 
            repo_url, 
            user['login'], 
            installation_url
        ))
        
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

@router.post("/setup-fern")
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

@router.post("/generate-sdks")
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