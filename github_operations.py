import json
import random
import asyncio
from typing import List, Tuple
from fastapi import HTTPException
from github import Github
from github.GithubException import GithubException
from config import TEMPLATE_OWNER, TEMPLATE_REPO
from models import RepositoryInfo, RepoAccessResult

async def create_repo_from_template(access_token: str, company_name: str, spec_file_name: str, spec_content: str) -> tuple[str, Github, str, str]:
    """Create a new repository from the template and delete existing spec."""
    try:
        g = Github(access_token)
        auth_user = g.get_user()
        print(f"Authenticated as user: {auth_user.login}")
        
        # Get the template repository
        template_repo = g.get_repo(f"{TEMPLATE_OWNER}/{TEMPLATE_REPO}")
        print(f"Template repo: {template_repo.full_name}, Is template: {template_repo.is_template}")
        
        # Create a new repository from the template
        repo_name = f"{company_name}-config"
        repo_description = f"SDK configuration for {company_name}"
        
        try:
            # Create repository from template using the correct method
            new_repo = auth_user.create_repo_from_template(
                name=repo_name,
                description=repo_description,
                private=True,
                repo=template_repo
            )

            async def verify_file_deleted(repo, file_path: str, max_retries: int = 3) -> bool:
                """Verify a file is deleted with retries."""
                for i in range(max_retries):
                    try:
                        repo.get_contents(file_path)
                        if i < max_retries - 1:  # Don't sleep on last attempt
                            await asyncio.sleep(1)  # Wait a second before retrying
                        continue  # File still exists
                    except GithubException as e:
                        if e.status == 404:  # File is gone
                            return True
                        raise  # Other error
                return False  # File still exists after all retries

            # Try to delete the existing OpenAPI spec file (trying both .yaml and .yml extensions)
            deleted = False
            max_retries = 3
            
            async def find_spec_file(repo, file_path: str) -> tuple[bool, any]:
                """Try to find a file with retries."""
                for attempt in range(max_retries):
                    try:
                        print(f"Attempt {attempt + 1}/{max_retries} to find {file_path}")
                        contents = repo.get_contents(file_path)
                        return True, contents
                    except GithubException as e:
                        if e.status != 404:  # Only retry on 404
                            raise
                        if attempt < max_retries - 1:
                            print(f"File not found, waiting before retry...")
                            await asyncio.sleep(2)  # Wait 2 seconds between attempts
                return False, None

            for file_path in ["fern/openapi.yaml", "fern/openapi.yml"]:
                try:
                    found, contents = await find_spec_file(new_repo, file_path)
                    if not found:
                        print(f"File {file_path} not found after {max_retries} attempts")
                        continue

                    # Handle if contents is a list (directory)
                    if isinstance(contents, list):
                        print(f"Warning: {file_path} is a directory containing {len(contents)} items")
                        continue
                        
                    print(f"Found file {file_path} with SHA: {contents.sha}")
                    
                    print(f"Attempting to delete {file_path}")
                    new_repo.delete_file(
                        path=contents.path,
                        message="Remove default OpenAPI spec",
                        sha=contents.sha
                    )
                    print(f"Delete API call completed for {file_path}")
                    
                    # Wait and verify deletion
                    if await verify_file_deleted(new_repo, file_path):
                        print(f"Verified deletion of {file_path}")
                        deleted = True
                        break  # Exit loop after successful deletion and verification
                    else:
                        print(f"Warning: {file_path} deletion could not be verified")
                except GithubException as e:
                    if e.status != 404:  # Only raise if error is not "file not found"
                        print(f"GitHub error for {file_path}: Status {e.status}, Data: {e.data}")
                        raise
                    print(f"Unexpected error for {file_path}")

            if not deleted:
                print("Warning: Could not find original spec file to delete")

            # Add a longer delay before creating the new file
            await asyncio.sleep(5)  # Wait 5 seconds before creating new file

            # Create the new spec file
            try:
                new_repo.create_file(
                    path=f"fern/{spec_file_name}",
                    message="Add OpenAPI specification",
                    content=spec_content,
                )
                print(f"Created new spec file: fern/{spec_file_name}")
            except GithubException as e:
                raise HTTPException(status_code=500, detail=f"Failed to create spec file: {str(e)}")

            # Update generators.yml with correct repository names and spec file
            try:
                generators_yml = new_repo.get_contents("fern/generators.yml")
                current_content = generators_yml.decoded_content.decode('utf-8')
                
                # Replace the commented repository lines with uncommented versions using the company name,
                # update the OpenAPI spec filename, and update package names
                updated_content = current_content.replace(
                    '    - openapi: openapi.yaml',
                    f'    - openapi: {spec_file_name}'
                ).replace(
                    '          # github:\n          #   repository: fern-demo/starter-python-sdk',
                    f'        github:\n          repository: {auth_user.login}/{company_name}-python-sdk'
                ).replace(
                    '          # github:\n          #   repository: fern-demo/starter-typescript-sdk',
                    f'        github:\n          repository: {auth_user.login}/{company_name}-typescript-sdk'
                ).replace(
                    'package-name: startersdk',
                    f'package-name: {company_name.lower()}-sdk'
                ).replace(
                    'pypi-package-name: startersdk',
                    f'pypi-package-name: {company_name.lower()}-sdk'
                ).replace(
                    'npm-package-name: startersdk',
                    f'npm-package-name: {company_name.lower()}-sdk'
                )
                
                new_repo.update_file(
                    path="fern/generators.yml",
                    message="Update SDK repository names and spec filename",
                    content=updated_content,
                    sha=generators_yml.sha
                )
                print("Updated generators.yml with SDK repository names and spec filename")

                # Update fern.config.json with the company name
                try:
                    fern_config = new_repo.get_contents("fern/fern.config.json")
                    config_content = json.loads(fern_config.decoded_content.decode('utf-8'))
                    
                    # Update the organization name - remove spaces and special characters, convert to lowercase
                    # and add random 6 digits at the end
                    base_name = ''.join(c.lower() for c in company_name if c.isalnum())
                    random_digits = str(random.randint(100000, 999999))
                    org_name = f"{base_name}{random_digits}"
                    config_content['organization'] = org_name
                    
                    # Convert back to JSON string with proper formatting
                    updated_config = json.dumps(config_content, indent=2)
                    
                    new_repo.update_file(
                        path="fern/fern.config.json",
                        message="Update organization name in fern.config.json",
                        content=updated_config,
                        sha=fern_config.sha
                    )
                    print(f"Updated fern.config.json with organization name: {org_name}")
                except GithubException as e:
                    print(f"Warning: Failed to update fern.config.json: {str(e)}")
                    # Don't raise an exception here as the main functionality succeeded

            except GithubException as e:
                print(f"Warning: Failed to update generators.yml: {str(e)}")
                # Don't raise an exception here as the main functionality succeeded

            # Create SDK repositories and install Fern API app
            try:
                # Create Python SDK repository
                python_repo_name = f"{company_name}-python-sdk"
                print(f"Creating Python SDK repository: {python_repo_name}")
                python_repo = auth_user.create_repo(
                    name=python_repo_name,
                    description=f"Python SDK for {company_name} API",
                    private=True,
                    auto_init=True  # Initialize with README
                )
                print(f"Created Python SDK repository: {python_repo_name}")

                # Create TypeScript SDK repository
                typescript_repo_name = f"{company_name}-typescript-sdk"
                print(f"Creating TypeScript SDK repository: {typescript_repo_name}")
                typescript_repo = auth_user.create_repo(
                    name=typescript_repo_name,
                    description=f"TypeScript SDK for {company_name} API",
                    private=True,
                    auto_init=True  # Initialize with README
                )
                print(f"Created TypeScript SDK repository: {typescript_repo_name}")

                # Install Fern API app in all repositories
                fern_app_url = "https://github.com/apps/fern-api/installations/new"
                repos_to_install = [
                    new_repo.full_name,  # Config repo
                    f"{auth_user.login}/{python_repo_name}",  # Python SDK repo
                    f"{auth_user.login}/{typescript_repo_name}"  # TypeScript SDK repo
                ]
                
                installation_url = f"{fern_app_url}?repository_ids={','.join([str(repo.id) for repo in [new_repo, python_repo, typescript_repo]])}"
                print(f"Installing Fern API app in repositories...")
                
                # Return the installation URL to the user
                return new_repo.html_url, g, new_repo.full_name, installation_url

            except GithubException as e:
                print(f"Warning: Failed to create SDK repositories: {str(e)}")
                # Don't raise an exception as the main config repo was created successfully
                return new_repo.html_url, g, new_repo.full_name, None
            
        except GithubException as e:
            print(f"Detailed GitHub error: Status {e.status}, Data: {e.data}")
            raise
            
    except GithubException as e:
        if e.status == 422:  # Repository already exists
            raise ValueError(f"A repository named '{repo_name}' already exists.")
        elif e.status == 403:  # Permission denied
            raise ValueError(f"Permission denied. GitHub says: {e.data.get('message', 'No message provided')}")
        elif e.status == 404:  # Template not found
            raise ValueError("Template repository not found. Please check the template exists and you have access to it.")
        raise ValueError(f"GitHub API error ({e.status}): {e.data.get('message', str(e))}")
    except Exception as e:
        raise ValueError(f"Failed to create repository: {str(e)}")

