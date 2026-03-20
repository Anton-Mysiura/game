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

        # Підключаємо renderer (малювання)
        from scenes.ui.wanderer_renderer import WandererRenderer
        self._renderer = WandererRenderer(self)
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
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)