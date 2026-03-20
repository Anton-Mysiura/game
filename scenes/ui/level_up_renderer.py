"""
Рендерер для LevelUpScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/level_up.py
"""
from ui.constants import RARITY_COLORS
import pygame
from scenes.ui.base_renderer import BaseRenderer
from ui.constants import *

from ui.assets import assets


class LevelUpRenderer(BaseRenderer):
    """
    Малює LevelUpScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        # Темний фон
        screen.fill(COLOR_BG)

        # Затемнення
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(180, int(self.scene.alpha * 0.7))))
        screen.blit(overlay, (0, 0))

        font_title  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_sub    = assets.get_font(FONT_SIZE_MEDIUM)
        font_level  = assets.get_font(FONT_SIZE_LARGE, bold=True)

        # Заголовок
        title = font_title.render("⬆ ПІДВИЩЕННЯ РІВНЯ!", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        level_text = font_level.render(
            f"Рівень {self.player.level}  —  Вибери бонус", True, COLOR_TEXT
        )
        screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 130))

        if self.scene._is_first_perk:
            import math
            pulse = 0.7 + 0.3 * abs(math.sin(self.scene._anim_t * 2.0))
            warn_col = tuple(int(c * pulse) for c in (220, 160, 60))
            warn = font_sub.render("Хм... негусто. Але вибирати треба.", True, warn_col)
            screen.blit(warn, (SCREEN_WIDTH // 2 - warn.get_width() // 2, 165))
            hint = assets.get_font(FONT_SIZE_SMALL).render(
                "Не хвилюйся — потім зможеш змінити на кращу.", True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 198))
        else:
            sub = font_sub.render("Клікни на картку щоб вибрати", True, COLOR_TEXT_DIM)
            screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 170))

        # Картки
        for i, (perk, rect) in enumerate(zip(self.scene.perks, self.scene.card_rects)):
            self._draw_card(screen, perk, rect, hovered=(i == self.scene.hovered))

    def _draw_card(self, screen, perk, rect, hovered: bool):
        rarity_color = RARITY_COLORS[perk.rarity]

        # Підсвічування при наведенні
        if hovered:
            glow = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
            glow.fill((*rarity_color, 60))
            screen.blit(glow, (rect.x - 6, rect.y - 6))
            draw_rect = rect.inflate(6, 6)
        else:
            draw_rect = rect

        # Фон картки
        bg_color = (30, 25, 40) if not hovered else (40, 35, 55)
        pygame.draw.rect(screen, bg_color, draw_rect, border_radius=16)

        # Кольорова смужка зверху (рідкість)
        stripe = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.w, 8)
        pygame.draw.rect(screen, rarity_color, stripe,
                         border_radius=16 if not hovered else 16)

        # Рамка
        border_width = 3 if hovered else 2
        pygame.draw.rect(screen, rarity_color, draw_rect,
                         border_width, border_radius=16)

        cx = draw_rect.centerx

        # Іконка
        font_icon = assets.get_font(64)
        icon_surf = font_icon.render(perk.icon, True, COLOR_TEXT)
        screen.blit(icon_surf, (cx - icon_surf.get_width() // 2, draw_rect.y + 30))

        # Рідкість
        font_rarity = assets.get_font(FONT_SIZE_SMALL, bold=True)
        rarity_surf = font_rarity.render(
            RARITY_NAMES[perk.rarity].upper(), True, rarity_color
        )
        screen.blit(rarity_surf, (cx - rarity_surf.get_width() // 2, draw_rect.y + 110))

        # Назва
        font_name = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        name_surf = font_name.render(perk.name, True, COLOR_TEXT)
        screen.blit(name_surf, (cx - name_surf.get_width() // 2, draw_rect.y + 140))

        # Опис (з переносами)
        font_desc = assets.get_font(FONT_SIZE_SMALL)
        self._draw_wrapped(screen, font_desc, perk.description,
                           COLOR_TEXT_DIM, draw_rect.x + 16,
                           draw_rect.y + 180, draw_rect.w - 32)

    def _draw_wrapped(self, screen, font, text: str, color,
                      x: int, y: int, max_width: int):
        """Малює текст з переносом рядків."""
        words = text.split()
        line = ""
        line_y = y

        for word in words:
            test = f"{line} {word}".strip()
            if font.size(test)[0] <= max_width:
                line = test
            else:
                if line:
                    surf = font.render(line, True, color)
                    screen.blit(surf, (x + max_width // 2 - surf.get_width() // 2, line_y))
                    line_y += font.get_height() + 4
                line = word

        if line:
            surf = font.render(line, True, color)
            screen.blit(surf, (x + max_width // 2 - surf.get_width() // 2, line_y))