"""
Рендерер для AdminScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/admin.py
"""
from scenes.core.admin import (
    _W, _H, _X, _Y, _TAB_H, _CONTENT_Y, _CONTENT_H, _ROW_H,
    _COL_L, _COL_R, _TABS,
    _C_PANEL, _C_HEADER, _C_ROW, _C_ROW_H, _C_SEL, _C_BORDER,
    _C_GOLD, _C_GREEN, _C_RED, _C_DIM, _C_TEXT,
)

import time
from game.data import MATERIALS
from game.data import ITEMS
from game.data import BLUEPRINTS
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button
from ui.constants import *
from ui.assets import assets


class AdminRenderer(BaseRenderer):
    """
    Малює AdminScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170)); screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, _C_PANEL,  (_X, _Y, _W, _H), border_radius=10)
        pygame.draw.rect(screen, _C_BORDER, (_X, _Y, _W, _H), 2, border_radius=10)

        # Заголовок
        fn_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = fn_title.render("ADMIN", True, _C_RED)
        screen.blit(title, (_X + 16, _Y + 10))

        self._draw_tabs(screen)
        self._draw_search_bar(screen)

        if   self.scene._tab == "player":     self._draw_player(screen)
        elif self.scene._tab == "materials":  self._draw_list(screen, MATERIALS,  self.scene._row_material)
        elif self.scene._tab == "items":      self._draw_list(screen, ITEMS,      self.scene._row_item)
        elif self.scene._tab == "blueprints": self._draw_list(screen, BLUEPRINTS, self.scene._row_blueprint)
        elif self.scene._tab == "battle":     self._draw_battle(screen)
        elif self.scene._tab == "skip":       self._draw_skip(screen)
        elif self.scene._tab == "system":     self._draw_system(screen)

        self._draw_statusbar(screen)
        self.scene._close_btn.draw(screen)
        if self.scene._input_mode: self._draw_input_overlay(screen)

    def _draw_tabs(self, screen):
        tab_w = _W // len(_TABS)
        for i, (label, key) in enumerate(_TABS):
            active = key == self.scene._tab
            x = _X + i * tab_w
            color = _C_SEL if active else _C_HEADER
            pygame.draw.rect(screen, color, (x+1, _Y+4, tab_w-2, _TAB_H-4), border_radius=6)
            if active:
                pygame.draw.rect(screen, _C_GOLD, (x+1, _Y+4, tab_w-2, _TAB_H-4), 1, border_radius=6)
            fn = assets.get_font(14)
            lbl = fn.render(label, True, _C_TEXT if active else _C_DIM)
            screen.blit(lbl, (x + (tab_w - lbl.get_width())//2,
                               _Y+4 + (_TAB_H-4-lbl.get_height())//2))

    def _draw_search_bar(self, screen):
        if self.scene._tab not in ("materials","items","blueprints"): return
        sy = _Y + _TAB_H + 8
        pygame.draw.rect(screen, _C_ROW, (_COL_L, sy, _W-32, 32), border_radius=4)
        pygame.draw.rect(screen, _C_BORDER, (_COL_L, sy, _W-32, 32), 1, border_radius=4)
        fn = assets.get_font(FONT_SIZE_SMALL)
        prompt = self.scene._search + "I" if self.scene._search else "Пошук..."
        lbl = fn.render(prompt, True, _C_TEXT if self.scene._search else _C_DIM)
        screen.blit(lbl, (_COL_L + 8, sy + 8))
        if self.scene._tab == "materials":
            qty_lbl = fn.render(f"x{self.scene._qty}  [Ctrl+Q]", True, _C_DIM)
            screen.blit(qty_lbl, (_COL_L + _W - 32 - qty_lbl.get_width() - 8, sy + 8))

    def _draw_list(self, screen, data_dict, row_fn):
        area = self.scene._rows_area()
        filtered = self.scene._filtered(data_dict)
        total = len(filtered)
        self.scene._clip_scroll(total)

        clip = pygame.Surface((area.width, area.height), pygame.SRCALPHA)
        first = self.scene._scroll // _ROW_H
        last  = min(total, first + area.height // _ROW_H + 2)
        off_y = -(self.scene._scroll % _ROW_H)

        for i in range(first, last):
            k, v = filtered[i]
            ry = (i - first) * _ROW_H + off_y
            row_fn(clip, ry, area.width, k, v, i == self.scene._hovered)

        screen.blit(clip, area.topleft)

        # Смуга прокрутки
        if total * _ROW_H > area.height:
            th = max(24, area.height * area.height // (total * _ROW_H))
            ty = int(self.scene._scroll / max(1, total*_ROW_H - area.height) * (area.height - th))
            sx = area.right + 4
            pygame.draw.rect(screen, _C_ROW,   (sx, area.y, 6, area.height), border_radius=3)
            pygame.draw.rect(screen, _C_GOLD,  (sx, area.y+ty, 6, th),       border_radius=3)

        # Кількість результатів
        fn = assets.get_font(FONT_SIZE_SMALL)
        cnt_lbl = fn.render(f"{total} записів", True, _C_DIM)
        screen.blit(cnt_lbl, (_COL_L, _Y + _H - 56))

    def _draw_player(self, screen):
        p = self.scene.player
        fn  = assets.get_font(FONT_SIZE_NORMAL)
        fns = assets.get_font(FONT_SIZE_SMALL)
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        sy  = _CONTENT_Y

        screen.blit(fnb.render("Статистика", True, _C_GOLD), (_COL_L, sy)); sy += 36
        stats = [
            ("Рівень",   str(p.level)),
            ("HP",       f"{p.hp} / {p.max_hp}"),
            ("Атака",    str(p.attack)),
            ("Захист",   str(p.defense)),
            ("Золото",   str(p.gold)),
            ("XP",       f"{p.xp} / {p.xp_next}"),
            ("Вбито",    str(getattr(p,"enemies_killed",0))),
            ("Перемог",  str(getattr(p,"battles_won",0))),
            ("Предметів",str(len(p.inventory))),
        ]
        for name, val in stats:
            pygame.draw.rect(screen, _C_ROW, (_COL_L, sy, _W//2-20, 30), border_radius=3)
            screen.blit(fns.render(name, True, _C_DIM),  (_COL_L+8, sy+7))
            screen.blit(fns.render(val,  True, _C_TEXT), (_COL_L+180, sy+7))
            sy += 34

        # Дії
        bx = _COL_R
        screen.blit(fnb.render("Швидкі дії", True, _C_GOLD), (bx, _CONTENT_Y))
        for btn in self.scene._player_btns:
            btn.draw(screen)

    def _draw_battle(self, screen):
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        fns = assets.get_font(FONT_SIZE_SMALL)
        sy  = _CONTENT_Y
        p   = self.scene.player

        screen.blit(fnb.render("Бойова статистика", True, _C_GOLD), (_COL_L, sy)); sy += 44
        rows = [
            ("Ворогів вбито",   getattr(p,"enemies_killed",0)),
            ("Перемог",         getattr(p,"battles_won",0)),
            ("Гоблінів",        getattr(p,"goblins_killed",0)),
            ("Орків",           getattr(p,"orcs_killed",0)),
            ("Темних лицарів",  getattr(p,"dark_knights_killed",0)),
            ("Критичних ударів",getattr(p,"total_crits",0)),
        ]
        for name, val in rows:
            pygame.draw.rect(screen, _C_ROW, (_COL_L, sy, 360, 30), border_radius=3)
            screen.blit(fns.render(name, True, _C_DIM),  (_COL_L+8, sy+7))
            screen.blit(fns.render(str(val), True, _C_TEXT), (_COL_L+260, sy+7))
            sy += 34

        screen.blit(fnb.render("Тестування", True, _C_GOLD), (_COL_R, _CONTENT_Y))
        for btn in self.scene._battle_btns:
            btn.draw(screen)

    def _draw_skip(self, screen):
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        fns = assets.get_font(FONT_SIZE_SMALL)
        sy  = _CONTENT_Y

        screen.blit(fnb.render("Пропуск очікувань", True, _C_GOLD), (_COL_L, sy))
        sy += 44

        # Малюємо кнопки
        for btn in self.scene._skip_btns:
            btn.draw(screen)

        # Права колонка — поточний статус таймерів
        bx = _COL_R
        screen.blit(fnb.render("Поточний стан", True, _C_GOLD), (bx, _CONTENT_Y))
        sy2 = _CONTENT_Y + 44

        def status_row(label, value, color=None):
            nonlocal sy2
            pygame.draw.rect(screen, _C_ROW, (bx, sy2, 300, 28), border_radius=3)
            screen.blit(fns.render(label, True, _C_DIM),  (bx+8,   sy2+6))
            clr = color or _C_TEXT
            screen.blit(fns.render(str(value), True, clr), (bx+180, sy2+6))
            sy2 += 32

        # Крафт
        q = getattr(self.scene.player, "crafting_queue", None)
        if q:
            active = [o for o in q.orders if not o.is_done()]
            done   = [o for o in q.orders if  o.is_done()]
            if active:
                secs = max(0, int(active[0].finish_at - time.time()))
                status_row("Крафт", f"{len(active)} в черзі, {secs}с",
                           _C_RED if secs > 0 else _C_GREEN)
            else:
                status_row("Крафт", "порожньо", _C_DIM)

        # Розбирання
        dq = getattr(self.scene.player, "dismantle_queue", None)
        if dq:
            active_d = [o for o in dq.orders if not o.is_done()]
            if active_d:
                secs = max(0, int(active_d[0].finish_at - time.time()))
                status_row("Розбирання", f"{len(active_d)} в черзі, {secs}с",
                           _C_RED if secs > 0 else _C_GREEN)
            else:
                status_row("Розбирання", "порожньо", _C_DIM)

        # Ринок
        m = getattr(self.scene.player, "market", None)
        if m:
            t = m.time_to_refresh()
            if t > 0:
                mins = int(t // 60); secs = int(t % 60)
                status_row("Ринок", f"оновлення через {mins}хв {secs}с", _C_RED)
            else:
                status_row("Ринок", "готовий до оновлення", _C_GREEN)

        # Шахтар
        mn = getattr(self.scene.player, "miner", None)
        if mn:
            tl = mn.time_left() if hasattr(mn, "time_left") else 0
            if tl > 0:
                mins = tl // 60; secs = tl % 60
                status_row("Шахтар", f"копає, {mins}хв {secs}с", _C_RED)
            else:
                status_row("Шахтар", "вільний", _C_GREEN)

        # Щоденні квести
        daily = getattr(self.scene.player, "daily_quests", None)
        if daily:
            done_count = sum(1 for dq2 in daily.quests if dq2.done)
            total      = len(daily.quests)
            status_row("Щоденні квести", f"{done_count}/{total} виконано",
                       _C_GREEN if done_count == total else _C_TEXT)

    def _draw_system(self, screen):
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        fns = assets.get_font(FONT_SIZE_SMALL)
        sy  = _CONTENT_Y

        screen.blit(fnb.render("Система", True, _C_GOLD), (_COL_L, sy)); sy += 44

        for btn in self.scene._system_btns:
            btn.draw(screen)
        sy += 48 * len(self.scene._system_btns)

        sy += 16
        info = [
            ("FPS", str(round(self.scene.game.clock.get_fps())) if hasattr(self.scene.game,"clock") else "?"),
            ("Сцена", type(self.scene.game.current_scene).__name__ if hasattr(self.scene.game,"current_scene") else "?"),
        ]
        for k, v in info:
            screen.blit(fns.render(f"{k}:  {v}", True, _C_DIM), (_COL_L, sy))
            sy += 24

        sy += 20
        screen.blit(fnb.render("Гарячі клавіші", True, _C_GOLD), (_COL_L, sy)); sy += 36
        for k, v in [("F12","Адмін-панель"),("Ctrl+F5","Hot-reload"),
                     ("F5","Зберегти"),("Ctrl+Q","Змінити кількість"),
                     ("Scroll","Прокрутка"),("Друкування","Пошук")]:
            screen.blit(fns.render(k, True, _C_GOLD), (_COL_L, sy))
            screen.blit(fns.render(v, True, _C_DIM),  (_COL_L+130, sy))
            sy += 24

    def _draw_input_overlay(self, screen):
        ov = pygame.Surface((_W, _H), pygame.SRCALPHA)
        ov.fill((0,0,0,160)); screen.blit(ov, (_X, _Y))
        prompts = {"gold":"Скільки золота?","xp":"Скільки XP?",
                   "level":"Рівень (1-99):","qty":"Кількість за клік:"}
        fn = assets.get_font(FONT_SIZE_MEDIUM)
        ix, iy = SCREEN_WIDTH//2-180, SCREEN_HEIGHT//2-60
        pygame.draw.rect(screen, _C_PANEL, (ix-20,iy-20,400,120), border_radius=8)
        pygame.draw.rect(screen, _C_GOLD,  (ix-20,iy-20,400,120), 2, border_radius=8)
        screen.blit(fn.render(prompts.get(self.scene._input_mode,"Введіть:"), True, _C_TEXT), (ix, iy))
        ir = pygame.Rect(ix, iy+40, 360, 44)
        pygame.draw.rect(screen, _C_ROW, ir, border_radius=4)
        pygame.draw.rect(screen, _C_GOLD, ir, 2, border_radius=4)
        screen.blit(fn.render((self.scene._input or "0")+"I", True, _C_TEXT), (ir.x+10, ir.y+8))
        screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
            "Enter - ОК  |  ESC - скасувати", True, _C_DIM), (ix, iy+92))

    def _draw_statusbar(self, screen):
        sy = _Y + _H - 52
        if self.scene._msg and self.scene._msg_timer > 0:
            screen.blit(assets.get_font(FONT_SIZE_NORMAL).render(
                self.scene._msg, True, self.scene._msg_color), (_X+16, sy+12))
        elif self.scene._tab in ("materials","items","blueprints"):
            screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
                "Друкуй для пошуку  *  колесо миші - прокрутка  *  Ctrl+Q - змінити кількість",
                True, _C_DIM), (_X+16, sy+14))