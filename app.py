import os
from pathlib import Path

from flask import Flask, abort, send_from_directory
from pathlib import Path
from PIL import Image


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

def crea_gif(cartella, prefisso, numero_frame, output, durata=83, salto=2, scala=0.5):
    frames = []

    for i in range(1, numero_frame + 1, salto):
        nome = f"{prefisso}{i:08d}.png"
        percorso = Path(cartella) / nome

        img = Image.open(percorso).convert("RGBA")
        dimensioni = (
            max(1, int(img.width * scala)),
            max(1, int(img.height * scala))
        )
        img = img.resize(dimensioni, Image.Resampling.LANCZOS)

        # GIF usa trasparenza a 1 bit: convertiamo in palette indicizzata.
        rgba = img.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
        frames.append(rgba)

    if not frames:
        raise ValueError(f"Nessun frame trovato in {cartella}")

    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=durata,
        loop=0 if "walk" in output.lower() else 1,
        optimize=True,
        disposal=2
    )

crea_gif("rana_walk", "WALK", 42, "rana_walk.gif")
crea_gif("rana_hi", "HI", 73, "rana_hi.gif")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
