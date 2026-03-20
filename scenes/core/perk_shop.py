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

        # Підключаємо renderer (малювання)
        from scenes.ui.perk_shop_renderer import PerkShopRenderer
        self._renderer = PerkShopRenderer(self)
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
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)
