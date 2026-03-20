"""
Сцена вибору перку при підвищенні рівня.
"""

import pygame
from .base import Scene
from ui.assets import assets
from ui.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, COLOR_BG,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, FONT_SIZE_HUGE,
)
from game.perk_system import RARITY_COLORS, RARITY_NAMES
from game.save_manager import autosave


CARD_W = 280
CARD_H = 360
CARD_GAP = 40


class LevelUpScene(Scene):
    """Екран вибору картки перку після підвищення рівня."""

    def __init__(self, game):
        super().__init__(game)

        self.perks = self.player.pending_perk_choices[:]
        self.hovered = -1
        self.chosen  = -1
        # Онбординг — перший вибір перку
        self._is_first_perk = self.game.scene_data.pop("onboarding_perk_first", False)
        self._anim_t = 0.0

        # Координати карток (горизонтально по центру)
        total_w = len(self.perks) * CARD_W + (len(self.perks) - 1) * CARD_GAP
        start_x = SCREEN_WIDTH // 2 - total_w // 2
        card_y   = SCREEN_HEIGHT // 2 - CARD_H // 2

        self.card_rects = [
            pygame.Rect(start_x + i * (CARD_W + CARD_GAP), card_y, CARD_W, CARD_H)
            for i in range(len(self.perks))
        ]

        # Анімація появи
        self.alpha = 0
        self.fade_speed = 300  # одиниць/сек

        # Підключаємо renderer (малювання)
        from scenes.ui.level_up_renderer import LevelUpRenderer
        self._renderer = LevelUpRenderer(self)
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self.hovered = next(
                (i for i, r in enumerate(self.card_rects) if r.collidepoint(pos)),
                -1
            )

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for i, rect in enumerate(self.card_rects):
                if rect.collidepoint(pos) and self.chosen == -1:
                    self.chosen = i
                    self._choose_perk(i)
                    return

    def _choose_perk(self, index: int):
        """Застосовує вибраний перк."""
        perk = self.perks[index]
        self.player.apply_perk(perk)
        autosave(self.player)
        if self._is_first_perk:
            # Направляємо в навчання перків
            self.game.scene_data["onboarding_perk_tutorial"] = True
            self.game.change_scene("perks")
        else:
            self.game.change_scene("village")

    def update(self, dt: float):
        if self.alpha < 255:
            self.alpha = min(255, self.alpha + self.fade_speed * dt)
        self._anim_t += dt

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)