"""
Рендерер для ForestEventScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/forest_event.py
"""
from scenes.core.forest_event import PANEL_H, PANEL_W, PANEL_X, PANEL_Y
from game.data import MATERIALS
import pygame
from scenes.ui.base_renderer import BaseRenderer
from ui.constants import *

from ui.assets import assets


class ForestEventRenderer(BaseRenderer):
    """
    Малює ForestEventScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        # Темний оверлей
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(180, int(self.scene.alpha * 0.7))))
        screen.blit(overlay, (0, 0))

        # Панель
        panel = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panel.fill((22, 28, 22, 230))
        pygame.draw.rect(panel, (60, 100, 60), (0, 0, PANEL_W, PANEL_H), 2, border_radius=16)
        screen.blit(panel, (PANEL_X, PANEL_Y))

        if self.scene.state == "choice":
            self._draw_choice(screen)
        else:
            self._draw_result(screen)

    def _draw_choice(self, screen):
        ev = self.scene.event
        cx = SCREEN_WIDTH // 2

        # Іконка
        font_icon = assets.get_font(72)
        icon_s = font_icon.render(ev.icon, True, COLOR_TEXT)
        screen.blit(icon_s, (cx - icon_s.get_width() // 2, PANEL_Y + 18))

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title_s = font_title.render(ev.title, True, COLOR_GOLD)
        screen.blit(title_s, (cx - title_s.get_width() // 2, PANEL_Y + 95))

        # Опис (з переносом)
        font_desc = assets.get_font(FONT_SIZE_NORMAL)
        self._draw_wrapped(screen, font_desc, ev.description,
                           COLOR_TEXT_DIM, PANEL_X + 40, PANEL_Y + 140, PANEL_W - 80)

        # Кнопки вибору
        font_btn = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        for i, (rect, choice) in enumerate(zip(self.scene._choice_rects, ev.choices)):
            hov = i == self.scene._hovered
            bg  = (50, 80, 50) if hov else (30, 48, 30)
            border = COLOR_GOLD if hov else (70, 110, 70)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, border, rect, 2, border_radius=10)

            label_s = font_btn.render(choice.label, True,
                                      COLOR_GOLD if hov else COLOR_TEXT)
            screen.blit(label_s,
                        (rect.centerx - label_s.get_width() // 2,
                         rect.centery - label_s.get_height() // 2))

    def _draw_result(self, screen):
        cx = SCREEN_WIDTH // 2
        res = self.scene.result

        # Іконка результату
        icon = "✅" if res.hp_delta >= 0 and res.gold_delta >= 0 else (
               "⚔" if res.enemy else "❗")
        font_icon = assets.get_font(64)
        icon_s = font_icon.render(icon, True, COLOR_TEXT)
        screen.blit(icon_s, (cx - icon_s.get_width() // 2, PANEL_Y + 24))

        # Текст результату
        font_desc = assets.get_font(FONT_SIZE_NORMAL)
        self._draw_wrapped(screen, font_desc, res.text,
                           COLOR_TEXT, PANEL_X + 40, PANEL_Y + 105, PANEL_W - 80)

        # Здобутки / втрати
        loot_y = PANEL_Y + 220
        font_loot = assets.get_font(FONT_SIZE_NORMAL, bold=True)

        if res.gold_delta != 0:
            col  = COLOR_GOLD if res.gold_delta > 0 else (220, 80, 80)
            sign = "+" if res.gold_delta > 0 else ""
            s = font_loot.render(f"{sign}{res.gold_delta} 🪙", True, col)
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        if res.hp_delta != 0:
            col  = (80, 220, 80) if res.hp_delta > 0 else (220, 80, 80)
            sign = "+" if res.hp_delta > 0 else ""
            s = font_loot.render(f"{sign}{res.hp_delta} ❤", True, col)
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        for item in res.items_gained:
            s = font_loot.render(f"+ {item.name}", True, (100, 220, 255))
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        for mat_id, qty in res.materials_gained.items():
            mat = MATERIALS.get(mat_id)
            name = mat.name if mat else mat_id
            s = font_loot.render(f"+ {name} ×{qty}", True, (180, 220, 130))
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        if res.enemy:
            s = font_loot.render(f"⚔ Почнеться бій!", True, (220, 80, 80))
            screen.blit(s, (cx - s.get_width() // 2, loot_y))

        # Кнопка продовжити
        hov = pygame.mouse.get_pos()
        btn_col = (60, 100, 60) if self.scene._continue_rect.collidepoint(hov) else (40, 70, 40)
        pygame.draw.rect(screen, btn_col, self.scene._continue_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, self.scene._continue_rect, 2, border_radius=10)
        label = "⚔ До бою!" if res.enemy else "Продовжити →"
        font_btn = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        s = font_btn.render(label, True, COLOR_GOLD)
        screen.blit(s, (self.scene._continue_rect.centerx - s.get_width() // 2,
                        self.scene._continue_rect.centery - s.get_height() // 2))

        # Підказка
        font_hint = assets.get_font(FONT_SIZE_SMALL)
        hint = font_hint.render("Enter / Пробіл щоб продовжити", True, COLOR_TEXT_DIM)
        screen.blit(hint, (cx - hint.get_width() // 2, PANEL_Y + PANEL_H - 22))

    def _draw_wrapped(self, screen, font, text, color, x, y, max_w):
        """Малює текст з переносом рядків (підтримує \n)."""
        line_h = font.get_height() + 4
        for paragraph in text.split("\n"):
            words = paragraph.split()
            line  = ""
            for word in words:
                test = (line + " " + word).strip()
                if font.size(test)[0] <= max_w:
                    line = test
                else:
                    if line:
                        s = font.render(line, True, color)
                        screen.blit(s, (x, y))
                        y += line_h
                    line = word
            if line:
                s = font.render(line, True, color)
                screen.blit(s, (x, y))
                y += line_h
        return y