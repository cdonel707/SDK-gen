import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Directories
UPLOADS_DIR = "uploads"

# Session management
sessions = {} 