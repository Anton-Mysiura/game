"""
Ігрове ядро: дані, гравець, вороги, збереження, туторіали.
"""

from .data import (
    Material,
    Item,
    Blueprint,
    MATERIALS,
    ITEMS,
    BLUEPRINTS,
    TUTORIALS,
    make_weapon_from_blueprint
)
from .player import Player
from .enemy import Enemy, make_goblin, make_orc, make_dark_knight, make_dragon
from .save_manager import SaveManager, autosave, SAVES_DIR
from .tutorial_manager import TutorialManager
from .achievements import Achievement, ACHIEVEMENTS, AchievementManager
from .animation import Animation, AnimationController, AnimationLoader
from .fighter import Fighter
from .fighter_ai import FighterAI, create_enemy_ai

__all__ = [
    # Дані
    'Material',
    'Item',
    'Blueprint',
    'MATERIALS',
    'ITEMS',
    'BLUEPRINTS',
    'TUTORIALS',
    'make_weapon_from_blueprint',

    # Гравець
    'Player',

    # Вороги
    'Enemy',
    'make_goblin',
    'make_orc',
    'make_dark_knight',
    'make_dragon',

    # Збереження
    'SaveManager',
    'autosave',
    'SAVES_DIR',

    # Туторіали
    'TutorialManager',

    # Досягнення
    'Achievement',
    'ACHIEVEMENTS',
    'AchievementManager',

    # Файтинг
    'Animation',
    'AnimationController',
    'AnimationLoader',
    'Fighter',
    'FighterAI',
    'create_enemy_ai',
]