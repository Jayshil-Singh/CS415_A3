import os
import secrets
from dotenv import find_dotenv, set_key

def generate_api_key(length=32):
    """Generates a secure hexadecimal API key."""
    return secrets.token_hex(length)

def store_api_key_in_env(api_key, key_name="APP_API_KEY"):
    """Stores the API key in the .env file in the project root."""
    # Attempt to find an existing .env file in the project root or create one.
    # This assumes API_KEY_GEN.py is two levels down from the project root (e.g., project_root/main_app/API_KEY_GEN.py)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, ".env")

    # Create .env if it doesn't exist
    if not os.path.exists(dotenv_path):
        with open(dotenv_path, "w") as f:
            pass # Create an empty .env file

    set_key(dotenv_path, key_name, api_key)
    print(f"API Key '{key_name}' stored/updated in {dotenv_path}")

if __name__ == "__main__":
    new_api_key = generate_api_key()
    store_api_key_in_env(new_api_key)
    print(f"Generated API Key: {new_api_key}")