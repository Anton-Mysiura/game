"""
Система іконок предметів і матеріалів.

draw_icon(screen, icon_id, x, y, size) — малює PNG іконку або fallback емодзі.
get_icon_surf(icon_id, size) — повертає Surface з іконкою.

icon_id — це material_id або item_id з game/data.py.
PNG шукається в assets/textures/items/{icon_id}.png
Якщо файлу нема — рендерується емодзі як раніше.
"""
from __future__ import annotations
import pygame
from pathlib import Path
from ui.constants import TEXTURES_DIR

# Кеш Surface щоб не завантажувати кожен кадр
_cache: dict[str, pygame.Surface] = {}

# Папка з іконками
_ICONS_DIR = TEXTURES_DIR / "items"


def _emoji_fallback(emoji: str, size: int) -> pygame.Surface:
    """Рендерить емодзі на прозорому Surface."""
    from ui.assets import assets
    font = assets.get_font(int(size * 0.85))
    surf = font.render(emoji, True, (255, 255, 255))
    # Масштабуємо до потрібного розміру якщо треба
    if surf.get_width() != size or surf.get_height() != size:
        out = pygame.Surface((size, size), pygame.SRCALPHA)
        scaled = pygame.transform.smoothscale(surf, (min(size, surf.get_width()),
                                                      min(size, surf.get_height())))
        ox = (size - scaled.get_width()) // 2
        oy = (size - scaled.get_height()) // 2
        out.blit(scaled, (ox, oy))
        return out
    return surf


def get_icon_surf(icon_id: str, emoji: str, size: int) -> pygame.Surface:
    """
    Повертає Surface з іконкою розміром size×size.

    Спочатку шукає assets/textures/items/{icon_id}.png
    Якщо не знайдено — повертає емодзі.

    Args:
        icon_id:  ID матеріалу або предмету (наприклад "iron_ore", "rusty_sword")
        emoji:    запасний символ (mat.icon або item.icon)
        size:     розмір у пікселях
    """
    cache_key = f"{icon_id}_{size}"
    if cache_key in _cache:
        return _cache[cache_key]

    png_path = _ICONS_DIR / f"{icon_id}.png"
    surf = None

    if png_path.exists():
        try:
            raw = pygame.image.load(str(png_path)).convert_alpha()
            surf = pygame.transform.smoothscale(raw, (size, size))
        except Exception:
            surf = None

    if surf is None:
        surf = _emoji_fallback(emoji, size)

    _cache[cache_key] = surf
    return surf


def draw_icon(screen: pygame.Surface,
              icon_id: str,
              emoji: str,
              x: int, y: int,
              size: int = 32,
              alpha: int = 255) -> None:
    """
    Малює іконку предмету/матеріалу на екрані.

    Args:
        screen:   pygame Surface
        icon_id:  ID матеріалу/предмету
        emoji:    запасний символ
        x, y:     верхній лівий кут
        size:     розмір у пікселях (іконка завжди квадратна)
        alpha:    прозорість 0–255
    """
    surf = get_icon_surf(icon_id, emoji, size)
    if alpha < 255:
        surf = surf.copy()
        surf.set_alpha(alpha)
    screen.blit(surf, (x, y))


def clear_cache() -> None:
    """Очищає кеш (викликати при зміні розміру вікна)."""
    _cache.clear()