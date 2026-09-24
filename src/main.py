"""Command-line entry point for Meong Meong!."""

import os
import sys


if "--smoke-test" in sys.argv:
    # Headless mode verifies initialization and drawing without opening a
    # visible window. Normal launches do not set these variables.
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.game import Game


def main() -> int:
    pygame.mixer.pre_init(44_100, -16, 1, 512)
    pygame.init()
    try:
        game = Game()
        try:
            game.run(max_frames=5 if "--smoke-test" in sys.argv else None)
        except KeyboardInterrupt:
            # Closing a development run with Ctrl+C should not print a crash traceback.
            pass
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
