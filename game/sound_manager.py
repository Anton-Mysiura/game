"""
Менеджер звуків та музики.
"""

import logging

import pygame
from ui.constants import SOUNDS_DIR, MUSIC_DIR
log = logging.getLogger(__name__)


class SoundManager:
    """Singleton для керування всіма звуками гри."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.enabled = True
        self.music_enabled = True
        self.sfx_volume = 0.7
        self.music_volume = 0.4
        self.show_damage_numbers = True
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._sounds_loaded = False

    def _ensure_loaded(self):
        """Завантажує звуки при першому використанні (після init mixer)."""
        if not self._sounds_loaded:
            self._sounds_loaded = True
            self._load_sounds()

    def _load_sounds(self):
        """Завантажує всі звукові ефекти."""
        sound_files = {
            "sword_hit":   "sword_hit.wav",
            "sword_swing": "sword_swing.wav",
            "hurt":        "hurt.ogg",
            "grunt":       "grunt.wav",
            "jump":        "jump.wav",
        }

        for name, filename in sound_files.items():
            path = SOUNDS_DIR / filename
            if path.exists():
                try:
                    sound = pygame.mixer.Sound(str(path))
                    sound.set_volume(self.sfx_volume)
                    self._sounds[name] = sound
                    log.info("Завантажено звук: %s", name)
                except Exception as e:
                    log.warning("Не вдалось завантажити звук %s: %s", name, e)
            else:
                log.warning("Звук не знайдено: %s", path)

    def play(self, name: str, volume: float = None):
        """Відтворює звуковий ефект."""
        if not self.enabled:
            return
        self._ensure_loaded()
        sound = self._sounds.get(name)
        if sound:
            if volume is not None:
                sound.set_volume(volume)
            else:
                sound.set_volume(self.sfx_volume)
            sound.play()

    def play_music(self, filename: str, loop: bool = True):
        """Запускає фонову музику."""
        if not self.music_enabled:
            return
        self._ensure_loaded()
        path = MUSIC_DIR / filename
        if not path.exists():
            log.warning("Музика не знайдена: %s", path)
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            log.info("Грає музика: %s", filename)
        except Exception as e:
            log.warning("Не вдалось запустити музику: %s", e)

    def stop_music(self):
        """Зупиняє музику."""
        pygame.mixer.music.stop()

    def pause_music(self):
        pygame.mixer.music.pause()

    def unpause_music(self):
        pygame.mixer.music.unpause()

    def set_sfx_volume(self, volume: float):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self._sounds.values():
            sound.set_volume(self.sfx_volume)

    def set_music_volume(self, volume: float):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)


# Глобальний екземпляр
sounds = SoundManager()