import requests
import json

BASE_URL = 'http://127.0.0.1:5002/auth'

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
        verify_response = requests.get(f'{BASE_URL}/verify', headers=headers)
        print("\nToken Verification Response:")
        print(f"Status Code: {verify_response.status_code}")
        print(f"Response: {json.dumps(verify_response.json(), indent=2)}")

if __name__ == '__main__':
    test_login() 