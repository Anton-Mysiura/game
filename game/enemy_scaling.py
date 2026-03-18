"""
Масштабування ворогів залежно від рівня гравця.

Кожен ворог має базовий рівень (base_level).
При створенні рахується різниця між рівнем гравця і базовим —
і статистики масштабуються відповідно.

Формула:
  effective_level = base_level + clamp(player_level - base_level, 0, MAX_OVERSHOOT)
  scale = 1 + (effective_level - base_level) * SCALE_PER_LEVEL
"""
import math
import random
from typing import Optional

# Скільки рівнів "вгору" від базового ворог може рости разом з гравцем
MAX_OVERSHOOT = 8
# Приріст стату за кожен рівень понад базовий
SCALE_PER_LEVEL = 0.12   # +12% за рівень

# Базові рівні ворогів
BASE_LEVELS = {
    "goblin":           1,
    "orc":              3,
    "dark_knight":      5,
    "dragon":           8,
    # Нові вороги
    "dark_wolf":        2,
    "skeleton":         2,
    "goblin_shaman":    3,
    "forest_troll":     3,
    "fire_imp":         4,
    "orc_berserker":    4,
    "stone_golem":      5,
    "tower_guard":      5,
    "ruin_wraith":      5,
    "cursed_knight":    6,
    "shadow_assassin":  6,
}

# Мінімальний рівень ворога (щоб завжди мати хоча б базові стати)
def _scale(value: float, factor: float) -> int:
    return max(1, int(value * factor))


def scale_enemy(enemy, player_level: int) -> None:
    """
    Масштабує ворога на місці під рівень гравця.
    Також встановлює enemy.level для відображення.
    """
    base = BASE_LEVELS.get(enemy.sprite_name, 1)
    overshoot = max(0, min(player_level - base, MAX_OVERSHOOT))
    enemy.level = base + overshoot

    if overshoot == 0:
        return   # базові стати — нічого не змінювати

    factor = 1.0 + overshoot * SCALE_PER_LEVEL

    enemy.hp      = _scale(enemy.hp,      factor)
    enemy.max_hp  = enemy.hp
    enemy.attack  = _scale(enemy.attack,  factor)
    enemy.defense = _scale(enemy.defense, max(1.0, 1.0 + overshoot * 0.06))

    # XP і gold теж ростуть, але повільніше
    reward_factor = 1.0 + overshoot * 0.08
    enemy.xp_reward   = _scale(enemy.xp_reward,   reward_factor)
    enemy.gold_reward = _scale(enemy.gold_reward,  reward_factor)


def enemy_level(sprite_name: str, player_level: int) -> int:
    """Повертає ефективний рівень ворога для відображення."""
    base = BASE_LEVELS.get(sprite_name, 1)
    overshoot = max(0, min(player_level - base, MAX_OVERSHOOT))
    return base + overshoot


def level_color(enemy_level: int, player_level: int) -> tuple:
    """Колір рівня ворога відносно гравця."""
    diff = enemy_level - player_level
    if diff >= 3:   return (220,  60,  60)   # червоний — набагато сильніший
    if diff >= 1:   return (220, 140,  40)   # помаранчевий — сильніший
    if diff == 0:   return (220, 200,  80)   # жовтий — рівний
    if diff >= -2:  return (120, 200,  80)   # зелений — слабший
    return              (100, 140, 100)       # сірий-зелений — легкий