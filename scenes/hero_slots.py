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
from scenes.hero_roulette import _get_idle_frames, _RARITY_BG

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
        screen.fill((10, 8, 6))

        fh = assets.get_font(FONT_SIZE_LARGE, bold=True)
        t = fh.render("⚔ Герої", True, COLOR_GOLD)
        screen.blit(t, (_SW // 2 - t.get_width() // 2, 18))

        fn = assets.get_font(FONT_SIZE_SMALL)
        spin_s = fn.render(f"🎰 Спінів: {self.roster.spins_left}", True,
                           COLOR_GOLD if self.roster.spins_left > 0 else COLOR_TEXT_DIM)
        screen.blit(spin_s, (_SW - 180, 22))

        self._draw_slots(screen)
        self._draw_slot_label(screen)
        self._draw_collection(screen)
        self._draw_collection_label(screen)

        self._btn_back.draw(screen)
        self._btn_roulette.draw(screen)
        if self._sel_coll >= 0:
            self._btn_set.draw(screen)

        # Tooltip поверх усього
        if self._hover_idx >= 0:
            coll = self.roster.collection
            if self._hover_idx < len(coll):
                hero = HEROES.get(coll[self._hover_idx].hero_id)
                if hero:
                    self._draw_tooltip(screen, hero, pygame.mouse.get_pos())

    def _draw_slot_label(self, screen: pygame.Surface):
        fm = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        lbl = fm.render("Активні слоти:", True, COLOR_GOLD)
        screen.blit(lbl, (30, _SLOT_Y - 24))

    def _draw_collection_label(self, screen: pygame.Surface):
        fm = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        coll = self.roster.collection
        lbl = fm.render(f"Колекція ({len(coll)} героїв):", True, COLOR_GOLD)
        screen.blit(lbl, (30, _GRID_Y - 26))

    def _draw_slots(self, screen: pygame.Surface):
        mp = pygame.mouse.get_pos()
        fs = assets.get_font(FONT_SIZE_SMALL)

        for i in range(4):
            r = self._slot_rect(i)
            is_active  = (i == self.roster.active_slot)
            is_sel     = (i == self._sel_slot)
            is_locked  = (i >= self.roster.slots_unlocked)
            is_hov     = r.collidepoint(mp)
            hero_id    = self.roster.slots[i] if not is_locked else None
            hero       = HEROES.get(hero_id) if hero_id else None
            rar_col    = HERO_RARITY_COLORS.get(hero.rarity, (180,180,180)) if hero else (80,70,50)

            # Фон
            bg_a = 220
            if is_active:   bg = (50, 42, 12)
            elif is_sel:    bg = (38, 32, 14)
            elif is_hov:    bg = (30, 26, 16)
            else:           bg = (18, 15, 10)
            border = COLOR_GOLD if is_active else rar_col if is_sel else (60, 52, 28)

            surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            surf.fill((*bg, bg_a))
            pygame.draw.rect(surf, border, surf.get_rect(), 2, border_radius=10)
            screen.blit(surf, r.topleft)

            if is_locked:
                # Замок
                lf = assets.get_font(32)
                ls = lf.render("🔒", True, (100, 90, 60))
                screen.blit(ls, (r.x + r.w//2 - ls.get_width()//2, r.y + 38))
                slot_num = i + 1
                if slot_num in SLOT_UNLOCK_LEVELS:
                    req = SLOT_UNLOCK_LEVELS[slot_num]
                    cond = f"Рівень {req}"
                    ok = self.player.level >= req
                elif slot_num in SLOT_UNLOCK_GOLD:
                    cost = SLOT_UNLOCK_GOLD[slot_num]
                    cond = f"{cost} 🪙"
                    ok = self.player.gold >= cost
                else:
                    cond, ok = "???", False
                cs = fs.render(cond, True, (120,200,80) if ok else (160,120,60))
                screen.blit(cs, (r.x + r.w//2 - cs.get_width()//2, r.y + 80))
            elif hero:
                # Анімація idle
                frames = _get_idle_frames(hero.hero_id)
                if frames:
                    t = self._anim_t.get(hero.hero_id, 0.0)
                    if hero.hero_id not in self._anim_t:
                        self._anim_t[hero.hero_id] = 0.0
                    fidx = int(t * 8) % len(frames)
                    frame = frames[fidx]
                    scale_f = (r.w - 16) / frame.get_width()
                    fw = int(frame.get_width() * scale_f)
                    fh_px = int(frame.get_height() * scale_f)
                    scaled = pygame.transform.scale(frame, (fw, min(fh_px, r.h - 48)))
                    screen.blit(scaled, (r.x + r.w//2 - fw//2, r.y + 4))
                else:
                    fi = assets.get_font(40)
                    ic = fi.render(hero.icon, True, rar_col)
                    screen.blit(ic, (r.x + r.w//2 - ic.get_width()//2, r.y + 20))

                # Назва внизу
                nm = fs.render(hero.name[:16], True, rar_col)
                screen.blit(nm, (r.x + r.w//2 - nm.get_width()//2, r.y + r.h - 36))
                rn = assets.get_font(10).render(HERO_RARITY_NAMES_UA.get(hero.rarity,""), True, rar_col)
                screen.blit(rn, (r.x + r.w//2 - rn.get_width()//2, r.y + r.h - 20))
                if is_active:
                    act = fs.render("▶ АКТИВНИЙ", True, COLOR_GOLD)
                    screen.blit(act, (r.x + r.w//2 - act.get_width()//2, r.y + r.h - 54))
            else:
                em = fs.render("— порожньо —", True, (80, 70, 50))
                screen.blit(em, (r.x + r.w//2 - em.get_width()//2, r.y + r.h//2 - 8))

            # Номер слоту
            ns = assets.get_font(10).render(f"Слот {i+1}", True, COLOR_TEXT_DIM)
            screen.blit(ns, (r.x + 8, r.y + 6))

    def _draw_collection(self, screen: pygame.Surface):
        coll = self.roster.collection
        fs = assets.get_font(FONT_SIZE_SMALL)

        if not coll:
            fn = assets.get_font(FONT_SIZE_NORMAL)
            hint = fn.render("Колекція порожня — крути рулетку!", True, COLOR_TEXT_DIM)
            screen.blit(hint, (30, _GRID_Y))
            return

        for row in range(_GRID_ROWS_VIS):
            for col in range(_CARDS_PER_ROW):
                idx = (self._scroll + row) * _CARDS_PER_ROW + col
                if idx >= len(coll):
                    break
                oh   = coll[idx]
                hero = HEROES.get(oh.hero_id)
                if not hero:
                    continue

                r = self._card_rect(row, col)
                is_sel = (idx == self._sel_coll)
                is_hov = (idx == self._hover_idx)
                rar_col = HERO_RARITY_COLORS.get(hero.rarity, (180,180,180))

                # Фон
                if is_sel:       bg = (60, 50, 14, 220)
                elif is_hov:     bg = (40, 36, 18, 200)
                else:            bg = (20, 17, 12, 180)
                border = rar_col if (is_sel or is_hov) else (50, 44, 28)

                surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                surf.fill(bg)
                pygame.draw.rect(surf, border, surf.get_rect(), 2, border_radius=8)
                screen.blit(surf, r.topleft)

                # Смужка рідкості зліва
                pygame.draw.rect(screen, rar_col, (r.x, r.y, 3, r.h), border_radius=2)

                # Анімація idle
                frames = _get_idle_frames(hero.hero_id)
                if frames:
                    if hero.hero_id not in self._anim_t:
                        self._anim_t[hero.hero_id] = 0.0
                    t = self._anim_t[hero.hero_id]
                    fidx = int(t * 8) % len(frames)
                    frame = frames[fidx]
                    scale_f = (r.w - 10) / frame.get_width()
                    fw = int(frame.get_width() * scale_f)
                    fh_px = int(frame.get_height() * scale_f)
                    fh_clamped = min(fh_px, r.h - 44)
                    fw_clamped = int(fw * fh_clamped / fh_px) if fh_px > 0 else fw
                    scaled = pygame.transform.scale(frame, (fw_clamped, fh_clamped))
                    screen.blit(scaled, (r.x + r.w//2 - fw_clamped//2, r.y + 4))
                else:
                    fi = assets.get_font(32)
                    ic = fi.render(hero.icon, True, rar_col)
                    screen.blit(ic, (r.x + r.w//2 - ic.get_width()//2, r.y + 20))

                # Назва
                nm = fs.render(hero.name[:14], True, rar_col if (is_sel or is_hov) else COLOR_TEXT)
                screen.blit(nm, (r.x + r.w//2 - nm.get_width()//2, r.y + r.h - 34))
                rn = assets.get_font(10).render(HERO_RARITY_NAMES_UA.get(hero.rarity,""), True, rar_col)
                screen.blit(rn, (r.x + r.w//2 - rn.get_width()//2, r.y + r.h - 18))

                # Мітка "в слоті"
                for si, sid in enumerate(self.roster.slots):
                    if sid == oh.hero_id:
                        sl = assets.get_font(10).render(f"[Слот {si+1}]", True, COLOR_GOLD)
                        screen.blit(sl, (r.x + r.w - sl.get_width() - 6, r.y + 6))
                        break

    def _draw_tooltip(self, screen: pygame.Surface, hero, mp):
        """Спливаюче вікно з повним описом героя."""
        tw, th = 320, 260
        # Позиція — щоб не вилізти за край
        tx = min(mp[0] + 16, _SW - tw - 8)
        ty = min(mp[1] + 8,  _SH - th - 8)
        if ty < 0: ty = 8

        rar_col = HERO_RARITY_COLORS.get(hero.rarity, (180,180,180))
        bg_raw  = _RARITY_BG.get(hero.rarity, (20,20,20))

        panel = pygame.Surface((tw, th), pygame.SRCALPHA)
        panel.fill((*bg_raw, 240))
        pygame.draw.rect(panel, rar_col, panel.get_rect(), 2, border_radius=10)
        screen.blit(panel, (tx, ty))

        px, py = tx + 12, ty + 10
        fh = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        fs = assets.get_font(FONT_SIZE_SMALL)
        f10 = assets.get_font(10)

        # Іконка + назва
        fi = assets.get_font(32)
        ic = fi.render(hero.icon, True, rar_col)
        screen.blit(ic, (px, py))
        screen.blit(fh.render(hero.name, True, rar_col), (px + 42, py + 2))
        rar_name = HERO_RARITY_NAMES_UA.get(hero.rarity, "")
        screen.blit(f10.render(f"✦ {rar_name}", True, rar_col), (px + 42, py + 22))
        py += 44

        # Лор
        screen.blit(f10.render(hero.lore[:55], True, COLOR_TEXT_DIM), (px, py)); py += 16

        pygame.draw.line(screen, (60,55,35), (px, py), (tx+tw-12, py)); py += 8

        # Бонуси
        b = hero.passive_bonuses()
        parts = []
        if b["hp"]:      parts.append(f"+{b['hp']}HP")
        if b["attack"]:  parts.append(f"+{b['attack']}ATK")
        if b["defense"]: parts.append(f"+{b['defense']}DEF")
        if b["crit"]:    parts.append(f"+{int(b['crit']*100)}%крит")
        if b["dodge"]:   parts.append(f"+{int(b['dodge']*100)}%ухил")
        if parts:
            screen.blit(fs.render("  ".join(parts), True, (120,200,120)), (px, py)); py += 18

        pygame.draw.line(screen, (60,55,35), (px, py), (tx+tw-12, py)); py += 8

        # Навички
        for sk in hero.skills:
            prefix = "⚡" if not sk.is_passive else "🔹"
            col = (255,200,80) if not sk.is_passive else COLOR_TEXT
            screen.blit(f10.render(f"{prefix} {sk.name}: {sk.desc[:42]}", True, col), (px, py))
            py += 15
            if py > ty + th - 14:
                break