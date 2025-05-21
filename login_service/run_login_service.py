from login_service_packages import create_app
import os

app = create_app()
 
if __name__ == '__main__':
    port = int(os.environ.get("LOGIN_SERVICE_PORT", 5002))  # Default to 5002
    app.run(host='127.0.0.1', port=port) 