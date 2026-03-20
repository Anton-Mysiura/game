"""
Сцена рандомної події в лісі.
"""

import pygame
from .base import Scene
from ui.assets import assets
from ui.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, COLOR_HP, COLOR_BG,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, FONT_SIZE_HUGE,
)
from game.forest_events import ForestEvent, EventResult
from game.save_manager import autosave


PANEL_W = 780
PANEL_H = 480
PANEL_X = SCREEN_WIDTH  // 2 - PANEL_W // 2
PANEL_Y = SCREEN_HEIGHT // 2 - PANEL_H // 2


class ForestEventScene(Scene):
    """Показує рандомну подію з вибором дій."""

    def __init__(self, game):
        super().__init__(game)

        self.event: ForestEvent = game.scene_data.get("forest_event")
        self.return_scene: str  = game.scene_data.get("return_scene", "forest")

        # Стан: "choice" → гравець вибирає | "result" → показуємо результат
        self.state   = "choice"
        self.result: EventResult | None = None

        # Кнопки вибору (будуємо в update)
        self._choice_rects: list[pygame.Rect] = []
        self._hovered = -1

        # Кнопка "Продовжити" після результату
        self._continue_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 130, PANEL_Y + PANEL_H - 65, 260, 48
        )

        # Анімація появи
        self.alpha = 0.0

        self._build_choice_rects()

        # Підключаємо renderer (малювання)
        from scenes.ui.forest_event_renderer import ForestEventRenderer
        self._renderer = ForestEventRenderer(self)
    def _build_choice_rects(self):
        if not self.event:
            return
        n = len(self.event.choices)
        btn_h = 52
        gap   = 10
        total = n * btn_h + (n - 1) * gap
        start_y = PANEL_Y + PANEL_H - total - 75

        self._choice_rects = []
        for i in range(n):
            r = pygame.Rect(PANEL_X + 40, start_y + i * (btn_h + gap),
                            PANEL_W - 80, btn_h)
            self._choice_rects.append(r)

    # ── Events ──────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self.state == "choice":
                self._hovered = next(
                    (i for i, r in enumerate(self._choice_rects)
                     if r.collidepoint(pos)), -1
                )
            else:
                self._hovered = -1

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "choice":
                for i, r in enumerate(self._choice_rects):
                    if r.collidepoint(pos):
                        self._resolve(i)
                        return
            else:
                if self._continue_rect.collidepoint(pos):
                    self._go_next()

        if event.type == pygame.KEYDOWN:
            if self.state == "result" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_next()

    def _resolve(self, choice_idx: int):
        choice = self.event.choices[choice_idx]
        self.result = choice.resolve(self.player)
        self.state = "result"
        autosave(self.player)

    def _go_next(self):
        if self.result and self.result.enemy:
            # Бій — після бою повертаємось у ліс
            self.game.change_scene(
                "battle",
                enemy=self.result.enemy,
                return_scene=self.return_scene,
            )
        else:
            self.game.change_scene(self.return_scene)

    # ── Update ──────────────────────────────────────────────

    def update(self, dt: float):
        self.alpha = min(255, self.alpha + 400 * dt)

    # ── Draw ────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)