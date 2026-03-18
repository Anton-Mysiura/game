"""
UI компоненти: Button, Panel, ProgressBar, Slot.
Стилі читаються з config/ui.py — редагуй там.
"""

import pygame
from typing import Optional, Callable
from .constants import *
from .assets import assets


# ══════════════════════════════════════════
#  КНОПКА
# ══════════════════════════════════════════

class Button:
    """
    Кнопка з підтримкою текстур і стилів.

    style — назва стилю з config/ui.py → BUTTON_STYLES:
        "default", "small", "danger", "success", "gold"
        або будь-який стиль що ти додав сам.
    """

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback: Optional[Callable] = None,
                 enabled: bool = True,
                 style: str = "default"):
        self.rect     = pygame.Rect(x, y, width, height)
        self.text     = text
        self.callback = callback
        self.enabled  = enabled
        self.style    = style
        self.hovered  = False
        self.pressed  = False
        self.selected = False  # для вкладок / активних станів

        # Кешуємо стиль
        self._style_dict = assets.get_button_style(style)

    # ── стан ──────────────────────────────────────────────────────
    def _current_state(self) -> str:
        if not self.enabled:    return "disabled"
        if self.selected:       return "pressed"
        if self.pressed:        return "pressed"
        if self.hovered:        return "hover"
        return "normal"

    # ── оновлення ─────────────────────────────────────────────────
    def update(self, mouse_pos: tuple, mouse_clicked: bool):
        if not self.enabled:
            self.hovered = False
            return

        self.hovered = self.rect.collidepoint(mouse_pos)

        if self.hovered and mouse_clicked and not self.pressed:
            self.pressed = True
            if self.callback:
                self.callback()
        elif not mouse_clicked:
            self.pressed = False

    # ── малювання ─────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        state = self._current_state()
        size  = (self.rect.width, self.rect.height)

        # Спочатку пробуємо текстуру
        tex = assets.get_button_texture(self.style, state, size)

        if tex:
            screen.blit(tex, self.rect)
        else:
            # Малюємо кольоровий прямокутник зі стилю
            s = self._style_dict
            color = s.get(f"color_{state}", s.get("color_normal", (80, 60, 40)))
            radius = s.get("corner_radius", 0)

            if radius > 0:
                pygame.draw.rect(screen, color, self.rect, border_radius=radius)
            else:
                pygame.draw.rect(screen, color, self.rect)

            # Рамка
            bw = s.get("border_width", 2)
            bc = s.get("border_color", COLOR_GOLD)
            if bw > 0:
                if radius > 0:
                    pygame.draw.rect(screen, bc, self.rect, bw, border_radius=radius)
                else:
                    pygame.draw.rect(screen, bc, self.rect, bw)

        # Текст
        s = self._style_dict
        font_size = s.get("font_size", FONT_SIZE_NORMAL)
        text_color = s.get("text_color_dis" if not self.enabled else "text_color",
                           COLOR_TEXT if self.enabled else COLOR_TEXT_DIM)
        font = assets.get_font(font_size)
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    # ── зручні методи ──────────────────────────────────────────────
    def move(self, x: int, y: int):
        """Переміщує кнопку."""
        self.rect.topleft = (x, y)

    def set_style(self, style: str):
        """Змінює стиль кнопки на льоту."""
        self.style = style
        self._style_dict = assets.get_button_style(style)


# ══════════════════════════════════════════
#  ПАНЕЛЬ
# ══════════════════════════════════════════

class Panel:
    """
    Прямокутна панель з підтримкою текстур і стилів.

    style — назва стилю з config/ui.py → PANEL_STYLES:
        "dark", "overlay", "wood", "stone"

    Зворотна сумісність: підтримує alpha=True, color=(...), use_texture=...
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 style: str = "dark",
                 # ── параметри зворотної сумісності ──
                 alpha: bool = False,
                 color: tuple = None,
                 use_texture: bool = False,
                 texture_name: str = "panel_dark"):
        self.rect  = pygame.Rect(x, y, width, height)
        # Якщо передано alpha=True — використовуємо стиль overlay
        if alpha and style == "dark":
            style = "overlay"
        self.style = style
        self._color_override = color   # якщо явно передали колір
        self._rebuild()

    def _rebuild(self):
        s = assets.get_panel_style(self.style)
        self._style_dict = s
        self._texture    = assets.get_panel_texture(self.style,
                                                    (self.rect.w, self.rect.h))
        alpha = s.get("alpha", 255)

        if not self._texture:
            color = self._color_override or s.get("color", COLOR_PANEL)
            if alpha < 255:
                self._surface = pygame.Surface(
                    (self.rect.w, self.rect.h), pygame.SRCALPHA)
                self._surface.fill((*color[:3], alpha))
            else:
                self._surface = pygame.Surface((self.rect.w, self.rect.h))
                self._surface.fill(color)

    def draw(self, screen: pygame.Surface):
        s = self._style_dict
        if self._texture:
            screen.blit(self._texture, self.rect)
        else:
            screen.blit(self._surface, self.rect)

        bw = s.get("border_width", 2)
        bc = s.get("border_color", COLOR_GOLD)
        r  = s.get("corner_radius", 0)
        if bw > 0:
            if r > 0:
                pygame.draw.rect(screen, bc, self.rect, bw, border_radius=r)
            else:
                pygame.draw.rect(screen, bc, self.rect, bw)

    def set_style(self, style: str):
        self.style = style
        self._rebuild()

    def resize(self, width: int, height: int):
        self.rect.size = (width, height)
        self._rebuild()


# ══════════════════════════════════════════
#  ПРОГРЕС-БАР
# ══════════════════════════════════════════

class ProgressBar:
    """Бар прогресу (HP/XP)."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 color_fill: tuple, show_text: bool = True):
        self.rect       = pygame.Rect(x, y, width, height)
        self.color_fill = color_fill
        self.show_text  = show_text

    def draw(self, screen: pygame.Surface, current: int, maximum: int, label: str = ""):
        value = max(0.0, min(1.0, current / maximum if maximum > 0 else 0))

        pygame.draw.rect(screen, COLOR_BAR_BG, self.rect)

        fill_w = int(self.rect.width * value)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(screen, self.color_fill, fill_rect)

        pygame.draw.rect(screen, (80, 70, 50), self.rect, 1)

        if self.show_text and maximum > 0:
            font = assets.get_font(FONT_SIZE_SMALL)
            txt  = f"{label}{current}/{maximum}" if label else f"{current}/{maximum}"
            surf = font.render(txt, True, COLOR_TEXT)
            rect = surf.get_rect(center=self.rect.center)
            screen.blit(surf, rect)


