"""
Константи для UI (кольори, розміри, шляхи).
"""

from pathlib import Path

# ══════════════════════════════════════════
#  РОЗМІРИ ЕКРАНУ
# ══════════════════════════════════════════

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# ══════════════════════════════════════════
#  КОЛЬОРИ
# ══════════════════════════════════════════

# Основні
COLOR_BG = (20, 15, 10)
COLOR_PANEL = (40, 30, 20)
COLOR_PANEL_ALPHA = (40, 30, 20, 220)
COLOR_TEXT = (220, 200, 180)
COLOR_TEXT_DIM = (150, 140, 130)
COLOR_GOLD = (255, 215, 0)
COLOR_SILVER = (192, 192, 192)

# Бари прогресу
COLOR_HP = (200, 50, 50)
COLOR_HP_LOW = (255, 100, 100)
COLOR_XP = (50, 120, 200)
COLOR_BAR_BG = (40, 40, 40)

# Кнопки
COLOR_BTN_NORMAL = (80, 60, 40)
COLOR_BTN_HOVER = (120, 90, 60)
COLOR_BTN_PRESSED = (60, 45, 30)
COLOR_BTN_DISABLED = (50, 40, 30)

# Статус
COLOR_SUCCESS = (50, 200, 50)
COLOR_ERROR = (200, 50, 50)
COLOR_WARNING = (255, 180, 0)
COLOR_INFO = (100, 150, 255)

# Рідкість
COLOR_COMMON = (200, 200, 200)
COLOR_UNCOMMON = (100, 200, 100)
COLOR_RARE = (100, 100, 255)
COLOR_EPIC = (200, 100, 255)
COLOR_LEGENDARY = (255, 165, 0)

# ══════════════════════════════════════════
#  ШЛЯХИ
# ══════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
TEXTURES_DIR = ASSETS_DIR / "textures"
FONTS_DIR = ASSETS_DIR / "fonts"
SAVES_DIR = BASE_DIR / "saves"

# Підпапки текстур
TEXTURES_UI = TEXTURES_DIR / "ui"
TEXTURES_CHARACTERS = TEXTURES_DIR / "characters"
TEXTURES_ITEMS = TEXTURES_DIR / "items"
TEXTURES_LOCATIONS = TEXTURES_DIR / "locations"
TEXTURES_ICONS = TEXTURES_DIR / "icons"

# ← ДОДАЙ ЦЮ СТРІЧКУ ↓
ANIMATIONS_DIR = ASSETS_DIR / "animations"
SOUNDS_DIR = ASSETS_DIR / "sounds"
MUSIC_DIR = ASSETS_DIR / "music"

# ══════════════════════════════════════════
#  РОЗМІРИ UI ЕЛЕМЕНТІВ
# ══════════════════════════════════════════

# Кнопки
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_SMALL_WIDTH = 150
BUTTON_SMALL_HEIGHT = 40

# Панелі
PANEL_PADDING = 20
PANEL_MARGIN = 10

# Інвентар
SLOT_SIZE = 64
INVENTORY_COLS = 5
INVENTORY_ROWS = 4

# Текст
FONT_SIZE_SMALL = 16
FONT_SIZE_NORMAL = 20
FONT_SIZE_MEDIUM = 24
FONT_SIZE_LARGE = 32
FONT_SIZE_TITLE = 48
FONT_SIZE_HUGE = 64


# ══════════════════════════════════════════
#  ІНІЦІАЛІЗАЦІЯ ПАПОК
# ══════════════════════════════════════════

def init_directories():
    """Створює всі необхідні директорії."""
    SAVES_DIR.mkdir(exist_ok=True)

    for subdir in [TEXTURES_UI, TEXTURES_CHARACTERS, TEXTURES_ITEMS,
                   TEXTURES_LOCATIONS, TEXTURES_ICONS, FONTS_DIR]:
        subdir.mkdir(parents=True, exist_ok=True)


# Автоматично створюємо при імпорті
init_directories()