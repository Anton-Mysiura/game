"""
Спливаюче сповіщення про нове досягнення.
"""

import pygame
from ui.constants import *
from ui.assets import assets
from game.achievements import ACHIEVEMENTS


class AchievementNotification:
    """Спливаюче повідомлення про досягнення."""

    def __init__(self, achievement_id: str):
        self.achievement_id = achievement_id
        self.achievement = ACHIEVEMENTS[achievement_id]
        self.timer = 5.0  # Показувати 5 секунд
        self.y_offset = -150  # Починаємо зверху (поза екраном)
        self.target_y = 20
        self.animation_speed = 500

    def update(self, dt: float) -> bool:
        """Оновлення. Повертає False коли треба видалити."""
        # Анімація з'їзду
        if self.y_offset < self.target_y:
            self.y_offset += self.animation_speed * dt
            self.y_offset = min(self.y_offset, self.target_y)

        # Таймер
        self.timer -= dt

        # Анімація від'їзду
        if self.timer < 0.5:
            self.y_offset -= self.animation_speed * dt * 2

        return self.timer > 0

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # Панель
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, int(self.y_offset), 500, 100)
        panel_surface = pygame.Surface((500, 100), pygame.SRCALPHA)
        panel_surface.fill((40, 30, 20, 240))
        screen.blit(panel_surface, panel_rect)

        # Рамка
        pygame.draw.rect(screen, COLOR_GOLD, panel_rect, 3)

        # Іконка
        font_icon = assets.get_font(50)
        icon = font_icon.render(self.achievement.icon, True, COLOR_TEXT)
        screen.blit(icon, (panel_rect.x + 20, panel_rect.y + 25))

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_SMALL, bold=True)
        title = font_title.render("🏆 ДОСЯГНЕННЯ РОЗБЛОКОВАНО!", True, COLOR_GOLD)
        screen.blit(title, (panel_rect.x + 100, panel_rect.y + 15))

        # Назва
        font_name = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        name = font_name.render(self.achievement.name, True, COLOR_TEXT)
        screen.blit(name, (panel_rect.x + 100, panel_rect.y + 40))

        # Нагорода
        if self.achievement.reward_gold > 0:
            font_reward = assets.get_font(FONT_SIZE_SMALL)
            reward = font_reward.render(f"+{self.achievement.reward_gold} 🪙", True, COLOR_GOLD)
            screen.blit(reward, (panel_rect.x + 100, panel_rect.y + 70))