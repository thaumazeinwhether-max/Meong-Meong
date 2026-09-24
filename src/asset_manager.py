"""Centralized loading and reuse of images, fonts, and simple sound effects."""

from pathlib import Path

import pygame

from src import config
from src.sound_manager import SilentSound, SoundManager
from src.sprite_layout import layout_for


class AssetManager:
    def __init__(self, sounds: SoundManager | None = None) -> None:
        self._images: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}
        self._sheets: dict[str, pygame.Surface] = {}
        self._frames: dict[tuple[str, int, int, int, bool], pygame.Surface] = {}
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self.sounds = sounds or SoundManager()

    def font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._fonts:
            preferred = ["Yu Gothic UI", "Meiryo", "Noto Sans CJK JP", "Arial"]
            path = pygame.font.match_font(preferred, bold=bold)
            self._fonts[key] = pygame.font.Font(path, size) if path else pygame.font.Font(None, size)
        return self._fonts[key]

    def image(self, path: Path, size: tuple[int, int]) -> pygame.Surface:
        key = (str(path), size)
        if key in self._images:
            return self._images[key]
        try:
            source = pygame.image.load(path).convert_alpha()
            image = pygame.transform.smoothscale(source, size)
        except (FileNotFoundError, pygame.error) as error:
            print(f"Asset load warning: {path}: {error}")
            image = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(image, config.PEACH, image.get_rect(), border_radius=24)
        self._images[key] = image
        return image

    def kurum(self, size: int) -> pygame.Surface:
        return self.image(config.KURUM_MASTER_PATH, (size, size))

    def kurum_frame(
        self,
        sheet_name: str,
        row: int,
        column: int,
        size: int,
        flip_x: bool = False,
    ) -> pygame.Surface:
        key = (sheet_name, row, column, size, flip_x)
        if key in self._frames:
            return self._frames[key]
        sheet = self._load_sheet(sheet_name)
        layout = layout_for(sheet_name, row, column)
        cell = sheet.subsurface(layout.rect).copy()
        # Image generation can leave isolated semi-transparent flecks. Keep
        # meaningful connected shapes (Kurum and toys) and remove tiny islands.
        source_mask = pygame.mask.from_surface(cell, threshold=8)
        clean_mask = pygame.Mask(cell.get_size())
        for component in source_mask.connected_components(24):
            clean_mask.draw(component, (0, 0))
        alpha_filter = clean_mask.to_surface(
            setcolor=(255, 255, 255, 255),
            unsetcolor=(255, 255, 255, 0),
        )
        cell.blit(alpha_filter, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # A fixed anatomical measurement keeps a crouch small and a jump
        # extended; normalizing each full bounding box would distort posture.
        scale = size * layout.head_fraction / layout.head_width
        scaled_size = (max(1, int(cell.get_width() * scale)), max(1, int(cell.get_height() * scale)))
        scaled = pygame.transform.smoothscale(cell, scaled_size)
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        if flip_x:
            scaled = pygame.transform.flip(scaled, True, False)
        anchor_x = layout.anchor[0] * scale
        if flip_x:
            anchor_x = scaled.get_width() - anchor_x
        position = (round(size / 2 - anchor_x), round(size * 0.94 - layout.anchor[1] * scale))
        canvas.blit(scaled, position)
        self._frames[key] = canvas
        return canvas

    def _load_sheet(self, sheet_name: str) -> pygame.Surface:
        if sheet_name in self._sheets:
            return self._sheets[sheet_name]
        paths = {
            "motion": config.KURUM_MOTION_SHEET_PATH,
            "action": config.KURUM_ACTION_SHEET_PATH,
            "gait": config.ASSETS_DIR / "character/animations/kurum_gait_v2.png",
            "rest": config.ASSETS_DIR / "character/animations/kurum_rest_v2.png",
        }
        path = paths[sheet_name]
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except (FileNotFoundError, pygame.error) as error:
            # Missing animation sheets must be visible during validation,
            # rather than silently turning Kurum into an invisible surface.
            raise RuntimeError(f"Animation asset could not be loaded: {path}") from error
        self._sheets[sheet_name] = sheet
        return sheet

    def room_background(self) -> pygame.Surface:
        return self.image(config.ROOM_BACKGROUND_PATH, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def walk_background(self) -> pygame.Surface:
        return self.image(config.WALK_BACKGROUND_PATH, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def sound(self, name: str) -> pygame.mixer.Sound | SilentSound:
        return self.sounds.get(name)
