"""
Менеджер ресурсів (текстури, шрифти, фони).
Читає шляхи з config/ui.py — редагуй там, а не тут.
"""

import pygame
from pathlib import Path
from typing import Optional


class AssetManager:
    """Завантажує і кешує текстури та шрифти."""

    def __init__(self):
        self._textures: dict = {}
        self._fonts:    dict = {}
        self._cfg = None

    @property
    def _ui_cfg(self):
        if self._cfg is None:
            from config import ui as u
            self._cfg = u
        return self._cfg

    # ════════════════════════════════════════
    #  ТЕКСТУРИ
    # ════════════════════════════════════════

    def load_texture(self, category: str, name: str,
                     size: tuple = None) -> pygame.Surface:
        key = f"{category}/{name}" + (f"_{size[0]}x{size[1]}" if size else "")
        if key in self._textures:
            return self._textures[key]

        from ui.constants import TEXTURES_DIR
        path = TEXTURES_DIR / category / f"{name}.png"

        if path.exists():
            try:
                surf = pygame.image.load(str(path)).convert_alpha()
                if size:
                    surf = pygame.transform.scale(surf, size)
            except Exception:
                surf = self._placeholder(name, size or (64, 64))
        else:
            surf = self._placeholder(name, size or (64, 64))

        self._textures[key] = surf
        return surf

    def load_from_path(self, filepath: str,
                       size: tuple = None) -> Optional[pygame.Surface]:
        """Завантажує текстуру за довільним шляхом."""
        path = Path(filepath)
        key = str(path) + (f"_{size[0]}x{size[1]}" if size else "")
        if key in self._textures:
            return self._textures[key]
        if not path.exists():
            return None
        try:
            surf = pygame.image.load(str(path)).convert_alpha()
            if size:
                surf = pygame.transform.scale(surf, size)
            self._textures[key] = surf
            return surf
        except Exception:
            return None

    def _placeholder(self, name: str, size: tuple) -> pygame.Surface:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        h = sum(ord(c) for c in name)
        color = ((h * 50) % 120 + 40, (h * 30) % 120 + 40, (h * 70) % 120 + 40, 200)
        surf.fill(color)
        pygame.draw.rect(surf, (160, 140, 100, 200), surf.get_rect(), 2)
        return surf

    # ════════════════════════════════════════
    #  ФОНИ СЦЕН
    # ════════════════════════════════════════

    def get_background(self, scene_name: str,
                       screen_size: tuple = (1280, 720)) -> Optional[pygame.Surface]:
        cfg = self._ui_cfg
        tex_name = cfg.SCENE_BACKGROUNDS.get(scene_name)
        if not tex_name:
            return None
        is_tiled = cfg.SCENE_BACKGROUND_TILE.get(scene_name, False)
        raw = self.load_texture("ui/bg", tex_name)
        if is_tiled:
            return self._tile_surface(raw, screen_size)
        return pygame.transform.scale(raw, screen_size)

    def _tile_surface(self, tile: pygame.Surface, screen_size: tuple) -> pygame.Surface:
        surf = pygame.Surface(screen_size, pygame.SRCALPHA)
        tw, th = tile.get_size()
        for y in range(0, screen_size[1], th):
            for x in range(0, screen_size[0], tw):
                surf.blit(tile, (x, y))
        return surf

    # ════════════════════════════════════════
    #  КНОПКИ
    # ════════════════════════════════════════

    def get_button_texture(self, style_name: str, state: str,
                           size: tuple) -> Optional[pygame.Surface]:
        cfg = self._ui_cfg
        style = cfg.BUTTON_STYLES.get(style_name, cfg.BUTTON_STYLES["default"])
        tex_name = style.get(state)
        if not tex_name:
            return None
        return self.load_texture("ui/button", tex_name, size)

    def get_button_style(self, style_name: str) -> dict:
        cfg = self._ui_cfg
        return cfg.BUTTON_STYLES.get(style_name, cfg.BUTTON_STYLES["default"])

    # ════════════════════════════════════════
    #  ПАНЕЛІ
    # ════════════════════════════════════════

    def get_panel_texture(self, style_name: str,
                          size: tuple) -> Optional[pygame.Surface]:
        cfg = self._ui_cfg
        style = cfg.PANEL_STYLES.get(style_name, cfg.PANEL_STYLES["dark"])
        tex_name = style.get("texture")
        if not tex_name:
            return None
        return self.load_texture("ui/panel", tex_name, size)

    def get_panel_style(self, style_name: str) -> dict:
        cfg = self._ui_cfg
        return cfg.PANEL_STYLES.get(style_name, cfg.PANEL_STYLES["dark"])

    # ════════════════════════════════════════
    #  ІКОНКИ
    # ════════════════════════════════════════

    def get_icon(self, icon_name: str,
                 size: tuple = (32, 32)) -> Optional[pygame.Surface]:
        cfg = self._ui_cfg
        tex_name = cfg.UI_ICONS.get(icon_name)
        if not tex_name:
            return None
        return self.load_texture("ui/icon", tex_name, size)

    def get_slot_texture(self, state: str = "empty",
                         size: tuple = (64, 64)) -> Optional[pygame.Surface]:
        cfg = self._ui_cfg
        key_map = {"empty": "empty_texture", "hover": "hover_texture",
                   "selected": "selected_texture"}
        tex_name = cfg.SLOT_STYLE.get(key_map.get(state, "empty_texture"))
        if not tex_name:
            return None
        return self.load_texture("ui/slot", tex_name, size)

    # ════════════════════════════════════════
    #  ШРИФТИ
    # ════════════════════════════════════════

    def get_font(self, size: int, bold: bool = False,
                 variant: str = "main") -> pygame.font.Font:
        key = f"{variant}_{size}_{bold}"
        if key in self._fonts:
            return self._fonts[key]

        from ui.constants import FONTS_DIR
        cfg = self._ui_cfg
        font_file = cfg.FONTS.get(variant) or cfg.FONTS.get("main")
        font = None

        if font_file:
            path = FONTS_DIR / font_file
            if path.exists():
                try:
                    font = pygame.font.Font(str(path), size)
                except Exception:
                    font = None

        if font is None:
            font = pygame.font.Font(None, size)

        if bold:
            font.set_bold(True)

        self._fonts[key] = font
        return font

    # ════════════════════════════════════════
    #  КУРСОР
    # ════════════════════════════════════════

    def apply_cursor(self):
        cfg = self._ui_cfg
        if not cfg.CURSOR.get("use_custom"):
            return
        tex_name = cfg.CURSOR.get("texture")
        if not tex_name:
            return
        surf = self.load_texture("ui", tex_name)
        if surf:
            hotspot = cfg.CURSOR.get("hotspot", (0, 0))
            pygame.mouse.set_cursor(pygame.cursors.Cursor(hotspot, surf))

    # ════════════════════════════════════════
    #  УТИЛІТИ
    # ════════════════════════════════════════

    def reload(self):
        """Перезавантажує всі ресурси (для hot-reload)."""
        self._textures.clear()
        self._fonts.clear()
        self._cfg = None

    def preload(self):
        """Попереднє завантаження ресурсів."""
        from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT
        cfg = self._ui_cfg
        for scene in cfg.SCENE_BACKGROUNDS:
            self.get_background(scene, (SCREEN_WIDTH, SCREEN_HEIGHT))
        for style_name in cfg.BUTTON_STYLES:
            for state in ("normal", "hover", "pressed", "disabled"):
                self.get_button_texture(style_name, state, (200, 50))
        for icon in cfg.UI_ICONS:
            self.get_icon(icon)


# Глобальний синглтон
assets = AssetManager()
