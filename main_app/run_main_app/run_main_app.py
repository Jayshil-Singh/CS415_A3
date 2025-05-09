from flask import Flask, render_template, url_for

# tell Flask where to find your templates & static assets:
app = Flask(
    __name__,
    template_folder="main_app_packages/templates",
    static_folder="main_app_packages/static"
)

@app.route("/")
def home():
    # this will load templates/homepage.html and pull in your header/footer
    return render_template("homepage.html")

if __name__ == "__main__":
    # start the dev server on port 5000
    app.run(debug=True)
