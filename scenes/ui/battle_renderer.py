"""
Рендерер для BattleScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/battle.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

import random
from ui.components import Button, Panel, ProgressBar, TextBox
from ui.constants import *
from ui.assets import assets


class BattleRenderer(BaseRenderer):
    """
    Малює BattleScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # Фон
        super().draw(screen)

        # Панель бою
        self.scene.battle_panel.draw(screen)

        # Спрайти персонажів
        player_sprite = assets.load_texture("characters", "player_attack", (128, 128))
        enemy_sprite = assets.load_texture("characters", self.scene.enemy.sprite_name, (128, 128))

        screen.blit(player_sprite, (200, 250))
        screen.blit(enemy_sprite, (SCREEN_WIDTH - 328, 250))

        # Імена та HP
        font = assets.get_font(FONT_SIZE_MEDIUM, bold=True)

        # Гравець
        player_name = font.render(self.scene.player.name, True, COLOR_TEXT)
        screen.blit(player_name, (150, 390))
        self.scene.player_hp_bar.draw(screen, self.scene.player.hp, self.scene.player.max_hp)

        # Ворог
        enemy_name = font.render(self.scene.enemy.name, True, COLOR_TEXT)
        screen.blit(enemy_name, (SCREEN_WIDTH - 350, 390))
        self.scene.enemy_hp_bar.draw(screen, self.scene.enemy.hp, self.scene.enemy.max_hp)

        # Лог подій
        self.scene.log_box.draw(screen, COLOR_TEXT)

        # Кнопки (якщо бій не закінчився)
        if not self.scene.battle_over:
            self.scene.draw_buttons(screen)
        else:
            # Повідомлення про завершення
            font_end = assets.get_font(FONT_SIZE_LARGE, bold=True)
            if self.scene.player_won:
                end_text = font_end.render("ПЕРЕМОГА!", True, COLOR_SUCCESS)
            else:
                end_text = font_end.render("ПОРАЗКА...", True, COLOR_ERROR)

            screen.blit(end_text, (SCREEN_WIDTH // 2 - end_text.get_width() // 2, 550))