"""
╔══════════════════════════════════════════╗
║  ГЕРОЇ                                   ║
║  Додавай нових героїв тут!               ║
╚══════════════════════════════════════════╝

Як додати нового героя:
1. Додай блок у HEROES_DATA нижче
2. Переконайся що папка з анімацією існує в assets/animations/
3. Готово!

Рідкості:
    "common"    — 50% шанс в рулетці
    "rare"      — 30% шанс
    "epic"      — 15% шанс
    "legendary" — 5% шанс

Активні навички (active_id):
    "charge_attack"  — атака з розбігу
    "holy_strike"    — заряджений удар
    "dark_spin"      — AoE обертання
    "iaido"          — блискавичний удар (ігнорує 30% захисту)
    "fate_arrow"     — постріл 200% урону
    "berserker_rage" — режим берсерку
    "double_strike"  — подвійний удар
    "stealth_strike" — удар з тіні
    "fireball"       — вогняний шар
    "thunder_clap"   — удар блискавкою
"""

# ══════════════════════════════════════════
#  ШАНСИ У РУЛЕТЦІ
# ══════════════════════════════════════════

RARITY_WEIGHTS = {
    "common":    50.0,
    "rare":      30.0,
    "epic":      15.0,
    "legendary":  5.0,
}

# ══════════════════════════════════════════
#  КАТАЛОГ ГЕРОЇВ
# ══════════════════════════════════════════
# anim_folder → підпапка в assets/animations/
# frame_h     → висота одного кадру у спрайтшіті (px)
# anim_*      → (назва_файлу, кількість_кадрів) або (None, 0) якщо немає
# skills      → список навичок:
#     {"passive": True, "name": "...", "desc": "...", hp/attack/defense/crit/dodge/parry: ...}
#     {"passive": False, "name": "...", "desc": "...", "active_id": "..."}

