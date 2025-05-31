# test_login.py
import requests
import json

# Update BASE_URL to point to your Flask microservice's authentication path
# This should match your run_es.py's blueprint prefix + /auth
BASE_URL = 'http://127.0.0.1:5004/enrollment_services/auth' # Changed port and added blueprint prefix

def test_login():
    # Test login with student credentials
    login_data = {
        'username': 'student1',
        'password': 'student123'
    }

    response = requests.post(f'{BASE_URL}/login', json=login_data)
    print("\nStudent Login Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        token = response.json()['token']

        # Test token verification
        headers = {'Authorization': f'Bearer {token}'}
        verify_response = requests.get(f'{BASE_URL}/verify_token', headers=headers) # Corrected endpoint name
        print("\nToken Verification Response:")
        print(f"Status Code: {verify_response.status_code}")
        print(f"Response: {json.dumps(verify_response.json(), indent=2)}")

        # Test accessing a protected endpoint (e.g., get_programs)
        # You'll need to run this AFTER you've applied @token_required to get_programs in routes.py
        protected_url = 'http://127.0.0.1:5004/enrollment_services/programs'
        protected_response = requests.get(protected_url, headers=headers)
        print("\nProtected Programs Endpoint Response:")
        print(f"Status Code: {protected_response.status_code}")
        print(f"Response: {json.dumps(protected_response.json(), indent=2)}")


if __name__ == '__main__':
    test_login()