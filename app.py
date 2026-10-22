import os
from pathlib import Path

from flask import Flask, abort, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_site(path):
    # Serve the landing page at the root.
    if not path:
        index_file = BASE_DIR / "index.html"
        if index_file.is_file():
            return send_from_directory(BASE_DIR, "index.html")
        abort(404, description="index.html non trovato nella cartella del progetto.")

    # Serve files and folders (e.g. logo.svg, rana_walk/, rana_hi/).
    requested_file = (BASE_DIR / path).resolve()

    # Prevent paths from escaping the project directory.
    if BASE_DIR not in requested_file.parents and requested_file != BASE_DIR:
        abort(404)

    if requested_file.is_file():
        return send_from_directory(requested_file.parent, requested_file.name)

    abort(404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
