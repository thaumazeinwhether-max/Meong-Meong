r"""Render repeatable review sheets without modifying saved user progress.

Run: .venv\Scripts\python.exe -m tools.preview_animation
Outputs go to data/animation_review (printed on completion).
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import random

from src import config
from src.animation import CharacterAnimator, KURUM_CLIPS
from src.game import Game
from src.models import UserProgress, UserSession


def main():
    output = config.DATA_DIR / "animation_review"
    output.mkdir(parents=True, exist_ok=True)
    pygame.init()
    try:
        game = Game(":memory:")
        game.current_user = UserSession(1, "review", "クルム", UserProgress(True, True, True))
        groups = {
            "gait": [("walk", i) for i in range(4)],
            "rest": [("lie_down", i) for i in range(3)] + [("rest", 0)],
            "jump": [("run", 0), ("jump_rise", 0), ("jump_air", 0), ("land", 0)],
            "front": [("idle", 0), ("blink", 0), ("tail", 1), ("sit", 0)],
        }
        for name, states in groups.items():
            sheet = pygame.Surface((1200, 360))
            sheet.fill((190, 203, 208))
            for i, (state, index) in enumerate(states):
                animator = CharacterAnimator(KURUM_CLIPS, state)
                animator.frame_index = index
                foot = (150 + i * 300, 325)
                pygame.draw.line(sheet, (150, 170, 180), (i * 300, 325), ((i + 1) * 300, 325))
                pygame.draw.line(sheet, (150, 170, 180), (foot[0], 65), foot)
                animator.draw(sheet, game.assets, 290, foot, facing_right=True)
                sheet.blit(game.assets.font(18).render(f"{state}: {index}", True, (40, 40, 40)), (i * 300 + 10, 10))
            pygame.image.save(sheet, output / f"{name}.png")
        for name in ("room", "walk"):
            game.change_screen(name)
            game.current_screen.draw(game.surface)
            pygame.image.save(game.surface, output / f"{name}_screen.png")
        # Exercise long-running room choices and the whole jump arc, not just
        # constructors. Obstacles are disabled only in this isolated preview.
        game.change_screen("room")
        game.current_screen.routine.random = random.Random(7)
        states = set()
        for _ in range(7200):
            pygame.event.pump()
            game.current_screen.update(1 / 60)
            states.add(game.current_screen.animator.state)
            game.current_screen.draw(game.surface)
        game.change_screen("walk")
        walk = game.current_screen
        walk.distance_until_pattern = 1e9
        for i in range(1800):
            pygame.event.pump()
            if i % 90 == 0:
                walk.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            walk.update(1 / 60)
            states.add(walk.animator.state)
            walk.draw(game.surface)
        print("9000 continuous room/jump frames rendered; states:", sorted(states))
        print(output)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
