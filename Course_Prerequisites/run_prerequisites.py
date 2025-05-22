
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, redirect
from Course_Prerequisites.App.prereq import prereq_bp

app = Flask(__name__)
app.register_blueprint(prereq_bp, url_prefix='/prerequisites')

@app.route('/')
def root_redirect():
    return redirect("/prerequisites")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006)
