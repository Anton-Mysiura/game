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
        screen.fill((8, 6, 4))

        # Заголовок
        fh = assets.get_font(FONT_SIZE_LARGE, bold=True)
        t = fh.render("⚔ Рулетка Героїв", True, COLOR_GOLD)
        screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, 24))

        # Спіни
        fs = assets.get_font(FONT_SIZE_NORMAL)
        sc = COLOR_GOLD if self.roster.spins_left > 0 else COLOR_ERROR
        st = fs.render(f"🎰 Спінів: {self.roster.spins_left}", True, sc)
        screen.blit(st, (SCREEN_WIDTH // 2 - st.get_width() // 2, 72))

        self._draw_strip(screen)

        if self._state == self._ST_IDLE:
            fn = assets.get_font(FONT_SIZE_NORMAL)
            hint = fn.render("Натисни 'Крутити' щоб отримати героя!", True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                               self._strip_y + self._card_h + 24))
            self._btn_spin.draw(screen)

        elif self._state == self._ST_SPINNING:
            fn = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
            col = (int(200 + 55 * math.sin(time.time() * 8)),
                   int(150 + 50 * math.sin(time.time() * 6)), 50)
            txt = fn.render("Крутиться...", True, col)
            screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                               self._strip_y + self._card_h + 24))

        elif self._state == self._ST_RESULT:
            self._draw_result(screen)
            self._btn_keep.draw(screen)
            if self.roster.can_spin():
                self._btn_reroll.draw(screen)
            else:
                fn = assets.get_font(FONT_SIZE_SMALL)
                ns = fn.render("Більше немає спінів — залиш цього героя", True, COLOR_TEXT_DIM)
                screen.blit(ns, (SCREEN_WIDTH // 2 - ns.get_width() // 2, SCREEN_HEIGHT - 60))

    def _draw_strip(self, screen: pygame.Surface):
        cw = self._card_w
        ch = self._card_h
        sy = self._strip_y
        cx = SCREEN_WIDTH // 2
        visible_w = int(SCREEN_WIDTH * 0.85)
        mask_x = cx - visible_w // 2

        # Перший абсолютний індекс видимої зони
        first_abs = int(self._strip_offset) // cw - 1
        count = visible_w // cw + 4

        for i in range(count):
            abs_idx  = first_abs + i
            list_idx = abs_idx % len(self._strip_ids)
            hid  = self._strip_ids[list_idx]
            hero = HEROES.get(hid)
            if not hero:
                continue

            card_x = abs_idx * cw - int(self._strip_offset)
            if card_x + cw < mask_x or card_x > mask_x + visible_w:
                continue

            dist = abs(card_x + cw // 2 - cx)
            brightness = max(0.25, 1.0 - dist / (visible_w // 2))
            self._draw_card(screen, hero, card_x, sy, cw - 6, ch, brightness)

        # Центральна рамка
        pygame.draw.rect(screen, COLOR_GOLD,
                         (cx - cw // 2 - 3, sy - 4, cw + 6, ch + 8), 3, border_radius=10)

    def _draw_card(self, screen: pygame.Surface, hero, x: int, y: int,
                   w: int, h: int, brightness: float):
        rar_col = HERO_RARITY_COLORS.get(hero.rarity, (160, 160, 160))
        bg_raw  = _RARITY_BG.get(hero.rarity, (20, 20, 20))
        bg      = tuple(int(c * brightness) for c in bg_raw)
        border  = tuple(int(c * brightness) for c in rar_col)

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((*bg, 220))
        pygame.draw.rect(surf, border, surf.get_rect(), 2, border_radius=8)
        screen.blit(surf, (x, y))

        # Idle анімація
        frames = _get_idle_frames(hero.hero_id)
        if frames:
            t = self._anim_timers.get(hero.hero_id, 0.0)
            fps = 8.0
            frame_idx = int(t * fps) % len(frames)
            frame = frames[frame_idx]
            # Масштабуємо до ширини картки
            scale_f = (w - 8) / frame.get_width()
            fw = int(frame.get_width() * scale_f)
            fh_px = int(frame.get_height() * scale_f)
            scaled = pygame.transform.scale(frame, (fw, fh_px))
            if brightness < 0.99:
                dim = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
                dim.fill((0, 0, 0, int((1 - brightness) * 160)))
                scaled.blit(dim, (0, 0))
            anim_y = y + (h - fh_px) // 2 - 10
            screen.blit(scaled, (x + 4, anim_y))
            if hero.hero_id not in self._anim_timers:
                self._anim_timers[hero.hero_id] = 0.0
        else:
            # Fallback — емодзі
            fi = assets.get_font(44)
            icon = fi.render(hero.icon, True, border)
            screen.blit(icon, (x + w // 2 - icon.get_width() // 2, y + 20))

        # Назва
        fn = assets.get_font(FONT_SIZE_SMALL, bold=True)
        nc = tuple(int(c * brightness) for c in (220, 200, 160))
        ns = fn.render(hero.name[:14], True, nc)
        screen.blit(ns, (x + w // 2 - ns.get_width() // 2, y + h - 36))

        # Рідкість
        fr = assets.get_font(10)
        rn = HERO_RARITY_NAMES_UA.get(hero.rarity, "")
        rs = fr.render(rn, True, border)
        screen.blit(rs, (x + w // 2 - rs.get_width() // 2, y + h - 18))

    def _draw_result(self, screen: pygame.Surface):
        if not self._result_hero:
            return
        hero = self._result_hero
        rar_col = HERO_RARITY_COLORS.get(hero.rarity, COLOR_GOLD)

        pw, ph = 480, 200
        px = SCREEN_WIDTH // 2 - pw // 2
        py = self._strip_y + self._card_h + 18

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((*_RARITY_BG.get(hero.rarity, (20, 20, 20)), 230))
        pygame.draw.rect(panel, rar_col, panel.get_rect(), 2, border_radius=12)
        screen.blit(panel, (px, py))

        fi = assets.get_font(44)
        icon = fi.render(hero.icon, True, rar_col)
        screen.blit(icon, (px + 16, py + 12))

        fh = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        name = fh.render(hero.name, True, rar_col)
        screen.blit(name, (px + 72, py + 14))

        fs = assets.get_font(FONT_SIZE_SMALL)
        rar_name = HERO_RARITY_NAMES_UA.get(hero.rarity, "")
        screen.blit(fs.render(f"✦ {rar_name}", True, rar_col), (px + 72, py + 42))
        screen.blit(fs.render(hero.lore[:65], True, COLOR_TEXT_DIM), (px + 16, py + 68))

        y_sk = py + 90
        for sk in hero.skills:
            prefix = "⚡" if not sk.is_passive else "🔹"
            col = (255, 200, 80) if not sk.is_passive else COLOR_TEXT
            screen.blit(fs.render(f"{prefix} {sk.name}: {sk.desc[:50]}", True, col), (px + 16, y_sk))
            y_sk += 18
            if y_sk > py + ph - 16:
                break

        b = hero.passive_bonuses()
        parts = []
        if b["hp"]:      parts.append(f"+{b['hp']}HP")
        if b["attack"]:  parts.append(f"+{b['attack']}ATK")
        if b["defense"]: parts.append(f"+{b['defense']}DEF")
        if b["crit"]:    parts.append(f"+{int(b['crit']*100)}%крит")
        if parts:
            bs = fs.render("  ".join(parts), True, (120, 200, 120))
            screen.blit(bs, (px + 16, py + ph - 22))