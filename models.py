from pydantic import BaseModel
from typing import List, Optional

class RepositoryInfo(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    permissions: dict

class RepoAccessRequest(BaseModel):
    repositories: List[str]
    usernames: List[str]

class RepoAccessResult(BaseModel):
    repository: str
    username: str
    success: bool
    message: str

class UserSession(BaseModel):
    login: str
    avatar_url: str
    access_token: str 