# SDK Generator Application

A FastAPI application for generating SDKs from OpenAPI specifications using GitHub repositories and the Fern API.

## Modular Structure

This application has been organized into the following modules for better maintainability:

### Core Files

- **`main.py`** - Application entry point with FastAPI app initialization and middleware setup
- **`config.py`** - Configuration management and environment variables
- **`models.py`** - Pydantic data models and schemas

### Feature Modules

- **`auth.py`** - GitHub OAuth authentication handling
- **`github_operations.py`** - GitHub API operations (repository creation, management)
- **`utils.py`** - Utility functions (file validation, etc.)
- **`templates.py`** - HTML template generation
- **`routes.py`** - Web route handlers (form pages, OAuth flows)
- **`api.py`** - REST API endpoints

## Key Features

- GitHub OAuth authentication
- OpenAPI specification validation (JSON/YAML)
- Repository creation from templates
- SDK generation for Python and TypeScript
- Repository access management
- Fern API integration

## Installation

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn python-github python-dotenv pydantic httpx pyyaml
   ```

2. Set up environment variables:
   ```bash
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   RAILWAY_PUBLIC_DOMAIN=your_domain
   ```

3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Architecture Benefits

- **Separation of Concerns**: Each module handles a specific aspect of functionality
- **Maintainability**: Easy to locate and modify specific features
- **Testability**: Individual modules can be tested in isolation
- **Scalability**: New features can be added as separate modules
- **Code Reusability**: Common functionality is centralized in utility modules

## Module Dependencies

```
main.py
├── config.py
├── routes.py
│   ├── auth.py
│   ├── github_operations.py
│   ├── utils.py
│   └── templates.py
└── api.py
    ├── auth.py
    ├── github_operations.py
    └── models.py
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
uvicorn main:app --reload
```

3. Open your browser and visit `http://localhost:8000`

## Deployment

This app is configured for deployment on Railway. Simply connect your repository to Railway and it will automatically build and deploy the application.

## Project Structure

```
.
├── main.py           # FastAPI application
├── requirements.txt  # Python dependencies
├── railway.toml      # Railway configuration
└── README.md         # This file
``` 