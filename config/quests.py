"""
╔══════════════════════════════════════════════════════════════╗
║  КВЕСТИ                                                      ║
║  Додавай нові квести тут — більше нічого не треба чіпати    ║
╚══════════════════════════════════════════════════════════════╝

ЯК ДОДАТИ НОВИЙ КВЕСТ:
───────────────────────
1. Додай блок у QUESTS_DATA нижче
2. Готово! Квест автоматично з'явиться у старости

Формат умов (unlock_when / complete_when):
  "always"                    → завжди доступний
  "quest:назва_квесту"        → після виконання іншого квесту
  "level:5"                   → коли рівень гравця >= 5
  "kills:goblin:3"            → вбито >= 3 гоблінів
  "kills:orc:5"               → вбито >= 5 орків
  "kills:any:10"              → будь-які 10 вбивств
  "material:iron_bar:5"       → є >= 5 залізних зливків
  "gold:100"                  → є >= 100 золота
  "weapon_attack:13"          → є зброя з атакою >= 13
  "wins:3"                    → виграно >= 3 боїв

Для складних умов — пиши Python лямбду:
  "lambda p: p.level >= 5 and 'q_welcome' in p.quests_done"
"""

# ══════════════════════════════════════════
#  СЮЖЕТНІ КВЕСТИ
# ══════════════════════════════════════════

