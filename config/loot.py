"""
╔══════════════════════════════════════════╗
║  ЛУТ: МАТЕРІАЛИ, ПРЕДМЕТИ, КРЕСЛЕННИКИ  ║
║  Все в одному місці для легкого правлення║
╚══════════════════════════════════════════╝

ЯК ДОДАТИ НОВИЙ МАТЕРІАЛ:
    Додай рядок у MATERIALS_DATA нижче.
    Ключ стане material_id.

ЯК ДОДАТИ НОВИЙ ПРЕДМЕТ:
    Додай рядок у ITEMS_DATA нижче.

ЯК ДОДАТИ НОВИЙ КРЕСЛЕНИК:
    Додай блок у BLUEPRINTS_DATA нижче.
    recipe — словник {material_id: кількість}.
    bonus_materials — матеріали що дають бонус при крафті.
"""

# ══════════════════════════════════════════
#  МАТЕРІАЛИ
# ══════════════════════════════════════════
# Ключ → (name, icon, description, rarity, attack, defense, hp, crit, multiplier, is_metal)

MATERIALS_DATA = {
    # ──────────────────── Common ────────────────────────────
    "wood":            ("Дерево",            "🪵", "Звичайне дерево з лісу",        "common",    0, 0,  0, 0.00, 1.0,  False),
    "iron_ore":        ("Залізна руда",      "🪨", "Сирий метал",                   "common",    0, 0,  0, 0.00, 1.1,  True),
    "iron_bar":        ("Залізний зливок",   "⬛", "Очищене залізо",                "common",    0, 0,  0, 0.00, 1.3,  True),
    "leather":         ("Шкіра",             "🟫", "Знята зі звірів",               "common",    0, 0,  0, 0.00, 1.0,  False),
    "bone":            ("Кістка",            "🦴", "Залишок після бою",             "common",    0, 0,  0, 0.00, 0.9,  False),
    "bone_dust":       ("Кісткова пудра",    "⬜", "Подрібнені кістки",             "common",    1, 0,  0, 0.00, 1.0,  False),

    # ──────────────────── Uncommon ──────────────────────────
    "silver_ore":      ("Срібна руда",       "🥈", "Блискуча руда з руїн",          "uncommon",  0, 0,  0, 0.00, 1.6,  True),
    "silver_bar":      ("Срібний зливок",    "⚪", "Очищене срібло",                "uncommon",  1, 0,  0, 0.02, 2.0,  True),
    "enchanted_wood":  ("Зачароване дерево", "🌿", "Деревина просочена магією",     "uncommon",  0, 0,  8, 0.00, 1.5,  False),
    "shadow_cloth":    ("Тіньова тканина",   "🩶", "Тканина з пітьми",              "uncommon",  0, 2,  0, 0.00, 1.4,  False),
    "quartz":          ("Кварц",             "🔷", "Прозорий камінь",               "uncommon",  0, 0,  0, 0.01, 1.5,  False),
    "hardwood":        ("Тверде дерево",     "🌳", "Міцніше за залізо",             "uncommon",  0, 1,  5, 0.00, 1.4,  False),
    "iron_chain":      ("Залізний ланцюг",   "⛓", "Плетіння ланцюгів",             "uncommon",  0, 2,  0, 0.00, 1.3,  True),

    # ──────────────────── Rare ──────────────────────────────
    "dark_steel":      ("Темна сталь",       "🖤", "Рідкісний метал з тіней",       "rare",      2, 0,  0, 0.00, 2.8,  True),
    "magic_core":      ("Магічне ядро",      "✨", "Згусток чистої магії",          "rare",      0, 0,  0, 0.03, 2.5,  False),
    "fire_gem":        ("Вогняний камінь",   "🔥", "Горить вічним вогнем",          "rare",      2, 0,  0, 0.02, 2.6,  False),
    "frost_crystal":   ("Кристал льоду",     "❄",  "Вічна крига зі скель",          "rare",      0, 3, 12, 0.00, 2.4,  False),
    "storm_shard":     ("Уламок бурі",       "⚡", "Тріщить від статики",           "rare",      2, 0,  0, 0.03, 2.7,  False),
    "blood_crystal":   ("Кривавий кристал",  "🔴", "Кристал що пульсує",            "rare",      3, 0,  0, 0.04, 2.9,  False),
    "mithril_ore":     ("Мітрилова руда",    "🩵", "Легкий але міцний метал",       "rare",      0, 0,  0, 0.00, 3.0,  True),
    "mithril_bar":     ("Мітриловий зливок", "💙", "Найміцніший відомий метал",     "rare",      0, 4, 15, 0.00, 3.8,  True),

    # ──────────────────── Epic ──────────────────────────────
    "dragon_scale":    ("Луска дракона",     "💎", "Непробивна луска",              "epic",      0, 3, 10, 0.00, 4.5,  False),
    "void_essence":    ("Есенція пустоти",   "🌀", "Матерія між світами",           "epic",      4, 0,  0, 0.05, 5.0,  False),
    "phoenix_feather": ("Перо фенікса",      "🪶", "Горить але не згорає",          "epic",      3, 0, 20, 0.03, 4.8,  False),
    "shadow_essence":  ("Есенція тіні",      "🌑", "Згусток темряви",               "epic",      2, 2,  0, 0.04, 4.6,  False),
    "runic_stone":     ("Рунічний камінь",   "🪨", "Вкритий давніми рунами",        "epic",      2, 3, 10, 0.00, 4.2,  False),

    # ──────────────────── Legendary ─────────────────────────
    "star_metal":      ("Зіркова сталь",     "⭐", "Впала зі зірок",               "legendary", 5, 2,  0, 0.04, 6.5,  True),
    "ancient_core":    ("Древнє ядро",       "🌐", "Серце стародавнього духа",      "legendary", 3, 3, 25, 0.05, 7.0,  False),
    "dragonite":       ("Драконіт",          "🐉", "Серце дракона — чистий вогонь", "legendary", 6, 0,  0, 0.06, 7.3,  True),
}


