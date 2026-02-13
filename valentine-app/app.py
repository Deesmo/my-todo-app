from flask import Flask, render_template, send_from_directory

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/static/photos/<path:filename>")
def photos(filename):
    return send_from_directory("static/photos", filename)


@app.route("/static/music/<path:filename>")
def music(filename):
    return send_from_directory("static/music", filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
