"""
Рендерер для TowerScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/tower.py
"""
from game.enemy_scaling import level_color
from game.data import MATERIALS
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets


class TowerRenderer(BaseRenderer):
    """
    Малює TowerScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        if self.scene._free_roam and self.scene._next_enemy:
            self._draw_enemy_mini(screen)

    def _draw_enemy_mini(self, screen):
        enemy = self.scene._next_enemy
        cx, cy, cw, ch = SCREEN_WIDTH - 210, 110, 190, 90
        surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        surf.fill((18, 14, 10, 210))
        lclr = level_color(enemy.level, self.scene.player.level)
        pygame.draw.rect(surf, lclr, surf.get_rect(), 2, border_radius=8)
        screen.blit(surf, (cx, cy))
        font  = assets.get_font(FONT_SIZE_SMALL)
        font_h = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        screen.blit(font_h.render(enemy.name, True, COLOR_TEXT), (cx + 8, cy + 6))
        screen.blit(font.render(f"Рів.{enemy.level}  ❤{enemy.hp}  ⚔{enemy.attack}  🛡{enemy.defense}",
                                True, COLOR_TEXT_DIM), (cx + 8, cy + 30))
        if enemy.loot_materials:
            mats = [k for k, v in enemy.loot_materials.items() if v > 0]
            icons = "".join(MATERIALS[m].icon for m in mats[:4] if m in MATERIALS)
            screen.blit(font.render(f"Лут: {icons}", True, COLOR_GOLD), (cx + 8, cy + 54))