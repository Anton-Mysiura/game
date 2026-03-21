"""
Рендерер для WandererScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/wanderer.py
"""
from game.data import MATERIALS
from game.data import BLUEPRINTS
from ui.constants import RARITY_COLORS
import pygame
from scenes.ui.base_renderer import BaseRenderer

import math
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from ui.icons import draw_icon


class WandererRenderer(BaseRenderer):
    """
    Малює WandererScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        self._draw_header(screen)
        self._draw_lots(screen)
        self._draw_info(screen)

        # Оновлюємо кнопку купити
        if self.scene._sel >= 0 and self.scene._sel < len(self.scene._w.lots):
            lot = self.scene._w.lots[self.scene._sel]
            if not lot.sold:
                can = self.scene.player.gold >= lot.price
                self.scene.buy_btn.text    = f"💰 Купити  {lot.price}🪙"
                self.scene.buy_btn.enabled = can
            else:
                self.scene.buy_btn.text    = "✓ Продано"
                self.scene.buy_btn.enabled = False
        else:
            self.scene.buy_btn.text    = "💰 Купити"
            self.scene.buy_btn.enabled = False

        self.scene.draw_buttons(screen)

        # Таймер зникнення
        self._draw_timer(screen)

    def _draw_header(self, screen):
        fh = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fs = assets.get_font(FONT_SIZE_SMALL)
        pulse = 0.85 + 0.15 * abs(math.sin(self.scene._anim * 1.2))
        col = tuple(int(c * pulse) for c in (255, 200, 80))
        screen.blit(fh.render("🧳 Мандрівний торговець", True, col), (CARDS_X, 50))
        screen.blit(fs.render("Рідкісні товари — лише сьогодні!", True, COLOR_TEXT_DIM),
                    (CARDS_X, 90))
        gold = fs.render(f"💰 {self.scene.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold, (SCREEN_WIDTH - gold.get_width() - 40, 55))

    def _draw_lots(self, screen):
        fn  = assets.get_font(FONT_SIZE_NORMAL)
        fsm = assets.get_font(FONT_SIZE_SMALL)
        mp  = pygame.mouse.get_pos()

        for i, lot in enumerate(self.scene._w.lots):
            r   = self.scene._card_rect(i)
            rar_col = RARITY_COLORS.get(lot.rarity, (180, 180, 180))

            # Фон карточки
            if lot.sold:
                bg_col = (15, 12, 8, 120)
            elif i == self.scene._sel:
                bg_col = (80, 65, 20, 220)
            elif r.collidepoint(mp):
                bg_col = (50, 45, 30, 200)
            else:
                bg_col = (20, 16, 10, 190)

            bg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            bg.fill(bg_col)
            pygame.draw.rect(bg, rar_col if not lot.sold else (60, 55, 45),
                             bg.get_rect(), 2, border_radius=8)
            screen.blit(bg, (r.x, r.y))

            if lot.sold:
                sold_s = fn.render("ПРОДАНО", True, (100, 90, 70))
                screen.blit(sold_s, (r.centerx - sold_s.get_width() // 2,
                                     r.centery - sold_s.get_height() // 2))
                continue

            # Іконка
            draw_icon(screen, lot.item_id, lot.icon, r.x + 10, r.y + 10, size=32)

            # Назва
            name = lot.name + (f" ×{lot.qty}" if lot.qty > 1 else "")
            screen.blit(fn.render(name, True, rar_col), (r.x + 48, r.y + 10))

            # Рідкість
            rar_ua = {"common":"Звичайний","uncommon":"Незвичайний",
                      "rare":"Рідкісний","epic":"Епічний","legendary":"Легендарний"}
            screen.blit(fsm.render(rar_ua.get(lot.rarity, ""), True, rar_col),
                        (r.x + 48, r.y + 34))

            # Ціна
            price_col = COLOR_GOLD if self.scene.player.gold >= lot.price else COLOR_ERROR
            p_s = fn.render(f"{lot.price}🪙", True, price_col)
            screen.blit(p_s, (r.right - p_s.get_width() - 10, r.bottom - p_s.get_height() - 8))

    def _draw_info(self, screen):
        if self.scene._sel < 0 or self.scene._sel >= len(self.scene._w.lots):
            return
        lot = self.scene._w.lots[self.scene._sel]
        if lot.sold:
            return
        fsm = assets.get_font(FONT_SIZE_SMALL)
        ix  = CARDS_X + 2 * (CARD_W + CARD_PAD) + 20
        iy  = CARDS_Y

        if lot.item_type == "blueprint":
            bp = BLUEPRINTS.get(lot.bp_id)
            if bp:
                lines = [f"📜 Кресленик: {bp.result_name}", f"Рецепт:"]
                for mat_id, qty in bp.recipe.items():
                    mat  = MATERIALS.get(mat_id)
                    have = self.scene.player.materials.get(mat_id, 0)
                    clr_m = (100,220,100) if have >= qty else COLOR_ERROR
                    lines.append(f"  {mat.icon if mat else '?'} {mat.name if mat else mat_id} {have}/{qty}")
                for line in lines:
                    s = fsm.render(line, True, COLOR_TEXT)
                    screen.blit(s, (ix, iy)); iy += 20

    def _draw_timer(self, screen):
        fsm  = assets.get_font(FONT_SIZE_SMALL)
        left = self.scene._w.time_left
        m, s = divmod(left, 60)
        pulse = 0.7 + 0.3 * abs(math.sin(self.scene._anim * 2))
        col   = (220, 80, 80) if left < 120 else (180, 160, 100)
        col   = tuple(int(c * pulse) for c in col)
        t = fsm.render(f"⏱ Зникне через {m:02d}:{s:02d}", True, col)
        screen.blit(t, (SCREEN_WIDTH - t.get_width() - 40, 90))