import json
import yaml
from pathlib import Path

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

def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower()

def is_valid_github_username(username: str) -> bool:
    """Validate GitHub username format."""
    import re
    github_username_regex = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$')
    return github_username_regex.match(username) is not None 