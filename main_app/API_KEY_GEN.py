import secrets
api_key = secrets.token_hex(32)
print(f"Generated API Key: {api_key}")