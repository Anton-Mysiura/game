"""
Рендерер для MainMenuScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/main_menu.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

import random
from datetime import datetime
from ui.components import Button, Panel, TextBox, ScrollableList
from ui.constants import *
from ui.assets import assets


class MainMenuRenderer(BaseRenderer):
    """
    Малює MainMenuScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        super().draw(screen)

        # Персонажі завжди видимі (під панелями)
        self._draw_menu_characters(screen)

        if self.scene.state == "main":
            self._draw_main_menu(screen)
        elif self.scene.state == "load":
            self._draw_load_menu(screen)
        elif self.scene.state == "new_game":
            self._draw_new_game_menu(screen)
        elif self.scene.state == "overwrite":
            self._draw_overwrite_menu(screen)
        elif self.scene.state == "name_input":
            self._draw_name_input(screen)

    def _draw_menu_characters(self, screen: pygame.Surface):
        """Малює всіх 4 персонажів по боках меню."""
        import math
        for i, c in enumerate(self.scene._chars):
            if not c["ctrl"]:
                continue
            frame = c["ctrl"].get_current_frame()
            if not frame:
                continue

            # Кожен персонаж гойдається з невеликим зсувом фази
            float_y = math.sin(self.scene._float_t * 1.8 + i * 1.1) * 4

            if c["flip"]:
                frame = pygame.transform.flip(frame, True, False)

            char_x = c["x"]
            char_y = int(SCREEN_HEIGHT - 55 - frame.get_height() + float_y)

            # Тінь
            sx = char_x + frame.get_width() // 2 - self.scene._shadow.get_width() // 2
            screen.blit(self.scene._shadow, (sx, SCREEN_HEIGHT - 48))

            # Персонаж
            screen.blit(frame, (char_x, char_y))

    def _draw_main_menu(self, screen):
        """Малює головне меню."""
        # Заголовок
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("⚔ Темне Королівство ⚔", True, COLOR_GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title, title_rect)

        # Кнопки
        for btn in self.scene.buttons:
            btn.draw(screen)

    def _draw_load_menu(self, screen):
        """Малює меню завантаження."""
        # Панель
        panel = Panel(SCREEN_WIDTH // 2 - 350, 100, 700, 550, alpha=True)
        panel.draw(screen)

        # Заголовок
        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = font.render("Завантажити гру", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        # Список збережень
        font_item = assets.get_font(FONT_SIZE_NORMAL)
        y = 200

        for i, save in enumerate(self.scene.saves_list):
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, y, 600, 60)

            # Фон
            color = COLOR_BTN_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_PANEL
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(screen, COLOR_GOLD, btn_rect, 2)

            # Текст
            if save["valid"]:
                text = f"{save['filename']}  |  {save['player_name']}  Рівень {save['level']}  |  {save['modified'].strftime('%Y-%m-%d %H:%M')}"
            else:
                text = f"{save['filename']}  |  ПОШКОДЖЕНО"

            text_surf = font_item.render(text, True, COLOR_TEXT if save["valid"] else COLOR_ERROR)
            screen.blit(text_surf, (btn_rect.x + 20, btn_rect.y + 20))

            y += 70

        # Кнопка "Назад"
        for btn in self.scene.load_buttons:
            btn.draw(screen)

    def _draw_new_game_menu(self, screen):
        """Малює меню нової гри."""
        panel = Panel(SCREEN_WIDTH // 2 - 250, 150, 500, 400, alpha=True)
        panel.draw(screen)

        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = font.render("Нова гра", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))

        # Кнопки
        for btn in self.scene.new_game_buttons:
            btn.draw(screen)

    def _draw_overwrite_menu(self, screen):
        """Малює меню перезапису."""
        # Панель
        panel = Panel(SCREEN_WIDTH // 2 - 350, 100, 700, 550, alpha=True)
        panel.draw(screen)

        # Заголовок
        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = font.render("Вибери збереження для перезапису", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        # Список
        font_item = assets.get_font(FONT_SIZE_NORMAL)
        y = 200

        for i, save in enumerate(self.scene.saves_list):
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, y, 600, 60)

            color = COLOR_BTN_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_PANEL
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(screen, COLOR_GOLD, btn_rect, 2)

            text = f"{save['filename']}  |  {save['player_name']}  Рівень {save['level']}"
            text_surf = font_item.render(text, True, COLOR_TEXT)
            screen.blit(text_surf, (btn_rect.x + 20, btn_rect.y + 20))

            y += 70

        # Кнопка назад
        for btn in self.scene.overwrite_buttons:
            btn.draw(screen)

    def _draw_name_input(self, screen):
        """Малює екран введення імені."""
        panel = Panel(SCREEN_WIDTH // 2 - 300, 200, 600, 300, alpha=True)
        panel.draw(screen)

        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = font.render("Введи ім'я героя", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 230))

        # Поле вводу
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 300, 400, 50)
        pygame.draw.rect(screen, COLOR_PANEL, input_rect)
        pygame.draw.rect(screen, COLOR_GOLD, input_rect, 3)

        font_input = assets.get_font(FONT_SIZE_MEDIUM)
        input_text = font_input.render(self.scene.name_input + "_", True, COLOR_TEXT)
        screen.blit(input_text, (input_rect.x + 10, input_rect.y + 12))

        # Підказка
        font_hint = assets.get_font(FONT_SIZE_SMALL)
        hint = font_hint.render("Натисни Enter для початку", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 380))

        # Інфо про збереження
        info = font_hint.render(f"Збереження: {self.scene.save_name_input}", True, COLOR_TEXT_DIM)
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 420))