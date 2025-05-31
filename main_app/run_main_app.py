import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_app.main_app_packages import create_app

app = create_app()

if __name__ == '__main__':
    # Debug will be set from Config, but port can be overridden here if needed
    port = int(os.environ.get("MAIN_APP_PORT", 5000)) # Default to 5000 if not set
    app.run(host='127.0.0.1', port=port)