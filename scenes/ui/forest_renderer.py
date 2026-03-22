"""
Рендерер для ForestScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/forest.py
"""
from game.enemy_scaling import level_color
from game.data import MATERIALS
import pygame
from scenes.ui.base_renderer import BaseRenderer

import random
from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets


class ForestRenderer(BaseRenderer):
    """
    Малює ForestScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)

        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("🌲 Темний Ліс", True, COLOR_GOLD)
        screen.blit(font_title.render("🌲 Темний Ліс", True, (0, 0, 0)),
                    (SCREEN_WIDTH // 2 - title.get_width() // 2 + 2, 52))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # Лічильник вбивств у free_roam
        if self.scene.stage == "free_roam":
            font_s = assets.get_font(FONT_SIZE_SMALL)
            kills  = font_s.render(
                f"⚔ Вбито: {self.scene.player.enemies_killed}   "
                f"👺 Гоблінів: {self.scene.player.goblins_killed}   "
                f"👹 Орків: {self.scene.player.orcs_killed}",
                True, COLOR_TEXT_DIM)
            screen.blit(kills, (40, 96))

            # Показуємо інформацію про поточного ворога
            if self.scene._next_enemy:
                self._draw_enemy_card(screen)

        self.scene.dialog_panel.draw(screen)
        self.scene.text_box.draw(screen)
        self.scene.draw_buttons(screen)

        if self.scene._confirm_callback is not None:
            self._draw_low_hp_confirm(screen)

    def _draw_enemy_card(self, screen):
        """Міні-картка ворога у правому куті."""
        enemy = self.scene._next_enemy
        if not enemy:
            return

        cx = SCREEN_WIDTH - 210
        cy = 110
        cw, ch = 190, 100

        surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        surf.fill((18, 14, 10, 210))
        lclr = level_color(enemy.level, self.scene.player.level)
        pygame.draw.rect(surf, lclr, surf.get_rect(), 2, border_radius=8)
        screen.blit(surf, (cx, cy))

        font  = assets.get_font(FONT_SIZE_SMALL)
        font_h = assets.get_font(FONT_SIZE_NORMAL, bold=True)

        screen.blit(font_h.render(enemy.name, True, COLOR_TEXT), (cx + 8, cy + 6))
        screen.blit(font.render(f"Рівень {enemy.level}", True, lclr), (cx + 8, cy + 26))
        screen.blit(font.render(f"❤ {enemy.hp}   ⚔ {enemy.attack}   🛡 {enemy.defense}",
                                True, COLOR_TEXT_DIM), (cx + 8, cy + 46))
        # Очікуваний лут
        if enemy.loot_materials:
            mats = [k for k, v in enemy.loot_materials.items() if v > 0]
            icons = "".join(MATERIALS[m].icon for m in mats[:4] if m in MATERIALS)
            screen.blit(font.render(f"Лут: {icons}", True, COLOR_GOLD), (cx + 8, cy + 66))

    def _draw_low_hp_confirm(self, screen: pygame.Surface):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(cx - 220, cy - 110, 440, 210)
        pygame.draw.rect(screen, (45, 20, 20), panel_rect, border_radius=14)
        pygame.draw.rect(screen, COLOR_ERROR, panel_rect, 2, border_radius=14)
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        warn = font_title.render("⚠ Небезпечно низьке HP!", True, COLOR_ERROR)
        screen.blit(warn, (cx - warn.get_width() // 2, cy - 95))
        font = assets.get_font(FONT_SIZE_NORMAL)
        hp_text = font.render(
            f"У тебе лише {self.scene.player.hp} / {self.scene.player.max_hp} HP.",
            True, COLOR_TEXT)
        screen.blit(hp_text, (cx - hp_text.get_width() // 2, cy - 48))
        question = font.render("Все одно йти в бій?", True, COLOR_TEXT_DIM)
        screen.blit(question, (cx - question.get_width() // 2, cy - 18))
        mouse_pos = pygame.mouse.get_pos()
        yes_rect = pygame.Rect(cx - 160, cy + 60, 140, 44)
        no_rect  = pygame.Rect(cx + 20,  cy + 60, 140, 44)
        yes_color = (160, 40, 40) if yes_rect.collidepoint(mouse_pos) else (120, 30, 30)
        no_color  = COLOR_BTN_HOVER if no_rect.collidepoint(mouse_pos) else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, yes_color, yes_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_ERROR, yes_rect, 2, border_radius=10)
        pygame.draw.rect(screen, no_color,  no_rect,  border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, no_rect,  2, border_radius=10)
        yes_lbl = font.render("⚔ Так, вперед!", True, COLOR_TEXT)
        no_lbl  = font.render("↩ Назад",        True, COLOR_TEXT)
        screen.blit(yes_lbl, (yes_rect.centerx - yes_lbl.get_width() // 2,
                               yes_rect.centery - yes_lbl.get_height() // 2))
        screen.blit(no_lbl,  (no_rect.centerx  - no_lbl.get_width()  // 2,
                               no_rect.centery  - no_lbl.get_height()  // 2))