# ══════════════════════════════════════════
#  СЛОТ ІНВЕНТАРЮ
# ══════════════════════════════════════════

class InventorySlot:
    """
    Слот інвентарю з підтримкою текстур.
    Стиль читається з config/ui.py → SLOT_STYLE.
    """

    def __init__(self, x: int, y: int, size: int = SLOT_SIZE):
        self.rect     = pygame.Rect(x, y, size, size)
        self.size     = size
        self.hovered  = False
        self.selected = False
        self._sty     = None   # кешований стиль

    def _style(self) -> dict:
        if self._sty is None:
            from config.ui import SLOT_STYLE
            self._sty = SLOT_STYLE
        return self._sty

    def update(self, mouse_pos: tuple):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, screen: pygame.Surface,
             icon_surf: Optional[pygame.Surface] = None,
             count: int = 0, label: str = ""):
        s     = self._style()
        state = "selected" if self.selected else ("hover" if self.hovered else "empty")
        tex   = assets.get_slot_texture(state, (self.size, self.size))

        if tex:
            screen.blit(tex, self.rect)
        else:
            color_key = (f"color_{state}" if state != "hover"
                         else "color_hover")
            color = s.get(color_key, s.get("color_empty", (35, 28, 18)))
            r = s.get("corner_radius", 3)
            pygame.draw.rect(screen, color, self.rect,
                             border_radius=r)
            bw = s.get("border_width", 1)
            bc = s.get("border_color", (100, 85, 55))
            pygame.draw.rect(screen, bc, self.rect, bw,
                             border_radius=r)

        # Іконка предмету
        if icon_surf:
            icon_size = self.size - 12
            scaled    = pygame.transform.scale(icon_surf, (icon_size, icon_size))
            icon_rect = scaled.get_rect(center=self.rect.center)
            screen.blit(scaled, icon_rect)

        # Кількість
        if count > 1:
            font = assets.get_font(FONT_SIZE_SMALL)
            txt  = font.render(str(count), True, COLOR_TEXT)
            screen.blit(txt, (self.rect.right - txt.get_width() - 3,
                               self.rect.bottom - txt.get_height() - 2))

        # Мітка під слотом
        if label:
            font = assets.get_font(FONT_SIZE_SMALL - 2)
            txt  = font.render(label, True, COLOR_TEXT_DIM)
            rect = txt.get_rect(midtop=(self.rect.centerx,
                                        self.rect.bottom + 2))
            screen.blit(txt, rect)


# ══════════════════════════════════════════
#  ТЕКСТОВИЙ БЛОК
# ══════════════════════════════════════════

class TextBox:
    """Багаторядковий текст з автоматичним переносом."""

    def __init__(self, x: int, y: int, width: int, font_size: int = FONT_SIZE_NORMAL):
        self.x = x
        self.y = y
        self.width = width
        self.font_size = font_size
        self.lines: list = []
        self.line_height = font_size + 4

    def set_text(self, text: str):
        self.lines = []
        font = assets.get_font(self.font_size)
        words = text.split()
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= self.width:
                current_line = test_line
            else:
                if current_line:
                    self.lines.append(current_line)
                current_line = word
        if current_line:
            self.lines.append(current_line)

    def draw(self, screen: pygame.Surface, color: tuple = COLOR_TEXT):
        font = assets.get_font(self.font_size)
        y = self.y
        for line in self.lines:
            surf = font.render(line, True, color)
            screen.blit(surf, (self.x, y))
            y += self.line_height


# ══════════════════════════════════════════
#  ПРОКРУЧУВАНИЙ СПИСОК
# ══════════════════════════════════════════

