"""
╔══════════════════════════════════════════╗
║  ВОРОГИ                                  ║
║  Додавай нових ворогів тут!              ║
╚══════════════════════════════════════════╝

Як додати нового ворога:
1. Додай запис у ENEMY_DEFINITIONS нижче
2. Додай його в SPAWN_TABLES у відповідну локацію
3. Готово! Більше нічого змінювати не треба.

Формат ворога:
    "ключ": {
        "name":       "Назва",          # відображається у бою
        "hp":         50,               # початкові HP
        "attack":     12,               # базова атака
        "defense":    3,                # базовий захист
        "xp":         30,               # нагорода досвідом
        "gold":       15,               # нагорода золотом
        "level":      2,                # базовий рівень для скейлінгу
        "sprite":     "goblin",         # яку анімацію використовувати
        "behavior":   "balanced",       # стиль бою (див. нижче)
        "loot_items": ["small_potion"], # предмети (з ITEMS)
        "loot_materials": {             # матеріали що падають
            "bone": (1, 3),             # (мін, макс) або просто число
            "leather": 1,
        },
    },

Стилі поведінки (behavior):
    "balanced"    — збалансований
    "aggressive"  — постійно атакує
    "defensive"   — часто блокує, чекає на помилку
    "berserker"   — повільний але дуже сильний
    "skirmisher"  — швидкий, багато ухилень, слабкий удар
"""