# ══════════════════════════════════════════
#  ПРЕДМЕТИ (ITEMS)
# ══════════════════════════════════════════
# Ключ → (name, type, value, icon, description, attack, defense, hp, hp_restore, crit)

ITEMS_DATA = {
    # Зброя
    "rusty_sword":   ("Іржавий меч",        "weapon", 5,   "⚔",  "Старий меч",                        5, 0, 0, 0, 0.00),
    # Зілля
    "small_potion":  ("Мале зілля",         "potion", 10,  "🧪", "Відновлює 20 HP",                   0, 0, 0, 20, 0.00),
    "big_potion":    ("Велике зілля",       "potion", 25,  "🍶", "Відновлює 50 HP",                   0, 0, 0, 50, 0.00),
    "power_potion":  ("Зілля сили",         "potion", 30,  "💪", "+5 до атаки",                       5, 0, 0, 0, 0.00),
    # Броня
    "leather_armor": ("Шкіряна броня",      "armor",  40,  "🥋", "+5 до захисту",                     0, 5, 0, 0, 0.00),
    "chainmail":     ("Кольчуга",           "armor",  80,  "🛡", "+10 до захисту",                    0, 10, 0, 0, 0.00),
    "shadow_vest":   ("Тіньовий жилет",     "armor",  120, "🩶", "+14 захист, +20 HP",                0, 14, 20, 0, 0.00),
    "dragon_armor":  ("Броня дракона",      "armor",  300, "💎", "+22 захист, +40 HP",                0, 22, 40, 0, 0.00),
    "mithril_plate": ("Мітрилові латні",    "armor",  220, "💙", "+18 захист, +30 HP",                0, 18, 30, 0, 0.00),
    "bone_armor":    ("Кісткова броня",     "armor",  70,  "🦴", "+8 захист",                         0, 8, 0, 0, 0.00),
    "silver_mail":   ("Срібна кольчуга",    "armor",  150, "⚪", "+12 захист, +1% крит",              0, 12, 0, 0, 0.01),
}


# ══════════════════════════════════════════
#  КРЕСЛЕННИКИ (BLUEPRINTS)
# ══════════════════════════════════════════

