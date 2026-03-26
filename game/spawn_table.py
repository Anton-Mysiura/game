"""
Таблиці спавну ворогів для кожної локації.
Випадковий вибір ворога залежить від рівня гравця і локації.

Кожен запис у таблиці: SpawnEntry з вагою, мін/макс рівнем гравця,
і фабрикою ворога.

Виклик: pick_enemy(location, player_level) → Enemy
"""
import random
from dataclasses import dataclass
from typing import Callable, Optional

from .enemy import Enemy, make_goblin, make_orc, make_dark_knight
from .data import ITEMS
from .enemy_scaling import scale_enemy


@dataclass
class SpawnEntry:
    factory:    Callable       # make_XXX(player_level) → Enemy
    weight:     int            # відносна вага (більше = частіше)
    min_level:  int = 1        # мінімальний рівень гравця
    max_level:  int = 99       # максимальний рівень гравця
    label:      str = ""       # назва для логів


# ══════════════════════════════════════════
#  ДОПОМІЖНА ФАБРИКА
# ══════════════════════════════════════════

def _make_enemy(name: str, hp: int, attack: int, defense: int,
                xp: int, gold: int, level: int, player_level: int,
                sprite: str = "goblin", behavior: str = "balanced",
                loot_items=None, loot_materials=None) -> Enemy:
    """Будує і скейлить ворога — позбавляє від дублювання в фабриках."""
    e = Enemy(
        name, hp, attack, defense, xp, gold,
        loot_items=loot_items,
        loot_materials=loot_materials or {},
        sprite_name=sprite,
        behavior=behavior,
    )
    e.level = level
    scale_enemy(e, player_level)
    return e


# ══════════════════════════════════════════
#  ФАБРИКИ ВОРОГІВ
# ══════════════════════════════════════════

def _make_forest_troll(player_level: int) -> Enemy:
    return _make_enemy(
        "Лісовий Троль", 70, 14, 4, 40, 18, level=3,
        player_level=player_level, sprite="orc", behavior="berserker",
        loot_materials={"hardwood": random.randint(1, 3), "bone": random.randint(1, 2), "iron_ore": 1},
    )


def _make_skeleton(player_level: int) -> Enemy:
    return _make_enemy(
        "Скелет-воїн", 40, 10, 2, 22, 8, level=2,
        player_level=player_level, sprite="goblin", behavior="balanced",
        loot_materials={"bone": random.randint(2, 4), "bone_dust": 1},
    )


def _make_dark_wolf(player_level: int) -> Enemy:
    return _make_enemy(
        "Темний Вовк", 35, 13, 1, 20, 7, level=2,
        player_level=player_level, sprite="goblin", behavior="skirmisher",
        loot_materials={"leather": random.randint(1, 2), "bone": 1},
    )


def _make_goblin_shaman(player_level: int) -> Enemy:
    return _make_enemy(
        "Гоблін-Шаман", 45, 11, 1, 28, 12, level=3,
        player_level=player_level, sprite="goblin", behavior="balanced",
        loot_items=[ITEMS["small_potion"]],
        loot_materials={"magic_core": 1, "bone_dust": random.randint(1, 2)},
    )


def _make_orc_berserker(player_level: int) -> Enemy:
    return _make_enemy(
        "Орк-Берсерк", 65, 18, 2, 45, 20, level=4,
        player_level=player_level, sprite="orc", behavior="berserker",
        loot_materials={"dark_steel": 1, "leather": random.randint(1, 2), "iron_bar": 1},
    )


def _make_stone_golem(player_level: int) -> Enemy:
    return _make_enemy(
        "Кам'яний Голем", 90, 16, 8, 55, 22, level=5,
        player_level=player_level, sprite="dark_knight", behavior="defensive",
        loot_materials={"iron_ore": random.randint(2, 4), "quartz": 1, "mithril_ore": 1},
    )


def _make_ruin_wraith(player_level: int) -> Enemy:
    return _make_enemy(
        "Примара Руїн", 55, 20, 3, 50, 18, level=5,
        player_level=player_level, sprite="dark_knight", behavior="aggressive",
        loot_materials={
            "shadow_cloth": 1,
            "magic_core":   random.randint(1, 2),
            "void_essence": 1 if random.random() < 0.3 else 0,
        },
    )


def _make_tower_guard(player_level: int) -> Enemy:
    return _make_enemy(
        "Страж Вежі", 75, 17, 6, 48, 20, level=5,
        player_level=player_level, sprite="dark_knight", behavior="defensive",
        loot_materials={"iron_chain": 1, "dark_steel": random.randint(1, 2), "leather": 1},
    )


