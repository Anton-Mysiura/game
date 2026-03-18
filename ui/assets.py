"""
Менеджер ресурсів (завантаження текстур та шрифтів).
"""

import pygame
from pathlib import Path
from .constants import TEXTURES_DIR, FONTS_DIR


class AssetManager:
    """Завантаження та кешування текстур і шрифтів."""

    def __init__(self):
        self.textures = {}
        self.fonts = {}

    def load_texture(self, category: str, name: str, size: tuple = None) -> pygame.Surface:
        key = f"{category}/{name}"
        if size:
            key += f"_{size[0]}x{size[1]}"

        if key in self.textures:
            return self.textures[key]

        path = TEXTURES_DIR / category / f"{name}.png"

        print(f"🔍 Шукаю текстуру: {path}")  # ДЕБАГ
        print(f"   Існує: {path.exists()}")  # ДЕБАГ

        if path.exists():
            try:
                surf = pygame.image.load(str(path)).convert_alpha()
                if size:
                    surf = pygame.transform.scale(surf, size)
                print(f"   ✅ Завантажено!")  # ДЕБАГ
            except Exception as e:
                print(f"   ❌ Помилка: {e}")  # ДЕБАГ
                surf = self._create_placeholder(name, size or (64, 64))
        else:
            print(f"   ⚠ Файл не знайдено, створюю плейсхолдер")  # ДЕБАГ
            surf = self._create_placeholder(name, size or (64, 64))

        self.textures[key] = surf
        return surf

    def _create_placeholder(self, name: str, size: tuple) -> pygame.Surface:
        """Створює кольоровий плейсхолдер з рамкою."""
        surf = pygame.Surface(size)

        # Колір залежить від назви (хеш)
        hash_val = sum(ord(c) for c in name)
        color = (
            (hash_val * 50) % 150 + 50,
            (hash_val * 30) % 150 + 50,
            (hash_val * 70) % 150 + 50,
        )
        surf.fill(color)

        # Рамка
        pygame.draw.rect(surf, (200, 200, 200), surf.get_rect(), 2)

        # Назва (якщо вміщається)
        if size[0] >= 64 and size[1] >= 64:
            font = self.get_font(12)
            text = font.render(name[:10], True, (255, 255, 255))
            text_rect = text.get_rect(center=(size[0]//2, size[1]//2))
            surf.blit(text, text_rect)

        return surf

    def get_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        """
        Отримує шрифт заданого розміру.

        Args:
            size: розмір шрифту
            bold: жирний шрифт

        Returns:
            pygame.font.Font
        """
        key = f"{size}_{bold}"

        if key not in self.fonts:
            # Спробуємо завантажити кастомний шрифт
            font_path = FONTS_DIR / "main.ttf"

            if font_path.exists():
                try:
                    font = pygame.font.Font(str(font_path), size)
                except Exception:  # Помилка завантаження шрифту
                    font = pygame.font.Font(None, size)
            else:
                # Використовуємо системний шрифт
                font = pygame.font.Font(None, size)

            if bold:
                font.set_bold(True)

            self.fonts[key] = font

        return self.fonts[key]

    def preload_common_assets(self):
        """Попереднє завантаження часто використовуваних текстур."""
        # UI елементи
        self.load_texture("ui", "button_normal", (200, 60))
        self.load_texture("ui", "button_hover", (200, 60))
        self.load_texture("ui", "button_pressed", (200, 60))
        self.load_texture("ui", "panel_dark", (800, 600))
        self.load_texture("ui", "panel_wood", (600, 500))

        # Персонажі
        self.load_texture("characters", "player_idle", (128, 128))
        self.load_texture("characters", "player_attack", (128, 128))

        # Локації
        self.load_texture("locations", "village", (1280, 720))
        self.load_texture("locations", "main_menu_bg", (1280, 720))

        # Іконки
        self.load_texture("ui", "gold_coin", (32, 32))
        self.load_texture("ui", "slot_empty", (64, 64))

    def clear_cache(self):
        """Очищає кеш текстур (звільняє пам'ять)."""
        self.textures.clear()
        self.fonts.clear()


# Глобальний менеджер ресурсів
assets = AssetManager()