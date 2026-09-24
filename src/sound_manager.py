"""Centralized sound creation, caching, volume, and overlap control."""

from array import array
import math
import random

import pygame


class SilentSound:
    def play(self) -> None:
        return None


class SoundManager:
    """Provide small original effects without relying on unknown-license files."""

    VOLUMES = {
        "click": 0.28,
        "success": 0.32,
        "jump": 0.28,
        "correct": 0.30,
        "treat": 0.27,
        "bad": 0.22,
        "unlock": 0.35,
        "bark": 0.38,
        "typing_error": 0.20,
    }

    def __init__(self) -> None:
        self.audio_available = pygame.mixer.get_init() is not None
        self._sounds: dict[str, pygame.mixer.Sound | SilentSound] = {}
        self._last_played_ms: dict[str, int] = {}

    def get(self, name: str) -> pygame.mixer.Sound | SilentSound:
        if name not in self._sounds:
            self._sounds[name] = self._create(name) if self.audio_available else SilentSound()
        return self._sounds[name]

    def play(self, name: str, minimum_interval_ms: int = 0) -> bool:
        """Play once unless the named effect is still inside its cooldown."""
        now = pygame.time.get_ticks()
        last = self._last_played_ms.get(name, -1_000_000)
        if now - last < minimum_interval_ms:
            return False
        self._last_played_ms[name] = now
        self.get(name).play()
        return True

    def _create(self, name: str) -> pygame.mixer.Sound:
        if name == "bark":
            sound = self._make_bark()
        elif name in {"bad", "typing_error"}:
            sound = self._make_double_buzz(170 if name == "bad" else 205)
        else:
            frequencies = {
                "click": 620,
                "success": 780,
                "jump": 520,
                "correct": 880,
                "treat": 740,
                "unlock": 980,
            }
            duration = 0.32 if name == "unlock" else 0.11
            sound = self._make_tone(frequencies.get(name, 440), duration)
        sound.set_volume(self.VOLUMES.get(name, 0.3))
        return sound

    def _make_tone(self, frequency: int, duration: float) -> pygame.mixer.Sound:
        sample_rate = 44_100
        sample_count = int(sample_rate * duration)
        samples = array("h")
        for index in range(sample_count):
            fade = min(1.0, index / 500, (sample_count - index) / 900)
            value = int(8_000 * fade * math.sin(2 * math.pi * frequency * index / sample_rate))
            samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _make_double_buzz(self, frequency: int) -> pygame.mixer.Sound:
        sample_rate = 44_100
        duration = 0.16
        samples = array("h")
        for index in range(int(sample_rate * duration)):
            time = index / sample_rate
            pulse = 1.0 if time < 0.055 or 0.085 < time < 0.14 else 0.0
            envelope = min(1.0, index / 180, (int(sample_rate * duration) - index) / 220)
            value = int(4_800 * envelope * pulse * math.sin(2 * math.pi * frequency * time))
            samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _make_bark(self) -> pygame.mixer.Sound:
        """Create a short friendly, stylized bark-like sound from original synthesis."""
        sample_rate = 44_100
        duration = 0.20
        sample_count = int(sample_rate * duration)
        samples = array("h")
        random_source = random.Random(42)
        for index in range(sample_count):
            time = index / sample_rate
            frequency = 235 - 90 * (time / duration)
            body = math.sin(2 * math.pi * frequency * time)
            roughness = random_source.uniform(-1.0, 1.0) * 0.32
            attack = min(1.0, time / 0.012)
            release = max(0.0, 1.0 - time / duration) ** 1.8
            samples.append(int(10_000 * attack * release * (body * 0.68 + roughness)))
        return pygame.mixer.Sound(buffer=samples.tobytes())
