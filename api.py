from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List
from auth import get_current_user
from github_operations import get_user_repositories, add_users_to_repositories
from models import RepoAccessRequest, RepoAccessResult

router = APIRouter()

@router.get("/api/repositories")
async def get_repositories(request: Request):
    """Get user's repositories where they have admin access."""
    try:
        user = await get_current_user(request)
        repositories = await get_user_repositories(user['access_token'])
        
        # Convert Pydantic models to dict for JSON response
        return [repo.dict() for repo in repositories]
        
    except Exception as e:
        print(f"Error fetching repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")

@router.post("/api/add-repo-access")
async def add_repo_access(request: Request):
    """Add users to repositories with maintain permissions."""
    try:
        user = await get_current_user(request)
        data = await request.json()
        
        repositories = data.get('repositories', [])
        usernames = data.get('usernames', [])
        
        if not repositories:
            raise HTTPException(status_code=400, detail="No repositories specified")
        if not usernames:
            raise HTTPException(status_code=400, detail="No usernames specified")
        
        results = await add_users_to_repositories(
            user['access_token'], 
            repositories, 
            usernames
        )
        
        # Convert Pydantic models to dict for JSON response
        return [result.dict() for result in results]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding repo access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add repository access: {str(e)}") 