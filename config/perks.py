"""
╔══════════════════════════════════════════════════════════════╗
║  ПЕРКИ ТА СКІЛ-ТРИ                                         ║
║  Додавай нові перки і вузли скіл-три тут                   ║
╚══════════════════════════════════════════════════════════════╝

ЯК ДОДАТИ НОВИЙ ПЕРК:
  Додай блок у PERKS_DATA. Перк автоматично з'явиться
  у пулі при підвищенні рівня.

ЯК ДОДАТИ ВУЗОЛ У СКІЛ-ТРИ:
  Додай блок у SKILL_NODES_DATA у відповідну гілку.
  tier — рівень у гілці (1=перший, 5=останній)
  requires — id попереднього вузла (або None для першого)

Статистики для stat/effect:
  "attack"       "defense"     "max_hp"
  "crit_chance"  "atk_speed"   "dodge"
  "gold_bonus"   "xp_bonus"    "loot_chance"
"""

# ══════════════════════════════════════════
#  ШАНСИ РІДКОСТЕЙ ПЕРКІВ
# ══════════════════════════════════════════

PERK_RARITY_WEIGHTS = {
    "common":    50.0,
    "uncommon":  25.0,
    "rare":      12.0,
    "epic":       7.0,
    "mythic":     3.0,
    "legendary":  1.5,
    "god":        0.5,
}

PERK_RARITY_NAMES = {
    "common":    "Звичайна",
    "uncommon":  "Незвичайна",
    "rare":      "Рідкісна",
    "epic":      "Епічна",
    "mythic":    "Міфічна",
    "legendary": "Легендарна",
    "god":       "GOD",
}

PERK_RARITY_COLORS = {
    "common":    (200, 200, 200),
    "uncommon":  (80,  200, 80),
    "rare":      (80,  120, 255),
    "epic":      (180, 80,  255),
    "mythic":    (255, 80,  80),
    "legendary": (255, 200, 0),
    "god":       (255, 255, 255),
}


# ══════════════════════════════════════════
#  ПЕРКИ
# ══════════════════════════════════════════
# Формат:
#   "id": {
#       "name":   "Назва",
#       "desc":   "Опис що бачить гравець",
#       "rarity": "common",
#       "icon":   "⚔",
#       "effect": {"stat": значення, ...}
#   }
#
# effect — словник статів що збільшуються:
#   attack, defense, max_hp, crit_chance (0.05 = 5%),
#   atk_speed, dodge, gold_bonus, xp_bonus

