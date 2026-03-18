"""
UI модуль: компоненти, константи, ресурси.
"""

# Спочатку константи (вони не залежать від нічого)
from .constants import *

# Потім assets (залежить від constants)
from .assets import AssetManager, assets

# Потім компоненти (залежать від assets та constants)
from .components import (
    Button,
    Panel,
    ProgressBar,
    TextBox,
    ScrollableList,
    InventoryGrid
)

__all__ = [
    # Константи
    'SCREEN_WIDTH',
    'SCREEN_HEIGHT',
    'FPS',
    'COLOR_BG',
    'COLOR_PANEL',
    'COLOR_PANEL_ALPHA',
    'COLOR_TEXT',
    'COLOR_TEXT_DIM',
    'COLOR_GOLD',
    'COLOR_HP',
    'COLOR_XP',
    'COLOR_BTN_NORMAL',
    'COLOR_BTN_HOVER',
    'COLOR_BTN_PRESSED',
    'BASE_DIR',
    'ASSETS_DIR',
    'TEXTURES_DIR',
    'SAVES_DIR',

    # Ресурси
    'AssetManager',
    'assets',

    # Компоненти
    'Button',
    'Panel',
    'ProgressBar',
    'TextBox',
    'ScrollableList',
    'InventoryGrid',
]