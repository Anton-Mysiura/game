"""
Індекс героїв — вкладка в бестіарії.
Показує всіх 42 героїв, згрупованих по класу.
"""
import pygame

from ui.components import Button
from ui.constants import (SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_GOLD, COLOR_TEXT,
                           COLOR_TEXT_DIM, COLOR_ERROR, FONT_SIZE_LARGE,
                           FONT_SIZE_MEDIUM, FONT_SIZE_NORMAL, FONT_SIZE_SMALL)
from ui.assets import assets
from game.heroes import HEROES, HERO_GROUPS, HERO_RARITY_COLORS, HERO_RARITY_NAMES_UA

_SW, _SH = SCREEN_WIDTH, SCREEN_HEIGHT

# Layout
_LIST_X   = 30
_LIST_W   = 340
_LIST_Y   = 90
_ROW_H    = 44
_VISIBLE  = (_SH - _LIST_Y - 60) // _ROW_H

_INFO_X   = _LIST_X + _LIST_W + 20
_INFO_W   = _SW - _INFO_X - 30
_INFO_Y   = _LIST_Y


class HeroIndexWidget:
    """
    Вбудований віджет індексу героїв для бестіарія.
    Використовується як підрозділ в BestiaryScene.
    """

    def __init__(self, player):
        self.player = player
        self.roster  = player.hero_roster

        # Плоский список для прокрутки: group headers + hero rows
        self._rows = self._build_rows()
        self._scroll = 0
        self._sel    = -1

        # Підключаємо renderer (малювання)
        from scenes.ui.hero_index_renderer import HeroIndexRenderer
        self._renderer = HeroIndexRenderer(self)
    def _build_rows(self) -> list:
        rows = []
        for group_id, gdata in HERO_GROUPS.items():
            rows.append(("header", group_id, gdata))
            for hid in gdata["variants"]:
                hero = HEROES.get(hid)
                if hero:
                    rows.append(("hero", hid, hero))
        return rows

    @property
    def _selected_hero(self):
        if self._sel < 0 or self._sel >= len(self._rows):
            return None
        row = self._rows[self._sel]
        if row[0] == "hero":
            return row[2]
        return None

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(len(self._rows) - _VISIBLE, self._scroll - event.y))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            for i in range(_VISIBLE):
                idx = self._scroll + i
                if idx >= len(self._rows):
                    break
                r = pygame.Rect(_LIST_X, _LIST_Y + i * _ROW_H, _LIST_W, _ROW_H - 3)
                if r.collidepoint(mp):
                    row = self._rows[idx]
                    if row[0] == "hero":
                        self._sel = idx

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)