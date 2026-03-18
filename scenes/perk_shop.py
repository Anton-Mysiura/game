"""
Крамниця перків — купити бонусні картки або замінити один з існуючих перків.
"""

import pygame
from .base import Scene
from ui.assets import assets
from ui.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, COLOR_BG,
    COLOR_ERROR, COLOR_SUCCESS, COLOR_BTN_NORMAL, COLOR_BTN_HOVER,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, FONT_SIZE_HUGE,
)
from game.perk_system import PERKS, RARITY_COLORS, RARITY_NAMES, roll_perks
from game.save_manager import autosave


# ══════════════════════════════════════════
#  Економіка
# ══════════════════════════════════════════

EXTRA_BASE_COST  = 50   # базова ціна бонусних карток
REROLL_BASE_COST = 80   # базова ціна рерола
COST_MULTIPLIER  = 2    # множник з кожною покупкою

CARD_W   = 260
CARD_H   = 320
CARD_GAP = 30


def extra_cost(bought: int) -> int:
    return EXTRA_BASE_COST * (COST_MULTIPLIER ** bought)


def reroll_cost(bought: int) -> int:
    return REROLL_BASE_COST * (COST_MULTIPLIER ** bought)


# ══════════════════════════════════════════
#  Сцена
# ══════════════════════════════════════════

