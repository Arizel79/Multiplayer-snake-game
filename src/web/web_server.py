from flask import Flask, send_from_directory

app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory("www", "game.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("www", filename)


def main():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