def _make_cursed_knight(player_level: int) -> Enemy:
    return _make_enemy(
        "Проклятий Лицар", 100, 22, 7, 70, 30, level=6,
        player_level=player_level, sprite="dark_knight", behavior="defensive",
        loot_items=[ITEMS.get("chainmail", ITEMS["small_potion"])],
        loot_materials={"dark_steel": random.randint(1, 2), "magic_core": 1, "iron_chain": 1},
    )


def _make_fire_imp(player_level: int) -> Enemy:
    return _make_enemy(
        "Вогняний Імп", 38, 15, 1, 30, 14, level=4,
        player_level=player_level, sprite="goblin", behavior="skirmisher",
        loot_materials={
            "fire_gem":   1 if random.random() < 0.4 else 0,
            "magic_core": 1,
            "bone_dust":  1,
        },
    )


def _make_shadow_assassin(player_level: int) -> Enemy:
    return _make_enemy(
        "Тіньовий Вбивця", 60, 24, 3, 60, 25, level=6,
        player_level=player_level, sprite="dark_knight", behavior="skirmisher",
        loot_materials={
            "shadow_cloth":   random.randint(1, 2),
            "shadow_essence": 1 if random.random() < 0.25 else 0,
            "void_essence":   1 if random.random() < 0.2 else 0,
        },
    )


# ══════════════════════════════════════════
#  ТАБЛИЦІ СПАВНУ ПО ЛОКАЦІЯХ
# ══════════════════════════════════════════

SPAWN_TABLES: dict[str, list[SpawnEntry]] = {

    "forest": [
        SpawnEntry(factory=make_goblin,         weight=30, min_level=1, label="Гоблін"),
        SpawnEntry(factory=_make_dark_wolf,     weight=25, min_level=1, label="Темний Вовк"),
        SpawnEntry(factory=_make_skeleton,      weight=20, min_level=1, label="Скелет"),
        SpawnEntry(factory=_make_goblin_shaman, weight=15, min_level=2, label="Гоблін-Шаман"),
        SpawnEntry(factory=make_orc,            weight=20, min_level=2, label="Орк"),
        SpawnEntry(factory=_make_forest_troll,  weight=12, min_level=3, label="Лісовий Троль"),
        SpawnEntry(factory=_make_orc_berserker, weight=10, min_level=4, label="Орк-Берсерк"),
        SpawnEntry(factory=_make_fire_imp,      weight=8,  min_level=4, label="Вогняний Імп"),
    ],

    "tower": [
        SpawnEntry(factory=make_dark_knight,      weight=25, min_level=3, label="Темний Лицар"),
        SpawnEntry(factory=_make_tower_guard,     weight=30, min_level=3, label="Страж Вежі"),
        SpawnEntry(factory=_make_cursed_knight,   weight=20, min_level=5, label="Проклятий Лицар"),
        SpawnEntry(factory=_make_stone_golem,     weight=15, min_level=4, label="Кам'яний Голем"),
        SpawnEntry(factory=_make_shadow_assassin, weight=10, min_level=6, label="Тіньовий Вбивця"),
    ],

    "ruins": [
        SpawnEntry(factory=make_dark_knight,      weight=20, min_level=3, label="Темний Лицар"),
        SpawnEntry(factory=_make_ruin_wraith,     weight=30, min_level=3, label="Примара Руїн"),
        SpawnEntry(factory=_make_stone_golem,     weight=20, min_level=4, label="Кам'яний Голем"),
        SpawnEntry(factory=_make_skeleton,        weight=25, min_level=1, label="Скелет"),
        SpawnEntry(factory=_make_shadow_assassin, weight=12, min_level=5, label="Тіньовий Вбивця"),
        SpawnEntry(factory=_make_cursed_knight,   weight=10, min_level=5, label="Проклятий Лицар"),
    ],
}


# ── Публічний API ─────────────────────────────────────────────────

def pick_enemy(location: str, player_level: int) -> Optional[Enemy]:
    """
    Випадково вибирає ворога з таблиці для локації.
    Враховує мін/макс рівень гравця.
    Повертає готовий Enemy або None якщо таблиця порожня.
    """
    table = SPAWN_TABLES.get(location, [])
    eligible = [e for e in table if e.min_level <= player_level <= e.max_level]
    if not eligible:
        eligible = table
    if not eligible:
        return None
    weights = [e.weight for e in eligible]
    chosen  = random.choices(eligible, weights=weights, k=1)[0]
    return chosen.factory(player_level)


def get_encounter_pool(location: str, player_level: int) -> list[str]:
    """Повертає список назв ворогів що можуть зустрітись (для UI)."""
    table = SPAWN_TABLES.get(location, [])
    return [e.label for e in table if e.min_level <= player_level <= e.max_level]