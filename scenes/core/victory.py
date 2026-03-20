"""
Сцена перемоги (фінальний екран після дракона).
"""

import pygame
from .base import Scene
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.save_manager import autosave


class VictoryScene(Scene):
    """Екран перемоги."""

    def __init__(self, game):
        super().__init__(game)

        # Фінальна нагорода
        self.player.gold += 200
        autosave(self.player)

        # Кнопки
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 500, 300, 60,
                   "🏘 Повернутись до села", lambda: game.change_scene("village")),
            Button(SCREEN_WIDTH // 2 - 150, 580, 300, 60,
                   "📊 Фінальна статистика", lambda: game.push_scene("stats")),
        ]

        # Підключаємо renderer (малювання)
        from scenes.ui.victory_renderer import VictoryRenderer
        self._renderer = VictoryRenderer(self)
    def handle_event(self, event: pygame.event.Event):
        """Обробка подій."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                btn.update(mouse_pos, True)

    def update(self, dt: float):
        """Оновлення."""
        mouse_pos = pygame.mouse.get_pos()

        for btn in self.buttons:
            btn.update(mouse_pos, False)

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)