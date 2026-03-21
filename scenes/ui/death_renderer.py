"""
Рендерер для DeathScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/death.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button
from ui.constants import *
from ui.assets import assets


class DeathRenderer(BaseRenderer):
    """
    Малює DeathScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

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
        if self.scene.player:
            font_stats = assets.get_font(FONT_SIZE_NORMAL)
            stats_text = f"Досягнутий рівень: {self.scene.player.level}  |  Зібрано золота: {self.scene.player.gold} 🪙"
            stats = font_stats.render(stats_text, True, COLOR_TEXT_DIM)
            screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, 400))

        # Кнопки
        for btn in self.scene.buttons:
            btn.draw(screen)