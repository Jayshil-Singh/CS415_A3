from f_h_services import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("FEES_HOLDS_SERVICE_PORT", 5004))
    app.run(host='127.0.0.1', port=port)