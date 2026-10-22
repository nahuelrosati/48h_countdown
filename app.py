
import os
import logging
from pathlib import Path

from flask import Flask, send_from_directory, abort
from PIL import Image

# --------------------------------------------------
# CONFIGURAZIONE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

WALK_DIR = BASE_DIR / "rana_walk"
HI_DIR = BASE_DIR / "rana_hi"

WALK_OUTPUT = STATIC_DIR / "rana_walk.webp"
HI_OUTPUT = STATIC_DIR / "rana_hi.webp"

FPS = 12
DURATION_MS = round(1000 / FPS)
FRAME_STEP = 2
SCALE = 0.5

# Qualità WebP: valore inferiore = file più leggero.
WEBP_QUALITY = 75

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(STATIC_DIR))


# --------------------------------------------------
# GENERAZIONE WEBP ANIMATO
# --------------------------------------------------

def crea_webp(cartella, prefisso, numero_frame, output, loop=0):
    """
    Converte i frame PNG in WebP animato.
    Salta un frame ogni due e riduce le dimensioni al 50%.
    Genera il file soltanto se non esiste già.
    """

    if output.exists() and output.stat().st_size > 0:
        logger.info("WebP già presente: %s", output.name)
        return True

    if not cartella.is_dir():
        logger.warning("Cartella non trovata: %s", cartella)
        return False

    frames = []

    try:
        for i in range(1, numero_frame + 1, FRAME_STEP):
            nome_file = f"{prefisso}{i:08d}.png"
            percorso = cartella / nome_file

            if not percorso.is_file():
                logger.warning("Frame mancante: %s", percorso)
                continue

            with Image.open(percorso) as sorgente:
                frame = sorgente.convert("RGBA")

                nuova_larghezza = max(1, round(frame.width * SCALE))
                nuova_altezza = max(1, round(frame.height * SCALE))

                frame = frame.resize(
                    (nuova_larghezza, nuova_altezza),
                    Image.Resampling.LANCZOS
                )

                # Copia indipendente prima di chiudere il file sorgente.
                frames.append(frame.copy())

        if not frames:
            logger.error("Nessun frame valido in %s", cartella)
            return False

        logger.info(
            "Creo %s con %s frame ridotti...",
            output.name,
            len(frames)
        )

        frames[0].save(
            output,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=DURATION_MS,
            loop=loop,
            quality=WEBP_QUALITY,
            method=4,
            lossless=False,
            exact=True
        )

        logger.info(
            "Creato %s (%.2f MB)",
            output.name,
            output.stat().st_size / (1024 * 1024)
        )

        return True

    except Exception:
        logger.exception("Errore durante la creazione di %s", output.name)

        # Elimina un eventuale file incompleto.
        if output.exists():
            output.unlink()

        return False

    finally:
        for frame in frames:
            frame.close()


def prepara_animazioni():
    """Crea le animazioni mancanti all'avvio dell'app."""

    forza = os.getenv("FORCE_REBUILD_WEBP", "0") == "1"

    if forza:
        for file in (WALK_OUTPUT, HI_OUTPUT):
            if file.exists():
                file.unlink()

    # Camminata: 42 frame originali, uno ogni due.
    crea_webp(
        cartella=WALK_DIR,
        prefisso="WALK",
        numero_frame=42,
        output=WALK_OUTPUT,
        loop=0
    )

    # Saluto: 73 frame originali, uno ogni due.
    crea_webp(
        cartella=HI_DIR,
        prefisso="HI",
        numero_frame=73,
        output=HI_OUTPUT,
        loop=1
    )


# --------------------------------------------------
# PREPARAZIONE ANIMAZIONI
# --------------------------------------------------

prepara_animazioni()


# --------------------------------------------------
# ROUTE FLASK
# --------------------------------------------------

@app.route("/")
def home():
    if not (STATIC_DIR / "index.html").is_file():
        abort(404, description="static/index.html non trovato")

    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    file_path = (STATIC_DIR / filename).resolve()

    if not file_path.is_relative_to(STATIC_DIR.resolve()):
        abort(404)

    if not file_path.is_file():
        abort(404)

    return send_from_directory(STATIC_DIR, filename)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )
