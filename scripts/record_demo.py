"""Render a demo GIF without opening a window.

    python scripts/record_demo.py docs/demo.gif

Requires Pillow (`pip install pillow`).
"""

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from pathfinder.app import App  # noqa: E402
from pathfinder.maze import generate_maze  # noqa: E402


def capture(app: App, scale: float) -> Image.Image:
    raw = pygame.image.tobytes(app.screen, "RGB")
    image = Image.frombytes("RGB", app.screen.get_size(), raw)
    size = (int(image.width * scale), int(image.height * scale))
    return image.resize(size, Image.LANCZOS)


def record(app: App, algorithm: str, steps_per_frame: int, frames: list, scale: float) -> None:
    app.algorithm = algorithm
    app.start_search()
    tick = 0
    while not app.finished or app.path_shown < len(app.step.path):
        app.advance(steps_per_frame)
        if app.finished and app.path_shown < len(app.step.path):
            app.path_shown = min(app.path_shown + 3, len(app.step.path))
        app.draw()
        tick += 1
        if tick % 2 == 0:
            frames.append(capture(app, scale))
    app.draw()
    frames.extend([capture(app, scale)] * 15)  # hold the result


def main(out: str) -> None:
    app = App()
    generate_maze(app.grid, random.Random(7))
    frames: list[Image.Image] = []
    scale = 0.55
    record(app, "Dijkstra", 10, frames, scale)
    record(app, "A*", 4, frames, scale)

    # One shared palette (no dithering) lets the GIF encoder store only the
    # pixels that change between frames, which keeps the file small.
    sample = Image.new("RGB", (frames[0].width, frames[0].height * 2))
    sample.paste(frames[len(frames) // 3], (0, 0))
    sample.paste(frames[-1], (0, frames[0].height))
    palette = sample.quantize(colors=96, method=Image.MAXCOVERAGE)
    palette_frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    palette_frames[0].save(out, save_all=True, append_images=palette_frames[1:], duration=60, loop=0, optimize=True)
    print(f"{len(frames)} frames -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/demo.gif")
