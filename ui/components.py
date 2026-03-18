"""
UI компоненти (кнопки, панелі, бари прогресу, текстові поля).
"""

import pygame
from typing import Optional, Callable
from .constants import *
from .assets import assets


class Button:
    """Кнопка з hover ефектом та callback."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback: Optional[Callable] = None, enabled: bool = True,
                 use_textures: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.enabled = enabled
        self.hovered = False
        self.pressed = False
        self.selected = False  # НОВИЙ стан для вкладок
        self.use_textures = use_textures

        # Завантажуємо текстури якщо потрібно
        if self.use_textures:
            try:
                self.texture_normal = assets.load_texture("ui", "button_normal", (width, height))
                self.texture_hover = assets.load_texture("ui", "button_hover", (width, height))
                self.texture_pressed = assets.load_texture("ui", "button_pressed", (width, height))
                self.texture_selected = assets.load_texture("ui", "button_pressed",
                                                            (width, height))  # Використовуємо pressed для selected
                print(f"✅ Button текстури завантажено для '{text}'")
            except Exception as e:
                print(f"❌ Помилка завантаження текстур кнопки: {e}")
                self.use_textures = False

    def update(self, mouse_pos: tuple, mouse_clicked: bool):
        """Оновлює стан кнопки."""
        if not self.enabled:
            return

        self.hovered = self.rect.collidepoint(mouse_pos)

        if self.hovered and mouse_clicked and not self.pressed:
            self.pressed = True
            if self.callback:
                self.callback()
        elif not mouse_clicked:
            self.pressed = False

    def draw(self, screen: pygame.Surface):
        """Малює кнопку."""
        # Вибір текстури/кольору
        if self.use_textures:
            # Використовуємо текстури
            if self.selected:
                texture = self.texture_selected
            elif not self.enabled:
                texture = self.texture_normal  # Для disabled використовуємо normal
            elif self.pressed:
                texture = self.texture_pressed
            elif self.hovered:
                texture = self.texture_hover
            else:
                texture = self.texture_normal

            screen.blit(texture, self.rect)
        else:
            # Використовуємо кольори (fallback)
            if self.selected or not self.enabled:
                color = COLOR_BTN_PRESSED
            elif self.pressed:
                color = COLOR_BTN_PRESSED
            elif self.hovered:
                color = COLOR_BTN_HOVER
            else:
                color = COLOR_BTN_NORMAL

            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, COLOR_GOLD, self.rect, 2)

        # Текст (завжди)
        font = assets.get_font(FONT_SIZE_NORMAL)
        text_color = COLOR_TEXT if self.enabled else COLOR_TEXT_DIM
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class Panel:
    """Панель для групування UI елементів."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 alpha: bool = False, color: tuple = COLOR_PANEL,
                 use_texture: bool = False, texture_name: str = "panel_dark"):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.alpha = alpha
        self.use_texture = use_texture

        if use_texture:
            try:
                self.texture = assets.load_texture("ui", texture_name, (width, height))
                print(f"✅ Panel текстура завантажена: {texture_name}")
            except Exception as e:
                print(f"❌ Помилка завантаження текстури панелі: {e}")
                self.use_texture = False

        if not use_texture:
            if alpha:
                self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
                self.surface.fill(COLOR_PANEL_ALPHA)
            else:
                self.surface = pygame.Surface((width, height))
                self.surface.fill(color)

    def draw(self, screen: pygame.Surface):
        """Малює панель."""
        if self.use_texture:
            screen.blit(self.texture, self.rect)
        else:
            screen.blit(self.surface, self.rect)
            pygame.draw.rect(screen, COLOR_GOLD, self.rect, 3)


