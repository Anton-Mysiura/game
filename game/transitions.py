"""
Плавні переходи між сценами (fade-out → scene swap → fade-in).

Архітектура:
  - Game тримає один екземпляр TransitionManager
  - change_scene / pop_scene починають fade-out
  - Коли fade-out завершено — TransitionManager сам виконує відкладену зміну сцени
    і починає fade-in
  - draw() малює чорний прямокутник з потрібною прозорістю поверх готового кадру

Налаштування:
  FADE_OUT  — час затемнення (старої сцени)
  FADE_IN   — час просвітлення (нової сцени)

Деякі переходи (battle, death, victory) можна зробити повільнішими —
передавай duration=(out, in) у request().
"""

from __future__ import annotations
import pygame
from typing import Callable, Optional

# Стандартна тривалість (секунди)
DEFAULT_OUT = 0.18
DEFAULT_IN  = 0.22

# Для «важливих» переходів (battle / death)
DRAMATIC_OUT = 0.35
DRAMATIC_IN  = 0.30


class TransitionManager:
    """Керує станом переходу між сценами."""

    def __init__(self):
        self._state:    str   = "idle"   # idle | fade_out | fade_in
        self._t:        float = 0.0      # поточний час фази
        self._dur_out:  float = DEFAULT_OUT
        self._dur_in:   float = DEFAULT_IN
        self._callback: Optional[Callable] = None   # виконується між out і in

    # ── Публічний API ──────────────────────────────────────────

    @property
    def busy(self) -> bool:
        """True поки йде будь-яка фаза переходу."""
        return self._state != "idle"

    def request(self, callback: Callable,
                duration: tuple[float, float] | None = None):
        """
        Запускає перехід.

        callback — функція що викликається після fade-out
                   (зазвичай lambda: game.change_scene(...) без анімації)
        duration — (fade_out_sec, fade_in_sec); None = за замовчуванням
        """
        if duration:
            self._dur_out, self._dur_in = duration
        else:
            self._dur_out, self._dur_in = DEFAULT_OUT, DEFAULT_IN

        self._callback = callback
        self._t        = 0.0
        self._state    = "fade_out"

    def skip(self):
        """Миттєво завершує поточний перехід (для тестів / адмін-консолі)."""
        if self._state == "fade_out" and self._callback:
            self._callback()
        self._state    = "idle"
        self._callback = None

    # ── Update / Draw ──────────────────────────────────────────

    def update(self, dt: float):
        if self._state == "idle":
            return

        self._t += dt

        if self._state == "fade_out":
            if self._t >= self._dur_out:
                # Виконуємо зміну сцени
                if self._callback:
                    self._callback()
                    self._callback = None
                self._t     = 0.0
                self._state = "fade_in"

        elif self._state == "fade_in":
            if self._t >= self._dur_in:
                self._t     = 0.0
                self._state = "idle"

    def draw(self, screen: pygame.Surface):
        if self._state == "idle":
            return

        if self._state == "fade_out":
            alpha = int(255 * min(1.0, self._t / max(self._dur_out, 0.001)))
        else:  # fade_in
            alpha = int(255 * (1.0 - min(1.0, self._t / max(self._dur_in, 0.001))))

        if alpha <= 0:
            return

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))


# Глобальний синглтон (ініціалізується з Game.__init__)
_manager: Optional[TransitionManager] = None


def get_transition_manager() -> TransitionManager:
    global _manager
    if _manager is None:
        _manager = TransitionManager()
    return _manager