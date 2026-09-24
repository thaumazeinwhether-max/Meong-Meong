"""Room, play selection, and minigame selection screens."""

import math
import random

import pygame

from src import config
from src.animation import CharacterAnimator, KURUM_CLIPS
from src.components import Button, draw_bowl, draw_panel, draw_play_icon, draw_text
from src.screens.base import BaseScreen
from src.room_behavior import RoomBehavior


class RoomScreen(BaseScreen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.animator = CharacterAnimator(KURUM_CLIPS, "idle")
        self.routine = RoomBehavior(self.animator)
        self.character_x = 650.0
        self.target_x = self.character_x
        self.facing_right = True
        self.feed_phase: str | None = None
        self.feed_phase_time = 0.0
        self.feed_bowl_x = 840
        self.feed_requested = False
        self.buttons = [
            Button(pygame.Rect(60, 600, 235, 62), "ごはん", self.feed, config.PEACH),
            Button(pygame.Rect(315, 600, 235, 62), "あそぶ", lambda: game.change_screen("play_select"), config.MINT),
            Button(pygame.Rect(570, 600, 250, 62), "ミニゲーム", lambda: game.change_screen("minigame_select"), config.SKY),
            Button(pygame.Rect(1040, 40, 175, 50), "ログアウト", self.logout, (157, 151, 157)),
        ]

    def feed(self) -> None:
        if self.feed_phase is None:
            if self.routine.state != "idle":
                self.feed_requested = True
                self.routine.idle_requested = True
                return
            self.feed_requested = False
            self.feed_bowl_x = 840 if self.character_x < 760 else 460
            self.feed_phase = "bowl"
            self.feed_phase_time = 0.0
            self.animator.play("blink", restart=True)
            self.assets.sounds.play("treat")

    def logout(self) -> None:
        self.game.current_user = None
        self.game.change_screen("login")

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.feed_phase is not None or self.feed_requested:
            return
        for button in self.buttons:
            button.handle_event(event, self.click_sound)

    def update(self, dt: float) -> None:
        if self.feed_phase is not None:
            self._update_feeding(dt)
            return
        self.routine.update(dt, config.ROOM_CHARACTER_SIZE)
        self.character_x = self.routine.x
        self.facing_right = self.routine.facing_right
        if self.feed_requested and self.routine.state == "idle":
            self.feed()

    def _update_feeding(self, dt: float) -> None:
        self.feed_phase_time += dt
        travelled = 0.0
        if self.feed_phase == "approach":
            direction = 1 if self.target_x > self.character_x else -1
            self.facing_right = direction > 0
            travelled = min(abs(self.target_x - self.character_x), 105 * dt)
            self.character_x += direction * travelled
        self.animator.update(dt, travel=travelled, size=config.ROOM_CHARACTER_SIZE)
        if self.feed_phase == "bowl" and self.feed_phase_time >= 0.55:
            self.feed_phase = "approach"
            self.feed_phase_time = 0.0
            self.target_x = float(self.feed_bowl_x)
            self.animator.play("walk", restart=True)
        elif self.feed_phase == "approach":
            if abs(self.target_x - self.character_x) < 0.01:
                self.character_x = self.target_x
                self.feed_phase = "eating"
                self.feed_phase_time = 0.0
                self.animator.play("eat", restart=True)
        elif self.feed_phase == "eating" and self.animator.finished:
            self.feed_phase = "happy"
            self.feed_phase_time = 0.0
            self.animator.play("happy", restart=True)
            self.assets.sounds.play("success")
        elif self.feed_phase == "happy" and "happy" in self.animator.completed:
            self.feed_phase = None
            self.routine.x = self.character_x
            self.routine.idle_requested = False
            self.routine.enter("idle")
            self.routine.duration = 8.0

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface)
        nickname = self.game.current_user.nickname if self.game.current_user else "クルム"
        draw_panel(surface, pygame.Rect(35, 25, 420, 90), alpha=220)
        draw_text(surface, f"{nickname}のおへや", self.assets.font(34, True), config.INK, (60, 48))
        draw_text(surface, "今日は何をして過ごす？", self.assets.font(20), config.MUTED_INK, (62, 87))

        self.animator.draw(surface, self.assets, config.ROOM_CHARACTER_SIZE, (self.character_x, 580), self.facing_right)
        if self.feed_phase is not None:
            if self.feed_phase in {"bowl", "approach"}:
                # The eating sprite already includes its bowl.
                draw_bowl(surface, (self.feed_bowl_x, 565), 1.0)
            messages = {
                "bowl": "ごはんだよ！",
                "approach": "とことこ…",
                "eating": "もぐもぐ…",
                "happy": "おいしかった！",
            }
            draw_text(surface, messages[self.feed_phase], self.assets.font(28, True), config.PEACH_DARK, (650, 255), center=True)
        for button in self.buttons:
            button.enabled = self.feed_phase is None and not self.feed_requested
            button.draw(surface, self.assets.font(24, True))


