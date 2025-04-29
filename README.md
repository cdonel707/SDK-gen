# Simple Hello World Web App

A minimal web application that displays "Hello World" using FastAPI.

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