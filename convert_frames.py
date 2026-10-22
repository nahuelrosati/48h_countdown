#!/usr/bin/env python3
"""Convert rana_walk/ and rana_hi/ PNG frames into prebuilt animated WebP files.
Run locally before pushing/deploying: python convert_frames.py
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
STATIC.mkdir(exist_ok=True)

FPS = 12
FRAME_DURATION_MS = round(1000 / FPS)
FRAME_STEP = 2       # use every other source frame
SCALE = 0.5          # half width and height
QUALITY = 75
METHOD = 4


def convert(folder_name: str, prefix: str, frame_count: int, output_name: str, loop: int):
    source_dir = ROOT / folder_name
    output_path = STATIC / output_name
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Cartella non trovata: {source_dir}")

    frames = []
    missing = []
    for number in range(1, frame_count + 1, FRAME_STEP):
        path = source_dir / f"{prefix}{number:08d}.png"
        if not path.is_file():
            missing.append(path.name)
            continue
        with Image.open(path) as source:
            frame = source.convert("RGBA")
            size = (max(1, round(frame.width * SCALE)), max(1, round(frame.height * SCALE)))
            frame = frame.resize(size, Image.Resampling.LANCZOS)
            frames.append(frame)

    if not frames:
        raise RuntimeError(f"Nessun frame trovato in {source_dir}; controlla nomi ed estensioni PNG.")
    if missing:
        print(f"Nota: {len(missing)} frame mancanti in {folder_name}; verranno saltati.")

    try:
        frames[0].save(
            output_path,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=FRAME_DURATION_MS,
            loop=loop,
            quality=QUALITY,
            method=METHOD,
            lossless=False,
            exact=True,
            minimize_size=True,
        )
    finally:
        for frame in frames:
            frame.close()

    print(f"Creato: {output_path.relative_to(ROOT)} ({output_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    convert("rana_walk", "WALK", 42, "rana_walk.webp", loop=0)
    convert("rana_hi", "HI", 73, "rana_hi.webp", loop=1)
    print("Conversione completata. Inserisci static/rana_walk.webp e static/rana_hi.webp nel repository.")