class PlaySelectScreen(BaseScreen):
    PLAY_LABELS = {
        "pet": "なでる",
        "nosework": "ノーズワーク",
        "tug": "ひっぱりっこ",
        "ball": "ボール遊び",
    }

    def __init__(self, game) -> None:
        super().__init__(game)
        self.selected_play: str | None = None
        self.animator = CharacterAnimator(KURUM_CLIPS, "idle")
        self.animation_time = 0.0
        self.phase_index = 0
        self.phase_time = 0.0
        self.character_x = 640.0
        self.facing_right = True
        self.sequence: list[tuple[float, str]] = []
        self.buttons: list[Button] = []
        self._build_buttons()

    def _build_buttons(self) -> None:
        available = ["pet"]
        progress = self.game.current_user.progress if self.game.current_user else None
        if progress and progress.nosework_unlocked:
            available.append("nosework")
        if progress and progress.tug_unlocked:
            available.append("tug")
        if progress and progress.ball_unlocked:
            available.append("ball")
        start_x = 110 + (4 - len(available)) * 120
        for index, play_id in enumerate(available):
            rect = pygame.Rect(start_x + index * 245, 500, 215, 66)
            self.buttons.append(Button(rect, self.PLAY_LABELS[play_id], lambda p=play_id: self.start_play(p), config.MINT))
        self.buttons.append(Button(pygame.Rect(520, 615, 240, 52), "部屋へ戻る", lambda: self.game.change_screen("room"), (157, 151, 157)))

    def start_play(self, play_id: str) -> None:
        self.selected_play = play_id
        self.animation_time = 0.0
        self.phase_index = 0
        self.phase_time = 0.0
        self.character_x = 640.0
        sequences = {
            "pet": [(1.4, random.choice(["pet_happy", "belly"])), (1.2, "happy")],
            "nosework": [(1.3, "sniff"), (1.4, "walk"), (1.3, "sniff"), (1.5, "found")],
            "tug": [(1.0, "tug_bite"), (2.3, "tug_pull"), (1.4, "tug_win")],
            "ball": [(0.9, "watch_ball"), (1.5, "chase_ball"), (1.5, "carry_ball"), (1.2, "happy")],
        }
        self.sequence = sequences[play_id]
        self.animator.play(self.sequence[0][1], restart=True)
        self.assets.sounds.play("success")

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.selected_play is not None:
            return
        for button in self.buttons:
            button.handle_event(event, self.click_sound)

    def update(self, dt: float) -> None:
        if self.selected_play is None:
            self.animator.update(dt)
            return
        self.animation_time += dt
        self.phase_time += dt
        state = self.sequence[self.phase_index][1]
        previous_x = self.character_x
        if state in {"walk", "chase_ball"}:
            self.character_x += 105 * dt
            self.facing_right = True
        elif state == "carry_ball":
            self.character_x -= 105 * dt
            self.facing_right = False

        self.animator.update(dt, travel=abs(self.character_x - previous_x), size=330)

        clip = self.animator.clips[self.animator.state]
        reaction_done = clip.loop or self.animator.finished or state in self.animator.completed
        if self.phase_time >= self.sequence[self.phase_index][0] and reaction_done:
            self.phase_index += 1
            self.phase_time = 0.0
            if self.phase_index < len(self.sequence):
                self.animator.play(self.sequence[self.phase_index][1], restart=True)
            else:
                self.game.change_screen("room")
                return

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface)
        draw_panel(surface, pygame.Rect(60, 35, 1160, 630), alpha=205)
        draw_text(surface, "クルムとあそぶ", self.assets.font(44, True), config.INK, (640, 80), center=True)
        self.animator.draw(surface, self.assets, 330, (self.character_x, 485), self.facing_right)
        if self.selected_play:
            label = self.PLAY_LABELS[self.selected_play]
            if self.selected_play == "nosework":
                pygame.draw.circle(surface, config.GOLD, (875, 458), 12)
            elif self.selected_play == "tug":
                pygame.draw.line(surface, config.PEACH_DARK, (820, 360), (1010, 345), 14)
            elif self.selected_play == "ball":
                progress = min(1.0, self.animation_time / 1.8)
                ball_x = int(820 + 230 * progress)
                ball_y = int(365 - math.sin(progress * math.pi) * 150)
                pygame.draw.circle(surface, (83, 156, 222), (ball_x, ball_y), 24)
            else:
                draw_play_icon(surface, self.selected_play, (860, 330), 1.35)
            draw_text(surface, f"{label}、たのしいね！", self.assets.font(31, True), config.PEACH_DARK, (640, 160), center=True)
        else:
            draw_text(surface, "遊びを選んでね", self.assets.font(24), config.MUTED_INK, (640, 140), center=True)
            for button in self.buttons:
                button.draw(surface, self.assets.font(22, True))