HEROES_DATA = {

    # ══════════════════════ ЛИЦАР ══════════════════════
    "knight_1": {
        "name": "Лицар", "group": "knight", "rarity": "rare", "icon": "⚔",
        "lore": "Ветеран сотні битв. Щит тримає міцніше за скелю.",
        "anim_folder": "knight/Knight_1", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 4), "attack1": ("Attack 1", 5), "attack2": ("Attack 2", 4),
            "attack3": ("Attack 3", 4), "hurt": ("Hurt", 2), "dead": ("Dead", 6),
            "run": ("Run", 7), "walk": ("Walk", 8), "jump": ("Jump", 6),
            "block": ("Defend", 5), "special1": ("Run+Attack", 6),
        },
        "base": {"hp": 8, "attack": 0, "defense": 4, "crit": 0.0, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Залізна шкіра",  "desc": "+10 захисту",          "defense": 10},
            {"passive": True,  "name": "Загартований",   "desc": "+12 HP",                "hp": 12},
            {"passive": False, "name": "Натиск",         "desc": "Атака з розбігу — подвійний урон", "active_id": "charge_attack"},
        ],
    },

    "knight_2": {
        "name": "Срібний Лицар", "group": "knight", "rarity": "epic", "icon": "🛡",
        "lore": "Обраний орденом. Срібні обладунки відбивають прокляття.",
        "anim_folder": "knight/Knight_2", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 4), "attack1": ("Attack 1", 5), "attack2": ("Attack 2", 4),
            "attack3": ("Attack 3", 4), "hurt": ("Hurt", 2), "dead": ("Dead", 6),
            "run": ("Run", 7), "walk": ("Walk", 8), "jump": ("Jump", 6),
            "block": ("Defend", 5), "special1": ("Run+Attack", 6),
        },
        "base": {"hp": 12, "attack": 0, "defense": 8, "crit": 0.0, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Срібний щит",      "desc": "+15 захисту, +5% парирування", "defense": 15, "parry": 0.05},
            {"passive": True,  "name": "Загартоване серце", "desc": "+20 HP",                       "hp": 20},
            {"passive": False, "name": "Священний удар",   "desc": "Заряджений удар — +60% урону", "active_id": "holy_strike"},
        ],
    },

    "knight_3": {
        "name": "Темний Лицар", "group": "knight", "rarity": "legendary", "icon": "🌑",
        "lore": "Впав у тінь, але сила не зменшилась.",
        "anim_folder": "knight/Knight_3", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 4), "attack1": ("Attack 1", 5), "attack2": ("Attack 2", 4),
            "attack3": ("Attack 3", 4), "hurt": ("Hurt", 2), "dead": ("Dead", 6),
            "run": ("Run", 7), "walk": ("Walk", 8), "jump": ("Jump", 6),
            "block": ("Defend", 5), "special1": ("Run+Attack", 6),
        },
        "base": {"hp": 8, "attack": 8, "defense": 8, "crit": 0.0, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Темна сила",   "desc": "+20 атаки, +8% крит",      "attack": 20, "crit": 0.08},
            {"passive": True,  "name": "Нічна броня",  "desc": "+20 захисту, +22 HP",       "defense": 20, "hp": 22},
            {"passive": False, "name": "Темний вихор", "desc": "AoE удар — ошелешує ворога", "active_id": "dark_spin"},
        ],
    },

    # ══════════════════════ САМУРАЙ ══════════════════════
    "samurai": {
        "name": "Самурай", "group": "samurai", "rarity": "rare", "icon": "⚔",
        "lore": "Кодекс бусідо у кожному ударі.",
        "anim_folder": "samurai/Samurai", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 4), "attack2": ("Attack_2", 5),
            "attack3": ("Attack_3", 4), "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "run": ("Run", 8), "walk": ("Walk", 9), "jump": ("Jump", 9),
            "block": ("Protection", 2),
        },
        "base": {"hp": 0, "attack": 6, "defense": 0, "crit": 0.0, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Концентрація", "desc": "+10 атаки, +5% крит", "attack": 10, "crit": 0.05},
            {"passive": False, "name": "Іайдо",        "desc": "Блискавичний удар — ігнорує 30% захисту", "active_id": "iaido"},
        ],
    },

    "samurai_archer": {
        "name": "Самурай-Лучник", "group": "samurai", "rarity": "epic", "icon": "🏹",
        "lore": "Клинок і лук — два шляхи, одна смерть.",
        "anim_folder": "samurai/Samurai_Archer", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 9), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 5),
            "attack3": ("Attack_3", 6), "hurt": ("Hurt", 3), "dead": ("Dead", 5),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 9),
            "special1": ("Shot", 14),
        },
        "base": {"hp": 0, "attack": 8, "defense": 0, "crit": 0.04, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Снайпер",       "desc": "+12 атаки, +10% крит", "attack": 12, "crit": 0.10},
            {"passive": True,  "name": "Легкі кроки",   "desc": "+8% ухилення",          "dodge": 0.08},
            {"passive": False, "name": "Стріла долі",   "desc": "Постріл з 200% урону",  "active_id": "fate_arrow"},
        ],
    },

    "samurai_commander": {
        "name": "Самурай-Командир", "group": "samurai", "rarity": "legendary", "icon": "👑",
        "lore": "Командував армією в сотні тисяч. Кожен удар — наказ долі.",
        "anim_folder": "samurai/Samurai_Commander", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 4),
            "attack3": ("Attack_3", 4), "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 9),
            "block": ("Protect", 3),
        },
        "base": {"hp": 10, "attack": 10, "defense": 5, "crit": 0.05, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Стратег",       "desc": "+18 атаки, +10 захисту",    "attack": 18, "defense": 10},
            {"passive": True,  "name": "Командирська воля", "desc": "+25 HP, +5% крит",       "hp": 25, "crit": 0.05},
            {"passive": False, "name": "Смертельний наказ", "desc": "Серія з 3 ударів підряд", "active_id": "triple_strike"},
        ],
    },

    # ══════════════════════ НІНДЗЯ ══════════════════════
    "kunoichi": {
        "name": "Куноїчі", "group": "ninja", "rarity": "epic", "icon": "🌸",
        "lore": "Тінь серед тіней. Вражає перш ніж ворог відчує небезпеку.",
        "anim_folder": "ninja/Kunoichi", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 5),
            "hurt": ("Hurt", 3), "dead": ("Dead", 5),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 6),
        },
        "base": {"hp": 0, "attack": 5, "defense": 0, "crit": 0.08, "dodge": 0.05},
        "skills": [
            {"passive": True,  "name": "Отруйний клинок", "desc": "+8 атаки, +12% крит",  "attack": 8, "crit": 0.12},
            {"passive": True,  "name": "Тіньовий крок",   "desc": "+15% ухилення",         "dodge": 0.15},
            {"passive": False, "name": "Удар з тіні",     "desc": "Невидимий удар +150% урону", "active_id": "stealth_strike"},
        ],
    },

    "ninja_monk": {
        "name": "Ніндзя-Монах", "group": "ninja", "rarity": "rare", "icon": "🥋",
        "lore": "Поєднує медитацію і смерть у єдине ціле.",
        "anim_folder": "ninja/Ninja_Monk", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 5),
            "hurt": ("Hurt", 3), "dead": ("Dead", 5),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 6),
        },
        "base": {"hp": 0, "attack": 7, "defense": 2, "crit": 0.05, "dodge": 0.03},
        "skills": [
            {"passive": True,  "name": "Залізний кулак", "desc": "+12 атаки",              "attack": 12},
            {"passive": False, "name": "Подвійний удар", "desc": "Два удари за одну дію",  "active_id": "double_strike"},
        ],
    },

    "ninja_peasant": {
        "name": "Ніндзя-Селянин", "group": "ninja", "rarity": "common", "icon": "🌾",
        "lore": "Здається звичайним. Насправді — вбивця.",
        "anim_folder": "ninja/Ninja_Peasant", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 5),
            "hurt": ("Hurt", 3), "dead": ("Dead", 5),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 6),
        },
        "base": {"hp": 0, "attack": 4, "defense": 0, "crit": 0.06, "dodge": 0.04},
        "skills": [
            {"passive": True, "name": "Маскування", "desc": "+8% ухилення, +6 атаки", "dodge": 0.08, "attack": 6},
        ],
    },

    # ══════════════════════ СКЕЛЕТ (гравець) ══════════════════════
    "skeleton_warrior": {
        "name": "Скелет-Воїн", "group": "skeleton", "rarity": "rare", "icon": "💀",
        "lore": "Піднятий з мертвих магією. Не відчуває болю.",
        "anim_folder": "skeleton/Skeleton_Warrior", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 4),
            "attack3": ("Attack_3", 4), "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "run": ("Run", 8), "walk": ("Walk", 8),
            "block": ("Protect", 3),
        },
        "base": {"hp": 5, "attack": 8, "defense": 3, "crit": 0.0, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Кісткова броня",  "desc": "+12 захисту",             "defense": 12},
            {"passive": False, "name": "Крик смерті",     "desc": "Залякує ворога, -20% атаки ворога", "active_id": "death_scream"},
        ],
    },

    "skeleton_archer": {
        "name": "Скелет-Лучник", "group": "skeleton", "rarity": "common", "icon": "🏹",
        "lore": "Стріляє без утоми. Кістки не втомлюються.",
        "anim_folder": "skeleton/Skeleton_Archer", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 4),
            "attack3": ("Attack_3", 4), "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "walk": ("Walk", 8),
        },
        "base": {"hp": 0, "attack": 7, "defense": 0, "crit": 0.07, "dodge": 0.0},
        "skills": [
            {"passive": True, "name": "Мертве око", "desc": "+10% крит, +8 атаки", "crit": 0.10, "attack": 8},
        ],
    },

    # ══════════════════════ ВАМПІР ══════════════════════
    "vampire_1": {
        "name": "Вампір", "group": "vampire", "rarity": "epic", "icon": "🧛",
        "lore": "Живиться кров'ю ворогів. Сильніший вночі.",
        "anim_folder": "vampire/1", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 4),
            "attack3": ("Attack_3", 4), "attack4": ("Attack_4", 5),
            "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 6),
        },
        "base": {"hp": 0, "attack": 6, "defense": 2, "crit": 0.06, "dodge": 0.04},
        "skills": [
            {"passive": True,  "name": "Кровосос",      "desc": "+15 атаки, +10% крит",         "attack": 15, "crit": 0.10},
            {"passive": True,  "name": "Вампірська регенерація", "desc": "+20 HP",              "hp": 20},
            {"passive": False, "name": "Укус вампіра",  "desc": "Краде 30% HP від нанесеного урону", "active_id": "vampiric_bite"},
        ],
    },

    # ══════════════════════ ПЕРЕВЕРТЕНЬ ══════════════════════
    "black_werewolf": {
        "name": "Чорний Вовкулак", "group": "werewolf", "rarity": "epic", "icon": "🐺",
        "lore": "Найстрашніший з зграї. Темна шерсть не відбиває місяця.",
        "anim_folder": "werewolf/Black_Werewolf", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 4),
            "attack3": ("Attack_3", 4), "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "run": ("Run", 8), "walk": ("walk", 8), "jump": ("Jump", 6),
            "special1": ("Run+Attack", 6),
        },
        "base": {"hp": 5, "attack": 10, "defense": 0, "crit": 0.05, "dodge": 0.05},
        "skills": [
            {"passive": True,  "name": "Зграйна лють",  "desc": "+18 атаки, +8% ухилення", "attack": 18, "dodge": 0.08},
            {"passive": True,  "name": "Загартування",  "desc": "+15 HP",                   "hp": 15},
            {"passive": False, "name": "Берсерк",       "desc": "+50% атаки на 2 ходи",     "active_id": "berserker_rage"},
        ],
    },

    # ══════════════════════ МАГИ ══════════════════════
    "fire_wizard": {
        "name": "Вогняний Маг", "group": "wizard", "rarity": "legendary", "icon": "🔥",
        "lore": "Вогонь його слухається як пес господаря.",
        "anim_folder": "wizard/Fire Wizard", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 4),
            "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 6),
            "special1": ("Fireball", 8), "special2": ("Flame_jet", 10),
        },
        "base": {"hp": 0, "attack": 12, "defense": 0, "crit": 0.08, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Вогняне серце",  "desc": "+20 атаки, +12% крит",           "attack": 20, "crit": 0.12},
            {"passive": True,  "name": "Вогнестійкість", "desc": "+8 захисту, +15 HP",              "defense": 8, "hp": 15},
            {"passive": False, "name": "Вогненна куля",  "desc": "Вогненний шар — 250% урону AoE", "active_id": "fireball"},
        ],
    },

    "lightning_mage": {
        "name": "Маг Блискавки", "group": "wizard", "rarity": "epic", "icon": "⚡",
        "lore": "Ловить бурі голими руками.",
        "anim_folder": "wizard/Lightning Mage", "frame_h": 128,
        "anim": {
            "idle": ("Idle", 6), "attack1": ("Attack_1", 5), "attack2": ("Attack_2", 4),
            "hurt": ("Hurt", 3), "dead": ("Dead", 6),
            "run": ("Run", 8), "walk": ("Walk", 8), "jump": ("Jump", 6),
        },
        "base": {"hp": 0, "attack": 10, "defense": 0, "crit": 0.09, "dodge": 0.0},
        "skills": [
            {"passive": True,  "name": "Статичний заряд", "desc": "+14 атаки, +15% крит", "attack": 14, "crit": 0.15},
            {"passive": False, "name": "Удар грому",      "desc": "Блискавка — 180% урону, шанс оглушення", "active_id": "thunder_clap"},
        ],
    },
}