PERKS_DATA = {

    # ──────────────── Звичайні ──────────────────────
    "dmg_5": {
        "name":   "+5% шкоди",
        "desc":   "Всі удари наносять на 5% більше шкоди",
        "rarity": "common", "icon": "⚔",
        "effect": {"attack_pct": 0.05},
    },
    "atk_speed_5": {
        "name":   "+5% швидкість атаки",
        "desc":   "Атаки виконуються на 5% швидше",
        "rarity": "common", "icon": "⚡",
        "effect": {"atk_speed": 0.05},
    },
    "hp_20": {
        "name":   "+20 HP",
        "desc":   "Збільшує максимальне HP на 20",
        "rarity": "common", "icon": "❤",
        "effect": {"max_hp": 20},
    },
    "def_3": {
        "name":   "+3 захисту",
        "desc":   "Ворожі удари поглинаються краще",
        "rarity": "common", "icon": "🛡",
        "effect": {"defense": 3},
    },
    "gold_10": {
        "name":   "+10% золота",
        "desc":   "Вороги залишають більше монет",
        "rarity": "common", "icon": "💰",
        "effect": {"gold_bonus": 0.10},
    },
    "xp_10": {
        "name":   "+10% XP",
        "desc":   "Досвід нараховується швидше",
        "rarity": "common", "icon": "✨",
        "effect": {"xp_bonus": 0.10},
    },

    # ──────────────── Незвичайні ────────────────────
    "crit_7": {
        "name":   "+7% критичний удар",
        "desc":   "Збільшує шанс критичного удару на 7%",
        "rarity": "uncommon", "icon": "🎯",
        "effect": {"crit_chance": 0.07},
    },
    "hp_40": {
        "name":   "+40 HP",
        "desc":   "Значно збільшує запас здоров'я",
        "rarity": "uncommon", "icon": "💖",
        "effect": {"max_hp": 40},
    },
    "atk_8": {
        "name":   "+8 атаки",
        "desc":   "Твої удари стають відчутно сильнішими",
        "rarity": "uncommon", "icon": "⚔",
        "effect": {"attack": 8},
    },
    "dodge_8": {
        "name":   "+8% ухилення",
        "desc":   "Частіше уникаєш ворожих ударів",
        "rarity": "uncommon", "icon": "💨",
        "effect": {"dodge": 0.08},
    },
    "loot_15": {
        "name":   "+15% лут",
        "desc":   "Вороги залишають більше матеріалів",
        "rarity": "uncommon", "icon": "📦",
        "effect": {"loot_chance": 0.15},
    },

    # ──────────────── Рідкісні ──────────────────────
    "berserker": {
        "name":   "Берсерк",
        "desc":   "+15% шкоди, -5% захисту",
        "rarity": "rare", "icon": "🔥",
        "effect": {"attack_pct": 0.15, "defense_pct": -0.05},
    },
    "tank": {
        "name":   "Залізна шкіра",
        "desc":   "+8 захисту, +50 HP",
        "rarity": "rare", "icon": "⛨",
        "effect": {"defense": 8, "max_hp": 50},
    },
    "assassin": {
        "name":   "Асасин",
        "desc":   "+15% крит, +10% швидкість",
        "rarity": "rare", "icon": "🗡",
        "effect": {"crit_chance": 0.15, "atk_speed": 0.10},
    },
    "gold_hoarder": {
        "name":   "Скнара",
        "desc":   "+30% золота від усіх джерел",
        "rarity": "rare", "icon": "💎",
        "effect": {"gold_bonus": 0.30},
    },

    # ──────────────── Епічні ────────────────────────
    "warlord": {
        "name":   "Полководець",
        "desc":   "+20 атаки, +20% шкоди",
        "rarity": "epic", "icon": "👑",
        "effect": {"attack": 20, "attack_pct": 0.20},
    },
    "immortal": {
        "name":   "Безсмертний",
        "desc":   "+100 HP, +10 захисту",
        "rarity": "epic", "icon": "💠",
        "effect": {"max_hp": 100, "defense": 10},
    },
    "phantom": {
        "name":   "Фантом",
        "desc":   "+20% ухилення, +20% крит",
        "rarity": "epic", "icon": "👁",
        "effect": {"dodge": 0.20, "crit_chance": 0.20},
    },

    # ──────────────── Mythic ────────────────────────
    "death_dealer": {
        "name":   "Жнець смерті",
        "desc":   "+30% шкоди, +25% крит",
        "rarity": "mythic", "icon": "☠",
        "effect": {"attack_pct": 0.30, "crit_chance": 0.25},
    },
    "fortress": {
        "name":   "Фортеця",
        "desc":   "+15 захисту, +150 HP, -10% швидкість",
        "rarity": "mythic", "icon": "🏰",
        "effect": {"defense": 15, "max_hp": 150, "atk_speed": -0.10},
    },

    # ──────────────── Legendary ─────────────────────
    "god_of_war": {
        "name":   "Бог війни",
        "desc":   "+40% шкоди, +15% крит, +10 атаки",
        "rarity": "legendary", "icon": "🌟",
        "effect": {"attack_pct": 0.40, "crit_chance": 0.15, "attack": 10},
    },

    # ──────────────── GOD ───────────────────────────
    "omnipotent": {
        "name":   "Всемогутній",
        "desc":   "+50% до всього. Ти просто бог.",
        "rarity": "god", "icon": "✦",
        "effect": {
            "attack_pct": 0.50, "defense_pct": 0.50,
            "max_hp": 200, "crit_chance": 0.30,
            "gold_bonus": 0.50, "xp_bonus": 0.50,
        },
    },
}


# ══════════════════════════════════════════
#  СКІЛ-ТРИ
# ══════════════════════════════════════════
# Гілки: "strength" | "endurance" | "agility"
# tier: 1..5 (1 = перший вузол у гілці)
# requires: id попереднього вузла або None