class MinigameSelectScreen(BaseScreen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.cards = [
            (pygame.Rect(100, 205, 330, 300), "お散歩ジャンプ", "Spaceで障害物をジャンプ", "walk", config.MINT),
            (pygame.Rect(475, 205, 330, 300), "吠えるタイピング", "流れる英単語を入力", "typing", config.SKY),
            (pygame.Rect(850, 205, 330, 300), "おやつキャッチ", "左右キーでおやつをキャッチ", "catch", config.PEACH),
        ]
        self.buttons = [
            Button(pygame.Rect(rect.x + 55, rect.bottom - 78, 220, 54), "あそぶ", lambda g=game_id: game.change_screen(g), color)
            for rect, _, _, game_id, color in self.cards
        ]
        self.back_button = Button(pygame.Rect(520, 595, 240, 52), "部屋へ戻る", lambda: game.change_screen("room"), (157, 151, 157))

    def handle_event(self, event: pygame.event.Event) -> None:
        for button in self.buttons:
            button.handle_event(event, self.click_sound)
        self.back_button.handle_event(event, self.click_sound)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface, dim=True)
        draw_text(surface, "ミニゲーム", self.assets.font(50, True), config.WHITE, (640, 80), center=True)
        for index, (rect, title, description, game_id, color) in enumerate(self.cards):
            draw_panel(surface, rect, alpha=245)
            pygame.draw.circle(surface, color, (rect.centerx, rect.y + 72), 42)
            icon_font = self.assets.font(33, True)
            icon = {"walk": "JUMP", "typing": "ABC", "catch": "+1"}[game_id]
            draw_text(surface, icon, icon_font, config.WHITE, (rect.centerx, rect.y + 72), center=True)
            draw_text(surface, title, self.assets.font(28, True), config.INK, (rect.centerx, rect.y + 132), center=True)
            draw_text(surface, description, self.assets.font(18), config.MUTED_INK, (rect.centerx, rect.y + 176), center=True)
            self.buttons[index].draw(surface, self.assets.font(22, True))
        self.back_button.draw(surface, self.assets.font(21, True))
