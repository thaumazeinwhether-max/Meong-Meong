"""Main application controller and screen routing."""

import pygame

from src import config
from src.asset_manager import AssetManager
from src.database_manager import DatabaseManager
from src.minigames.catch_game import CatchGame
from src.minigames.typing_game import TypingGame
from src.minigames.walk_game import WalkGame
from src.models import GameResult, UserSession
from src.screens.auth_screens import LoginScreen, NicknameScreen, RegisterScreen, TitleScreen
from src.screens.base import BaseScreen
from src.screens.home_screens import MinigameSelectScreen, PlaySelectScreen, RoomScreen
from src.screens.result_screens import ResultScreen, UnlockScreen


class Game:
    def __init__(self, database_path=config.DATABASE_PATH) -> None:
        pygame.display.set_caption(config.GAME_TITLE)
        self.surface = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.database = DatabaseManager(database_path)
        self.current_user: UserSession | None = None
        self.pending_unlock: str | None = None
        self.running = True
        self.current_screen: BaseScreen = TitleScreen(self)
        try:
            icon = pygame.transform.smoothscale(self.assets.kurum(128), (64, 64))
            pygame.display.set_icon(icon)
        except pygame.error as error:
            print(f"Window icon warning: {error}")

    def change_screen(self, screen_name: str, **kwargs) -> None:
        # End any IME composition owned by the previous screen. An input
        # screen constructor starts text input again for its focused field.
        pygame.key.stop_text_input()
        factories = {
            "title": TitleScreen,
            "login": LoginScreen,
            "register": RegisterScreen,
            "nickname": NicknameScreen,
            "room": RoomScreen,
            "play_select": PlaySelectScreen,
            "minigame_select": MinigameSelectScreen,
            "walk": WalkGame,
            "typing": TypingGame,
            "catch": CatchGame,
        }
        if screen_name not in factories:
            raise ValueError(f"Unknown screen: {screen_name}")
        self.current_screen = factories[screen_name](self, **kwargs)

    def complete_game(self, result: GameResult) -> None:
        if self.current_user is None:
            self.change_screen("login")
            return
        saved = self.database.save_game_result(self.current_user.user_id, result.game_id, result.score)
        self.current_user.progress = saved.progress
        result.is_new_best = saved.best_updated
        result.unlocked_play = saved.newly_unlocked
        result.best_score = {
            "walk": saved.progress.walk_best,
            "typing": saved.progress.typing_best,
            "catch": saved.progress.catch_best,
        }[result.game_id]
        self.pending_unlock = saved.newly_unlocked
        self.current_screen = ResultScreen(self, result)

    def leave_result(self, destination: str) -> None:
        if self.pending_unlock:
            self.current_screen = UnlockScreen(self, self.pending_unlock, destination)
        else:
            self.change_screen(destination)

    def finish_unlock(self, destination: str) -> None:
        self.pending_unlock = None
        self.change_screen(destination)

    def run(self, max_frames: int | None = None) -> None:
        frame_count = 0
        while self.running:
            dt = min(self.clock.tick(config.FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_screen.handle_event(event)
            self.current_screen.update(dt)
            self.current_screen.draw(self.surface)
            pygame.display.flip()
            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                self.running = False