ENEMY_DEFINITIONS = {

    # ══════════════════════════════
    #  СЛАБКІ ВОРОГИ (рівні 1-3)
    # ══════════════════════════════

    "goblin": {
        "name":     "Гоблін",
        "hp":       30, "attack": 7, "defense": 1,
        "xp":       15, "gold": 5,
        "level":    1,
        "sprite":   "goblin",
        "behavior": "skirmisher",
        "loot_items":     ["small_potion"],
        "loot_materials": {"wood": (1, 2), "bone": 1},
    },

    "dark_wolf": {
        "name":     "Темний Вовк",
        "hp":       35, "attack": 13, "defense": 1,
        "xp":       20, "gold": 7,
        "level":    2,
        "sprite":   "goblin",
        "behavior": "aggressive",
        "loot_items":     [],
        "loot_materials": {"leather": (1, 2), "bone": 1},
    },

    "skeleton": {
        "name":     "Скелет-воїн",
        "hp":       40, "attack": 10, "defense": 2,
        "xp":       22, "gold": 8,
        "level":    2,
        "sprite":   "goblin",
        "behavior": "balanced",
        "loot_items":     [],
        "loot_materials": {"bone": (2, 4), "bone_dust": 1},
    },

    "goblin_shaman": {
        "name":     "Гоблін-Шаман",
        "hp":       45, "attack": 11, "defense": 1,
        "xp":       28, "gold": 12,
        "level":    3,
        "sprite":   "goblin",
        "behavior": "balanced",
        "loot_items":     ["small_potion"],
        "loot_materials": {"magic_core": 1, "bone_dust": (1, 2)},
    },

    # ══════════════════════════════
    #  СЕРЕДНІ ВОРОГИ (рівні 3-5)
    # ══════════════════════════════

    "orc": {
        "name":     "Орк",
        "hp":       55, "attack": 12, "defense": 3,
        "xp":       30, "gold": 12,
        "level":    2,
        "sprite":   "orc",
        "behavior": "berserker",
        "loot_items":     ["leather_armor"],
        "loot_materials": {"leather": (1, 2), "iron_ore": (1, 3)},
    },

    "forest_troll": {
        "name":     "Лісовий Троль",
        "hp":       70, "attack": 14, "defense": 4,
        "xp":       40, "gold": 18,
        "level":    3,
        "sprite":   "orc",
        "behavior": "berserker",
        "loot_items":     [],
        "loot_materials": {"hardwood": (1, 3), "bone": (1, 2), "iron_ore": 1},
    },

    "orc_berserker": {
        "name":     "Орк-Берсерк",
        "hp":       65, "attack": 18, "defense": 2,
        "xp":       45, "gold": 20,
        "level":    4,
        "sprite":   "orc",
        "behavior": "berserker",
        "loot_items":     [],
        "loot_materials": {"dark_steel": 1, "leather": (1, 2), "iron_bar": 1},
    },

    "fire_imp": {
        "name":     "Вогняний Імп",
        "hp":       38, "attack": 15, "defense": 1,
        "xp":       30, "gold": 14,
        "level":    4,
        "sprite":   "goblin",
        "behavior": "skirmisher",
        "loot_items":     [],
        "loot_materials": {"fire_gem": 1, "magic_core": 1, "bone_dust": 1},
        # fire_gem падає з шансом 40%
        "loot_chance": {"fire_gem": 0.4},
    },

    # ══════════════════════════════
    #  СИЛЬНІ ВОРОГИ (рівні 5-7)
    # ══════════════════════════════

    "stone_golem": {
        "name":     "Кам'яний Голем",
        "hp":       90, "attack": 16, "defense": 8,
        "xp":       55, "gold": 22,
        "level":    5,
        "sprite":   "dark_knight",
        "behavior": "defensive",
        "loot_items":     [],
        "loot_materials": {"iron_ore": (2, 4), "quartz": 1, "mithril_ore": 1},
    },

    "ruin_wraith": {
        "name":     "Примара Руїн",
        "hp":       55, "attack": 20, "defense": 3,
        "xp":       50, "gold": 18,
        "level":    5,
        "sprite":   "dark_knight",
        "behavior": "aggressive",
        "loot_items":     [],
        "loot_materials": {"shadow_cloth": 1, "magic_core": (1, 2), "void_essence": 1},
        "loot_chance": {"void_essence": 0.3},
    },

    "tower_guard": {
        "name":     "Страж Вежі",
        "hp":       75, "attack": 17, "defense": 6,
        "xp":       48, "gold": 20,
        "level":    5,
        "sprite":   "dark_knight",
        "behavior": "defensive",
        "loot_items":     [],
        "loot_materials": {"iron_chain": 1, "dark_steel": (1, 2), "leather": 1},
    },

    "dark_knight": {
        "name":     "Темний Лицар",
        "hp":       80, "attack": 18, "defense": 6,
        "xp":       60, "gold": 25,
        "level":    3,
        "sprite":   "dark_knight",
        "behavior": "defensive",
        "loot_items":     ["chainmail"],
        "loot_materials": {"dark_steel": (1, 2), "magic_core": 1},
    },

    "cursed_knight": {
        "name":     "Проклятий Лицар",
        "hp":       100, "attack": 22, "defense": 7,
        "xp":       70, "gold": 30,
        "level":    6,
        "sprite":   "dark_knight",
        "behavior": "aggressive",
        "loot_items":     ["chainmail"],
        "loot_materials": {"dark_steel": (1, 2), "magic_core": 1, "iron_chain": 1},
    },

    "shadow_assassin": {
        "name":     "Тіньовий Вбивця",
        "hp":       60, "attack": 24, "defense": 3,
        "xp":       60, "gold": 25,
        "level":    6,
        "sprite":   "dark_knight",
        "behavior": "skirmisher",
        "loot_items":     [],
        "loot_materials": {"shadow_cloth": (1, 2), "shadow_essence": 1, "void_essence": 1},
        "loot_chance": {"shadow_essence": 0.25, "void_essence": 0.2},
    },

    # ══════════════════════════════
    #  БОС
    # ══════════════════════════════

    "dragon": {
        "name":     "Дракон Морвет",
        "hp":       150, "attack": 25, "defense": 8,
        "xp":       150, "gold": 80,
        "level":    8,
        "sprite":   "dragon",
        "behavior": "aggressive",
        "loot_items":     [],
        "loot_materials": {"dragon_scale": 2, "magic_core": 2, "dark_steel": 1},
    },
}


# ══════════════════════════════════════════
#  ТАБЛИЦІ СПАВНУ ПО ЛОКАЦІЯХ
# ══════════════════════════════════════════
# Формат: {"ворог_ключ": вага, ...}
# Більша вага = частіше з'являється
# min_level = мінімальний рівень гравця щоб ворог спавнився

SPAWN_TABLES = {

    "forest": [
        # (ключ_ворога, вага, мін_рівень_гравця)
        ("goblin",        30, 1),
        ("dark_wolf",     25, 1),
        ("skeleton",      20, 1),
        ("goblin_shaman", 15, 2),
        ("orc",           20, 2),
        ("forest_troll",  12, 3),
        ("orc_berserker", 10, 4),
        ("fire_imp",       8, 4),
    ],

    "tower": [
        ("dark_knight",    25, 3),
        ("tower_guard",    30, 3),
        ("cursed_knight",  20, 5),
        ("stone_golem",    15, 4),
        ("shadow_assassin",10, 6),
    ],

    "ruins": [
        ("dark_knight",    20, 3),
        ("ruin_wraith",    30, 3),
        ("stone_golem",    20, 4),
        ("skeleton",       25, 1),
        ("shadow_assassin",12, 5),
        ("cursed_knight",  10, 5),
    ],
}