async def get_user_repositories(access_token: str) -> List[RepositoryInfo]:
    """Get user's repositories where they have admin access."""
    try:
        g = Github(access_token)
        auth_user = g.get_user()
        
        repositories = []
        for repo in auth_user.get_repos():
            try:
                # Check if user has admin permissions
                if repo.permissions and repo.permissions.admin:
                    repositories.append(RepositoryInfo(
                        id=repo.id,
                        name=repo.name,
                        full_name=repo.full_name,
                        description=repo.description,
                        private=repo.private,
                        permissions={
                            'admin': repo.permissions.admin,
                            'maintain': repo.permissions.maintain if hasattr(repo.permissions, 'maintain') else False,
                            'push': repo.permissions.push,
                            'pull': repo.permissions.pull
                        }
                    ))
            except Exception as repo_error:
                print(f"Error processing repo {repo.name}: {str(repo_error)}")
                continue
        
        return repositories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")

async def add_users_to_repositories(access_token: str, repositories: List[str], usernames: List[str]) -> List[RepoAccessResult]:
    """Add users to repositories with maintain permissions."""
    g = Github(access_token)
    results = []
    
    for repo_name in repositories:
        repo = g.get_repo(repo_name)
        for username in usernames:
            try:
                repo.add_to_collaborators(username, permission='maintain')
                results.append(RepoAccessResult(
                    repository=repo_name,
                    username=username,
                    success=True,
                    message='Successfully added as maintainer'
                ))
            except Exception as e:
                results.append(RepoAccessResult(
                    repository=repo_name,
                    username=username,
                    success=False,
                    message=str(e)
                ))
    
    return results 