from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import yaml
from pathlib import Path

app = FastAPI()

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

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

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>SDK Setup</title>
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
                .form-group {
                    margin-bottom: 1rem;
                    text-align: left;
                }
                label {
                    display: block;
                    margin-bottom: 0.5rem;
                    color: #555;
                }
                input[type="text"],
                input[type="file"] {
                    width: 100%;
                    padding: 0.5rem;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    padding: 0.5rem 1rem;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 1rem;
                    margin-top: 1rem;
                }
                button:hover {
                    background-color: #45a049;
                }
                .error {
                    color: red;
                    margin-top: 1rem;
                }
                .success {
                    color: green;
                    margin-top: 1rem;
                }
                .file-info {
                    font-size: 0.9rem;
                    color: #666;
                    margin-top: 0.5rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
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

@app.post("/submit")
async def handle_submission(
    company_name: str = Form(...),
    openapi_spec: UploadFile = File(...)
):
    try:
        # Get file extension
        file_extension = Path(openapi_spec.filename).suffix.lower()
        if file_extension not in ['.json', '.yaml', '.yml']:
            raise ValueError("Unsupported file type. Please upload a JSON or YAML file.")

        # Read and validate the file
        content = await openapi_spec.read()
        spec_data = validate_openapi(content, file_extension)

        # Save the file with appropriate extension
        file_path = f"uploads/{company_name}_openapi{file_extension}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        return HTMLResponse(f"""
            <div class="container">
                <h1>Success!</h1>
                <p class="success">Received submission for {company_name}</p>
                <p>OpenAPI spec saved successfully as {file_extension.upper()}.</p>
                <a href="/">Submit another</a>
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
                <p class="error">An error occurred: {str(e)}</p>
                <a href="/">Try again</a>
            </div>
        """) 