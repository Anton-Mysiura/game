"""
Сцена журналу бою — детальний перегляд що відбулось в останній битві.
"""
import pygame
from .base import Scene
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.battle_log import EventType, EVENT_META

# Фільтри
FILTERS = [
    ("Всі",     None),
    ("Удари",   {EventType.HIT, EventType.CRIT}),
    ("Шкода",   {EventType.ENEMY_HIT}),
    ("Спец",    {EventType.BURN, EventType.STUN, EventType.LIFESTEAL, EventType.COMBO}),
]

ROW_H      = 34
VISIBLE_H  = 380   # висота зони скролу
LIST_X     = 60
LIST_Y     = 200
LIST_W     = SCREEN_WIDTH - 120


class BattleLogScene(Scene):
    """Екран журналу бою."""

    def __init__(self, game):
        super().__init__(game)
        self.record = game.last_battle_record

        self.close_btn = Button(SCREEN_WIDTH - 230, 20, 200, 50,
                                "✖ Закрити", lambda: game.pop_scene())

        # Фільтр-кнопки
        self._filter_idx = 0
        self._filter_btns = []
        bx = LIST_X
        for i, (label, _) in enumerate(FILTERS):
            self._filter_btns.append(
                Button(bx, 150, 130, 36, label, lambda i=i: self._set_filter(i))
            )
            bx += 138

        self._scroll_y   = 0
        self._max_scroll = 0
        self._filtered   = []
        self._rebuild()

    # ── Фільтрація ────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.battle_log_renderer import BattleLogRenderer
        self._renderer = BattleLogRenderer(self)
    def _set_filter(self, idx: int):
        self._filter_idx = idx
        self._scroll_y = 0
        self._rebuild()

    def _rebuild(self):
        if not self.record:
            self._filtered = []
            return
        allowed = FILTERS[self._filter_idx][1]
        if allowed is None:
            self._filtered = self.record.events
        else:
            self._filtered = [e for e in self.record.events if e.etype in allowed]
        total_h = len(self._filtered) * ROW_H
        self._max_scroll = max(0, total_h - VISIBLE_H)

    # ── Події ─────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.pop_scene()
            elif event.key == pygame.K_UP:
                self._scroll_y = max(0, self._scroll_y - ROW_H * 3)
            elif event.key == pygame.K_DOWN:
                self._scroll_y = min(self._max_scroll, self._scroll_y + ROW_H * 3)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mp = pygame.mouse.get_pos()
            if event.button == 1:
                self.close_btn.update(mp, True)
                for btn in self._filter_btns:
                    btn.update(mp, True)
            elif event.button == 4:
                self._scroll_y = max(0, self._scroll_y - ROW_H * 2)
            elif event.button == 5:
                self._scroll_y = min(self._max_scroll, self._scroll_y + ROW_H * 2)

    def update(self, dt: float):
        mp = pygame.mouse.get_pos()
        self.close_btn.update(mp, False)
        for btn in self._filter_btns:
            btn.update(mp, False)

    # ── Малювання ─────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)