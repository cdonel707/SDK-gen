from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from github import Github
import os
from dotenv import load_dotenv
import httpx
import json
from typing import Optional

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

# Environment variables
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/auth/github")
async def github_auth():
    return {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": f"{os.getenv('RAILWAY_STATIC_URL')}/auth/callback"
    }

@app.post("/setup")
async def setup_sdk(company_name: str, openapi_spec: str, languages: list[str]):
    try:
        # Initialize GitHub client
        g = Github(GITHUB_ACCESS_TOKEN)
        
        # Normalize company name
        normalized_name = company_name.lower().replace(" ", "-")
        
        # Create config repo
        config_repo_name = f"{normalized_name}-config"
        config_repo = g.get_user().create_repo(
            config_repo_name,
            description=f"Configuration repository for {company_name} SDK",
            private=False
        )
        
        # Create SDK repos
        sdk_repos = {}
        for lang in languages:
            repo_name = f"{normalized_name}-{lang.lower()}-sdk"
            sdk_repos[lang] = g.get_user().create_repo(
                repo_name,
                description=f"{company_name} {lang} SDK",
                private=False
            )
        
        # TODO: Add OpenAPI spec to config repo
        # TODO: Update generators.yml
        # TODO: Run Fern CLI
        
        return {
            "status": "success",
            "repos": {
                "config": config_repo.html_url,
                "sdks": {lang: repo.html_url for lang, repo in sdk_repos.items()}
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 