QUESTS_DATA = [

    # ──────────────── АКТ 1: Перші кроки ────────────────────────

    {
        "id":      "q_welcome",
        "title":   "Перші кроки",
        "icon":    "🏘",
        "story": [
            "Слухай, мандрівнику...",
            "Наше село оточене небезпекою. Гобліни щодня\n"
            "нападають на поля й забирають нашу їжу.",
            "Ти виглядаєш як боєць. Допоможи нам —\n"
            "переможи кількох гоблінів у лісі.",
            "Ось золото на початок. Більше отримаєш\n"
            "коли повернешся з перемогою.",
        ],
        "unlock_when":   "always",
        "complete_when": "kills:goblin:3",
        "objective":     "Вбий 3 гоблінів у лісі",
        "reward_gold":   40,
        "reward_xp":     30,
        "unlocks":       "q_iron_for_village",
    },

    {
        "id":      "q_iron_for_village",
        "title":   "Залізо для села",
        "icon":    "⚒",
        "story": [
            "Добре, добре! Ти справжній воїн.",
            "Але нашому ковалю потрібне залізо.\n"
            "Без нього ми не зможемо зробити нові інструменти.",
            "У лісі є місця де можна знайти руду.\n"
            "Принеси мені кілька залізних зливків.",
        ],
        "unlock_when":   "quest:q_welcome",
        "complete_when": "material:iron_bar:5",
        "objective":     "Мати 5 залізних зливків",
        "reward_gold":   50,
        "reward_xp":     25,
        "reward_mats":   {"leather": 3, "bone": 4},
        "unlocks":       "q_first_sword",
    },

    {
        "id":      "q_first_sword",
        "title":   "Справжній клинок",
        "icon":    "⚔",
        "story": [
            "Ти вже не новачок, це видно.",
            "Але з тим іржавим залізом далеко не підеш.\n"
            "Час скувати щось гідне.",
            "Піди до майстерні й скуй собі залізний меч\n"
            "або щось краще. Я буду чекати.",
        ],
        "unlock_when":   "quest:q_iron_for_village",
        "complete_when": "weapon_attack:13",
        "objective":     "Скрафтити зброю з атакою 13+",
        "reward_gold":   60,
        "reward_xp":     40,
        "reward_mats":   {"silver_ore": 3},
        "unlocks":       "q_orc_threat",
    },

    # ──────────────── АКТ 2: Загроза орків ──────────────────────

    {
        "id":      "q_orc_threat",
        "title":   "Загроза з півночі",
        "icon":    "🧟",
        "story": [
            "Є погані новини, герою...",
            "Розвідники донесли що орки збираються\n"
            "в лісі на північ від села.",
            "Нам потрібен хтось хоробрий щоб зупинити їх\n"
            "поки вони не стали справжньою армією.",
            "Переможи орків — наш народ буде в безпеці.",
        ],
        "unlock_when":   "quest:q_first_sword",
        "complete_when": "kills:orc:5",
        "objective":     "Вбий 5 орків",
        "reward_gold":   80,
        "reward_xp":     60,
        "reward_mats":   {"dark_steel": 1, "iron_chain": 2},
        "unlocks":       "q_ruins_mystery",
    },

    {
        "id":      "q_ruins_mystery",
        "title":   "Таємниця руїн",
        "icon":    "🗿",
        "story": [
            "Давно забуті руїни на сході...",
            "Старожили кажуть що там ховається щось темне.\n"
            "Мандрівники що йшли туди — не поверталися.",
            "Ти єдиний кому я можу довіряти цей пошук.\n"
            "Дізнайся що відбувається в руїнах.",
        ],
        "unlock_when":   "quest:q_orc_threat",
        "complete_when": "kills:dark_knight:3",
        "objective":     "Переможи 3 темних лицарів у руїнах",
        "reward_gold":   100,
        "reward_xp":     80,
        "reward_mats":   {"magic_core": 2, "shadow_cloth": 2},
        "unlocks":       "q_silver_armor",
    },

    {
        "id":      "q_silver_armor",
        "title":   "Срібний захист",
        "icon":    "🛡",
        "story": [
            "Темні сили стають сильнішими...",
            "Тобі потрібен кращий захист якщо хочеш вижити\n"
            "в наступних битвах.",
            "Принеси срібла — майстер зробить тобі\n"
            "гідну броню для важких боїв.",
        ],
        "unlock_when":   "quest:q_ruins_mystery",
        "complete_when": "material:silver_bar:4",
        "objective":     "Зібрати 4 срібних зливки",
        "reward_gold":   90,
        "reward_xp":     70,
        "reward_mats":   {"enchanted_wood": 2, "quartz": 3},
        "unlocks":       "q_tower_siege",
    },

    # ──────────────── АКТ 3: Вежа та дракон ─────────────────────

    {
        "id":      "q_tower_siege",
        "title":   "Штурм вежі",
        "icon":    "🏰",
        "story": [
            "Настав час діяти рішуче.",
            "Темна вежа на горизонті — звідти управляють\n"
            "усіма монстрами в нашому краї.",
            "Якщо ти зруйнуєш їхню базу — монстри відступлять.\n"
            "Але будь обережний: там найсильніші стражі.",
        ],
        "unlock_when":   "quest:q_silver_armor",
        "complete_when": "kills:cursed_knight:2",
        "objective":     "Переможи 2 проклятих лицарів у вежі",
        "reward_gold":   150,
        "reward_xp":     120,
        "reward_mats":   {"mithril_ore": 3, "dark_steel": 2},
        "unlocks":       "q_dragon_slayer",
    },

    {
        "id":      "q_dragon_slayer",
        "title":   "Вбивця дракона",
        "icon":    "🐉",
        "story": [
            "Герою... я не хотів тобі це казати.",
            "За вежею спить дракон Морвет.\n"
            "Він — справжнє джерело зла в цих землях.",
            "Якщо ти переможеш його — наш край буде вільний.\n"
            "Але ніхто ще не повертався звідти живим...",
            "Хочу вірити що ти станеш першим.",
        ],
        "unlock_when":   "quest:q_tower_siege",
        "complete_when": "kills:dragon:1",
        "objective":     "Перемогти дракона Морвета",
        "reward_gold":   500,
        "reward_xp":     300,
        "reward_spins":  3,
        "reward_mats":   {"dragon_scale": 2, "ancient_core": 1},
    },

    # ──────────────── ПОВТОРЮВАНІ КВЕСТИ ─────────────────────────

    {
        "id":        "q_daily_hunt",
        "title":     "Полювання",
        "icon":      "🏹",
        "story":     ["Ліс завжди повний небезпек.\nОднак і нагород теж."],
        "unlock_when":   "quest:q_welcome",
        "complete_when": "kills:any:10",
        "objective":     "Вбий 10 будь-яких ворогів",
        "reward_gold":   30,
        "reward_xp":     20,
        "repeatable":    True,
    },

    {
        "id":        "q_material_run",
        "title":     "Для коваля",
        "icon":      "⛏",
        "story":     ["Коваль знову просить матеріали.\nТа ж сама пісня."],
        "unlock_when":   "level:3",
        "complete_when": "material:iron_bar:10",
        "objective":     "Принести 10 залізних зливків",
        "reward_gold":   50,
        "reward_xp":     30,
        "repeatable":    True,
    },
]


