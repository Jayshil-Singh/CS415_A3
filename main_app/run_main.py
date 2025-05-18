import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import requests # For making HTTP requests to microservices

# Load environment variables from .env file in the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Up two levels
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

app = Flask(__name__)

# Retrieve the API key and service URLs
API_KEY = os.getenv("APP_API_KEY")
LOGIN_SERVICE_URL = os.getenv("LOGIN_SERVICE_URL", "http://localhost:5001") # Example default
# Define other service URLs similarly, reading from .env or using defaults
# PROFILE_SERVICE_URL = os.getenv("PROFILE_SERVICE_URL", "http://localhost:5002")

if not API_KEY:
    raise RuntimeError("APP_API_KEY not found in environment. Please run API_KEY_GEN.py")

@app.route('/')
def index():
    return "Main App is Running. API Key Loaded."

@app.route('/login', methods=['POST'])
def handle_login():
    # This endpoint in the main app would receive login credentials
    # from the user's browser.
    # Then, it calls the actual login microservice.
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        headers = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}
        # Assuming your login service has an endpoint like /auth
        response = requests.post(f"{LOGIN_SERVICE_URL}/auth", json={"username": username, "password": password}, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        # If the request was successful, return the JSON response from the login service
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as http_err:
        # Specific handling for HTTP errors (4xx, 5xx)
        # Try to return the error message from the microservice if available
        try:
            error_details = response.json()
        except ValueError: # If the error response is not JSON
            error_details = response.text
        return jsonify({"error": "HTTP error from login service", "details": error_details}), response.status_code
    except requests.exceptions.ConnectionError as conn_err:
        # Specific handling for connection errors (e.g., service is down)
        return jsonify({"error": "Failed to connect to login service", "details": str(conn_err)}), 503 # Service Unavailable
    except requests.exceptions.Timeout as timeout_err:
        # Specific handling for timeout errors
        return jsonify({"error": "Login service request timed out", "details": str(timeout_err)}), 504 # Gateway Timeout
    except requests.exceptions.RequestException as req_err:
        # Catch any other request-related errors
        return jsonify({"error": "Error during request to login service", "details": str(req_err)}), 500
    except Exception as e:
        # Catch any other unexpected errors within the try block
        return jsonify({"error": "An unexpected error occurred in main app", "details": str(e)}), 500

# Example: How main_app might call another service (e.g., profile_service)
# @app.route('/get_profile/<user_id>')
# def get_user_profile(user_id):
#     try:
#         headers = {'X-API-Key': API_KEY}
#         # Make sure PROFILE_SERVICE_URL is defined above like LOGIN_SERVICE_URL
#         # response = requests.get(f"{PROFILE_SERVICE_URL}/profile/{user_id}", headers=headers)
#         response.raise_for_status()
#         return jsonify(response.json()), response.status_code
#     except requests.exceptions.RequestException as e:
#         return jsonify({"error": "Failed to connect to profile service", "details": str(e)}), 503


if __name__ == '__main__':
    # For development, you might need to start your microservices separately.
    # In production, you'd use something like Docker Compose or Kubernetes.
    print(f"Main app starting. Loaded API Key: {API_KEY[:5] if API_KEY else 'NOT_FOUND'}... (truncated)")
    app.run(port=5000, debug=True)