from fastapi.responses import HTMLResponse

def get_login_template() -> str:
    """Get the login page HTML template."""
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

def get_success_template(company_name: str, repo_url: str, user_login: str, installation_url: str) -> str:
    """Get the success page HTML template after SDK creation."""
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>SDK Setup - Success</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                /* Success page styles would go here - truncated for brevity */
                body {{ font-family: 'Inter', sans-serif; }}
                .container {{ max-width: 720px; margin: 0 auto; padding: 2rem; }}
                .success-icon {{ color: green; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1><span class="success-icon">✓</span> Setup Complete</h1>
                <p>Successfully set up SDK configuration for {company_name}</p>
                
                <ul>
                    <li>Configuration: <a href="{repo_url}">{repo_url}</a></li>
                    <li>Python SDK: <a href="https://github.com/{user_login}/{company_name}-python-sdk">Python SDK</a></li>
                    <li>TypeScript SDK: <a href="https://github.com/{user_login}/{company_name}-typescript-sdk">TypeScript SDK</a></li>
                </ul>
                
                <a href="{installation_url}" target="_blank">
                    <button>Install Fern API</button>
                </a>
                
                <a href="/">← Create Another SDK</a>
            </div>
        </body>
    </html>
    """

def get_main_template(user_login: str, avatar_url: str) -> str:
    """Get the main application page template with form and repository management."""
    # This would contain the full HTML template from the original file
    # For brevity, returning a simplified version here
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>SDK Setup</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                /* All the CSS styles from the original file would go here */
                body {{ font-family: 'Inter', sans-serif; }}
                .container {{ max-width: 640px; margin: 0 auto; padding: 2rem; }}
                .user-info {{ display: flex; align-items: center; justify-content: flex-end; }}
                .user-avatar {{ width: 32px; height: 32px; border-radius: 50%; }}
                /* ... rest of CSS ... */
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
                        <input type="text" id="company_name" name="company_name" required>
                    </div>
                    <div class="form-group">
                        <label for="openapi_spec">OpenAPI Specification</label>
                        <input type="file" id="openapi_spec" name="openapi_spec" accept=".json,.yaml,.yml" required>
                    </div>
                    <button type="submit">Generate SDK</button>
                </form>
                
                <!-- Repository Access Management Section -->
                <div>
                    <h1>Repository Access Management</h1>
                    <!-- Form and JavaScript would go here -->
                </div>
            </div>
            
            <script>
                /* All JavaScript from the original file would go here */
            </script>
        </body>
    </html>
    """ 