# ══════════════════════════════════════════
#  ЩОДЕННІ ЗАВДАННЯ
# ══════════════════════════════════════════
#
# quest_type — що відстежується:
#   "kill_goblin"   "kill_orc"   "kill_knight"  "kill_any"
#   "deal_damage"   "crit_hit"   "use_dodge"    "use_parry"
#   "win_nodamage"  "win_battles" "use_potion"
#   "heavy_kill"    "apply_bleed"

DAILY_QUESTS_POOL = [

    # Бойові вбивства
    {"id": "kill_goblin",  "title": "Мисливець на гоблінів", "icon": "🗡",
     "desc": "Вбий гоблінів",                  "type": "kill_goblin",   "target": 5,  "gold": 80,  "xp": 120},
    {"id": "kill_orc",     "title": "Ворог орків",           "icon": "⚔",
     "desc": "Переможи орків",                 "type": "kill_orc",      "target": 3,  "gold": 120, "xp": 180},
    {"id": "kill_knight",  "title": "Лицарська честь",       "icon": "🛡",
     "desc": "Здолай темних лицарів",          "type": "kill_knight",   "target": 2,  "gold": 200, "xp": 280},
    {"id": "kill_any_15",  "title": "Жнець",                 "icon": "💀",
     "desc": "Вбий 15 ворогів",                "type": "kill_any",      "target": 15, "gold": 100, "xp": 140},

    # Бойова механіка
    {"id": "deal_500",     "title": "Розрив шкоди",          "icon": "💥",
     "desc": "Нанеси 500 урону за один бій",   "type": "deal_damage",   "target": 500,"gold": 100, "xp": 150},
    {"id": "crit_3",       "title": "Снайпер",               "icon": "🎯",
     "desc": "Влучи крит. ударом 3 рази",      "type": "crit_hit",      "target": 3,  "gold": 90,  "xp": 130},
    {"id": "dodge_5",      "title": "Тінь вітру",            "icon": "💨",
     "desc": "Ухились 5 разів",                "type": "use_dodge",     "target": 5,  "gold": 90,  "xp": 120},
    {"id": "parry_2",      "title": "Майстер блоку",         "icon": "🛡",
     "desc": "Виконай 2 парирування",          "type": "use_parry",     "target": 2,  "gold": 150, "xp": 200},
    {"id": "win_nodmg",    "title": "Бездоганний",           "icon": "✨",
     "desc": "Виграй бій без отримання шкоди", "type": "win_nodamage",  "target": 1,  "gold": 250, "xp": 350},
    {"id": "win_3",        "title": "Переможець",            "icon": "🏆",
     "desc": "Виграй 3 бої підряд",            "type": "win_battles",   "target": 3,  "gold": 130, "xp": 180},
    {"id": "potion_use",   "title": "Алхімік",               "icon": "🧪",
     "desc": "Використай 2 зілля в бою",       "type": "use_potion",    "target": 2,  "gold": 70,  "xp": 100},
    {"id": "heavy_kill",   "title": "Нищівний удар",         "icon": "💪",
     "desc": "Вбий ворога зарядженим ударом",  "type": "heavy_kill",    "target": 1,  "gold": 180, "xp": 240},
    {"id": "bleed_3",      "title": "Кривавий шлях",         "icon": "🩸",
     "desc": "Накладіть кровотечу 3 рази",     "type": "apply_bleed",   "target": 3,  "gold": 110, "xp": 160},
]