class ProgressBar:
    """Бар прогресу (HP/XP)."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 color_fill: tuple, show_text: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_fill = color_fill
        self.show_text = show_text

    def draw(self, screen: pygame.Surface, current: int, maximum: int, label: str = ""):
        """Малює бар прогресу."""
        # Розраховуємо заповнення
        value = max(0.0, min(1.0, current / maximum if maximum > 0 else 0))

        # Фон
        pygame.draw.rect(screen, COLOR_BAR_BG, self.rect)

        # Заповнення
        fill_width = int(self.rect.width * value)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(screen, self.color_fill, fill_rect)

        # Рамка
        pygame.draw.rect(screen, COLOR_GOLD, self.rect, 2)

        # Текст
        if self.show_text:
            font = assets.get_font(FONT_SIZE_SMALL)
            if label:
                text = f"{label}: {current}/{maximum}"
            else:
                text = f"{current}/{maximum}"
            text_surf = font.render(text, True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)


class TextBox:
    """Багаторядковий текст з автоматичним переносом."""

    def __init__(self, x: int, y: int, width: int, font_size: int = FONT_SIZE_NORMAL):
        self.x = x
        self.y = y
        self.width = width
        self.font_size = font_size
        self.lines: list[str] = []
        self.line_height = font_size + 4

    def set_text(self, text: str):
        """Встановлює текст з автоматичним переносом."""
        self.lines = []
        font = assets.get_font(self.font_size)

        words = text.split()
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = font.size(test_line)[0]

            if test_width <= self.width:
                current_line = test_line
            else:
                if current_line:
                    self.lines.append(current_line)
                current_line = word

        if current_line:
            self.lines.append(current_line)

    def draw(self, screen: pygame.Surface, color: tuple = COLOR_TEXT):
        """Малює текст."""
        font = assets.get_font(self.font_size)
        y = self.y

        for line in self.lines:
            text_surf = font.render(line, True, color)
            screen.blit(text_surf, (self.x, y))
            y += self.line_height


class ScrollableList:
    """Прокручуваний список елементів."""

    def __init__(self, x: int, y: int, width: int, height: int, item_height: int = 40):
        self.rect = pygame.Rect(x, y, width, height)
        self.item_height = item_height
        self.items: list[str] = []
        self.scroll_offset = 0
        self.hovered_index = -1
        self.selected_index = -1

    def set_items(self, items: list[str]):
        """Встановлює список елементів."""
        self.items = items
        self.scroll_offset = 0
        self.selected_index = -1

    def update(self, mouse_pos: tuple, mouse_clicked: bool, scroll_delta: int = 0):
        """Оновлює стан списку."""
        # Прокрутка
        if scroll_delta != 0:
            self.scroll_offset += scroll_delta
            max_scroll = max(0, len(self.items) * self.item_height - self.rect.height)
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        # Hover та клік
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
        """Малює список."""
        # Фон
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.rect(screen, COLOR_GOLD, self.rect, 2)

        # Створюємо surface для відсічення
        list_surface = pygame.Surface((self.rect.width, self.rect.height))
        list_surface.fill(COLOR_PANEL)

        # Малюємо елементи
        font = assets.get_font(FONT_SIZE_NORMAL)
        y = -self.scroll_offset

        for i, item in enumerate(self.items):
            if y + self.item_height >= 0 and y < self.rect.height:
                # Фон елемента
                item_rect = pygame.Rect(0, y, self.rect.width, self.item_height)

                if i == self.selected_index:
                    pygame.draw.rect(list_surface, COLOR_BTN_PRESSED, item_rect)
                elif i == self.hovered_index:
                    pygame.draw.rect(list_surface, COLOR_BTN_HOVER, item_rect)

                # Текст
                text_surf = font.render(item, True, COLOR_TEXT)
                list_surface.blit(text_surf, (PANEL_PADDING, y + 10))

            y += self.item_height

        screen.blit(list_surface, self.rect)


class InventoryGrid:
    """Сітка інвентаря з слотами."""

    def __init__(self, x: int, y: int, cols: int = INVENTORY_COLS, rows: int = INVENTORY_ROWS):
        self.x = x
        self.y = y
        self.cols = cols
        self.rows = rows
        self.slot_size = SLOT_SIZE
        self.spacing = 5
        self.slots: list[Optional[object]] = [None] * (cols * rows)
        self.hovered_slot = -1
        self.selected_slot = -1

    def update(self, mouse_pos: tuple, mouse_clicked: bool):
        """Оновлює стан сітки."""
        self.hovered_slot = -1

        for i in range(len(self.slots)):
            slot_rect = self._get_slot_rect(i)
            if slot_rect.collidepoint(mouse_pos):
                self.hovered_slot = i
                if mouse_clicked:
                    self.selected_slot = i
                break

    def _get_slot_rect(self, index: int) -> pygame.Rect:
        """Повертає прямокутник слоту."""
        col = index % self.cols
        row = index // self.cols
        x = self.x + col * (self.slot_size + self.spacing)
        y = self.y + row * (self.slot_size + self.spacing)
        return pygame.Rect(x, y, self.slot_size, self.slot_size)

    def draw(self, screen: pygame.Surface, items: list):
        """Малює сітку інвентаря."""
        for i in range(len(self.slots)):
            slot_rect = self._get_slot_rect(i)

            # Фон слоту
            if i == self.selected_slot:
                pygame.draw.rect(screen, COLOR_BTN_PRESSED, slot_rect)
            elif i == self.hovered_slot:
                pygame.draw.rect(screen, COLOR_BTN_HOVER, slot_rect)
            else:
                pygame.draw.rect(screen, COLOR_PANEL, slot_rect)

            # Рамка
            pygame.draw.rect(screen, COLOR_GOLD, slot_rect, 2)

            # Предмет (якщо є)
            if i < len(items) and items[i]:
                item = items[i]
                font = assets.get_font(FONT_SIZE_SMALL)

                # Рамка мутації
                from game.mutations import get_mutation
                mut = get_mutation(item)
                if mut:
                    pygame.draw.rect(screen, mut.color, slot_rect, 3)

                text = font.render(item.icon, True, COLOR_TEXT)
                text_rect = text.get_rect(center=slot_rect.center)
                screen.blit(text, text_rect)

                # Мала іконка мутації в куті слоту
                if mut:
                    mut_ico = assets.get_font(14).render(mut.icon, True, mut.color)
                    screen.blit(mut_ico, (slot_rect.right - mut_ico.get_width() - 2,
                                          slot_rect.top + 2))