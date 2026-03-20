"""
Сцена рулетки героїв.
- Карточки показують анімацію idle героя
- Перший спін автоматичний
- Кнопки "Залишити" / "Ще раз" не конфліктують
"""
import math
import random
import time

import pygame

from .base import Scene
from ui.components import Button
from ui.constants import (SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_GOLD, COLOR_TEXT,
                           COLOR_TEXT_DIM, COLOR_ERROR, FONT_SIZE_LARGE,
                           FONT_SIZE_MEDIUM, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
                           ANIMATIONS_DIR)
from ui.assets import assets
from ui.notifications import notify
from game.heroes import HEROES, HERO_RARITY_COLORS, HERO_RARITY_NAMES_UA, ROULETTE_POOL
from game.animation import AnimationController, Animation, AnimationLoader

_ROULETTE_ORDER = list(HEROES.keys())

_RARITY_BG = {
    "common":    ( 30,  30,  30),
    "rare":      ( 15,  30,  60),
    "epic":      ( 40,  15,  60),
    "legendary": ( 60,  45,  10),
}

# Кеш idle-анімацій для карток
_IDLE_CACHE: dict[str, list] = {}


def _get_idle_frames(hero_id: str) -> list:
    """Повертає список кадрів idle-анімації для героя (з кешем)."""
    if hero_id in _IDLE_CACHE:
        return _IDLE_CACHE[hero_id]
    hero = HEROES.get(hero_id)
    if not hero:
        return []
    cfg = hero.anim
    fname, count = cfg.idle
    if not fname or not count:
        return []
    base = cfg.path()
    path = base / f"{fname}.png"
    if not path.exists():
        for p in base.iterdir():
            if p.suffix.lower() == '.png' and p.stem.lower() == fname.lower():
                path = p
                break
        else:
            _IDLE_CACHE[hero_id] = []
            return []
    try:
        frames = AnimationLoader.load_spritesheet(
            path, frame_width=cfg.frame_h, frame_height=cfg.frame_h,
            frame_count=count, scale=1.0)
    except Exception:
        frames = []
    _IDLE_CACHE[hero_id] = frames
    return frames


class HeroRouletteScene(Scene):

    _ST_IDLE     = "idle"
    _ST_SPINNING = "spinning"
    _ST_RESULT   = "result"

    def __init__(self, game):
        super().__init__(game)
        self.player = game.player
        self.roster  = self.player.hero_roster

        self._state        = self._ST_IDLE
        self._spin_t       = 0.0
        self._spin_dur     = 2.5
        self._strip_offset = 0.0
        self._strip_vel    = 0.0
        self._result_hero  = None

        # Стрічка — 4 повтори для плавного скролу
        self._strip_ids = _ROULETTE_ORDER * 4

        self._card_w  = 140
        self._card_h  = 180
        self._strip_y = SCREEN_HEIGHT // 2 - self._card_h // 2 - 20

        # Анімаційні таймери для карток (hero_id → час)
        self._anim_timers: dict[str, float] = {}

        cx = SCREEN_WIDTH // 2
        self._btn_spin   = Button(cx - 120, SCREEN_HEIGHT - 110, 240, 48,
                                  "🎰 Крутити!", self._do_spin)
        self._btn_keep   = Button(cx - 250, SCREEN_HEIGHT - 110, 220, 48,
                                  "✅ Залишити", self._do_keep)
        self._btn_reroll = Button(cx + 30,  SCREEN_HEIGHT - 110, 220, 48,
                                  "🔄 Ще раз",  self._do_reroll)

        # Перший спін — автоматично
        if not self.roster.first_spin_done:
            self._start_spin()

    # ── Спін ─────────────────────────────────────────────────────────
        # Підключаємо renderer (малювання)
        from scenes.ui.hero_roulette_renderer import HeroRouletteRenderer
        self._renderer = HeroRouletteRenderer(self)
    def _start_spin(self):
        """Починає анімацію спіну (не перевіряє can_spin)."""
        self._state      = self._ST_SPINNING
        self._spin_t     = 0.0
        self._strip_vel  = 3000.0
        self._result_hero = None
        ids = [p[0] for p in ROULETTE_POOL]
        ws  = [p[1] for p in ROULETTE_POOL]
        self._result_hero = HEROES[random.choices(ids, weights=ws, k=1)[0]]
        self.roster.spins_left   -= 1
        self.roster.first_spin_done = True

    def _do_spin(self):
        if not self.roster.can_spin():
            notify("Немає спінів!", kind="error")
            return
        self._start_spin()

    def _do_reroll(self):
        if not self.roster.can_spin():
            notify("Більше немає спінів!", kind="error")
            return
        self._start_spin()

    def _do_keep(self):
        if self._result_hero is None:
            return
        self.roster.add_hero(self._result_hero.hero_id)
        notify(f"🎉 {self._result_hero.name} доданий до колекції!", kind="item", duration=3.0)
        self._finish()

    def _finish(self):
        from game.save_manager import autosave
        from game.tutorial_manager import TutorialManager
        autosave(self.player)
        tutorial_data = TutorialManager.run_tutorial(self.player, "tut_welcome")
        if tutorial_data:
            self.game.change_scene("tutorial",
                                   tutorial_data=[{"id": "tut_welcome",
                                                   "title": "⚔ Ласкаво просимо!",
                                                   "pages": tutorial_data}],
                                   next_scene="village")
        else:
            self.game.change_scene("village")

    # ── Update ───────────────────────────────────────────────────────
    def update(self, dt: float):
        # Оновлюємо таймери анімацій
        for k in self._anim_timers:
            self._anim_timers[k] += dt

        if self._state != self._ST_SPINNING:
            return

        self._spin_t += dt
        progress = self._spin_t / self._spin_dur
        ease = 1.0 - (progress ** 2)
        self._strip_vel = max(40.0, 3000.0 * ease)
        self._strip_offset += self._strip_vel * dt

        if self._spin_t >= self._spin_dur:
            self._state = self._ST_RESULT
            self._align_to_result()

    def _align_to_result(self):
        if not self._result_hero:
            return
        hid = self._result_hero.hero_id
        cw = self._card_w
        cx = SCREEN_WIDTH // 2
        offset = len(_ROULETTE_ORDER)
        try:
            idx = self._strip_ids.index(hid, offset)
        except ValueError:
            idx = next((i for i, x in enumerate(self._strip_ids) if x == hid), 0)
        self._strip_offset = float(idx * cw + cw // 2 - cx)

    # ── Events ───────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos

            if self._state == self._ST_IDLE:
                self._btn_spin.update(mp, True)

            elif self._state == self._ST_RESULT:
                # Визначаємо яку кнопку натиснули — перевіряємо ОКРЕМО
                keep_rect   = pygame.Rect(self._btn_keep.rect)
                reroll_rect = pygame.Rect(self._btn_reroll.rect)
                if keep_rect.collidepoint(mp):
                    self._do_keep()
                elif reroll_rect.collidepoint(mp) and self.roster.can_spin():
                    self._do_reroll()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._state == self._ST_RESULT:
                self._do_keep()

    # ── Draw ─────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)