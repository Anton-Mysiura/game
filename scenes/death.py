"""
Сцена смерті гравця.
"""

import pygame
from .base import Scene
from ui.components import Button
from ui.constants import *
from ui.assets import assets
from game.save_manager import SaveManager


class DeathScene(Scene):
    """Екран смерті."""

    def __init__(self, game):
        super().__init__(game)

        # Кнопки
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 450, 300, 60,
                   "🔄 Завантажити гру", lambda: self._load_game()),
            Button(SCREEN_WIDTH // 2 - 150, 530, 300, 60,
                   "🏠 Головне меню", lambda: game.change_scene("main_menu")),
        ]

    def _load_game(self):
        """Завантажити останнє збереження."""
        if self.player and self.player.save_name:
            loaded = SaveManager.load_game(self.player.save_name)
            if loaded:
                self.game.player = loaded
                self.game.change_scene("village")
            else:
                # Не вдалося завантажити
                self.game.change_scene("main_menu")
        else:
            self.game.change_scene("main_menu")

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
        """Малювання."""
        # Темний фон з червоним відтінком
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(40 + (20 - 40) * progress)
            g = int(0)
            b = int(0)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Заголовок
        font_huge = assets.get_font(80, bold=True)
        title = font_huge.render("💀 ТИ ЗАГИНУВ 💀", True, COLOR_ERROR)

        # Тінь
        shadow = font_huge.render("💀 ТИ ЗАГИНУВ 💀", True, (0, 0, 0))
        screen.blit(shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 103))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        # Повідомлення
        font_text = assets.get_font(FONT_SIZE_LARGE)
        death_lines = [
            "Темрява поглинула тебе...",
            "",
            "Але це ще не кінець.",
            "Спробуй знову, герою!",
        ]

        y = 280
        for line in death_lines:
            text = font_text.render(line, True, COLOR_TEXT)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 40

        # Статистика смерті (якщо є гравець)
        if self.player:
            font_stats = assets.get_font(FONT_SIZE_NORMAL)
            stats_text = f"Досягнутий рівень: {self.player.level}  |  Зібрано золота: {self.player.gold} 🪙"
            stats = font_stats.render(stats_text, True, COLOR_TEXT_DIM)
            screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, 400))

        # Кнопки
        for btn in self.buttons:
            btn.draw(screen)