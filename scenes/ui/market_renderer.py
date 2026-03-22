"""
Рендерер для MarketScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/market.py
"""
from game.market import REFRESH_SEC, fmt_time_market, RARITY_UA, RARITY_COLOR
from scenes.core.market import CARD_H, CARD_W, GRID_Y
from game.data import RARITY_COLOR
from game.mutations import MUTATIONS
import pygame
from scenes.ui.base_renderer import BaseRenderer

import math
import logging
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from ui.icons import draw_icon, get_icon_surf


class MarketRenderer(BaseRenderer):
    """
    Малює MarketScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        self.scene.main_panel.draw(screen)

        self._draw_header(screen)
        self._draw_timer(screen)
        self._draw_lots(screen)
        self._draw_bottom_bar(screen)
        self._draw_msg(screen)

        self.scene.buy_btn.draw(screen)
        self.scene.refresh_btn.draw(screen)
        self.scene.exit_btn.draw(screen)

    # ── Шапка ─────────────────────────────────────────────────────

    def _draw_header(self, screen):
        font  = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = font.render("🏴 Чорний ринок", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 32))

        font_g = assets.get_font(FONT_SIZE_NORMAL)
        gold   = font_g.render(f"💰 {self.scene.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold, (40, 38))

    def _draw_timer(self, screen):
        """Таймер до наступного оновлення — правий верхній кут."""
        t    = self.scene.player.market.time_to_refresh()
        pct  = 1.0 - t / REFRESH_SEC

        font = assets.get_font(FONT_SIZE_SMALL)
        lbl  = font.render("Оновлення через:", True, COLOR_TEXT_DIM)
        screen.blit(lbl, (SCREEN_WIDTH - 240, 30))

        time_str = fmt_time_market(t)
        clr = (100, 220, 100) if t < 60 else (180, 180, 200)
        t_surf = assets.get_font(FONT_SIZE_NORMAL, bold=True).render(time_str, True, clr)
        screen.blit(t_surf, (SCREEN_WIDTH - 240, 48))

        # Мала прогрес-смужка
        bar_w = 200
        bx    = SCREEN_WIDTH - 240
        by    = 70
        pygame.draw.rect(screen, (40, 38, 30), (bx, by, bar_w, 6), border_radius=3)
        fill  = int(bar_w * pct)
        if fill > 0:
            pygame.draw.rect(screen, clr, (bx, by, fill, 6), border_radius=3)

    # ── Картки лотів ──────────────────────────────────────────────

    def _draw_lots(self, screen):
        lots = self.scene.player.market.lots
        for i, lot in enumerate(lots):
            self._draw_card(screen, i, lot)

    def _draw_card(self, screen, idx: int, lot):

        r        = self.scene._card_rect(idx)
        selected = idx == self.scene._sel
        rar_clr  = RARITY_COLOR.get(lot.rarity, (180, 180, 180))
        mp       = pygame.mouse.get_pos()
        hovered  = r.collidepoint(mp) and not lot.sold

        # ── Фон картки ────────────────────────────────────────────
        card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        if lot.sold:
            card_surf.fill((18, 16, 14, 160))
        elif selected:
            card_surf.fill((50, 42, 20, 230))
        elif hovered:
            card_surf.fill((35, 30, 18, 220))
        else:
            card_surf.fill((22, 18, 14, 210))
        screen.blit(card_surf, r.topleft)

        # Рамка — колір рідкісності (анімована якщо вибрана)
        border_w = 2
        border_clr = rar_clr
        if selected:
            pulse = 0.5 + 0.5 * math.sin(self.scene._anim_t * 4)
            border_clr = tuple(int(c * (0.7 + 0.3 * pulse)) for c in rar_clr)
            border_w = 3
        pygame.draw.rect(screen, border_clr if not lot.sold else (50, 48, 44),
                         r, border_w, border_radius=8)

        if lot.sold:
            # Плашка "Продано"
            sold_font = assets.get_font(FONT_SIZE_LARGE, bold=True)
            s = sold_font.render("ПРОДАНО", True, (120, 60, 60))
            s.set_alpha(180)
            screen.blit(s, (r.x + CARD_W // 2 - s.get_width() // 2,
                            r.y + CARD_H // 2 - s.get_height() // 2))
            return

        px, py = r.x + 12, r.y + 10
        font_h  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font    = assets.get_font(FONT_SIZE_SMALL)

        # ── Рідкісність ───────────────────────────────────────────
        rar_txt = font.render(
            f"◆ {RARITY_UA.get(lot.rarity, lot.rarity).upper()}", True, rar_clr)
        screen.blit(rar_txt, (px, py)); py += 18

        # ── Іконка і назва ────────────────────────────────────────
        icon, name, stat_lines, mut_info = self.scene._lot_display(lot)

        draw_icon(screen, lot.item_id, icon, px, py, size=30)

        name_x = px + 38
        # Колір назви — якщо є мутація, беремо її колір
        name_clr = COLOR_TEXT
        if lot.item_data.get("mutation"):
            mut = MUTATIONS.get(lot.item_data["mutation"])
            if mut:
                name_clr = mut.color
        name_surf = font_h.render(name[:26], True, name_clr)
        screen.blit(name_surf, (name_x, py + 2))
        py += 36

        # ── Характеристики ────────────────────────────────────────
        for line, clr in stat_lines:
            screen.blit(font.render(line, True, clr), (px, py)); py += 17

        # ── Мутація ───────────────────────────────────────────────
        if mut_info:
            mut_id, mut_rar = mut_info
            mut = MUTATIONS.get(mut_id)
            if mut:
                m_clr = RARITY_COLOR.get(mut.rarity, COLOR_TEXT)
                screen.blit(font.render(
                    f"✦ {mut.icon} {mut.name}: {mut.desc}", True, m_clr),
                    (px, py)); py += 17

        # ── Ціна ──────────────────────────────────────────────────
        price_clr = COLOR_GOLD if self.scene.player.gold >= lot.price else (220, 80, 80)
        price_surf = assets.get_font(FONT_SIZE_NORMAL, bold=True).render(
            f"💰 {lot.price}", True, price_clr)
        screen.blit(price_surf, (r.right - price_surf.get_width() - 12,
                                  r.bottom - price_surf.get_height() - 10))

    def _draw_bottom_bar(self, screen):
        if self.scene._sel < 0 or self.scene._sel >= len(self.scene.player.market.lots):
            return
        lot = self.scene.player.market.lots[self.scene._sel]
        if lot.sold:
            return
        font = assets.get_font(FONT_SIZE_SMALL)
        can  = self.scene.player.gold >= lot.price
        hint = f"Натисни «Купити» — {lot.price} золота" if can \
               else f"Не вистачає {lot.price - self.scene.player.gold} золота"
        clr  = (160, 220, 160) if can else (220, 100, 100)
        s    = font.render(hint, True, clr)
        screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, SCREEN_HEIGHT - 100))

    def _draw_msg(self, screen):
        if self.scene._msg_t <= 0:
            return
        alpha = min(255, int(self.scene._msg_t * 120))
        clr   = (100, 220, 100) if self.scene._msg_ok else (220, 100, 100)
        font  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        s     = font.render(self.scene._msg, True, clr)
        s.set_alpha(alpha)
        screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, GRID_Y - 30))