BLUEPRINTS_DATA = {

    # ════════════ ЗБРОЯ — Tier 1 (common) ════════════
    "bp_dagger": {
        "name": "Кресленик: Кинджал",
        "result": ("dagger", "Кинджал", 9, "🗡", "Швидкий клинок з тонким лезом"),
        "recipe": {"wood": 2, "iron_bar": 1},
        "unlock_cost": 12,
        "type": "weapon", "attack": 9,
        "rarity": "common",
    },
    "bp_iron_sword": {
        "name": "Кресленик: Залізний меч",
        "result": ("iron_sword", "Залізний меч", 13, "⚔", "Збалансована зброя ближнього бою"),
        "recipe": {"iron_bar": 3, "wood": 1},
        "unlock_cost": 20,
        "type": "weapon", "attack": 13,
        "rarity": "common",
    },
    "bp_battle_axe": {
        "name": "Кресленик: Бойова сокира",
        "result": ("battle_axe", "Бойова сокира", 17, "🪓", "Важка та потужна. Трощить броню"),
        "recipe": {"iron_bar": 4, "wood": 2, "leather": 1},
        "unlock_cost": 30,
        "type": "weapon", "attack": 17,
        "rarity": "common",
    },
    "bp_war_hammer": {
        "name": "Кресленик: Бойовий молот",
        "result": ("war_hammer", "Бойовий молот", 18, "🔨", "Дробить щити та кістки однаково"),
        "recipe": {"iron_bar": 5, "hardwood": 2},
        "bonus_materials": ["hardwood"],
        "unlock_cost": 32,
        "type": "weapon", "attack": 18,
        "rarity": "common",
    },
    "bp_bone_club": {
        "name": "Кресленик: Кісткова булава",
        "result": ("bone_club", "Кісткова булава", 12, "🦴", "Груба зброя з кісток ворогів"),
        "recipe": {"bone": 5, "bone_dust": 2, "leather": 1},
        "bonus_materials": ["bone_dust"],
        "unlock_cost": 18,
        "type": "weapon", "attack": 12,
        "rarity": "common",
    },
    "bp_bone_spear": {
        "name": "Кресленик: Кістяний спис",
        "result": ("bone_spear", "Кістяний спис", 15, "🦴", "Довгий спис з загостреної кістки"),
        "recipe": {"bone": 6, "bone_dust": 3, "wood": 2},
        "bonus_materials": ["bone_dust"],
        "unlock_cost": 22,
        "type": "weapon", "attack": 15,
        "rarity": "common",
    },

    # ════════════ ЗБРОЯ — Tier 2 (uncommon) ════════════
    "bp_silver_dagger": {
        "name": "Кресленик: Срібний кинджал",
        "result": ("silver_dagger", "Срібний кинджал", 14, "🥈", "Легкий та гострий. Добрий шанс критів"),
        "recipe": {"silver_bar": 2, "leather": 1},
        "bonus_materials": ["silver_bar"],
        "unlock_cost": 25,
        "type": "weapon", "attack": 14,
        "rarity": "uncommon",
    },
    "bp_silver_sword": {
        "name": "Кресленик: Срібний меч",
        "result": ("silver_sword", "Срібний меч", 19, "⚔", "Блискучий клинок з відмінним балансом"),
        "recipe": {"silver_bar": 3, "enchanted_wood": 1},
        "bonus_materials": ["silver_bar", "enchanted_wood"],
        "unlock_cost": 35,
        "type": "weapon", "attack": 19,
        "rarity": "uncommon",
    },
    "bp_quartz_blade": {
        "name": "Кресленик: Кварцовий клинок",
        "result": ("quartz_blade", "Кварцовий клинок", 16, "🔷", "Прозорий клинок що ловить світло"),
        "recipe": {"silver_bar": 2, "quartz": 3, "leather": 1},
        "bonus_materials": ["silver_bar", "quartz"],
        "unlock_cost": 28,
        "type": "weapon", "attack": 16,
        "rarity": "uncommon",
    },
    "bp_frost_blade": {
        "name": "Кресленик: Морозний клинок",
        "result": ("frost_blade", "Морозний клинок", 20, "❄", "Вкритий вічним льодом. Морозить ворогів"),
        "recipe": {"iron_bar": 3, "frost_crystal": 2},
        "bonus_materials": ["frost_crystal"],
        "unlock_cost": 38,
        "type": "weapon", "attack": 20,
        "rarity": "uncommon",
    },

    # ════════════ ЗБРОЯ — Tier 3 (rare) ════════════
    "bp_dark_blade": {
        "name": "Кресленик: Темний клинок",
        "result": ("dark_blade", "Темний клинок", 22, "🌑", "Магічний клинок що п'є душі"),
        "recipe": {"dark_steel": 3, "magic_core": 1, "leather": 2},
        "bonus_materials": ["dark_steel", "magic_core"],
        "unlock_cost": 50,
        "type": "weapon", "attack": 22,
        "rarity": "rare",
    },
    "bp_shadow_blade": {
        "name": "Кресленик: Тіньовий клинок",
        "result": ("shadow_blade", "Тіньовий клинок", 25, "🩶", "Зброя тіней. Часто б'є критично"),
        "recipe": {"dark_steel": 2, "shadow_cloth": 3, "magic_core": 1},
        "bonus_materials": ["magic_core", "shadow_cloth"],
        "unlock_cost": 60,
        "type": "weapon", "attack": 25,
        "rarity": "rare",
    },
    "bp_fire_sword": {
        "name": "Кресленик: Вогняний меч",
        "result": ("fire_sword", "Вогняний меч", 27, "🔥", "Леза горять вічним вогнем"),
        "recipe": {"iron_bar": 3, "fire_gem": 2, "magic_core": 1},
        "bonus_materials": ["fire_gem", "magic_core"],
        "unlock_cost": 65,
        "type": "weapon", "attack": 27,
        "rarity": "rare",
    },
    "bp_storm_blade": {
        "name": "Кресленик: Клинок бурі",
        "result": ("storm_blade", "Клинок бурі", 26, "⚡", "Кожен удар супроводжується тріском"),
        "recipe": {"dark_steel": 2, "storm_shard": 2, "magic_core": 1},
        "bonus_materials": ["storm_shard", "magic_core"],
        "unlock_cost": 62,
        "type": "weapon", "attack": 26,
        "rarity": "rare",
    },
    "bp_blood_sword": {
        "name": "Кресленик: Кривавий меч",
        "result": ("blood_sword", "Кривавий меч", 28, "🔴", "Живиться кров'ю ворогів"),
        "recipe": {"blood_crystal": 2, "iron_bar": 2, "leather": 2},
        "bonus_materials": ["blood_crystal"],
        "unlock_cost": 70,
        "type": "weapon", "attack": 28,
        "rarity": "rare",
    },
    "bp_runic_sword": {
        "name": "Кресленик: Рунічний меч",
        "result": ("runic_sword", "Рунічний меч", 30, "🪨", "Вкритий рунами давніх магів"),
        "recipe": {"runic_stone": 2, "dark_steel": 2, "magic_core": 1},
        "bonus_materials": ["runic_stone", "dark_steel"],
        "unlock_cost": 72,
        "type": "weapon", "attack": 30,
        "rarity": "rare",
    },

    # ════════════ ЗБРОЯ — Tier 4 (epic) ════════════
    "bp_mithril_sword": {
        "name": "Кресленик: Мітриловий меч",
        "result": ("mithril_sword", "Мітриловий меч", 32, "💙", "Надлегкий та надміцний"),
        "recipe": {"mithril_bar": 3, "enchanted_wood": 1, "magic_core": 1},
        "bonus_materials": ["mithril_bar", "magic_core"],
        "unlock_cost": 80,
        "type": "weapon", "attack": 32,
        "rarity": "epic",
    },
    "bp_void_blade": {
        "name": "Кресленик: Клинок пустоти",
        "result": ("void_blade", "Клинок пустоти", 30, "🌀", "Розриває простір між ударами"),
        "recipe": {"void_essence": 2, "dark_steel": 2, "magic_core": 2},
        "bonus_materials": ["void_essence", "magic_core"],
        "unlock_cost": 75,
        "type": "weapon", "attack": 30,
        "rarity": "epic",
    },
    "bp_shadow_reaper": {
        "name": "Кресленик: Коса тіней",
        "result": ("shadow_reaper", "Коса тіней", 33, "🌑", "Жне душі в темряві"),
        "recipe": {"shadow_essence": 2, "void_essence": 1, "dark_steel": 3},
        "bonus_materials": ["shadow_essence", "void_essence"],
        "unlock_cost": 85,
        "type": "weapon", "attack": 33,
        "rarity": "epic",
    },
    "bp_phoenix_sword": {
        "name": "Кресленик: Меч Фенікса",
        "result": ("phoenix_sword", "Меч Фенікса", 34, "🪶", "Відроджується з попелу битв"),
        "recipe": {"phoenix_feather": 2, "fire_gem": 2, "mithril_bar": 2},
        "bonus_materials": ["phoenix_feather", "fire_gem"],
        "unlock_cost": 88,
        "type": "weapon", "attack": 34,
        "rarity": "epic",
    },

    # ════════════ ЗБРОЯ — Tier 5 (legendary) ════════════
    "bp_dragon_sword": {
        "name": "Кресленик: Меч дракона",
        "result": ("dragon_sword", "Меч дракона", 38, "🐉", "Легендарна зброя кована з луски"),
        "recipe": {"dragon_scale": 2, "dark_steel": 2, "magic_core": 2},
        "bonus_materials": ["dragon_scale"],
        "unlock_cost": 90,
        "type": "weapon", "attack": 38,
        "rarity": "legendary",
    },
    "bp_star_blade": {
        "name": "Кресленик: Зірковий клинок",
        "result": ("star_blade", "Зірковий клинок", 40, "⭐", "Кований із зіркової сталі"),
        "recipe": {"star_metal": 3, "magic_core": 2, "enchanted_wood": 1},
        "bonus_materials": ["star_metal"],
        "unlock_cost": 100,
        "type": "weapon", "attack": 40,
        "rarity": "legendary",
    },
    "bp_void_dragon": {
        "name": "Кресленик: Дракон Пустоти",
        "result": ("void_dragon_sword", "Дракон Пустоти", 45, "🌌", "Найсильніша зброя відомих земель"),
        "recipe": {"dragon_scale": 3, "void_essence": 3, "magic_core": 3, "dark_steel": 2},
        "bonus_materials": ["dragon_scale", "void_essence", "magic_core"],
        "unlock_cost": 120,
        "type": "weapon", "attack": 45,
        "rarity": "legendary",
    },
    "bp_ancient_sword": {
        "name": "Кресленик: Клинок Вічності",
        "result": ("ancient_sword", "Клинок Вічності", 50, "🌐", "Зброя до якої доторкнулись боги"),
        "recipe": {"ancient_core": 2, "star_metal": 2, "dragon_scale": 2, "void_essence": 2},
        "bonus_materials": ["ancient_core", "star_metal"],
        "unlock_cost": 150,
        "type": "weapon", "attack": 50,
        "rarity": "legendary",
    },

    # ════════════ БРОНЯ ════════════
    "bp_leather_armor": {
        "name": "Кресленик: Шкіряна броня+",
        "result": ("crafted_leather", "Шкіряна броня+", 50, "🥋", "Покращена шкіряна броня мисливця"),
        "recipe": {"leather": 4, "bone": 2},
        "unlock_cost": 15,
        "type": "armor", "defense": 7,
        "rarity": "common",
    },
    "bp_bone_armor": {
        "name": "Кресленик: Кісткова броня",
        "result": ("crafted_bone_armor", "Кісткова броня", 65, "🦴", "Броня з кісток. Легка і міцна"),
        "recipe": {"bone": 6, "bone_dust": 3, "leather": 2},
        "bonus_materials": ["bone_dust"],
        "unlock_cost": 22,
        "type": "armor", "defense": 8,
        "rarity": "common",
    },
    "bp_hardwood_shield": {
        "name": "Кресленик: Дерев'яний щит",
        "result": ("hardwood_shield", "Дерев'яний щит", 55, "🌳", "Щит з твердого дерева"),
        "recipe": {"hardwood": 4, "iron_bar": 1, "leather": 2},
        "bonus_materials": ["hardwood"],
        "unlock_cost": 20,
        "type": "armor", "defense": 9, "hp": 10,
        "rarity": "common",
    },
    "bp_chainmail_plus": {
        "name": "Кресленик: Посилена кольчуга",
        "result": ("chainmail_plus", "Посилена кольчуга", 100, "🛡", "+13 захист, надійна броня"),
        "recipe": {"iron_bar": 5, "iron_chain": 3, "leather": 2},
        "bonus_materials": ["iron_chain"],
        "unlock_cost": 35,
        "type": "armor", "defense": 13,
        "rarity": "uncommon",
    },
    "bp_silver_mail": {
        "name": "Кресленик: Срібна кольчуга",
        "result": ("crafted_silver_mail", "Срібна кольчуга", 150, "⚪", "+12 захист, +1% крит. удар"),
        "recipe": {"silver_bar": 4, "leather": 2, "quartz": 1},
        "bonus_materials": ["silver_bar", "quartz"],
        "unlock_cost": 50,
        "type": "armor", "defense": 12,
        "rarity": "uncommon",
    },
    "bp_frost_armor": {
        "name": "Кресленик: Крижана броня",
        "result": ("frost_armor", "Крижана броня", 130, "❄", "+15 захист, +20 HP — вкрита льодом"),
        "recipe": {"frost_crystal": 3, "iron_bar": 4, "leather": 2},
        "bonus_materials": ["frost_crystal"],
        "unlock_cost": 55,
        "type": "armor", "defense": 15, "hp": 20,
        "rarity": "uncommon",
    },
    "bp_shadow_vest": {
        "name": "Кресленик: Тіньовий жилет",
        "result": ("crafted_shadow_vest", "Тіньовий жилет", 120, "🩶", "+14 захист, +20 HP — броня тіней"),
        "recipe": {"shadow_cloth": 4, "leather": 2, "dark_steel": 1},
        "bonus_materials": ["shadow_cloth", "dark_steel"],
        "unlock_cost": 45,
        "type": "armor", "defense": 14, "hp": 20,
        "rarity": "rare",
    },
    "bp_runic_armor": {
        "name": "Кресленик: Рунічна броня",
        "result": ("runic_armor", "Рунічна броня", 175, "🪨", "+16 захист, +25 HP, руни захисту"),
        "recipe": {"runic_stone": 2, "iron_bar": 4, "enchanted_wood": 2},
        "bonus_materials": ["runic_stone", "enchanted_wood"],
        "unlock_cost": 65,
        "type": "armor", "defense": 16, "hp": 25,
        "rarity": "rare",
    },
    "bp_mithril_plate": {
        "name": "Кресленик: Мітрилові латні",
        "result": ("crafted_mithril_plate", "Мітрилові латні", 220, "💙", "+18 захист, +30 HP — найміцніший метал"),
        "recipe": {"mithril_bar": 4, "enchanted_wood": 2, "iron_chain": 2},
        "bonus_materials": ["mithril_bar"],
        "unlock_cost": 75,
        "type": "armor", "defense": 18, "hp": 30,
        "rarity": "epic",
    },
    "bp_phoenix_armor": {
        "name": "Кресленик: Броня Фенікса",
        "result": ("phoenix_armor", "Броня Фенікса", 260, "🪶", "+20 захист, +35 HP — відроджує власника"),
        "recipe": {"phoenix_feather": 3, "mithril_bar": 3, "magic_core": 2},
        "bonus_materials": ["phoenix_feather", "mithril_bar"],
        "unlock_cost": 90,
        "type": "armor", "defense": 20, "hp": 35,
        "rarity": "epic",
    },
    "bp_dragon_armor": {
        "name": "Кресленик: Броня дракона",
        "result": ("crafted_dragon_armor", "Броня дракона", 300, "💎", "+22 захист, +40 HP — легендарна луска"),
        "recipe": {"dragon_scale": 3, "mithril_bar": 2, "magic_core": 2},
        "bonus_materials": ["dragon_scale", "mithril_bar"],
        "unlock_cost": 100,
        "type": "armor", "defense": 22, "hp": 40,
        "rarity": "legendary",
    },
    "bp_ancient_armor": {
        "name": "Кресленик: Броня Вічності",
        "result": ("ancient_armor", "Броня Вічності", 380, "🌐", "+28 захист, +50 HP — благословення богів"),
        "recipe": {"ancient_core": 2, "dragon_scale": 2, "star_metal": 2, "magic_core": 2},
        "bonus_materials": ["ancient_core", "star_metal", "dragon_scale"],
        "unlock_cost": 140,
        "type": "armor", "defense": 28, "hp": 50,
        "rarity": "legendary",
    },

    # ════════════ ІНСТРУМЕНТИ ════════════
    "bp_pickaxe": {
        "name": "Кресленик: Кайло",
        "result": ("pickaxe", "Кайло", 20, "⛏", "Обов'язковий інструмент шахтаря"),
        "recipe": {"iron_bar": 3, "wood": 2},
        "unlock_cost": 15,
        "type": "tool",
        "rarity": "common",
    },
    "bp_shovel": {
        "name": "Кресленик: Лопата",
        "result": ("shovel", "Лопата", 15, "🪣", "Прискорює копання на 10%"),
        "recipe": {"iron_bar": 2, "wood": 2, "leather": 1},
        "unlock_cost": 12,
        "type": "tool",
        "rarity": "common",
    },
}
