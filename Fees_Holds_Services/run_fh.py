from flask import Flask
from f_h_services.routes import fnh_bp

app = Flask(__name__)
app.register_blueprint(fnh_bp)

if __name__ == '__main__':
    app.run(debug=True)