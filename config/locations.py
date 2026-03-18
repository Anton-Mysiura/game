"""
╔══════════════════════════════════════════════════════════════╗
║  ЛОКАЦІЇ                                                     ║
║  Всі локації, події, нагороди — тут                         ║
╚══════════════════════════════════════════════════════════════╝

ЯК ДОДАТИ НОВУ ЛОКАЦІЮ:
  1. Додай блок у LOCATIONS нижче
  2. Додай ворогів у config/enemies.py → SPAWN_TABLES з тим самим ключем
  3. Додай сцену в scenes/ (якщо потрібна нова сцена)

Поля:
  id          — унікальний ключ (той самий що в SPAWN_TABLES)
  name        — назва що бачить гравець
  icon        — emoji
  description — короткий опис
  bg_music    — файл музики з assets/music/ (або None)
  bg_scene    — ключ фону з config/ui.py → SCENE_BACKGROUNDS
  bonus_*     — пасивні бонуси гравця коли він у цій локації
  min_level   — мінімальний рівень для входу
  events      — список подій що можуть статися (ключі з EVENTS)
  loot_bonus  — множник дропу (1.0 = звичайний, 1.5 = +50%)
"""

LOCATIONS = {

    # ══════════════════════════════════════════
    #  МИРНІ ЛОКАЦІЇ
    # ══════════════════════════════════════════

    "village": {
        "name":        "Пригорщина",
        "icon":        "🏘",
        "description": "Тихе село де починається пригода.",
        "bg_music":    None,
        "bg_scene":    "village",
        "bonus_hp":    5,
        "bonus_attack":  0,
        "bonus_defense": 0,
        "min_level":   1,
        "events":      [],
        "loot_bonus":  1.0,
    },

    # ══════════════════════════════════════════
    #  БОЙОВІ ЛОКАЦІЇ
    # ══════════════════════════════════════════

    "forest": {
        "name":        "Темний Ліс",
        "icon":        "🌲",
        "description": "Густий ліс повний гоблінів і небезпек.",
        "bg_music":    "battle music loop.flac",
        "bg_scene":    "forest",
        "bonus_hp":    0,
        "bonus_attack":  2,
        "bonus_defense": 0,
        "min_level":   1,
        "events":      ["find_chest", "find_herbs", "ambush", "merchant"],
        "loot_bonus":  1.0,
    },

    "ruins": {
        "name":        "Стародавні Руїни",
        "icon":        "🗿",
        "description": "Залишки стародавньої фортеці. Тут водяться привиди.",
        "bg_music":    "battle music loop.flac",
        "bg_scene":    "ruins",
        "bonus_hp":    0,
        "bonus_attack":  0,
        "bonus_defense": 3,
        "min_level":   3,
        "events":      ["find_chest", "cursed_shrine", "ambush", "ancient_treasure"],
        "loot_bonus":  1.2,
    },

    "tower": {
        "name":        "Вежа Лицаря",
        "icon":        "🏰",
        "description": "Темна вежа де панують прокляті лицарі.",
        "bg_music":    "battle music loop.flac",
        "bg_scene":    "tower",
        "bonus_hp":    10,
        "bonus_attack":  0,
        "bonus_defense": 5,
        "min_level":   4,
        "events":      ["find_chest", "ambush", "elite_guard"],
        "loot_bonus":  1.4,
    },

    "mine": {
        "name":        "Шахта",
        "icon":        "⛏",
        "description": "Глибока шахта повна руди та небезпек.",
        "bg_music":    None,
        "bg_scene":    "mine",
        "bonus_hp":    0,
        "bonus_attack":  0,
        "bonus_defense": 0,
        "min_level":   1,
        "events":      ["find_rare_ore", "cave_in"],
        "loot_bonus":  1.0,
    },

    # ══════════════════════════════════════════
    #  ФІНАЛЬНІ ЛОКАЦІЇ
    # ══════════════════════════════════════════

    "dragon_lair": {
        "name":        "Лігво Дракона",
        "icon":        "🐉",
        "description": "Тут живе дракон Морвет. Нікому не вдавалось вернутись.",
        "bg_music":    "battle music loop.flac",
        "bg_scene":    "battle",
        "bonus_hp":    0,
        "bonus_attack":  5,
        "bonus_defense": 0,
        "min_level":   7,
        "events":      [],
        "loot_bonus":  2.0,
    },
}


# ══════════════════════════════════════════
#  ПОДІЇ У ЛОКАЦІЯХ
# ══════════════════════════════════════════
# Кожна подія — шанс + опис + нагорода

EVENTS = {

    "find_chest": {
        "name":    "Знайдено скриню!",
        "icon":    "📦",
        "chance":  0.15,       # 15% шанс при кожному бої
        "desc":    "Серед дерев ти помітив стару скриню.",
        "reward":  {"gold": (20, 50)},   # (мін, макс)
    },

    "find_herbs": {
        "name":    "Лікувальні трави",
        "icon":    "🌿",
        "chance":  0.10,
        "desc":    "Ти знайшов рідкісні цілющі трави.",
        "reward":  {"items": ["small_potion"]},
    },

    "ambush": {
        "name":    "Засідка!",
        "icon":    "⚠",
        "chance":  0.08,
        "desc":    "З кущів вискочили вороги!",
        "reward":  {"extra_battle": True},
    },

    "merchant": {
        "name":    "Мандрівний торговець",
        "icon":    "🧙",
        "chance":  0.07,
        "desc":    "Старий торговець пропонує свій товар.",
        "reward":  {"shop_discount": 0.3},   # 30% знижка
    },

    "ancient_treasure": {
        "name":    "Давній скарб",
        "icon":    "💎",
        "chance":  0.05,
        "desc":    "За каменем ховається давній скарб.",
        "reward":  {"gold": (50, 120), "materials": {"magic_core": 1}},
    },

    "cursed_shrine": {
        "name":    "Прокляте святилище",
        "icon":    "🌑",
        "chance":  0.06,
        "desc":    "Чорний вівтар. Торкнутись чи ні?",
        "reward":  {"gold": (30, 80), "hp_cost": 10},
    },

    "elite_guard": {
        "name":    "Елітний страж",
        "icon":    "🛡",
        "chance":  0.10,
        "desc":    "На твоєму шляху стоїть елітний страж.",
        "reward":  {"extra_battle": True, "bonus_loot": 2.0},
    },

    "find_rare_ore": {
        "name":    "Рідкісна жила!",
        "icon":    "💎",
        "chance":  0.12,
        "desc":    "Ти знайшов жилу рідкісної руди.",
        "reward":  {"materials": {"mithril_ore": (1, 2)}},
    },

    "cave_in": {
        "name":    "Обвал!",
        "icon":    "💥",
        "chance":  0.05,
        "desc":    "Частина тунелю обвалилась!",
        "reward":  {"hp_cost": 15},
    },
}


# ══════════════════════════════════════════
#  КАРТА СВІТУ — порядок та зв'язки
# ══════════════════════════════════════════
# Визначає що відображається на карті і в якому порядку

WORLD_MAP = [
    # (location_id, позиція_x%, позиція_y%, unlocked_after_location)
    ("village",     20, 50, None),
    ("forest",      38, 35, "village"),
    ("mine",        30, 65, "village"),
    ("ruins",       57, 55, "forest"),
    ("tower",       72, 30, "ruins"),
    ("dragon_lair", 88, 50, "tower"),
]
