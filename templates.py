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
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>SDK Setup</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    min-height: 100vh;
                    background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%);
                    color: #1f2937;
                    line-height: 1.5;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 2rem;
                }}

                .container {{
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                    width: 100%;
                    max-width: 640px;
                    padding: 2.5rem;
                    transition: transform 0.2s ease;
                }}

                .container:hover {{
                    transform: translateY(-2px);
                }}

                h1 {{
                    font-size: 2rem;
                    font-weight: 600;
                    color: #111827;
                    margin-bottom: 2rem;
                    text-align: center;
                }}

                .form-group {{
                    margin-bottom: 1.5rem;
                }}

                label {{
                    display: block;
                    font-weight: 500;
                    margin-bottom: 0.5rem;
                    color: #374151;
                    font-size: 0.95rem;
                }}

                input[type="text"] {{
                    width: 100%;
                    padding: 0.75rem 1rem;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    font-size: 1rem;
                    transition: all 0.2s ease;
                    background: #f9fafb;
                }}

                input[type="text"]:focus {{
                    outline: none;
                    border-color: #2563eb;
                    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                    background: white;
                }}

                input[type="file"] {{
                    width: 100%;
                    padding: 0.75rem;
                    border: 2px dashed #d1d5db;
                    border-radius: 8px;
                    font-size: 0.95rem;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }}

                input[type="file"]:hover {{
                    border-color: #2563eb;
                    background: rgba(37, 99, 235, 0.05);
                }}

                textarea {{
                    width: 100%;
                    padding: 0.75rem 1rem;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    font-size: 1rem;
                    transition: all 0.2s ease;
                    background: #f9fafb;
                    min-height: 100px;
                    resize: vertical;
                    font-family: inherit;
                }}

                textarea:focus {{
                    outline: none;
                    border-color: #2563eb;
                    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                    background: white;
                }}

                .file-info {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    margin-top: 0.5rem;
                    padding-left: 0.5rem;
                }}

                button {{
                    width: 100%;
                    padding: 0.875rem 1.5rem;
                    background: #2563eb;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    margin-top: 1rem;
                }}

                button:hover {{
                    background: #1d4ed8;
                    transform: translateY(-1px);
                }}

                button:active {{
                    transform: translateY(0);
                }}

                #repository_dropdown {{
                    display: none;
                    position: absolute;
                    z-index: 1000;
                    width: 100%;
                    max-height: 200px;
                    overflow-y: auto;
                    background: white;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}

                .repo-item {{
                    padding: 0.75rem;
                    cursor: pointer;
                    border-bottom: 1px solid #f3f4f6;
                }}

                .repo-item:hover {{
                    background: #f9fafb;
                }}

                .repo-tag {{
                    background: #dbeafe;
                    color: #1e40af;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                    font-size: 0.875rem;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin: 0.25rem;
                }}

                .repo-tag button {{
                    background: none;
                    border: none;
                    color: #1e40af;
                    cursor: pointer;
                    padding: 0;
                    font-size: 1rem;
                    width: auto;
                    margin: 0;
                }}

                .user-info {{
                    display: flex;
                    align-items: center;
                    justify-content: flex-end;
                    margin-bottom: 2rem;
                    padding-bottom: 1rem;
                    border-bottom: 1px solid #e5e7eb;
                }}

                .user-info a {{
                    color: #4b5563;
                    text-decoration: none;
                    font-size: 0.95rem;
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    transition: all 0.2s ease;
                    margin-left: 1rem;
                }}

                .user-info a:hover {{
                    background: #f3f4f6;
                    color: #111827;
                }}

                .user-avatar {{
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    margin-right: 0.75rem;
                }}

                .user-name {{
                    font-weight: 500;
                    color: #374151;
                }}

                .username-input-container {{
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    background: white;
                    min-height: 44px;
                    padding: 0.5rem 0.75rem;
                    cursor: text;
                    transition: all 0.15s ease;
                    font-family: 'Slack-Lato', 'Lato', sans-serif;
                    line-height: 1.5;
                    font-size: 15px;
                    color: #1d1c1d;
                    white-space: nowrap;
                    overflow-x: auto;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                }}

                .username-input-container:focus-within {{
                    border-color: #1264a3;
                    box-shadow: 0 0 0 1px #1264a3;
                }}

                .username-pills-container {{
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                    flex-shrink: 0;
                }}

                .username-input {{
                    border: none;
                    outline: none;
                    background: transparent;
                    flex: 1;
                    min-width: 120px;
                    font-size: 15px;
                    padding: 0;
                    font-family: inherit;
                    color: #1d1c1d;
                }}

                .username-input::placeholder {{
                    color: #616061;
                    font-weight: 400;
                }}

                .username-pill {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                    background: #1264a3;
                    color: white;
                    padding: 0.125rem 0.25rem 0.125rem 0.5rem;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: 700;
                    line-height: 1.2;
                    cursor: default;
                    max-width: 200px;
                    font-family: inherit;
                    margin-right: 0.25rem;
                    vertical-align: middle;
                }}

                .username-pill.email {{
                    background: #e01e5a;
                }}

                .username-pill:hover {{
                    opacity: 0.9;
                }}

                .username-pill .pill-text {{
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 150px;
                }}

                .username-pill .remove-btn {{
                    background: transparent;
                    border: none;
                    border-radius: 2px;
                    width: 16px;
                    height: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    transition: background-color 0.15s ease;
                    margin-left: 0.125rem;
                }}

                .username-pill .remove-btn:hover {{
                    background: rgba(255, 255, 255, 0.2);
                }}

                .username-pill .remove-btn:active {{
                    background: rgba(255, 255, 255, 0.3);
                }}

                @media (max-width: 640px) {{
                    body {{
                        padding: 1rem;
                    }}

                    .container {{
                        padding: 1.5rem;
                    }}

                    h1 {{
                        font-size: 1.75rem;
                    }}
                }}
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
                        <input 
                            type="text" 
                            id="company_name" 
                            name="company_name" 
                            placeholder="Enter your company name"
                            required
                        >
                    </div>
                    <div class="form-group">
                        <label for="openapi_spec">OpenAPI Specification</label>
                        <input 
                            type="file" 
                            id="openapi_spec" 
                            name="openapi_spec" 
                            accept=".json,.yaml,.yml" 
                            required
                        >
                        <div class="file-info">
                            Supported formats: JSON (.json), YAML (.yaml, .yml)
                        </div>
                    </div>
                    <button type="submit">Generate SDK</button>
                </form>
                
                <!-- Repository Access Management Section -->
                <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e5e7eb;">
                    <h1 style="font-size: 1.5rem; margin-bottom: 1.5rem;">Repository Access Management</h1>
                    <form id="accessForm" style="margin-bottom: 2rem;">
                        <div class="form-group">
                            <label for="repository_select">Select Repositories</label>
                            <div style="position: relative;">
                                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                                    <input 
                                        type="text" 
                                        id="repository_search" 
                                        placeholder="Search repositories..."
                                        style="flex: 1; margin-bottom: 0;"
                                    >
                                    <button 
                                        type="button" 
                                        id="refresh_repos" 
                                        onclick="refreshRepositories()"
                                        style="width: auto; padding: 0.75rem; background: #6b7280; margin: 0;"
                                        title="Refresh repositories list"
                                    >
                                        ↻
                                    </button>
                                </div>
                                <div id="repository_dropdown"></div>
                            </div>
                            <div id="selected_repos" style="margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="github_usernames">GitHub Usernames or Emails</label>
                            <div id="username_input_container" class="username-input-container">
                                <div id="username_pills_container" class="username-pills-container"></div>
                                <input 
                                    type="text" 
                                    id="github_usernames" 
                                    name="github_usernames" 
                                    placeholder="Type usernames or emails and press space..."
                                    autocomplete="off"
                                    class="username-input"
                                >
                            </div>
                            <div class="file-info">
                                Type usernames/emails and press space to add them as tags. Users will be added with "Maintain" permissions.
                            </div>
                        </div>
                        <button type="button" onclick="addRepoAccess()" style="background: #059669;">
                            Add Repository Access
                        </button>
                    </form>
                    <div id="accessResults" style="margin-top: 1rem;">
                    </div>
                </div>
            </div>
            
            <script>
            let userRepositories = [];
            let selectedRepositories = [];
            let repositoriesLoaded = false;
            let isLoadingRepositories = false;

            // Initialize everything when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {{
                initializeRepositorySearch();
                initializeUsernameParser();
            }});

            // Also ensure repositories are loaded when page becomes visible
            document.addEventListener('visibilitychange', function() {{
                if (!document.hidden && !repositoriesLoaded && !isLoadingRepositories) {{
                    console.log('Page became visible, loading repositories...');
                    loadUserRepositories();
                }}
            }});

            // Force refresh on window focus as well
            window.addEventListener('focus', function() {{
                if (!repositoriesLoaded && !isLoadingRepositories) {{
                    console.log('Window focused, loading repositories...');
                    loadUserRepositories();
                }}
            }});

            let usernamePills = [];

            function initializeUsernameParser() {{
                const usernameInput = document.getElementById('github_usernames');
                const container = document.getElementById('username_input_container');
                
                if (!usernameInput || !container) return;
                
                // Handle input events
                usernameInput.addEventListener('keydown', handleUsernameKeydown);
                usernameInput.addEventListener('input', handleUsernameInput);
                usernameInput.addEventListener('paste', handleUsernamePaste);
                
                // Make container clickable to focus input
                container.addEventListener('click', function(e) {{
                    if (!e.target.closest('.username-pill')) {{
                        usernameInput.focus();
                    }}
                }});
                
                // Initialize display
                updateInputDisplay();
            }}

            function handleUsernameKeydown(e) {{
                const input = e.target;
                const cursorPos = input.selectionStart;
                const value = input.value;
                
                // Handle space, comma, semicolon, or enter to create pill
                if ((e.key === ' ' || e.key === ',' || e.key === ';' || e.key === 'Enter')) {{
                    const beforeCursor = value.substring(0, cursorPos);
                    const afterCursor = value.substring(cursorPos);
                    
                    // Find the current word being typed
                    const wordStart = Math.max(0, beforeCursor.lastIndexOf(' ') + 1);
                    const currentWord = beforeCursor.substring(wordStart).trim();
                    
                    if (currentWord) {{
                        e.preventDefault();
                        addUsernamePill(currentWord);
                        
                        // Update input value
                        const newValue = value.substring(0, wordStart) + value.substring(cursorPos);
                        input.value = newValue.trim();
                        updateInputDisplay();
                        return;
                    }}
                }}
                
                // Handle backspace to remove last pill when at start or after space
                if (e.key === 'Backspace' && cursorPos === 0 && usernamePills.length > 0) {{
                    e.preventDefault();
                    removeUsernamePill(usernamePills.length - 1);
                    return;
                }}
            }}

            function handleUsernameInput(e) {{
                updateInputDisplay();
            }}

            function handleUsernamePaste(e) {{
                setTimeout(() => {{
                    const input = e.target;
                    const value = input.value;
                    const tokens = value.split(/[\\s,;\\n\\r\\t]+/).filter(t => t.trim());
                    
                    if (tokens.length > 1) {{
                        e.preventDefault();
                        // Add all tokens as pills
                        tokens.forEach(token => {{
                            if (token.trim()) {{
                                addUsernamePill(token.trim());
                            }}
                        }});
                        input.value = '';
                        updateInputDisplay();
                    }}
                }}, 10);
            }}

            function addUsernamePill(input) {{
                const trimmedInput = input.trim();
                if (!trimmedInput) return;
                
                // Extract username from email if it's an email
                let username = trimmedInput;
                let isEmail = false;
                
                if (trimmedInput.includes('@')) {{
                    username = trimmedInput.split('@')[0];
                    isEmail = true;
                }}
                
                // Validate GitHub username
                if (!isValidGitHubUsername(username)) {{
                    console.log('Invalid GitHub username:', username);
                    return;
                }}
                
                // Check for duplicates
                if (usernamePills.some(pill => pill.username.toLowerCase() === username.toLowerCase())) {{
                    console.log('Duplicate username:', username);
                    return;
                }}
                
                // Add to pills array
                const pill = {{
                    original: trimmedInput,
                    username: username,
                    isEmail: isEmail
                }};
                
                usernamePills.push(pill);
                updateInputDisplay();
            }}

            function removeUsernamePill(index) {{
                if (index >= 0 && index < usernamePills.length) {{
                    usernamePills.splice(index, 1);
                    updateInputDisplay();
                }}
            }}

            function updateInputDisplay() {{
                const pillsContainer = document.getElementById('username_pills_container');
                const input = document.getElementById('github_usernames');
                
                if (!pillsContainer || !input) return;
                
                // Clear existing pills
                pillsContainer.innerHTML = '';
                
                // Create and insert pills
                usernamePills.forEach((pill, index) => {{
                    const displayText = pill.isEmail ? `${{pill.username}}` : pill.username;
                    const emailClass = pill.isEmail ? ' email' : '';
                    const tooltip = pill.isEmail ? `Extracted from email: ${{pill.original}}` : `GitHub username: ${{pill.username}}`;
                    
                    const pillElement = document.createElement('span');
                    pillElement.className = `username-pill${{emailClass}}`;
                    pillElement.title = tooltip;
                    pillElement.innerHTML = `
                        <span class="pill-text">${{displayText}}</span>
                        <button class="remove-btn" onclick="removeUsernamePill(${{index}})" type="button">×</button>
                    `;
                    
                    pillsContainer.appendChild(pillElement);
                }});
                
                // Update placeholder
                input.placeholder = usernamePills.length > 0 
                    ? 'Add more users...' 
                    : 'Type usernames or emails and press space...';
            }}

            function isValidGitHubUsername(username) {{
                // GitHub username rules:
                // - May only contain alphanumeric characters or single hyphens
                // - Cannot begin or end with a hyphen
                // - Maximum 39 characters
                const githubUsernameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{{0,37}}[a-zA-Z0-9])?$/;
                return githubUsernameRegex.test(username);
            }}

            function getUsernamesForSubmission() {{
                return usernamePills.map(pill => pill.username);
            }}

            async function initializeRepositorySearch() {{
                const searchInput = document.getElementById('repository_search');
                if (!searchInput) return;
                
                // Set up search input event listener
                searchInput.addEventListener('input', function(e) {{
                    console.log('Search input changed:', e.target.value);
                    handleRepositorySearch(e);
                }});
                
                // Add focus event to load repositories if not already loaded
                searchInput.addEventListener('focus', function() {{
                    console.log('Search input focused, checking repositories...');
                    if (!repositoriesLoaded && !isLoadingRepositories) {{
                        loadUserRepositories();
                    }}
                }});
                
                // Load repositories immediately
                await loadUserRepositories();
            }}

            async function loadUserRepositories(retryCount = 3) {{
                if (isLoadingRepositories) {{
                    console.log('Already loading repositories, skipping...');
                    return;
                }}
                
                isLoadingRepositories = true;
                const searchInput = document.getElementById('repository_search');
                
                // Show loading state
                if (searchInput) {{
                    const originalPlaceholder = searchInput.placeholder;
                    searchInput.placeholder = 'Loading repositories...';
                    searchInput.disabled = true;
                }}
                
                for (let attempt = 1; attempt <= retryCount; attempt++) {{
                    try {{
                        console.log(`Loading repositories... (attempt ${{attempt}}/${{retryCount}})`);
                        const response = await fetch('/api/repositories', {{
                            method: 'GET',
                            headers: {{
                                'Cache-Control': 'no-cache'
                            }}
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP error! status: ${{response.status}}`);
                        }}
                        
                        const repos = await response.json();
                        userRepositories = repos;
                        repositoriesLoaded = true;
                        console.log('Successfully loaded repositories:', repos.length, repos);
                        
                        // Update UI to ready state
                        if (searchInput) {{
                            searchInput.disabled = false;
                            if (repos.length === 0) {{
                                searchInput.placeholder = 'No repositories found with admin access';
                            }} else {{
                                searchInput.placeholder = 'Search repositories...';
                            }}
                        }}
                        
                        isLoadingRepositories = false;
                        return; // Success, exit retry loop
                        
                    }} catch (error) {{
                        console.error(`Failed to load repositories (attempt ${{attempt}}):`, error);
                        
                        if (attempt === retryCount) {{
                            // Final attempt failed
                            if (searchInput) {{
                                searchInput.placeholder = 'Error loading repositories - click to retry';
                                searchInput.disabled = false;
                                searchInput.style.cursor = 'pointer';
                                
                                // Add click handler to retry
                                const retryHandler = function() {{
                                    console.log('Retrying repository load...');
                                    searchInput.removeEventListener('click', retryHandler);
                                    searchInput.style.cursor = '';
                                    repositoriesLoaded = false;
                                    isLoadingRepositories = false;
                                    loadUserRepositories();
                                }};
                                searchInput.addEventListener('click', retryHandler);
                            }}
                        }} else {{
                            // Wait before retry (exponential backoff)
                            await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                        }}
                    }}
                }}
                
                isLoadingRepositories = false;
            }}

            function refreshRepositories() {{
                console.log('Manually refreshing repositories...');
                repositoriesLoaded = false;
                isLoadingRepositories = false;
                userRepositories = [];
                
                // Clear search and dropdown
                const searchInput = document.getElementById('repository_search');
                const dropdown = document.getElementById('repository_dropdown');
                
                if (searchInput) {{
                    searchInput.value = '';
                }}
                if (dropdown) {{
                    dropdown.style.display = 'none';
                }}
                
                // Reload repositories
                loadUserRepositories();
            }}

            function handleRepositorySearch(e) {{
                const searchTerm = e.target.value.toLowerCase();
                const dropdown = document.getElementById('repository_dropdown');
                
                console.log('Searching for:', searchTerm, 'Total repos:', userRepositories.length, 'Loaded:', repositoriesLoaded);
                
                // If repositories aren't loaded yet, try to load them
                if (!repositoriesLoaded && !isLoadingRepositories) {{
                    console.log('Repositories not loaded, loading now...');
                    loadUserRepositories();
                    dropdown.innerHTML = '<div class="repo-item" style="color: #6b7280; font-style: italic;">Loading repositories...</div>';
                    dropdown.style.display = 'block';
                    return;
                }}
                
                if (isLoadingRepositories) {{
                    dropdown.innerHTML = '<div class="repo-item" style="color: #6b7280; font-style: italic;">Loading repositories...</div>';
                    dropdown.style.display = 'block';
                    return;
                }}
                
                if (searchTerm.length === 0) {{
                    dropdown.style.display = 'none';
                    return;
                }}

                const filteredRepos = userRepositories.filter(repo => {{
                    const nameMatch = repo.name.toLowerCase().includes(searchTerm);
                    const notSelected = !selectedRepositories.some(selected => selected.id === repo.id);
                    console.log(`Repo ${{repo.name}}: nameMatch=${{nameMatch}}, notSelected=${{notSelected}}`);
                    return nameMatch && notSelected;
                }});

                console.log('Filtered repos:', filteredRepos.length, filteredRepos);

                if (filteredRepos.length === 0) {{
                    const message = userRepositories.length === 0 
                        ? 'No repositories available' 
                        : 'No matching repositories found';
                    dropdown.innerHTML = `<div class="repo-item" style="color: #6b7280; font-style: italic;">${{message}}</div>`;
                    dropdown.style.display = 'block';
                    return;
                }}

                dropdown.innerHTML = filteredRepos.map(repo => 
                    `<div class="repo-item" onclick="selectRepository(${{repo.id}})" data-repo-id="${{repo.id}}">
                        <strong>${{repo.name}}</strong>
                        <div style="font-size: 0.875rem; color: #6b7280;">${{repo.description || 'No description'}}</div>
                    </div>`
                ).join('');
                
                dropdown.style.display = 'block';
            }}

            function selectRepository(repoId) {{
                console.log('Selecting repository:', repoId);
                const repo = userRepositories.find(r => r.id === repoId);
                if (repo && !selectedRepositories.some(selected => selected.id === repoId)) {{
                    selectedRepositories.push(repo);
                    updateSelectedReposDisplay();
                    document.getElementById('repository_search').value = '';
                    document.getElementById('repository_dropdown').style.display = 'none';
                    console.log('Selected repositories:', selectedRepositories);
                }} else {{
                    console.log('Repository not found or already selected');
                }}
            }}

            function removeRepository(repoId) {{
                console.log('Removing repository:', repoId);
                selectedRepositories = selectedRepositories.filter(repo => repo.id !== repoId);
                updateSelectedReposDisplay();
            }}

            function updateSelectedReposDisplay() {{
                const container = document.getElementById('selected_repos');
                container.innerHTML = selectedRepositories.map(repo => 
                    `<span class="repo-tag">
                        ${{repo.name}}
                        <button onclick="removeRepository(${{repo.id}})" type="button">×</button>
                    </span>`
                ).join('');
                
                console.log('Updated selected repos display:', selectedRepositories.length);
            }}

            document.addEventListener('click', function(e) {{
                if (!e.target.closest('#repository_search') && !e.target.closest('#repository_dropdown')) {{
                    document.getElementById('repository_dropdown').style.display = 'none';
                }}
            }});

            async function addRepoAccess() {{
                const resultsDiv = document.getElementById('accessResults');
                
                if (selectedRepositories.length === 0) {{
                    resultsDiv.innerHTML = '<div style="color: #dc2626; background: #fef2f2; padding: 1rem; border-radius: 8px; border: 1px solid #fecaca;">Please select at least one repository.</div>';
                    return;
                }}
                
                // Get usernames from pills
                const usernames = getUsernamesForSubmission();
                
                if (usernames.length === 0) {{
                    resultsDiv.innerHTML = '<div style="color: #dc2626; background: #fef2f2; padding: 1rem; border-radius: 8px; border: 1px solid #fecaca;">Please add at least one GitHub username or email.</div>';
                    return;
                }}
                
                console.log('Adding repo access:', selectedRepositories.length, 'repos for users:', usernames);

                resultsDiv.innerHTML = '<div style="color: #2563eb; background: #eff6ff; padding: 1rem; border-radius: 8px; border: 1px solid #bfdbfe;">Processing...</div>';

                try {{
                    const response = await fetch('/api/add-repo-access', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            repositories: selectedRepositories.map(repo => repo.full_name),
                            usernames: usernames
                        }})
                    }});

                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}

                    const result = await response.json();
                    displayAccessResults(result);
                }} catch (error) {{
                    console.error('Error adding repo access:', error);
                    resultsDiv.innerHTML = '<div style="color: #dc2626; background: #fef2f2; padding: 1rem; border-radius: 8px; border: 1px solid #fecaca;">An error occurred. Please try again. Check console for details.</div>';
                }}
            }}

            function displayAccessResults(results) {{
                const resultsDiv = document.getElementById('accessResults');
                let html = '<div style="margin-top: 1rem;">';
                
                results.forEach(result => {{
                    const isSuccess = result.success;
                    const bgColor = isSuccess ? '#f0fdf4' : '#fef2f2';
                    const borderColor = isSuccess ? '#86efac' : '#fecaca';
                    const textColor = isSuccess ? '#15803d' : '#dc2626';
                    const icon = isSuccess ? '✓' : '✗';
                    
                    html += `<div style="background: ${{bgColor}}; border: 1px solid ${{borderColor}}; color: ${{textColor}}; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem;">
                        <strong>${{icon}} ${{result.repository}}</strong> - ${{result.username}}: ${{result.message}}
                    </div>`;
                }});
                
                html += '</div>';
                resultsDiv.innerHTML = html;
                
                if (results.some(r => r.success)) {{
                    setTimeout(() => {{
                        // Clear username pills
                        usernamePills = [];
                        document.getElementById('github_usernames').value = '';
                        updateInputDisplay();
                        
                        // Clear selected repositories
                        selectedRepositories = [];
                        updateSelectedReposDisplay();
                    }}, 3000);
                }}
            }}
            </script>
        </body>
    </html>
    """ 