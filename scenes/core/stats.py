"""
Сцена характеристик гравця — з вкладками.
Вкладки: Загальне | Бойова | Шахта | Репутація
"""
import math
import pygame
from .base import Scene
from ui.components import Button, Panel, ProgressBar
from ui.constants import *
from ui.assets import assets
from game.data import MATERIALS


def _fmt(seconds: float) -> str:
    t = int(seconds)
    h = t // 3600; m = (t % 3600) // 60; s = t % 60
    if h > 0: return f"{h} год {m:02d} хв"
    if m > 0: return f"{m} хв {s:02d} с"
    return f"{s} с"


TABS = [
    ("general",    "📊 Загальне"),
    ("combat",     "⚔ Бойова"),
    ("mine",       "⛏ Шахта"),
    ("reputation", "⭐ Репутація"),
]

TAB_W  = 180
TAB_H  = 38
TABS_X = 60
TABS_Y = 90
PNL_X  = 50
PNL_Y  = 138
PNL_W  = SCREEN_WIDTH - 100
PNL_H  = SCREEN_HEIGHT - 210


class StatsScene(Scene):
    """Екран характеристик з вкладками."""

    def __init__(self, game):
        super().__init__(game)
        self._tab   = "general"
        self._anim  = 0.0

        self.close_btn = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70,
                                200, 46, "Закрити", lambda: game.pop_scene())
        self.tab_btns  = [
            Button(TABS_X + i * (TAB_W + 6), TABS_Y, TAB_W, TAB_H, lbl,
                   lambda t=tid: self._switch(t))
            for i, (tid, lbl) in enumerate(TABS)
        ]
        self.hp_bar = ProgressBar(PNL_X + 20, PNL_Y + 100, PNL_W - 40, 30, COLOR_HP)
        self.xp_bar = ProgressBar(PNL_X + 20, PNL_Y + 148, PNL_W - 40, 30, COLOR_XP)
        self.main_panel = Panel(PNL_X, PNL_Y, PNL_W, PNL_H, alpha=True)

        # Підключаємо renderer (малювання)
        from scenes.ui.stats_renderer import StatsRenderer
        self._renderer = StatsRenderer(self)
    def _switch(self, tab: str):
        self._tab = tab

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            self.close_btn.update(mp, True)
            for btn in self.tab_btns:
                btn.update(mp, True)

    def update(self, dt: float):
        mp = pygame.mouse.get_pos()
        self.close_btn.update(mp, False)
        for btn in self.tab_btns:
            btn.update(mp, False)
        self._anim += dt

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)