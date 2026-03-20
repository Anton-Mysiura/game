"""
Рендерер для TutorialScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/tutorial.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets


class TutorialRenderer(BaseRenderer):
    """
    Малює TutorialScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # Затемнений фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Панель
        self.scene.panel.draw(screen)

        # Заголовок
        if self.scene.current_tutorial < len(self.scene.tutorial_data):
            tut = self.scene.tutorial_data[self.scene.current_tutorial]
            font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
            title = font_title.render(f"📖 {tut['title']}", True, COLOR_GOLD)
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 220))

            # Лічильник сторінок
            pages_count = len(tut["pages"])
            font_counter = assets.get_font(FONT_SIZE_SMALL)
            counter_text = f"[{self.scene.current_page + 1}/{pages_count}]"
            counter = font_counter.render(counter_text, True, COLOR_TEXT_DIM)
            screen.blit(counter, (SCREEN_WIDTH // 2 - counter.get_width() // 2, SCREEN_HEIGHT // 2 - 190))

        # Текст
        self.scene.text_box.draw(screen)

        # Кнопки
        self.scene.next_button.draw(screen)
        self.scene.skip_button.draw(screen)

        # Підказка
        font_hint = assets.get_font(FONT_SIZE_SMALL)
        hint = font_hint.render("Enter/Пробіл — далі  |  ESC — пропустити", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 50))