SKILL_NODES_DATA = {

    # ──────────────── Сила ──────────────────────────
    "str_1": {
        "name": "Гостре лезо",   "desc": "+5 до атаки",
        "icon": "⚔",  "branch": "strength", "tier": 1,
        "stat": "attack",      "value": 5,
        "requires": None,
    },
    "str_2": {
        "name": "Важкий удар",   "desc": "+8 до атаки",
        "icon": "🗡",  "branch": "strength", "tier": 2,
        "stat": "attack",      "value": 8,
        "requires": "str_1",
    },
    "str_3": {
        "name": "Точний удар",   "desc": "+5% шанс крит. удару",
        "icon": "🎯",  "branch": "strength", "tier": 3,
        "stat": "crit_chance", "value": 0.05,
        "requires": "str_2",
    },
    "str_4": {
        "name": "Руйнівник",     "desc": "+12 до атаки",
        "icon": "💢",  "branch": "strength", "tier": 4,
        "stat": "attack",      "value": 12,
        "requires": "str_3",
    },
    "str_5": {
        "name": "Берсерк",       "desc": "+15 до атаки, +10% крит",
        "icon": "🔥",  "branch": "strength", "tier": 5,
        "stat": "attack",      "value": 15,
        "extra_stat": "crit_chance", "extra_value": 0.10,
        "requires": "str_4",
    },

    # ──────────────── Витривалість ──────────────────
    "end_1": {
        "name": "Загартування",  "desc": "+20 до макс. HP",
        "icon": "❤",  "branch": "endurance", "tier": 1,
        "stat": "max_hp",      "value": 20,
        "requires": None,
    },
    "end_2": {
        "name": "Товста шкіра",  "desc": "+3 до захисту",
        "icon": "🛡",  "branch": "endurance", "tier": 2,
        "stat": "defense",     "value": 3,
        "requires": "end_1",
    },
    "end_3": {
        "name": "Стійкість",     "desc": "+30 до макс. HP",
        "icon": "💪",  "branch": "endurance", "tier": 3,
        "stat": "max_hp",      "value": 30,
        "requires": "end_2",
    },
    "end_4": {
        "name": "Броня воїна",   "desc": "+5 до захисту",
        "icon": "⛨",  "branch": "endurance", "tier": 4,
        "stat": "defense",     "value": 5,
        "requires": "end_3",
    },
    "end_5": {
        "name": "Незламний",     "desc": "+50 до макс. HP, +5 DEF",
        "icon": "🏛",  "branch": "endurance", "tier": 5,
        "stat": "max_hp",      "value": 50,
        "extra_stat": "defense", "extra_value": 5,
        "requires": "end_4",
    },

    # ──────────────── Спритність ────────────────────
    "agi_1": {
        "name": "Легкий крок",   "desc": "+5% швидкість атаки",
        "icon": "💨",  "branch": "agility", "tier": 1,
        "stat": "atk_speed",   "value": 0.05,
        "requires": None,
    },
    "agi_2": {
        "name": "Реакція",       "desc": "+10% швидкість атаки",
        "icon": "⚡",  "branch": "agility", "tier": 2,
        "stat": "atk_speed",   "value": 0.10,
        "requires": "agi_1",
    },
    "agi_3": {
        "name": "Тіньовий удар", "desc": "+7% шанс крит. удару",
        "icon": "🌑",  "branch": "agility", "tier": 3,
        "stat": "crit_chance", "value": 0.07,
        "requires": "agi_2",
    },
    "agi_4": {
        "name": "Вихор",         "desc": "+15% швидкість атаки",
        "icon": "🌀",  "branch": "agility", "tier": 4,
        "stat": "atk_speed",   "value": 0.15,
        "requires": "agi_3",
    },
    "agi_5": {
        "name": "Майстер бою",   "desc": "+20% шв. атаки, +5% крит",
        "icon": "👁",  "branch": "agility", "tier": 5,
        "stat": "atk_speed",   "value": 0.20,
        "extra_stat": "crit_chance", "extra_value": 0.05,
        "requires": "agi_4",
    },
}


# ══════════════════════════════════════════
#  ГІЛКИ СКІЛ-ТРИ
# ══════════════════════════════════════════

SKILL_BRANCHES = {
    "strength":  {"name": "Сила",         "icon": "⚔", "color": (220, 80,  60),  "nodes": ["str_1","str_2","str_3","str_4","str_5"]},
    "endurance": {"name": "Витривалість", "icon": "🛡", "color": (60,  160, 220), "nodes": ["end_1","end_2","end_3","end_4","end_5"]},
    "agility":   {"name": "Спритність",   "icon": "⚡", "color": (80,  200, 100), "nodes": ["agi_1","agi_2","agi_3","agi_4","agi_5"]},
}
