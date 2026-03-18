"""
Компонент Dropdown — випадаючий список з прокруткою.

Використання:
    from ui.dropdown import Dropdown

    self.filter_dd = Dropdown(
        x=100, y=152, width=180, height=34,
        label="Фільтр",
        options=[
            ("all",     "Все"),
            ("weapon",  "⚔ Зброя"),
            ("armor",   "🛡 Броня"),
        ],
        on_change=lambda val: self._set_filter(val),
    )

В handle_event (ПЕРЕД іншими обробниками):
    if self.filter_dd.handle_event(event): return

В update:
    self.filter_dd.update(pygame.mouse.get_pos())

В draw (ПІСЛЯ основного контенту, ПЕРЕД confirm):
    self.filter_dd.draw(screen)
"""

import math
import pygame
from ui.constants import (
    COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_BTN_NORMAL, COLOR_BTN_HOVER, COLOR_BTN_PRESSED,
    COLOR_PANEL, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, SCREEN_HEIGHT
)


# Скільки пунктів показувати одночасно до появи скролу
MAX_VISIBLE = 8
ITEM_H      = 30
SCROLL_W    = 8


class Dropdown:
    """
    Кнопка-заголовок + випадаючий список із скролом.
    Список відкривається вниз (або вгору якщо не влізає).
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 label: str,
                 options: list[tuple[str, str]],
                 on_change=None,
                 initial: str | None = None):
        """
        options: список (value, display_text)
        on_change: callback(value: str)
        initial: початкове значення (value); якщо None — перший елемент
        """
        self.x       = x
        self.y       = y
        self.width   = width
        self.height  = height
        self.label   = label
        self.options = options          # list[(value, text)]
        self.on_change = on_change

        self.header_rect = pygame.Rect(x, y, width, height)
        self._open       = False
        self._scroll     = 0           # індекс першого видимого пункту
        self._hovered    = -1          # індекс пункту під курсором
        self._anim_t     = 0.0

        # Встановлюємо початкове значення
        if initial and any(v == initial for v, _ in options):
            self._value = initial
        elif options:
            self._value = options[0][0]
        else:
            self._value = ""

    # ── Публічний API ────────────────────────────────────────────

    @property
    def value(self) -> str:
        return self._value

    def set_value(self, val: str, silent: bool = True):
        """Змінює значення програмно (без виклику on_change якщо silent=True)."""
        if any(v == val for v, _ in self.options):
            self._value = val
            if not silent and self.on_change:
                self.on_change(val)

    def close(self):
        self._open   = False
        self._hovered = -1

    # ── Геометрія списку ─────────────────────────────────────────

    def _visible_count(self) -> int:
        return min(MAX_VISIBLE, len(self.options))

    def _list_height(self) -> int:
        return self._visible_count() * ITEM_H

    def _list_rect(self) -> pygame.Rect:
        lh = self._list_height()
        # Відкриваємо вниз якщо влізає, інакше вгору
        if self.y + self.height + lh <= SCREEN_HEIGHT - 20:
            ly = self.y + self.height + 2
        else:
            ly = self.y - lh - 2
        return pygame.Rect(self.x, ly, self.width, lh)

    def _item_rect(self, local_idx: int) -> pygame.Rect:
        lr = self._list_rect()
        return pygame.Rect(lr.x, lr.y + local_idx * ITEM_H,
                           lr.width - (SCROLL_W + 2 if self._needs_scroll() else 0),
                           ITEM_H)

    def _needs_scroll(self) -> bool:
        return len(self.options) > MAX_VISIBLE

    def _scroll_track_rect(self) -> pygame.Rect:
        lr = self._list_rect()
        return pygame.Rect(lr.right - SCROLL_W, lr.y, SCROLL_W, lr.height)

    def _scroll_thumb_rect(self) -> pygame.Rect:
        tr = self._scroll_track_rect()
        total = len(self.options)
        vis   = self._visible_count()
        thumb_h = max(16, int(tr.height * vis / total))
        max_scroll = total - vis
        pct = self._scroll / max_scroll if max_scroll else 0
        thumb_y = tr.y + int((tr.height - thumb_h) * pct)
        return pygame.Rect(tr.x, thumb_y, SCROLL_W, thumb_h)

    # ── Обробка подій ────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Повертає True якщо подія спожита."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mp = event.pos

            # Клік по заголовку
            if self.header_rect.collidepoint(mp):
                self._open = not self._open
                self._scroll = max(0, self._selected_idx() - MAX_VISIBLE // 2)
                return True

            if self._open:
                lr = self._list_rect()

                # Скрол колесом
                if event.button == 4:
                    self._scroll = max(0, self._scroll - 1)
                    return True
                if event.button == 5:
                    self._scroll = min(len(self.options) - self._visible_count(),
                                       self._scroll + 1)
                    return True

                # Клік по пункту списку
                if event.button == 1:
                    if lr.collidepoint(mp):
                        for i in range(self._visible_count()):
                            ir = self._item_rect(i)
                            if ir.collidepoint(mp):
                                real_idx = i + self._scroll
                                val = self.options[real_idx][0]
                                if val != self._value:
                                    self._value = val
                                    if self.on_change:
                                        self.on_change(val)
                                self._open = False
                                return True
                        return True  # клік всередині списку але не по пункту
                    else:
                        # Клік поза списком — закрити
                        self._open = False
                        return False  # не споживаємо, щоб інші елементи реагували

        # Скрол колесом коли відкрито
        if event.type == pygame.MOUSEWHEEL and self._open:
            self._scroll = max(0, min(
                len(self.options) - self._visible_count(),
                self._scroll - event.y
            ))
            return True

        if event.type == pygame.KEYDOWN and self._open:
            if event.key == pygame.K_ESCAPE:
                self._open = False
                return True
            if event.key == pygame.K_UP:
                idx = max(0, self._selected_idx() - 1)
                self._value = self.options[idx][0]
                self._ensure_visible(idx)
                if self.on_change: self.on_change(self._value)
                return True
            if event.key == pygame.K_DOWN:
                idx = min(len(self.options) - 1, self._selected_idx() + 1)
                self._value = self.options[idx][0]
                self._ensure_visible(idx)
                if self.on_change: self.on_change(self._value)
                return True
            if event.key == pygame.K_RETURN:
                self._open = False
                return True

        return False

    def _selected_idx(self) -> int:
        for i, (v, _) in enumerate(self.options):
            if v == self._value:
                return i
        return 0

    def _ensure_visible(self, idx: int):
        vis = self._visible_count()
        if idx < self._scroll:
            self._scroll = idx
        elif idx >= self._scroll + vis:
            self._scroll = idx - vis + 1

    # ── Update ───────────────────────────────────────────────────

    def update(self, mouse_pos: tuple):
        self._anim_t += 0.016
        self._hovered = -1
        if self._open:
            for i in range(self._visible_count()):
                if self._item_rect(i).collidepoint(mouse_pos):
                    self._hovered = i + self._scroll
                    break

    # ── Draw ─────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        from ui.assets import assets

        font   = assets.get_font(FONT_SIZE_NORMAL)
        font_s = assets.get_font(FONT_SIZE_SMALL)

        # ── Заголовок кнопка ──
        hr     = self.header_rect
        mp     = pygame.mouse.get_pos()
        hov    = hr.collidepoint(mp)
        bg     = COLOR_BTN_HOVER if (hov or self._open) else COLOR_BTN_NORMAL
        border = COLOR_GOLD if self._open else (
            COLOR_GOLD if hov else (100, 80, 50))

        pygame.draw.rect(screen, bg, hr, border_radius=6)
        pygame.draw.rect(screen, border, hr, 2, border_radius=6)

        # Поточне значення
        cur_text = next((t for v, t in self.options if v == self._value), self._value)
        lbl_s = font_s.render(self.label + ":", True, COLOR_TEXT_DIM)
        val_s = font.render(cur_text, True, COLOR_TEXT)

        # Підпис зліва від кнопки
        screen.blit(lbl_s, (hr.x - lbl_s.get_width() - 8,
                              hr.centery - lbl_s.get_height() // 2))

        # Значення всередині кнопки
        screen.blit(val_s, (hr.x + 10, hr.centery - val_s.get_height() // 2))

        # Стрілка
        arrow = "▲" if self._open else "▼"
        arr_s = font_s.render(arrow, True, COLOR_GOLD)
        screen.blit(arr_s, (hr.right - arr_s.get_width() - 8,
                              hr.centery - arr_s.get_height() // 2))

        if not self._open:
            return

        # ── Список ──
        lr = self._list_rect()

        # Тінь
        shadow = pygame.Surface((lr.width + 6, lr.height + 6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 80))
        screen.blit(shadow, (lr.x - 2, lr.y + 4))

        # Фон списку
        bg_surf = pygame.Surface((lr.width, lr.height), pygame.SRCALPHA)
        bg_surf.fill((28, 22, 14, 248))
        screen.blit(bg_surf, lr)
        pygame.draw.rect(screen, COLOR_GOLD, lr, 2, border_radius=4)

        # Пункти
        vis = self._visible_count()
        for i in range(vis):
            real_idx = i + self._scroll
            val, txt  = self.options[real_idx]
            ir        = self._item_rect(i)
            is_sel    = (val == self._value)
            is_hov    = (real_idx == self._hovered)

            # Підсвітка рядка
            if is_sel:
                sel_s = pygame.Surface((ir.width, ir.height), pygame.SRCALPHA)
                sel_s.fill((60, 48, 12, 220))
                screen.blit(sel_s, ir)
                pygame.draw.rect(screen, COLOR_GOLD, ir, 1)
            elif is_hov:
                hov_s = pygame.Surface((ir.width, ir.height), pygame.SRCALPHA)
                hov_s.fill((50, 40, 20, 180))
                screen.blit(hov_s, ir)

            clr  = COLOR_GOLD if is_sel else COLOR_TEXT
            txt_s = font.render(txt, True, clr)
            screen.blit(txt_s, (ir.x + 10, ir.centery - txt_s.get_height() // 2))

            # Галочка для вибраного
            if is_sel:
                chk = font_s.render("✓", True, COLOR_GOLD)
                screen.blit(chk, (ir.right - chk.get_width() - 6,
                                   ir.centery - chk.get_height() // 2))

            # Розділювач між рядками
            if i < vis - 1:
                pygame.draw.line(screen, (60, 48, 30),
                                 (ir.x + 4, ir.bottom), (ir.right - 4, ir.bottom))

        # ── Скролбар ──
        if self._needs_scroll():
            tr = self._scroll_track_rect()
            th = self._scroll_thumb_rect()
            pygame.draw.rect(screen, (40, 32, 18), tr, border_radius=4)
            pygame.draw.rect(screen, COLOR_GOLD,   th, border_radius=4)