class PerkShopScene(Scene):
    """
    Крамниця перків.

    Режими:
      "menu"   — головний екран з двома кнопками
      "extra"  — вибір з 3 нових карток (куплено)
      "pick"   — вибір існуючого перку для заміни
      "reroll" — вибір з 3 нових карток (заміна)
    """

    def __init__(self, game):
        super().__init__(game)
        self.mode = "menu"

        # Картки що пропонуються
        self.offered_perks = []
        self.hovered_card  = -1
        self.chosen_card   = -1  # захист від подвійного кліку

        # Для режиму "pick" — перк який замінюємо
        self.reroll_target_idx = -1   # індекс у self.player.perks
        self.hovered_owned = -1

        # Скрол списку власних перків
        self.owned_scroll = 0

        # Повідомлення (feedback)
        self._msg      = ""
        self._msg_color = COLOR_SUCCESS
        self._msg_timer = 0.0

    # ──────────────────────────────────────
    #  Ціни
    # ──────────────────────────────────────

    @property
    def _extra_cost(self) -> int:
        return extra_cost(self.player.perk_shop_extra_bought)

    @property
    def _reroll_cost(self) -> int:
        return reroll_cost(self.player.perk_shop_reroll_bought)

    # ──────────────────────────────────────
    #  Логіка подій
    # ──────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.mode == "menu":
                self.game.pop_scene()
            else:
                self.mode = "menu"
                self.offered_perks = []
                self.reroll_target_idx = -1
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if event.button == 1:
                self._handle_click(mx, my)
            elif event.button == 4:
                self.owned_scroll = max(0, self.owned_scroll - 30)
            elif event.button == 5:
                self.owned_scroll = min(
                    getattr(self, "_owned_max_scroll", 0),
                    self.owned_scroll + 30
                )

        if event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()
            self._update_hovers(mx, my)

    def _handle_click(self, mx, my):
        if self.mode == "menu":
            self._handle_menu_click(mx, my)
        elif self.mode in ("extra", "reroll"):
            self._handle_card_click(mx, my)
        elif self.mode == "pick":
            self._handle_pick_click(mx, my)

    def _handle_menu_click(self, mx, my):
        # Кнопка "Закрити"
        close = self._close_rect()
        if close.collidepoint(mx, my):
            self.game.pop_scene()
            return

        # Кнопка "Бонусні картки"
        extra_btn = self._extra_btn_rect()
        if extra_btn.collidepoint(mx, my):
            if self.player.gold >= self._extra_cost:
                self.player.gold -= self._extra_cost
                self.player.perk_shop_extra_bought += 1
                self.offered_perks = roll_perks(3)
                self.chosen_card   = -1
                self.hovered_card  = -1
                self.mode = "extra"
                autosave(self.player)
            else:
                self._show_msg("Недостатньо золота!", COLOR_ERROR)
            return

        # Кнопка "Замінити перк"
        reroll_btn = self._reroll_btn_rect()
        if reroll_btn.collidepoint(mx, my):
            if not self.player.perks:
                self._show_msg("Спочатку отримай хоч один перк!", COLOR_ERROR)
            elif self.player.gold >= self._reroll_cost:
                self.mode = "pick"
                self.owned_scroll = 0
            else:
                self._show_msg("Недостатньо золота!", COLOR_ERROR)
            return

    def _handle_card_click(self, mx, my):
        if self.chosen_card != -1:
            return
        for i, rect in enumerate(self._card_rects()):
            if rect.collidepoint(mx, my):
                self.chosen_card = i
                perk = self.offered_perks[i]

                if self.mode == "extra":
                    self.player.apply_perk(perk)
                    self._show_msg(f"Отримано: {perk.name}!", COLOR_SUCCESS)
                else:  # reroll
                    # Видаляємо старий перк
                    old_perk_id = self.player.perks[self.reroll_target_idx]
                    self.player.perks.pop(self.reroll_target_idx)
                    # Застосовуємо новий
                    self.player.apply_perk(perk)
                    old_name = PERKS[old_perk_id].name if old_perk_id in PERKS else old_perk_id
                    self._show_msg(f"{old_name} → {perk.name}", COLOR_GOLD)

                autosave(self.player)
                self.mode = "menu"
                self.offered_perks = []
                self.reroll_target_idx = -1
                return

    def _handle_pick_click(self, mx, my):
        # Кнопка скасування
        cancel = self._cancel_rect()
        if cancel.collidepoint(mx, my):
            self.mode = "menu"
            return

        # Клік на один з власних перків
        for i, rect in enumerate(self._owned_rects()):
            if rect.collidepoint(mx, my):
                self.reroll_target_idx = i
                self.player.gold -= self._reroll_cost
                self.player.perk_shop_reroll_bought += 1
                self.offered_perks = roll_perks(3)
                self.chosen_card   = -1
                self.hovered_card  = -1
                self.mode = "reroll"
                autosave(self.player)
                return

    def _update_hovers(self, mx, my):
        if self.mode in ("extra", "reroll"):
            self.hovered_card = next(
                (i for i, r in enumerate(self._card_rects()) if r.collidepoint(mx, my)), -1
            )
        elif self.mode == "pick":
            self.hovered_owned = next(
                (i for i, r in enumerate(self._owned_rects()) if r.collidepoint(mx, my)), -1
            )

    def _show_msg(self, text: str, color):
        self._msg       = text
        self._msg_color = color
        self._msg_timer = 2.5

    # ──────────────────────────────────────
    #  Геометрія
    # ──────────────────────────────────────

    def _extra_btn_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH // 2 - 320, 260, 290, 200)

    def _reroll_btn_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH // 2 + 30, 260, 290, 200)

    def _close_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 80, 220, 50)

    def _cancel_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 80, 220, 50)

    def _card_rects(self) -> list[pygame.Rect]:
        total_w = len(self.offered_perks) * CARD_W + (len(self.offered_perks) - 1) * CARD_GAP
        start_x = SCREEN_WIDTH // 2 - total_w // 2
        card_y  = SCREEN_HEIGHT // 2 - CARD_H // 2 + 20
        return [
            pygame.Rect(start_x + i * (CARD_W + CARD_GAP), card_y, CARD_W, CARD_H)
            for i in range(len(self.offered_perks))
        ]

    def _owned_rects(self) -> list[pygame.Rect]:
        """Рядки списку власних перків (унікальних)."""
        unique = list(dict.fromkeys(self.player.perks))  # зберігаємо порядок, без дублів
        row_h   = 56
        list_x  = SCREEN_WIDTH // 2 - 300
        list_top = 200
        return [
            pygame.Rect(list_x, list_top + i * row_h - self.owned_scroll, 600, row_h - 6)
            for i in range(len(unique))
        ]

    # ──────────────────────────────────────
    #  Update
    # ──────────────────────────────────────

    def update(self, dt: float):
        if self._msg_timer > 0:
            self._msg_timer -= dt

    # ──────────────────────────────────────
    #  Draw
    # ──────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        if self.mode == "menu":
            self._draw_menu(screen)
        elif self.mode in ("extra", "reroll"):
            self._draw_card_pick(screen)
        elif self.mode == "pick":
            self._draw_pick_owned(screen)

        # Повідомлення
        if self._msg and self._msg_timer > 0:
            font = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
            surf = font.render(self._msg, True, self._msg_color)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT - 130))

    # ── Головне меню ──────────────────────

    def _draw_menu(self, screen: pygame.Surface):
        cx = SCREEN_WIDTH // 2

        # Заголовок
        font_huge  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_large = assets.get_font(FONT_SIZE_LARGE)
        font_med   = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)

        title  = font_huge.render("✨ Крамниця перків", True, COLOR_GOLD)
        shadow = font_huge.render("✨ Крамниця перків", True, (0, 0, 0))
        screen.blit(shadow, (cx - title.get_width() // 2 + 2, 52))
        screen.blit(title,  (cx - title.get_width() // 2,     50))

        gold_surf = font_large.render(f"💰 {self.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold_surf, (cx - gold_surf.get_width() // 2, 120))

        # ── Кнопка «Бонусні картки» ──
        extra_rect = self._extra_btn_rect()
        can_extra  = self.player.gold >= self._extra_cost
        self._draw_shop_btn(
            screen, extra_rect, can_extra,
            "🃏 Бонусні картки",
            f"Вибрати 1 з 3 нових перків",
            f"💰 {self._extra_cost} золота",
            (40, 60, 40), (100, 180, 100),
        )

        # ── Кнопка «Замінити перк» ──
        reroll_rect = self._reroll_btn_rect()
        can_reroll  = self.player.gold >= self._reroll_cost and bool(self.player.perks)
        self._draw_shop_btn(
            screen, reroll_rect, can_reroll,
            "🔄 Замінити перк",
            f"Видалити один з перків та\nвибрати новий замість нього",
            f"💰 {self._reroll_cost} золота",
            (60, 30, 60), (180, 80, 180),
        )

        # Прогрес знижок / підвищень
        next_extra  = extra_cost(self.player.perk_shop_extra_bought + 1)
        next_reroll = reroll_cost(self.player.perk_shop_reroll_bought + 1)
        hint = font_sm.render(
            f"Наст. бонус: {next_extra}💰   Наст. заміна: {next_reroll}💰",
            True, COLOR_TEXT_DIM
        )
        screen.blit(hint, (cx - hint.get_width() // 2, 490))

        # Закрити
        self._draw_close_btn(screen, "← Назад")

    def _draw_shop_btn(self, screen, rect, enabled, title, desc, cost_str,
                        bg_color, border_color):
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_desc  = assets.get_font(FONT_SIZE_SMALL)
        font_cost  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)

        # Hover
        hovered = rect.collidepoint(pygame.mouse.get_pos()) and enabled
        bg = tuple(min(c + 15, 255) for c in bg_color) if hovered else bg_color

        pygame.draw.rect(screen, bg, rect, border_radius=16)
        bc = border_color if enabled else (60, 60, 60)
        pygame.draw.rect(screen, bc, rect, 2 if not hovered else 3, border_radius=16)

        # Текст
        t = font_title.render(title, True, COLOR_TEXT if enabled else COLOR_TEXT_DIM)
        screen.blit(t, (rect.centerx - t.get_width() // 2, rect.y + 20))

        # Опис (з переносом)
        lines = desc.split("\n")
        dy = rect.y + 65
        for line in lines:
            s = font_desc.render(line, True, COLOR_TEXT_DIM)
            screen.blit(s, (rect.centerx - s.get_width() // 2, dy))
            dy += s.get_height() + 4

        # Ціна
        cost_color = COLOR_GOLD if enabled else COLOR_ERROR
        cs = font_cost.render(cost_str, True, cost_color)
        screen.blit(cs, (rect.centerx - cs.get_width() // 2, rect.bottom - 50))

        # "Недостатньо" якщо не може купити
        if not enabled and self.player.perks or not enabled:
            if not self.player.perks and "Замін" in title:
                no_s = font_desc.render("Немає перків для заміни", True, COLOR_ERROR)
                screen.blit(no_s, (rect.centerx - no_s.get_width() // 2, rect.bottom - 28))

    def _draw_close_btn(self, screen, label="← Закрити"):
        rect = self._close_rect()
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        bg = COLOR_BTN_HOVER if hovered else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, rect, 2, border_radius=10)
        font = assets.get_font(FONT_SIZE_MEDIUM)
        s = font.render(label, True, COLOR_TEXT)
        screen.blit(s, (rect.centerx - s.get_width() // 2,
                         rect.centery - s.get_height() // 2))

    # ── Вибір картки ──────────────────────

    def _draw_card_pick(self, screen: pygame.Surface):
        cx = SCREEN_WIDTH // 2
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_sub   = assets.get_font(FONT_SIZE_MEDIUM)

        if self.mode == "extra":
            title_text = "🃏 Вибери свій перк"
            sub_text   = "Клікни на картку"
        else:
            old_id   = self.player.perks[self.reroll_target_idx] if self.reroll_target_idx >= 0 else ""
            old_name = PERKS[old_id].name if old_id in PERKS else "?"
            title_text = f"🔄 Заміна: {old_name}"
            sub_text   = "Вибери новий перк замість старого"

        title = font_title.render(title_text, True, COLOR_GOLD)
        screen.blit(title, (cx - title.get_width() // 2, 40))
        sub = font_sub.render(sub_text, True, COLOR_TEXT_DIM)
        screen.blit(sub, (cx - sub.get_width() // 2, 110))

        for i, (perk, rect) in enumerate(zip(self.offered_perks, self._card_rects())):
            self._draw_perk_card(screen, perk, rect, hovered=(i == self.hovered_card))

        self._draw_close_btn(screen, "✗ Скасувати")

    def _draw_perk_card(self, screen, perk, rect, hovered: bool):
        rarity_color = RARITY_COLORS[perk.rarity]

        if hovered:
            glow = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
            glow.fill((*rarity_color, 55))
            screen.blit(glow, (rect.x - 6, rect.y - 6))
            draw_rect = rect.inflate(6, 6)
        else:
            draw_rect = rect

        bg = (35, 28, 48) if hovered else (28, 22, 38)
        pygame.draw.rect(screen, bg, draw_rect, border_radius=16)

        stripe = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.w, 7)
        pygame.draw.rect(screen, rarity_color, stripe, border_radius=16)

        pygame.draw.rect(screen, rarity_color, draw_rect,
                         3 if hovered else 2, border_radius=16)

        cx = draw_rect.centerx

        font_icon   = assets.get_font(56)
        font_rarity = assets.get_font(FONT_SIZE_SMALL, bold=True)
        font_name   = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_desc   = assets.get_font(FONT_SIZE_SMALL)

        icon_s = font_icon.render(perk.icon, True, COLOR_TEXT)
        screen.blit(icon_s, (cx - icon_s.get_width() // 2, draw_rect.y + 24))

        rar_s = font_rarity.render(RARITY_NAMES[perk.rarity].upper(), True, rarity_color)
        screen.blit(rar_s, (cx - rar_s.get_width() // 2, draw_rect.y + 98))

        name_s = font_name.render(perk.name, True, COLOR_TEXT)
        screen.blit(name_s, (cx - name_s.get_width() // 2, draw_rect.y + 126))

        self._draw_wrapped(screen, font_desc, perk.description, COLOR_TEXT_DIM,
                           draw_rect.x + 14, draw_rect.y + 164, draw_rect.w - 28)

    # ── Вибір перку для заміни ────────────

    def _draw_pick_owned(self, screen: pygame.Surface):
        cx = SCREEN_WIDTH // 2

        font_huge  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_med   = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)
        font_norm  = assets.get_font(FONT_SIZE_NORMAL)

        title = font_huge.render("🔄 Який перк замінити?", True, COLOR_GOLD)
        screen.blit(title, (cx - title.get_width() // 2, 40))

        cost_s = font_med.render(f"Вартість: 💰 {self._reroll_cost} золота", True, COLOR_GOLD)
        screen.blit(cost_s, (cx - cost_s.get_width() // 2, 110))

        warn_s = font_sm.render("Вибраний перк буде видалено назавжди!", True, COLOR_ERROR)
        screen.blit(warn_s, (cx - warn_s.get_width() // 2, 148))

        # Список
        unique  = list(dict.fromkeys(self.player.perks))
        row_h   = 56
        list_x  = cx - 300
        list_top = 200
        visible_h = SCREEN_HEIGHT - list_top - 100
        total_h   = len(unique) * row_h
        self._owned_max_scroll = max(0, total_h - visible_h)
        self.owned_scroll = min(self.owned_scroll, self._owned_max_scroll)

        clip = pygame.Rect(list_x - 4, list_top, 608, visible_h)
        screen.set_clip(clip)

        for i, perk_id in enumerate(unique):
            rect = pygame.Rect(list_x, list_top + i * row_h - self.owned_scroll,
                                600, row_h - 6)
            if rect.bottom < list_top or rect.top > list_top + visible_h:
                continue

            perk = PERKS.get(perk_id)
            if not perk:
                continue

            hovered = (i == self.hovered_owned)
            rarity_color = RARITY_COLORS[perk.rarity]

            bg = (60, 30, 30) if hovered else (35, 25, 35)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            bc = (220, 80, 80) if hovered else rarity_color
            pygame.draw.rect(screen, bc, rect, 2 if not hovered else 3, border_radius=10)

            # Кольорова смужка зліва
            pygame.draw.rect(screen, rarity_color, (rect.x, rect.y, 5, rect.h), border_radius=3)

            icon_s = assets.get_font(FONT_SIZE_LARGE).render(perk.icon, True, rarity_color)
            screen.blit(icon_s, (rect.x + 12, rect.centery - icon_s.get_height() // 2))

            name_s = assets.get_font(FONT_SIZE_NORMAL, bold=True).render(perk.name, True, COLOR_TEXT)
            screen.blit(name_s, (rect.x + 56, rect.y + 8))

            rar_s = font_sm.render(perk.rarity_name, True, rarity_color)
            screen.blit(rar_s, (rect.x + 56, rect.y + 32))

            cnt = self.player.perks.count(perk_id)
            if cnt > 1:
                cnt_s = font_norm.render(f"×{cnt}", True, COLOR_GOLD)
                screen.blit(cnt_s, (rect.right - cnt_s.get_width() - 12,
                                     rect.centery - cnt_s.get_height() // 2))

            if hovered:
                del_s = font_sm.render("🗑 Видалити", True, (220, 80, 80))
                screen.blit(del_s, (rect.right - del_s.get_width() - 40,
                                     rect.centery - del_s.get_height() // 2))

        screen.set_clip(None)

        # Скрол
        if self._owned_max_scroll > 0:
            sb_x = cx + 310
            pygame.draw.rect(screen, (40, 35, 50), (sb_x, list_top, 6, visible_h), border_radius=3)
            ratio   = visible_h / total_h
            thumb_h = max(24, int(visible_h * ratio))
            thumb_y = list_top + int((visible_h - thumb_h) * self.owned_scroll /
                                      self._owned_max_scroll)
            pygame.draw.rect(screen, COLOR_GOLD, (sb_x, thumb_y, 6, thumb_h), border_radius=3)

        self._draw_close_btn(screen, "✗ Скасувати")

    # ──────────────────────────────────────
    #  Утиліти
    # ──────────────────────────────────────

    @staticmethod
    def _draw_wrapped(screen, font, text: str, color, x, y, max_w):
        words, line, ly = text.split(), "", y
        for w in words:
            test = f"{line} {w}".strip()
            if font.size(test)[0] <= max_w:
                line = test
            else:
                if line:
                    s = font.render(line, True, color)
                    screen.blit(s, (x + max_w // 2 - s.get_width() // 2, ly))
                    ly += font.get_height() + 3
                line = w
        if line:
            s = font.render(line, True, color)
            screen.blit(s, (x + max_w // 2 - s.get_width() // 2, ly))