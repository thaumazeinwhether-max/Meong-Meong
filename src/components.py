"""Reusable visual controls kept intentionally small and readable."""

from collections.abc import Callable

import pygame

from src import config


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    position: tuple[int, int],
    center: bool = False,
) -> pygame.Rect:
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=position) if center else rendered.get_rect(topleft=position)
    surface.blit(rendered, rect)
    return rect


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 238) -> None:
    shadow = pygame.Surface((rect.width + 16, rect.height + 18), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (60, 45, 50, 45), shadow.get_rect(), border_radius=28)
    surface.blit(shadow, (rect.x - 4, rect.y + 6))
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*config.PANEL, alpha), panel.get_rect(), border_radius=24)
    pygame.draw.rect(panel, (255, 255, 255, 185), panel.get_rect(), width=2, border_radius=24)
    surface.blit(panel, rect.topleft)


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        on_click: Callable[[], None],
        color: tuple[int, int, int] = config.PEACH,
        enabled: bool = True,
    ) -> None:
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.color = color
        self.enabled = enabled

    def handle_event(self, event: pygame.event.Event, click_sound=None) -> None:
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            if click_sound:
                click_sound.play()
            self.on_click()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        color = tuple(min(255, value + 15) for value in self.color) if hovered else self.color
        if not self.enabled:
            color = (190, 186, 186)
        shadow_rect = self.rect.move(0, 5)
        pygame.draw.rect(surface, (125, 102, 106), shadow_rect, border_radius=18)
        pygame.draw.rect(surface, color, self.rect, border_radius=18)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=18)
        draw_text(surface, self.label, font, config.WHITE, self.rect.center, center=True)


class TextInput:
    def __init__(
        self,
        rect: pygame.Rect,
        placeholder: str,
        password: bool = False,
        max_length: int = 30,
        ascii_only: bool = False,
    ) -> None:
        self.rect = rect
        self.placeholder = placeholder
        self.password = password
        self.max_length = max_length
        self.ascii_only = ascii_only
        self.text = ""
        self.active = False
        self.composition_text = ""
        self.composition_start = 0
        self.composition_length = 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            focus_text_input([self], self if self.rect.collidepoint(event.pos) else None)
            return False
        if not self.active:
            return False

        # Editing keys belong to KEYDOWN. Printable text belongs to TEXTINPUT;
        # this is the SDL/Pygame path that also works reliably on Windows.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.composition_text:
                    self.clear_composition()
                else:
                    self.text = self.text[:-1]
                return True
            return False
        if event.type == pygame.TEXTEDITING:
            composition = event.text
            if self.ascii_only and any(not character.isascii() for character in composition):
                composition = ""
            self.composition_text = composition
            self.composition_start = getattr(event, "start", 0)
            self.composition_length = getattr(event, "length", 0)
            return True
        if event.type != pygame.TEXTINPUT:
            return False

        self.clear_composition()
        changed = False
        for character in event.text:
            if len(self.text) >= self.max_length:
                break
            if not character.isprintable():
                continue
            if self.ascii_only and (not character.isascii() or character.isspace()):
                continue
            self.text += character
            changed = True
        return changed

    def clear_composition(self) -> None:
        self.composition_text = ""
        self.composition_start = 0
        self.composition_length = 0

    @property
    def display_text(self) -> str:
        """Return masked text for drawing while preserving the real value."""
        if self.password:
            return "●" * len(self.text)
        return self.text

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, config.WHITE, self.rect, border_radius=14)
        border = config.PEACH_DARK if self.active else (200, 190, 190)
        pygame.draw.rect(surface, border, self.rect, width=3 if self.active else 2, border_radius=14)
        shown = self.display_text
        color = config.INK
        if not shown and not self.composition_text:
            shown = self.placeholder
            color = config.MUTED_INK
        clipped = shown
        while clipped and font.size(clipped)[0] > self.rect.width - 28:
            clipped = clipped[1:]
        text_position = (self.rect.x + 14, self.rect.y + 13)
        text_rect = draw_text(surface, clipped, font, color, text_position)
        if self.active and self.composition_text:
            composition = "●" * len(self.composition_text) if self.password else self.composition_text
            composition_x = min(text_rect.right + 2, self.rect.right - 24)
            composition_rect = draw_text(
                surface,
                composition,
                font,
                config.PEACH_DARK,
                (composition_x, self.rect.y + 13),
            )
            underline_right = min(composition_rect.right, self.rect.right - 12)
            pygame.draw.line(
                surface,
                config.PEACH_DARK,
                (composition_rect.left, self.rect.bottom - 10),
                (underline_right, self.rect.bottom - 10),
                2,
            )


