"""
Рендерер для VictoryScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/victory.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets


class VictoryRenderer(BaseRenderer):
    """
    Малює VictoryScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # Градієнтний фон (темний → золотий)
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(20 + (80 - 20) * progress)
            g = int(15 + (60 - 15) * progress)
            b = int(10 + (20 - 10) * progress)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Заголовок
        font_huge = assets.get_font(80, bold=True)
        title = font_huge.render("⚔ ПЕРЕМОГА! ⚔", True, COLOR_GOLD)

        # Ефект свічення
        glow_surface = pygame.Surface((title.get_width() + 10, title.get_height() + 10), pygame.SRCALPHA)
        glow_color = (255, 215, 0, 100)
        for offset in range(5, 0, -1):
            glow = font_huge.render("⚔ ПЕРЕМОГА! ⚔", True, glow_color)
            glow_surface.blit(glow, (offset, offset))

        screen.blit(glow_surface, (SCREEN_WIDTH // 2 - title.get_width() // 2 - 5, 95))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        # Панель з результатами
        panel = Panel(SCREEN_WIDTH // 2 - 350, 250, 700, 200, alpha=True)
        panel.draw(screen)

        # Текст перемоги
        font_text = assets.get_font(FONT_SIZE_MEDIUM)
        victory_lines = [
            "Дракон Морвет переможений!",
            "Темне Королівство врятовано!",
            "",
            f"Герой {self.scene.player.name} назавжди увійде в легенди.",
            f"Фінальний рівень: {self.scene.player.level}",
            f"Зібрано золота: {self.scene.player.gold} 🪙",
        ]

        y = 280
        for line in victory_lines:
            if line:
                text = font_text.render(line, True, COLOR_TEXT)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 30

        # Кнопки
        for btn in self.scene.buttons:
            btn.draw(screen)

        # Подяка
        font_small = assets.get_font(FONT_SIZE_SMALL)
        thanks = font_small.render("Дякуємо за гру! 🎮", True, COLOR_TEXT_DIM)
        screen.blit(thanks, (SCREEN_WIDTH // 2 - thanks.get_width() // 2, SCREEN_HEIGHT - 40))