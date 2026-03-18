"""
╔══════════════════════════════════════════════════════════════╗
║  КРАМНИЦЯ                                                    ║
║  Що продається, за скільки — змінюй тут                     ║
╚══════════════════════════════════════════════════════════════╝

ЯК ДОДАТИ ТОВАР:
  У SHOP_ITEMS або SHOP_BLUEPRINTS додай рядок:
    ("item_id", ціна),
  де item_id — ключ з config/loot.py → ITEMS_DATA або BLUEPRINTS_DATA

ЯК ПРИБРАТИ ТОВАР:
  Просто видали або закоментуй рядок — # ("iron_sword", 50),

ЯК ЗМІНИТИ ЦІНУ:
  Просто зміни число: ("small_potion", 15),  # було 10
"""

# ══════════════════════════════════════════
#  ПРЕДМЕТИ В КРАМНИЦІ
# ══════════════════════════════════════════
# Формат: ("item_id", ціна_в_золоті)

SHOP_ITEMS = [
    # Зілля
    ("small_potion",  10),
    ("big_potion",    25),
    ("power_potion",  30),
    # Броня
    ("leather_armor", 40),
    ("chainmail",     80),
]


# ══════════════════════════════════════════
#  КРЕСЛЕННИКИ В КРАМНИЦІ
# ══════════════════════════════════════════

SHOP_BLUEPRINTS = [

    # ── Інструменти шахтаря ──────────────────
    ("bp_pickaxe",          15),
    ("bp_shovel",           12),

    # ── Зброя Tier 1 (звичайна) ──────────────
    ("bp_dagger",           12),
    ("bp_iron_sword",       20),
    ("bp_battle_axe",       30),
    ("bp_war_hammer",       32),
    ("bp_bone_club",        18),
    ("bp_bone_spear",       22),

    # ── Зброя Tier 2 (незвичайна) ────────────
    ("bp_silver_dagger",    25),
    ("bp_silver_sword",     35),
    ("bp_quartz_blade",     28),
    ("bp_frost_blade",      38),

    # ── Зброя Tier 3 (рідкісна) ──────────────
    ("bp_dark_blade",       50),
    ("bp_shadow_blade",     60),
    ("bp_fire_sword",       65),
    ("bp_storm_blade",      62),
    ("bp_blood_sword",      70),
    ("bp_runic_sword",      72),

    # ── Зброя Tier 4 (епічна) ────────────────
    ("bp_mithril_sword",    80),
    ("bp_void_blade",       75),
    ("bp_shadow_reaper",    85),
    ("bp_phoenix_sword",    88),

    # ── Зброя Tier 5 (легендарна) ────────────
    ("bp_dragon_sword",     90),
    ("bp_star_blade",      100),
    ("bp_void_dragon",     120),
    ("bp_ancient_sword",   150),

    # ── Броня Tier 1 ─────────────────────────
    ("bp_leather_armor",    15),
    ("bp_bone_armor",       22),
    ("bp_hardwood_shield",  20),

    # ── Броня Tier 2 ─────────────────────────
    ("bp_chainmail_plus",   35),
    ("bp_silver_mail",      50),
    ("bp_frost_armor",      55),

    # ── Броня Tier 3 ─────────────────────────
    ("bp_shadow_vest",      45),
    ("bp_runic_armor",      65),
    ("bp_shadow_armor",     70),

    # ── Броня Tier 4–5 ───────────────────────
    ("bp_mithril_plate",    75),
    ("bp_phoenix_armor",    90),
    ("bp_dragon_armor",    100),
    ("bp_ancient_armor",   140),
]


# ══════════════════════════════════════════
#  НАЛАШТУВАННЯ КРАМНИЦІ
# ══════════════════════════════════════════

SHOP_CONFIG = {
    # Чи показувати кресленники що гравець вже має (сірим)
    "show_owned_blueprints": True,

    # Знижка за репутацію (% за кожен рівень репутації)
    "reputation_discount_per_level": 0.05,   # 5% за рівень

    # Максимальна знижка від репутації
    "max_reputation_discount": 0.30,         # 30%

    # Чи показувати ціну зі знижкою одразу
    "show_discounted_price": True,
}