def focus_text_input(fields: list[TextInput] | tuple[TextInput, ...], target: TextInput | None) -> None:
    """Give keyboard focus to exactly one field and update SDL text input."""
    for field in fields:
        if field is not target:
            field.clear_composition()
        field.active = field is target
    if target is None:
        pygame.key.stop_text_input()
    else:
        pygame.key.start_text_input()
        try:
            pygame.key.set_text_input_rect(target.rect)
        except pygame.error:
            # Headless tests can initialize the keyboard without a real window.
            pass


def focus_text_input_at(
    fields: list[TextInput] | tuple[TextInput, ...],
    position: tuple[int, int],
) -> None:
    """Select the field under a click, or clear focus when none was clicked."""
    target = next((field for field in fields if field.rect.collidepoint(position)), None)
    focus_text_input(fields, target)


def draw_bowl(surface: pygame.Surface, center: tuple[int, int], scale: float = 1.0) -> None:
    x, y = center
    width = int(110 * scale)
    pygame.draw.ellipse(surface, (236, 201, 145), (x - width // 2, y - 25 * scale, width, 38 * scale))
    pygame.draw.polygon(surface, (224, 137, 117), [
        (x - width // 2, y - 10 * scale),
        (x + width // 2, y - 10 * scale),
        (x + width * 0.38, y + 35 * scale),
        (x - width * 0.38, y + 35 * scale),
    ])
    pygame.draw.ellipse(surface, config.PEACH_DARK, (x - width * 0.38, y + 24 * scale, width * 0.76, 18 * scale))


def draw_treat(surface: pygame.Surface, center: tuple[int, int], size: int = 42) -> None:
    x, y = center
    radius = size // 2
    pygame.draw.circle(surface, (223, 157, 82), (x, y), radius)
    pygame.draw.circle(surface, (250, 199, 112), (x, y), radius - 5)
    for dx, dy in [(-8, -6), (9, -8), (2, 8), (-10, 10)]:
        pygame.draw.circle(surface, (110, 70, 54), (x + dx, y + dy), max(2, size // 14))


def draw_pooh(surface: pygame.Surface, center: tuple[int, int], size: int = 46) -> None:
    x, y = center
    brown = (116, 76, 55)
    pygame.draw.ellipse(surface, brown, (x - size * 0.45, y, size * 0.9, size * 0.38))
    pygame.draw.ellipse(surface, brown, (x - size * 0.34, y - size * 0.22, size * 0.68, size * 0.42))
    pygame.draw.ellipse(surface, brown, (x - size * 0.22, y - size * 0.43, size * 0.44, size * 0.4))
    pygame.draw.circle(surface, (45, 34, 31), (x - 7, int(y - size * 0.18)), 3)
    pygame.draw.circle(surface, (45, 34, 31), (x + 7, int(y - size * 0.18)), 3)


def draw_play_icon(surface: pygame.Surface, play_id: str, center: tuple[int, int], scale: float = 1.0) -> None:
    x, y = center
    if play_id == "pet":
        pygame.draw.circle(surface, config.PEACH, (x - int(16 * scale), y), int(18 * scale))
        pygame.draw.circle(surface, config.PEACH, (x + int(16 * scale), y), int(18 * scale))
        pygame.draw.ellipse(surface, config.PEACH_DARK, (x - 27 * scale, y - 3 * scale, 54 * scale, 40 * scale))
    elif play_id == "nosework":
        rect = pygame.Rect(x - 46 * scale, y - 24 * scale, 92 * scale, 52 * scale)
        pygame.draw.rect(surface, config.MINT, rect, border_radius=int(12 * scale))
        for dx in (-26, 0, 26):
            pygame.draw.circle(surface, config.GOLD, (int(x + dx * scale), y), int(7 * scale))
    elif play_id == "tug":
        pygame.draw.line(surface, (224, 105, 92), (x - 45 * scale, y), (x + 45 * scale, y), int(12 * scale))
        pygame.draw.circle(surface, config.SKY, (int(x - 46 * scale), y), int(16 * scale), width=int(7 * scale))
        pygame.draw.circle(surface, config.SKY, (int(x + 46 * scale), y), int(16 * scale), width=int(7 * scale))
    elif play_id == "ball":
        pygame.draw.circle(surface, (102, 173, 222), (x, y), int(33 * scale))
        pygame.draw.arc(surface, config.WHITE, (x - 30 * scale, y - 30 * scale, 60 * scale, 60 * scale), 0.2, 2.2, int(5 * scale))
