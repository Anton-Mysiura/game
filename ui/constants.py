"""
Константи для UI.
Всі кольори та розміри тепер у config/theme.py — редагуй там!
Цей файл лише перенаправляє до конфігу + задає шляхи.
"""

from pathlib import Path

# ── Імпортуємо все з теми ─────────────────────────────────────────
from config.theme import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    COLOR_BG, COLOR_PANEL, COLOR_PANEL_ALPHA,
    COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_GOLD, COLOR_SILVER,
    COLOR_HP, COLOR_HP_LOW, COLOR_XP, COLOR_BAR_BG,
    COLOR_BTN_NORMAL, COLOR_BTN_HOVER, COLOR_BTN_PRESSED, COLOR_BTN_DISABLED,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_INFO,
    COLOR_COMMON, COLOR_UNCOMMON, COLOR_RARE, COLOR_EPIC, COLOR_LEGENDARY,
    RARITY_COLORS, RARITY_NAMES_UA,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SMALL_WIDTH, BUTTON_SMALL_HEIGHT,
    PANEL_PADDING, PANEL_MARGIN,
    SLOT_SIZE, INVENTORY_COLS, INVENTORY_ROWS,
)
from config.theme import (
    FONT_SMALL  as FONT_SIZE_SMALL,
    FONT_NORMAL as FONT_SIZE_NORMAL,
    FONT_MEDIUM as FONT_SIZE_MEDIUM,
    FONT_LARGE  as FONT_SIZE_LARGE,
    FONT_TITLE  as FONT_SIZE_TITLE,
    FONT_HUGE   as FONT_SIZE_HUGE,
)

# ── Шляхи ─────────────────────────────────────────────────────────
BASE_DIR            = Path(__file__).parent.parent
ASSETS_DIR          = BASE_DIR / "assets"
TEXTURES_DIR        = ASSETS_DIR / "textures"
FONTS_DIR           = ASSETS_DIR / "fonts"
SAVES_DIR           = BASE_DIR / "saves"

TEXTURES_UI         = TEXTURES_DIR / "ui"
TEXTURES_CHARACTERS = TEXTURES_DIR / "characters"
TEXTURES_ITEMS      = TEXTURES_DIR / "items"
TEXTURES_LOCATIONS  = TEXTURES_DIR / "locations"
TEXTURES_ICONS      = TEXTURES_DIR / "icons"

ANIMATIONS_DIR      = ASSETS_DIR / "animations"
SOUNDS_DIR          = ASSETS_DIR / "sounds"
MUSIC_DIR           = ASSETS_DIR / "music"


def init_directories():
    """Створює всі необхідні директорії."""
    SAVES_DIR.mkdir(exist_ok=True)
    for subdir in [TEXTURES_UI, TEXTURES_CHARACTERS, TEXTURES_ITEMS,
                   TEXTURES_LOCATIONS, TEXTURES_ICONS, FONTS_DIR]:
        subdir.mkdir(parents=True, exist_ok=True)


init_directories()
