"""
Сцена торговця-мандрівника.
"""
from __future__ import annotations
import math
import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from ui.icons import draw_icon
from game.save_manager import autosave
from game.wanderer import WandererState, RARITY_COLORS

CARD_W  = 240
CARD_H  = 120
CARD_PAD = 16
CARDS_X = 60
CARDS_Y = 150


class WandererScene(SceneWithBackground, SceneWithButtons):
    """Торговець-мандрівник."""

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "village")
        SceneWithButtons.__init__(self, game)

        if not hasattr(self.player, "wanderer"):
            self.player.wanderer = WandererState()

        self._w = self.player.wanderer
        self._w.visited = True
        self._sel   = -1
        self._msg   = ""
        self._msg_t = 0.0
        self._anim  = 0.0

        self.exit_btn = Button(30, SCREEN_HEIGHT - 70, 180, 46,
                               "← Назад", lambda: self.game.change_scene("village"))
        self.buy_btn  = Button(CARDS_X, SCREEN_HEIGHT - 70, 220, 46,
                               "💰 Купити", self._buy)
        self.buttons  = [self.exit_btn, self.buy_btn]

    def _buy(self):
        if self._sel < 0:
            return
        ok, msg = self._w.buy(self._sel, self.player)
        self._msg   = msg
        self._msg_t = 2.5
        from ui.notifications import notify
        if ok:
            from game.reputation import add_reputation, REP_SHOP_SPEND_10
            lot = self._w.lots[self._sel]
            add_reputation(self.player, lot.price // 10 * REP_SHOP_SPEND_10)
            notify(f"🛒 Куплено у мандрівника: {lot.icon} {lot.name}", kind="item", duration=2.5)
            autosave(self.player)
            self._sel = -1
        else:
            notify(msg, kind="error", duration=2.0)

    def update(self, dt: float):
        super().update(dt)
        self._anim  += dt
        if self._msg_t > 0:
            self._msg_t -= dt

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            for i, lot in enumerate(self._w.lots):
                r = self._card_rect(i)
                if r.collidepoint(mp):
                    self._sel = i if self._sel != i else -1
                    break

    def _card_rect(self, i: int) -> pygame.Rect:
        col = i % 2
        row = i // 2
        x = CARDS_X + col * (CARD_W + CARD_PAD)
        y = CARDS_Y + row * (CARD_H + CARD_PAD)
        return pygame.Rect(x, y, CARD_W, CARD_H)

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        self._draw_header(screen)
        self._draw_lots(screen)
        self._draw_info(screen)

        # Оновлюємо кнопку купити
        if self._sel >= 0 and self._sel < len(self._w.lots):
            lot = self._w.lots[self._sel]
            if not lot.sold:
                can = self.player.gold >= lot.price
                self.buy_btn.text    = f"💰 Купити  {lot.price}🪙"
                self.buy_btn.enabled = can
            else:
                self.buy_btn.text    = "✓ Продано"
                self.buy_btn.enabled = False
        else:
            self.buy_btn.text    = "💰 Купити"
            self.buy_btn.enabled = False

        self.draw_buttons(screen)

        # Таймер зникнення
        self._draw_timer(screen)

    def _draw_header(self, screen):
        fh = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fs = assets.get_font(FONT_SIZE_SMALL)
        pulse = 0.85 + 0.15 * abs(math.sin(self._anim * 1.2))
        col = tuple(int(c * pulse) for c in (255, 200, 80))
        screen.blit(fh.render("🧳 Мандрівний торговець", True, col), (CARDS_X, 50))
        screen.blit(fs.render("Рідкісні товари — лише сьогодні!", True, COLOR_TEXT_DIM),
                    (CARDS_X, 90))
        gold = fs.render(f"💰 {self.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold, (SCREEN_WIDTH - gold.get_width() - 40, 55))

    def _draw_lots(self, screen):
        fn  = assets.get_font(FONT_SIZE_NORMAL)
        fsm = assets.get_font(FONT_SIZE_SMALL)
        mp  = pygame.mouse.get_pos()

        for i, lot in enumerate(self._w.lots):
            r   = self._card_rect(i)
            rar_col = RARITY_COLORS.get(lot.rarity, (180, 180, 180))

            # Фон карточки
            if lot.sold:
                bg_col = (15, 12, 8, 120)
            elif i == self._sel:
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
            from game.data import BP_RARITY_NAMES_UA
            rar_ua = {"common":"Звичайний","uncommon":"Незвичайний",
                      "rare":"Рідкісний","epic":"Епічний","legendary":"Легендарний"}
            screen.blit(fsm.render(rar_ua.get(lot.rarity, ""), True, rar_col),
                        (r.x + 48, r.y + 34))

            # Ціна
            price_col = COLOR_GOLD if self.player.gold >= lot.price else COLOR_ERROR
            p_s = fn.render(f"{lot.price}🪙", True, price_col)
            screen.blit(p_s, (r.right - p_s.get_width() - 10, r.bottom - p_s.get_height() - 8))

    def _draw_info(self, screen):
        if self._sel < 0 or self._sel >= len(self._w.lots):
            return
        lot = self._w.lots[self._sel]
        if lot.sold:
            return
        fsm = assets.get_font(FONT_SIZE_SMALL)
        ix  = CARDS_X + 2 * (CARD_W + CARD_PAD) + 20
        iy  = CARDS_Y

        if lot.item_type == "blueprint":
            from game.data import BLUEPRINTS, MATERIALS
            bp = BLUEPRINTS.get(lot.bp_id)
            if bp:
                lines = [f"📜 Кресленик: {bp.result_name}", f"Рецепт:"]
                for mat_id, qty in bp.recipe.items():
                    mat  = MATERIALS.get(mat_id)
                    have = self.player.materials.get(mat_id, 0)
                    clr_m = (100,220,100) if have >= qty else COLOR_ERROR
                    lines.append(f"  {mat.icon if mat else '?'} {mat.name if mat else mat_id} {have}/{qty}")
                for line in lines:
                    s = fsm.render(line, True, COLOR_TEXT)
                    screen.blit(s, (ix, iy)); iy += 20

    def _draw_timer(self, screen):
        fsm  = assets.get_font(FONT_SIZE_SMALL)
        left = self._w.time_left
        m, s = divmod(left, 60)
        pulse = 0.7 + 0.3 * abs(math.sin(self._anim * 2))
        col   = (220, 80, 80) if left < 120 else (180, 160, 100)
        col   = tuple(int(c * pulse) for c in col)
        t = fsm.render(f"⏱ Зникне через {m:02d}:{s:02d}", True, col)
        screen.blit(t, (SCREEN_WIDTH - t.get_width() - 40, 90))