class ScrollableList:
    """Прокручуваний список елементів."""

    def __init__(self, x: int, y: int, width: int, height: int, item_height: int = 40):
        self.rect = pygame.Rect(x, y, width, height)
        self.item_height = item_height
        self.items: list = []
        self.scroll_offset = 0
        self.hovered_index = -1
        self.selected_index = -1

    def set_items(self, items: list):
        self.items = items
        self.scroll_offset = 0
        self.selected_index = -1

    def update(self, mouse_pos: tuple, mouse_clicked: bool, scroll_delta: int = 0):
        if scroll_delta != 0:
            self.scroll_offset += scroll_delta
            max_scroll = max(0, len(self.items) * self.item_height - self.rect.height)
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        if self.rect.collidepoint(mouse_pos):
            relative_y = mouse_pos[1] - self.rect.y + self.scroll_offset
            index = relative_y // self.item_height
            if 0 <= index < len(self.items):
                self.hovered_index = index
                if mouse_clicked:
                    self.selected_index = index
            else:
                self.hovered_index = -1
        else:
            self.hovered_index = -1

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.rect(screen, COLOR_GOLD, self.rect, 2)

        list_surface = pygame.Surface((self.rect.width, self.rect.height))
        list_surface.fill(COLOR_PANEL)

        font = assets.get_font(FONT_SIZE_NORMAL)
        y = -self.scroll_offset

        for i, item in enumerate(self.items):
            if y + self.item_height >= 0 and y < self.rect.height:
                item_rect = pygame.Rect(0, y, self.rect.width, self.item_height)
                if i == self.selected_index:
                    pygame.draw.rect(list_surface, COLOR_BTN_PRESSED, item_rect)
                elif i == self.hovered_index:
                    pygame.draw.rect(list_surface, COLOR_BTN_HOVER, item_rect)
                text_surf = font.render(item, True, COLOR_TEXT)
                list_surface.blit(text_surf, (PANEL_PADDING, y + 10))
            y += self.item_height

        screen.blit(list_surface, self.rect)


# ══════════════════════════════════════════
#  СІТКА ІНВЕНТАРЮ
# ══════════════════════════════════════════

class InventoryGrid:
    """Сітка інвентаря з слотами."""

    def __init__(self, x: int, y: int,
                 cols: int = INVENTORY_COLS, rows: int = INVENTORY_ROWS):
        self.x = x
        self.y = y
        self.cols = cols
        self.rows = rows
        self.slot_size  = SLOT_SIZE
        self.spacing    = 5
        self.slots: list = [None] * (cols * rows)
        self.hovered_slot  = -1
        self.selected_slot = -1

    def update(self, mouse_pos: tuple, mouse_clicked: bool):
        self.hovered_slot = -1
        for i in range(len(self.slots)):
            if self._get_slot_rect(i).collidepoint(mouse_pos):
                self.hovered_slot = i
                if mouse_clicked:
                    self.selected_slot = i
                break

    def _get_slot_rect(self, index: int) -> pygame.Rect:
        col = index % self.cols
        row = index // self.cols
        x = self.x + col * (self.slot_size + self.spacing)
        y = self.y + row * (self.slot_size + self.spacing)
        return pygame.Rect(x, y, self.slot_size, self.slot_size)

    def draw(self, screen: pygame.Surface, items: list):
        s = assets.get_panel_style("dark") if hasattr(assets, 'get_panel_style') else {}
        slot_cfg = {}
        try:
            from config.ui import SLOT_STYLE
            slot_cfg = SLOT_STYLE
        except Exception:
            pass

        for i in range(len(self.slots)):
            slot_rect = self._get_slot_rect(i)

            if i == self.selected_slot:
                color = slot_cfg.get("color_selected", COLOR_BTN_PRESSED)
            elif i == self.hovered_slot:
                color = slot_cfg.get("color_hover", COLOR_BTN_HOVER)
            else:
                color = slot_cfg.get("color_empty", COLOR_PANEL)

            r = slot_cfg.get("corner_radius", 3)
            pygame.draw.rect(screen, color, slot_rect, border_radius=r)

            bc = slot_cfg.get("border_color", COLOR_GOLD)
            bw = slot_cfg.get("border_width", 1)
            pygame.draw.rect(screen, bc, slot_rect, bw, border_radius=r)

            if i < len(items) and items[i]:
                item = items[i]
                font = assets.get_font(FONT_SIZE_SMALL)
                try:
                    from game.mutations import get_mutation
                    mut = get_mutation(item)
                    if mut:
                        pygame.draw.rect(screen, mut.color, slot_rect, 3)
                except Exception:
                    mut = None

                text = font.render(item.icon, True, COLOR_TEXT)
                text_rect = text.get_rect(center=slot_rect.center)
                screen.blit(text, text_rect)

                if mut:
                    mut_ico = assets.get_font(14).render(mut.icon, True, mut.color)
                    screen.blit(mut_ico, (slot_rect.right - mut_ico.get_width() - 2,
                                          slot_rect.bottom - mut_ico.get_height() - 2))