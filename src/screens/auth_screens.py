"""Title, login, registration, and first-time nickname screens."""

import math

import pygame

from src import config
from src.animation import CharacterAnimator, KURUM_CLIPS
from src.components import (
    Button,
    TextInput,
    draw_panel,
    draw_text,
    focus_text_input,
    focus_text_input_at,
)
from src.database_manager import DuplicateUserError
from src.screens.base import BaseScreen


class TitleScreen(BaseScreen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.time = 0.0
        self.animator = CharacterAnimator(KURUM_CLIPS, "idle")
        self.start_button = Button(
            pygame.Rect(500, 565, 280, 68),
            "はじめる",
            lambda: self.game.change_screen("login"),
            config.PEACH,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        self.start_button.handle_event(event, self.click_sound)

    def update(self, dt: float) -> None:
        self.time += dt
        self.animator.update(dt)
        if self.time >= 5.0 and self.animator.state == "idle":
            self.animator.play("blink")
            self.time = 0.0

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface)
        veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        veil.fill((255, 248, 239, 62))
        surface.blit(veil, (0, 0))
        draw_text(surface, "Meong Meong!", self.assets.font(70, True), config.INK, (640, 92), center=True)
        draw_text(surface, "クルムと、やさしい時間を。", self.assets.font(28), config.MUTED_INK, (640, 155), center=True)
        self.animator.draw(surface, self.assets, 350, (640, 535))
        self.start_button.draw(surface, self.assets.font(30, True))


class LoginScreen(BaseScreen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.username = TextInput(pygame.Rect(470, 265, 410, 58), "ユーザー名", ascii_only=True, max_length=20)
        self.password = TextInput(pygame.Rect(470, 348, 410, 58), "パスワード", password=True, max_length=64)
        self.input_fields = (self.username, self.password)
        focus_text_input(self.input_fields, self.username)
        self.message = ""
        self.message_color = config.ERROR
        self.buttons = [
            Button(pygame.Rect(470, 438, 195, 58), "ログイン", self.login, config.PEACH),
            Button(pygame.Rect(685, 438, 195, 58), "新規登録", lambda: game.change_screen("register"), config.MINT),
            Button(pygame.Rect(570, 520, 210, 50), "タイトルへ戻る", lambda: game.change_screen("title"), (163, 158, 163)),
        ]

    def login(self) -> None:
        session = self.game.database.authenticate(self.username.text, self.password.text)
        if session is None:
            self.message = "ユーザー名またはパスワードが違います。"
            self.message_color = config.ERROR
            return
        self.game.current_user = session
        self.assets.sound("success").play()
        if session.nickname:
            self.game.change_screen("room")
        else:
            self.game.change_screen("nickname")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            focus_text_input_at(self.input_fields, event.pos)
        else:
            for field in self.input_fields:
                field.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not any(
            field.composition_text for field in self.input_fields
        ):
            self.login()
        for button in self.buttons:
            button.handle_event(event, self.click_sound)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface, dim=True)
        panel = pygame.Rect(405, 115, 540, 515)
        draw_panel(surface, panel)
        draw_text(surface, "ログイン", self.assets.font(46, True), config.INK, (675, 180), center=True)
        self.username.draw(surface, self.assets.font(25))
        self.password.draw(surface, self.assets.font(25))
        if self.message:
            draw_text(surface, self.message, self.assets.font(20, True), self.message_color, (675, 420), center=True)
        for button in self.buttons:
            button.draw(surface, self.assets.font(23, True))


class RegisterScreen(BaseScreen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.username = TextInput(pygame.Rect(455, 220, 440, 54), "ユーザー名（3〜20文字）", ascii_only=True, max_length=20)
        self.password = TextInput(pygame.Rect(455, 300, 440, 54), "パスワード（6文字以上）", password=True, max_length=64)
        self.confirm = TextInput(pygame.Rect(455, 380, 440, 54), "パスワードを再入力", password=True, max_length=64)
        self.input_fields = (self.username, self.password, self.confirm)
        focus_text_input(self.input_fields, self.username)
        self.message = ""
        self.buttons = [
            Button(pygame.Rect(455, 475, 210, 58), "登録する", self.register, config.PEACH),
            Button(pygame.Rect(685, 475, 210, 58), "ログインへ戻る", lambda: game.change_screen("login"), config.MINT),
        ]

    def register(self) -> None:
        if self.password.text != self.confirm.text:
            self.message = "確認用パスワードが一致しません。"
            return
        try:
            session = self.game.database.register_user(self.username.text, self.password.text)
        except (ValueError, DuplicateUserError) as error:
            self.message = str(error)
            return
        self.game.current_user = session
        self.assets.sound("success").play()
        self.game.change_screen("nickname")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            focus_text_input_at(self.input_fields, event.pos)
        else:
            for field in self.input_fields:
                field.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not any(
            field.composition_text for field in self.input_fields
        ):
            self.register()
        for button in self.buttons:
            button.handle_event(event, self.click_sound)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface, dim=True)
        panel = pygame.Rect(390, 85, 570, 535)
        draw_panel(surface, panel)
        draw_text(surface, "ユーザー登録", self.assets.font(43, True), config.INK, (675, 145), center=True)
        for field in (self.username, self.password, self.confirm):
            field.draw(surface, self.assets.font(23))
        if self.message:
            draw_text(surface, self.message, self.assets.font(19, True), config.ERROR, (675, 455), center=True)
        for button in self.buttons:
            button.draw(surface, self.assets.font(21, True))


class NicknameScreen(BaseScreen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.nickname = TextInput(pygame.Rect(455, 380, 370, 58), "1〜10文字", max_length=10)
        self.input_fields = (self.nickname,)
        focus_text_input(self.input_fields, self.nickname)
        self.animator = CharacterAnimator(KURUM_CLIPS, "idle")
        self.message = ""
        self.button = Button(pygame.Rect(515, 475, 250, 60), "この名前にする", self.save, config.PEACH)

    def save(self) -> None:
        if self.game.current_user is None:
            self.game.change_screen("login")
            return
        try:
            self.game.current_user = self.game.database.set_nickname(
                self.game.current_user.user_id,
                self.nickname.text,
            )
        except ValueError as error:
            self.message = str(error)
            return
        self.assets.sound("success").play()
        self.game.change_screen("room")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            focus_text_input_at(self.input_fields, event.pos)
        else:
            self.nickname.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not self.nickname.composition_text:
            self.save()
        self.button.handle_event(event, self.click_sound)

    def update(self, dt: float) -> None:
        self.animator.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface, dim=True)
        panel = pygame.Rect(365, 70, 550, 570)
        draw_panel(surface, panel)
        draw_text(surface, "クルムにニックネームを", self.assets.font(39, True), config.INK, (640, 135), center=True)
        self.animator.draw(surface, self.assets, 220, (640, 372))
        self.nickname.draw(surface, self.assets.font(26))
        if self.message:
            draw_text(surface, self.message, self.assets.font(20, True), config.ERROR, (640, 452), center=True)
        self.button.draw(surface, self.assets.font(24, True))
        draw_text(surface, "設定後は変更できません", self.assets.font(18), config.MUTED_INK, (640, 570), center=True)
