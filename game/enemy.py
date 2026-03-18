"""
Клас ворога та фабрики для створення ворогів.
"""

import random
from typing import Optional
from .data import Item, ITEMS
from .enemy_scaling import scale_enemy, BASE_LEVELS


class Enemy:
    """Ворог з характеристиками та лутом."""

    def __init__(self, name: str, hp: int, attack: int, defense: int,
                 xp_reward: int, gold_reward: int,
                 loot_items: Optional[list[Item]] = None,
                 loot_materials: Optional[dict[str, int]] = None,
                 sprite_name: str = "goblin",
                 behavior: str = "balanced"):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.loot_items = loot_items or []
        self.loot_materials = loot_materials or {}
        self.sprite_name = sprite_name
        self.level: int = 1
        # Поведінковий тип: "aggressive", "defensive", "skirmisher", "berserker", "balanced"
        self.behavior: str = behavior

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, damage: int) -> int:
        """Отримує шкоду. Повертає фактичну шкоду."""
        actual = max(1, damage - self.defense)
        self.hp = max(0, self.hp - actual)
        return actual

    def deal_damage(self) -> int:
        """Завдає шкоди з випадковим варіюванням."""
        return self.attack + random.randint(-2, 4)


# ══════════════════════════════════════════
#  ФАБРИКИ ВОРОГІВ
# ══════════════════════════════════════════

def make_goblin(player_level: int = 1) -> Enemy:
    e = Enemy(
        "Гоблін", 30, 7, 1, 15, 5,
        loot_items=[ITEMS["small_potion"]],
        loot_materials={"wood": random.randint(1, 2), "bone": 1},
        sprite_name="goblin",
        behavior="skirmisher"   # швидкий, багато ухилень, слабкий удар
    )
    e.level = BASE_LEVELS["goblin"]
    scale_enemy(e, player_level)
    return e


def make_orc(player_level: int = 1) -> Enemy:
    e = Enemy(
        "Орк", 55, 12, 3, 30, 12,
        loot_items=[ITEMS["leather_armor"]],
        loot_materials={"leather": random.randint(1, 2), "iron_ore": random.randint(1, 3)},
        sprite_name="orc",
        behavior="berserker"    # повільний, важкі удари, рідко блокує
    )
    e.level = BASE_LEVELS["orc"]
    scale_enemy(e, player_level)
    return e


def make_dark_knight(player_level: int = 1) -> Enemy:
    e = Enemy(
        "Темний Лицар", 80, 18, 6, 60, 25,
        loot_items=[ITEMS["chainmail"]],
        loot_materials={"dark_steel": random.randint(1, 2), "magic_core": 1},
        sprite_name="dark_knight",
        behavior="defensive"    # часто блокує, чекає на помилку, контратакує
    )
    e.level = BASE_LEVELS["dark_knight"]
    scale_enemy(e, player_level)
    return e


def make_dragon(player_level: int = 1) -> Enemy:
    e = Enemy(
        "Дракон Морвет", 150, 25, 8, 150, 80,
        loot_materials={"dragon_scale": 2, "magic_core": 2, "dark_steel": 1},
        sprite_name="dragon",
        behavior="aggressive"   # постійно наступає, rush-атаки
    )
    e.level = BASE_LEVELS["dragon"]
    scale_enemy(e, player_level)
    return e