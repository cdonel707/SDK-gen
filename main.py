from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import modularized components
from config import UPLOADS_DIR
from routes import router as web_router
from api import router as api_router

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

# Create uploads directory if it doesn't exist
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Include routers
app.include_router(web_router)
app.include_router(api_router) 