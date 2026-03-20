"""
Рендерер для HeroRouletteScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/hero_roulette.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer
from ui.constants import *

import math
import random
import time
from ui.components import Button
from ui.constants import *
from ui.assets import assets
from ui.notifications import notify


class HeroRouletteRenderer(BaseRenderer):
    """
    Малює HeroRouletteScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        screen.fill((8, 6, 4))

        # Заголовок
        fh = assets.get_font(FONT_SIZE_LARGE, bold=True)
        t = fh.render("⚔ Рулетка Героїв", True, COLOR_GOLD)
        screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, 24))

        # Спіни
        fs = assets.get_font(FONT_SIZE_NORMAL)
        sc = COLOR_GOLD if self.scene.roster.spins_left > 0 else COLOR_ERROR
        st = fs.render(f"🎰 Спінів: {self.scene.roster.spins_left}", True, sc)
        screen.blit(st, (SCREEN_WIDTH // 2 - st.get_width() // 2, 72))

        self._draw_strip(screen)

        if self.scene._state == self.scene._ST_IDLE:
            fn = assets.get_font(FONT_SIZE_NORMAL)
            hint = fn.render("Натисни 'Крутити' щоб отримати героя!", True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                               self.scene._strip_y + self.scene._card_h + 24))
            self.scene._btn_spin.draw(screen)

        elif self.scene._state == self.scene._ST_SPINNING:
            fn = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
            col = (int(200 + 55 * math.sin(time.time() * 8)),
                   int(150 + 50 * math.sin(time.time() * 6)), 50)
            txt = fn.render("Крутиться...", True, col)
            screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                               self.scene._strip_y + self.scene._card_h + 24))

        elif self.scene._state == self.scene._ST_RESULT:
            self._draw_result(screen)
            self.scene._btn_keep.draw(screen)
            if self.scene.roster.can_spin():
                self.scene._btn_reroll.draw(screen)
            else:
                fn = assets.get_font(FONT_SIZE_SMALL)
                ns = fn.render("Більше немає спінів — залиш цього героя", True, COLOR_TEXT_DIM)
                screen.blit(ns, (SCREEN_WIDTH // 2 - ns.get_width() // 2, SCREEN_HEIGHT - 60))

    def _draw_strip(self, screen: pygame.Surface):
        cw = self.scene._card_w
        ch = self.scene._card_h
        sy = self.scene._strip_y
        cx = SCREEN_WIDTH // 2
        visible_w = int(SCREEN_WIDTH * 0.85)
        mask_x = cx - visible_w // 2

        # Перший абсолютний індекс видимої зони
        first_abs = int(self.scene._strip_offset) // cw - 1
        count = visible_w // cw + 4

        for i in range(count):
            abs_idx  = first_abs + i
            list_idx = abs_idx % len(self.scene._strip_ids)
            hid  = self.scene._strip_ids[list_idx]
            hero = HEROES.get(hid)
            if not hero:
                continue

            card_x = abs_idx * cw - int(self.scene._strip_offset)
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
            t = self.scene._anim_timers.get(hero.hero_id, 0.0)
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
            if hero.hero_id not in self.scene._anim_timers:
                self.scene._anim_timers[hero.hero_id] = 0.0
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
        if not self.scene._result_hero:
            return
        hero = self.scene._result_hero
        rar_col = HERO_RARITY_COLORS.get(hero.rarity, COLOR_GOLD)

        pw, ph = 480, 200
        px = SCREEN_WIDTH // 2 - pw // 2
        py = self.scene._strip_y + self.scene._card_h + 18

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