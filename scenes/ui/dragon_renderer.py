"""
Рендерер для DragonScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/dragon.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets


class DragonRenderer(BaseRenderer):
    """
    Малює DragonScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # Фон
        super().draw(screen)

        # Затемнення
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 0, 0, 100))  # Червонуватий відтінок
        screen.blit(overlay, (0, 0))

        # Заголовок
        font_title = assets.get_font(72, bold=True)
        title = font_title.render("🐉 ЛІГВО ДРАКОНА", True, COLOR_ERROR)
        title_glow = font_title.render("🐉 ЛІГВО ДРАКОНА", True, (255, 100, 0))

        # Ефект свічення
        screen.blit(title_glow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 2, 52))
        screen.blit(title_glow, (SCREEN_WIDTH // 2 - title.get_width() // 2 - 2, 48))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # Спрайт дракона (великий)
        dragon_sprite = assets.load_texture("characters", "dragon", (256, 256))
        screen.blit(dragon_sprite, (SCREEN_WIDTH // 2 - 128, 150))

        # Діалог
        self.scene.dialog_panel.draw(screen)
        self.scene.text_box.draw(screen)

        # Кнопки
        self.scene.draw_buttons(screen)