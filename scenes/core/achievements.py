"""
Сцена досягнень зі скролом.
"""

import pygame
from .base import Scene
from ui.components import Button, Panel, ProgressBar
from ui.constants import *
from ui.assets import assets
from game.achievements import ACHIEVEMENTS, AchievementManager

# Розміри зони списку
LIST_X      = 60
LIST_Y      = 210
LIST_W      = 520
LIST_H      = SCREEN_HEIGHT - 290   # висота видимої зони
ITEM_H      = 78
ITEM_GAP    = 6
SCROLL_SPD  = 40


class AchievementsScene(Scene):
    """Екран досягнень."""

    def __init__(self, game):
        super().__init__(game)

        self.close_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 68, 200, 50,
            "Закрити", lambda: game.pop_scene()
        )
        self.main_panel = Panel(30, 30, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 70, alpha=True)
        self.progress   = AchievementManager.get_progress(self.player)

        # Тільки видимі досягнення
        self.achievement_list = [
            (aid, ach) for aid, ach in ACHIEVEMENTS.items()
            if not ach.hidden or aid in self.player.achievements_unlocked
        ]

        self.selected_index = -1
        self.scroll_y       = 0       # поточний зсув скролу (пікселі)
        self.scroll_target  = 0       # плавний скрол
        self._max_scroll     = max(0, len(self.achievement_list) * (ITEM_H + ITEM_GAP) - LIST_H)

        # Clip rect для списку
        self.list_clip = pygame.Rect(LIST_X, LIST_Y, LIST_W, LIST_H)

    # ─────────────────────────────────────────
        # Підключаємо renderer (малювання)
        from scenes.ui.achievements_renderer import AchievementsRenderer
        self._renderer = AchievementsRenderer(self)
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Скрол колесом
            if event.button == 4:   # вгору
                self.scroll_target = max(0, self.scroll_target - SCROLL_SPD * 3)
            elif event.button == 5: # вниз
                self.scroll_target = min(self._max_scroll, self.scroll_target + SCROLL_SPD * 3)

            elif event.button == 1:
                self.close_button.update(mouse_pos, True)

                # Клік по досягненню (тільки якщо в зоні списку)
                if self.list_clip.collidepoint(mouse_pos):
                    rel_y = mouse_pos[1] - LIST_Y + self.scroll_y
                    idx = int(rel_y // (ITEM_H + ITEM_GAP))
                    if 0 <= idx < len(self.achievement_list):
                        self.selected_index = idx

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.scroll_target = min(self._max_scroll, self.scroll_target + SCROLL_SPD)
            elif event.key == pygame.K_UP:
                self.scroll_target = max(0, self.scroll_target - SCROLL_SPD)
            elif event.key == pygame.K_ESCAPE:
                self.game.pop_scene()

    # ─────────────────────────────────────────
    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.close_button.update(mouse_pos, False)

        # Плавний скрол
        diff = self.scroll_target - self.scroll_y
        self.scroll_y += diff * min(1.0, dt * 14)

    # ─────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)