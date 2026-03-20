"""
Сцена лігва дракона (фінальний бій).
"""

import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets
from game.enemy import make_dragon


class DragonScene(SceneWithBackground, SceneWithButtons):
    """Лігво дракона Морвета."""

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "dragon_lair")
        SceneWithButtons.__init__(self, game)

        self.stage = "intro"  # intro | preparing | battle

        # Панель
        self.dialog_panel = Panel(SCREEN_WIDTH // 2 - 450, SCREEN_HEIGHT - 350, 900, 300, alpha=True)
        self.text_box = TextBox(SCREEN_WIDTH // 2 - 420, SCREEN_HEIGHT - 320, 840, FONT_SIZE_MEDIUM)

        self._show_intro()

        # Підключаємо renderer (малювання)
        from scenes.ui.dragon_renderer import DragonRenderer
        self._renderer = DragonRenderer(self)
    def _show_intro(self):
        """Вступ до лігва."""
        self.stage = "intro"

        text = (
            "Печера дракона. Повітря важке від жару.\n"
            "Величезна тінь ворушиться в глибині...\n\n"
            "🐉 МОРВЕТ — ВЛАДАР ТЕМНИХ ЗЕМЕЛЬ\n\n"
            "Це фінальний бій. Переконайся що ти готовий!"
        )
        self.text_box.set_text(text)

        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT - 100, 250, 60,
                   "⚔ БИТВА!", lambda: self._start_battle()),
            Button(SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT - 100, 250, 60,
                   "🏘 Підготуватись", lambda: self.game.change_scene("village")),
        ]

    def _start_battle(self):
        """Початок фінального бою."""
        enemy = make_dragon(self.player.level)
        self.game.change_scene("battle", enemy=enemy, return_scene="dragon_after_battle")

    def on_enter(self):
        """Викликається при вході."""
        super().on_enter()

        # Перевірка після бою
        if self.game.scene_data.get("from_battle") == "dragon_after_battle":
            # Перемога — перехід до екрану перемоги
            self.game.change_scene("victory")

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)