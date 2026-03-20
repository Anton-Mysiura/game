"""
Сцена управління слотами героїв.
- Слоти показують анімацію idle активного героя
- Колекція відображається як сітка карток з анімаціями
- При наведенні на картку — спливаючий tooltip з описом
"""
import pygame

from .base import Scene
from ui.components import Button
from ui.constants import (SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_GOLD, COLOR_TEXT,
                           COLOR_TEXT_DIM, COLOR_ERROR, FONT_SIZE_LARGE,
                           FONT_SIZE_MEDIUM, FONT_SIZE_NORMAL, FONT_SIZE_SMALL)
from ui.assets import assets
from ui.notifications import notify
from game.heroes import HEROES, HERO_RARITY_COLORS, HERO_RARITY_NAMES_UA
from game.hero_roster import SLOT_UNLOCK_LEVELS, SLOT_UNLOCK_GOLD
from scenes.core.hero_roulette import _get_idle_frames, _RARITY_BG

# ── Layout ────────────────────────────────────────────────────────────
_SW, _SH = SCREEN_WIDTH, SCREEN_HEIGHT

# Слоти зверху
_SLOT_Y   = 75
_SLOT_H   = 200
_SLOT_W   = 210
_SLOT_GAP = 16

# Сітка колекції
_GRID_Y      = _SLOT_Y + _SLOT_H + 50
_CARD_W      = 160
_CARD_H      = 200
_CARD_GAP    = 12
_CARDS_PER_ROW = (_SW - 60) // (_CARD_W + _CARD_GAP)
_GRID_ROWS_VIS = (_SH - _GRID_Y - 60) // (_CARD_H + _CARD_GAP)


class HeroSlotsScene(Scene):

    def __init__(self, game):
        super().__init__(game)
        self.player = game.player
        self.roster  = self.player.hero_roster

        self._sel_slot  = self.roster.active_slot
        self._scroll    = 0          # рядок прокрутки колекції
        self._hover_idx = -1         # індекс карточки колекції під курсором
        self._anim_t: dict[str, float] = {}   # hero_id → час анімації

        cx = _SW // 2
        self._btn_back     = Button(30, _SH - 50, 150, 36, "← Назад",
                                    lambda: self.game.pop_scene())
        self._btn_roulette = Button(_SW - 230, _SH - 50, 200, 36, "🎰 Рулетка",
                                    self._go_roulette)
        self._btn_set      = Button(cx - 100, _SH - 50, 200, 36, "✅ Поставити в слот",
                                    self._assign_hero)
        self._sel_coll = -1   # вибрана картка колекції

        # Підключаємо renderer (малювання)
        from scenes.ui.hero_slots_renderer import HeroSlotsRenderer
        self._renderer = HeroSlotsRenderer(self)
    def _go_roulette(self):
        if self.roster.can_spin():
            self.game.push_scene("hero_roulette")
        else:
            notify("Немає спінів рулетки!", kind="error")

    def _assign_hero(self):
        if self._sel_coll < 0:
            notify("Вибери героя!", kind="error")
            return
        coll = self.roster.collection
        if self._sel_coll >= len(coll):
            return
        oh = coll[self._sel_coll]
        if self.roster.set_hero_in_slot(oh.hero_id, self._sel_slot):
            h = HEROES[oh.hero_id]
            notify(f"⚔ {h.name} → Слот {self._sel_slot + 1}", kind="item")
            from game.save_manager import autosave
            autosave(self.player)
        else:
            notify("Не вдалось!", kind="error")

    def _unlock_slot(self, slot_idx: int):
        if slot_idx in SLOT_UNLOCK_LEVELS:
            req = SLOT_UNLOCK_LEVELS[slot_idx]
            if self.player.level >= req:
                self.roster.slots_unlocked = max(self.roster.slots_unlocked, slot_idx)
                notify(f"✅ Слот {slot_idx} розблоковано!", kind="item")
                from game.save_manager import autosave
                autosave(self.player)
            else:
                notify(f"Потрібен рівень {req}", kind="error")
        elif slot_idx in SLOT_UNLOCK_GOLD:
            cost = SLOT_UNLOCK_GOLD[slot_idx]
            if self.player.gold >= cost:
                spent = self.roster.unlock_gold_slot()
                self.player.gold -= spent
                self.player.gold_spent += spent
                notify(f"✅ Слот {slot_idx} розблоковано за {cost}🪙!", kind="item")
                from game.save_manager import autosave
                autosave(self.player)
            else:
                notify(f"Потрібно {cost}🪙", kind="error")

    # ── Update ───────────────────────────────────────────────────────
    def update(self, dt: float):
        for k in self._anim_t:
            self._anim_t[k] += dt
        mp = pygame.mouse.get_pos()
        self._hover_idx = self._card_at(mp)

    # ── Events ───────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            self._btn_back.update(mp, True)
            self._btn_roulette.update(mp, True)
            if self._sel_coll >= 0:
                self._btn_set.update(mp, True)

            # Клік по слоту
            for i in range(4):
                r = self._slot_rect(i)
                if r and r.collidepoint(mp):
                    if i < self.roster.slots_unlocked:
                        self._sel_slot = i
                        self.roster.switch_slot(i)
                    else:
                        self._unlock_slot(i + 1)

            # Клік по карточці колекції
            ci = self._card_at(mp)
            if ci >= 0:
                self._sel_coll = ci

        if event.type == pygame.MOUSEWHEEL:
            coll = self.roster.collection
            total_rows = (len(coll) + _CARDS_PER_ROW - 1) // _CARDS_PER_ROW
            self._scroll = max(0, min(total_rows - _GRID_ROWS_VIS, self._scroll - event.y))

    def _card_at(self, mp) -> int:
        """Повертає індекс карточки колекції під курсором або -1."""
        coll = self.roster.collection
        for row in range(_GRID_ROWS_VIS):
            for col in range(_CARDS_PER_ROW):
                idx = (self._scroll + row) * _CARDS_PER_ROW + col
                if idx >= len(coll):
                    return -1
                r = self._card_rect(row, col)
                if r.collidepoint(mp):
                    return idx
        return -1

    def _slot_rect(self, i: int) -> pygame.Rect:
        total_w = 4 * (_SLOT_W + _SLOT_GAP) - _SLOT_GAP
        sx = _SW // 2 - total_w // 2 + i * (_SLOT_W + _SLOT_GAP)
        return pygame.Rect(sx, _SLOT_Y, _SLOT_W, _SLOT_H)

    def _card_rect(self, row: int, col: int) -> pygame.Rect:
        total_w = _CARDS_PER_ROW * (_CARD_W + _CARD_GAP) - _CARD_GAP
        ox = _SW // 2 - total_w // 2
        x = ox + col * (_CARD_W + _CARD_GAP)
        y = _GRID_Y + row * (_CARD_H + _CARD_GAP)
        return pygame.Rect(x, y, _CARD_W, _CARD_H)

    # ── Draw ─────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)