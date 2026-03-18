"""
Ігрові дані: матеріали, предмети, кресленники, туторіали.
"""

from dataclasses import dataclass, field


@dataclass
class Material:
    material_id:  str
    name:         str
    icon:         str
    description:  str
    rarity:       str   = "common"   # common | uncommon | rare | epic | legendary
    # Бонус у крафті — застосовується 1 раз незалежно від кількості (унікальний баф)
    bonus_attack:  int   = 0
    bonus_defense: int   = 0
    bonus_hp:      int   = 0
    bonus_crit:    float = 0.0
    # Множник якості — впливає на фінальні характеристики предмета
    multiplier:    float = 1.0
    # Чи є металевим (тільки метали можна в слот "Лезо")
    is_metal:      bool  = False


@dataclass
class Item:
    item_id:      str
    name:         str
    item_type:    str       # weapon | armor | potion
    value:        int
    icon:         str
    description:  str
    attack_bonus:  int   = 0
    defense_bonus: int   = 0
    hp_bonus:      int   = 0
    hp_restore:    int   = 0
    crit_bonus:    float = 0.0
    mutation:      str   = ""   # mutation_id або "" якщо немає


@dataclass
class Blueprint:
    blueprint_id:  str
    name:          str
    result_id:     str
    result_name:   str
    result_value:  int
    result_icon:   str
    result_desc:   str
    recipe:        dict      # {material_id: кількість}
    unlock_cost:   int
    result_type:   str  = "weapon"
    result_attack:  int  = 0
    result_defense: int  = 0
    result_hp:      int  = 0
    # Матеріал що дає бонус (може бути кілька через bonus_materials)
    bonus_material:  str  = ""
    bonus_materials: tuple = ()   # tuple of material_id — всі дають бонус
    # Рідкість креслення — впливає на кількість використань
    rarity: str = "common"    # common | uncommon | rare | epic | legendary

    def can_craft(self, materials: dict) -> bool:
        return all(materials.get(m, 0) >= q for m, q in self.recipe.items())

    def calc_bonuses(self, materials_owned: dict = None) -> dict:
        """
        Рахує фінальні бонуси предмета.
        Кожен матеріал з bonus_materials (або bonus_material) дає бонус × кількість в рецепті.
        """
        atk  = self.result_attack
        defs = self.result_defense
        hp   = self.result_hp
        crit = 0.0

        bonus_ids = set(self.bonus_materials)
        if self.bonus_material:
            bonus_ids.add(self.bonus_material)

        for mat_id in bonus_ids:
            mat = MATERIALS.get(mat_id)
            if mat and mat_id in self.recipe:
                qty  = self.recipe[mat_id]
                atk  += mat.bonus_attack  * qty
                defs += mat.bonus_defense * qty
                hp   += mat.bonus_hp      * qty
                crit += mat.bonus_crit    * qty

        return {"attack": atk, "defense": defs, "hp": hp, "crit": round(crit, 4)}


# ── Кількість використань за рідкістю ────────────────────────────
BP_RARITY_USES: dict[str, int] = {
    "common":    2,
    "uncommon":  4,
    "rare":      7,
    "epic":      12,
    "legendary": 20,
}

# ── Назви рідкостей ───────────────────────────────────────────────
BP_RARITY_NAMES_UA: dict[str, str] = {
    "common":    "Звичайне",
    "uncommon":  "Незвичайне",
    "rare":      "Рідкісне",
    "epic":      "Епічне",
    "legendary": "Легендарне",
}

BP_RARITY_COLORS: dict[str, tuple] = {
    "common":    (180, 180, 180),
    "uncommon":  (100, 200, 100),
    "rare":      ( 80, 140, 220),
    "epic":      (180,  80, 220),
    "legendary": (255, 180,  40),
}


@dataclass
class OwnedBlueprint:
    """
    Кресленик у гравця — обгортка над Blueprint з лічильником використань.
    Коли uses_left досягає 0 — кресленик зламаний і видаляється.
    """
    blueprint: Blueprint
    uses_left: int

    # ── зручні проксі ────────────────────────────────────────────
    @property
    def blueprint_id(self) -> str:   return self.blueprint.blueprint_id
    @property
    def name(self)         -> str:   return self.blueprint.name
    @property
    def rarity(self)       -> str:   return self.blueprint.rarity
    @property
    def uses_max(self)     -> int:   return BP_RARITY_USES.get(self.blueprint.rarity, 2)
    @property
    def is_broken(self)    -> bool:  return self.uses_left <= 0

    def can_craft(self, materials: dict) -> bool:
        return not self.is_broken and self.blueprint.can_craft(materials)

    def use_one(self) -> None:
        """Зменшує лічильник на 1."""
        if self.uses_left > 0:
            self.uses_left -= 1

    # ── фабрика ──────────────────────────────────────────────────
    @staticmethod
    def new(blueprint: Blueprint) -> "OwnedBlueprint":
        """Створює новий OwnedBlueprint з повним запасом використань."""
        uses = BP_RARITY_USES.get(blueprint.rarity, 2)
        return OwnedBlueprint(blueprint=blueprint, uses_left=uses)


# ══════════════════════════════════════════
#  МАТЕРІАЛИ
# ══════════════════════════════════════════

MATERIALS = {
    # ── Common: базові ────────────────────────────────────────────
    "wood":           Material("wood",           "Дерево",            "🪵", "Звичайне дерево з лісу",
                               multiplier=1.0),
    "iron_ore":       Material("iron_ore",       "Залізна руда",      "🪨", "Сирий метал",
                               "common", multiplier=1.1, is_metal=True),
    "iron_bar":       Material("iron_bar",       "Залізний зливок",   "⬛", "Очищене залізо",
                               "common", multiplier=1.3, is_metal=True),
    "leather":        Material("leather",        "Шкіра",             "🟫", "Знята зі звірів",
                               multiplier=1.0),
    "bone":           Material("bone",           "Кістка",            "🦴", "Залишок після бою",
                               multiplier=0.9),
    "bone_dust":      Material("bone_dust",      "Кісткова пудра",    "⬜", "Подрібнені кістки",
                               "common", bonus_attack=1, multiplier=1.0),

    # ── Uncommon: середній рівень ──────────────────────────────────
    "silver_ore":     Material("silver_ore",     "Срібна руда",       "🥈", "Блискуча руда з руїн",
                               "uncommon", multiplier=1.6, is_metal=True),
    "silver_bar":     Material("silver_bar",     "Срібний зливок",    "⚪", "Очищене срібло",
                               "uncommon", bonus_attack=1, bonus_crit=0.02, multiplier=2.0, is_metal=True),
    "enchanted_wood": Material("enchanted_wood", "Зачароване дерево", "🌿", "Деревина просочена магією",
                               "uncommon", bonus_hp=8, multiplier=1.5),
    "shadow_cloth":   Material("shadow_cloth",   "Тіньова тканина",   "🩶", "Тканина з пітьми",
                               "uncommon", bonus_defense=2, multiplier=1.4),
    "quartz":         Material("quartz",         "Кварц",             "🔷", "Прозорий камінь",
                               "uncommon", bonus_crit=0.01, multiplier=1.5),
    "hardwood":       Material("hardwood",       "Тверде дерево",     "🌳", "Міцніше за залізо",
                               "uncommon", bonus_defense=1, bonus_hp=5, multiplier=1.4),
    "iron_chain":     Material("iron_chain",     "Залізний ланцюг",   "⛓", "Плетіння ланцюгів",
                               "uncommon", bonus_defense=2, multiplier=1.3, is_metal=True),

    # ── Rare: рідкісні ────────────────────────────────────────────
    "dark_steel":     Material("dark_steel",     "Темна сталь",       "🖤", "Рідкісний метал з тіней",
                               "rare", bonus_attack=2, multiplier=2.8, is_metal=True),
    "magic_core":     Material("magic_core",     "Магічне ядро",      "✨", "Згусток чистої магії",
                               "rare", bonus_crit=0.03, multiplier=2.5),
    "fire_gem":       Material("fire_gem",       "Вогняний камінь",   "🔥", "Горить вічним вогнем",
                               "rare", bonus_attack=2, bonus_crit=0.02, multiplier=2.6),
    "frost_crystal":  Material("frost_crystal",  "Кристал льоду",     "❄", "Вічна крига зі скель",
                               "rare", bonus_defense=3, bonus_hp=12, multiplier=2.4),
    "storm_shard":    Material("storm_shard",    "Уламок бурі",       "⚡", "Тріщить від статики",
                               "rare", bonus_attack=2, bonus_crit=0.03, multiplier=2.7),
    "blood_crystal":  Material("blood_crystal",  "Кривавий кристал",  "🔴", "Кристал що пульсує",
                               "rare", bonus_attack=3, bonus_crit=0.04, multiplier=2.9),
    "mithril_ore":    Material("mithril_ore",    "Мітрилова руда",    "🩵", "Легкий але міцний метал",
                               "rare", multiplier=3.0, is_metal=True),
    "mithril_bar":    Material("mithril_bar",    "Мітриловий зливок", "💙", "Найміцніший відомий метал",
                               "rare", bonus_defense=4, bonus_hp=15, multiplier=3.8, is_metal=True),

    # ── Epic: епічні ──────────────────────────────────────────────
    "dragon_scale":   Material("dragon_scale",   "Луска дракона",     "💎", "Непробивна луска",
                               "epic", bonus_defense=3, bonus_hp=10, multiplier=4.5),
    "void_essence":   Material("void_essence",   "Есенція пустоти",   "🌀", "Матерія між світами",
                               "epic", bonus_attack=4, bonus_crit=0.05, multiplier=5.0),
    "phoenix_feather":Material("phoenix_feather","Перо фенікса",      "🪶", "Горить але не згорає",
                               "epic", bonus_attack=3, bonus_hp=20, bonus_crit=0.03, multiplier=4.8),
    "shadow_essence": Material("shadow_essence", "Есенція тіні",      "🌑", "Згусток темряви",
                               "epic", bonus_attack=2, bonus_defense=2, bonus_crit=0.04, multiplier=4.6),
    "runic_stone":    Material("runic_stone",    "Рунічний камінь",   "🪨", "Вкритий давніми рунами",
                               "epic", bonus_attack=2, bonus_defense=3, bonus_hp=10, multiplier=4.2),

    # ── Legendary ─────────────────────────────────────────────────
    "star_metal":     Material("star_metal",     "Зіркова сталь",     "⭐", "Впала зі зірок",
                               "legendary", bonus_attack=5, bonus_defense=2, bonus_crit=0.04,
                               multiplier=6.5, is_metal=True),
    "ancient_core":   Material("ancient_core",   "Древнє ядро",       "🌐", "Серце стародавнього духа",
                               "legendary", bonus_attack=3, bonus_defense=3, bonus_hp=25, bonus_crit=0.05,
                               multiplier=7.0),
    "dragonite":      Material("dragonite",      "Драконіт",          "🐉", "Серце дракона — чистий вогонь",
                               "legendary", bonus_attack=6, bonus_crit=0.06,
                               multiplier=7.3, is_metal=True),
}

RARITY_COLOR = {
    "common":    (160, 160, 160),
    "uncommon":  (100, 200, 100),
    "rare":      (80,  140, 220),
    "epic":      (180,  80, 220),
    "legendary": (220, 180,  40),
}


# ══════════════════════════════════════════
#  ПРЕДМЕТИ
# ══════════════════════════════════════════

ITEMS = {
    # Стартові / магазин
    "rusty_sword":    Item("rusty_sword",   "Іржавий меч",        "weapon", 5,   "⚔",  "Старий меч",                attack_bonus=5),
    "small_potion":   Item("small_potion",  "Мале зілля",         "potion", 10,  "🧪", "Відновлює 20 HP",           hp_restore=20),
    "big_potion":     Item("big_potion",    "Велике зілля",       "potion", 25,  "🍶", "Відновлює 50 HP",           hp_restore=50),
    "power_potion":   Item("power_potion",  "Зілля сили",         "potion", 30,  "💪", "+5 до атаки",               attack_bonus=5),
    "leather_armor":  Item("leather_armor", "Шкіряна броня",      "armor",  40,  "🥋", "+5 до захисту",             defense_bonus=5),
    "chainmail":      Item("chainmail",     "Кольчуга",           "armor",  80,  "🛡", "+10 до захисту",            defense_bonus=10),
    # Броня з магазину/лут
    "shadow_vest":    Item("shadow_vest",   "Тіньовий жилет",     "armor",  120, "🩶", "+14 захист, +20 HP",        defense_bonus=14, hp_bonus=20),
    "dragon_armor":   Item("dragon_armor",  "Броня дракона",      "armor",  300, "💎", "+22 захист, +40 HP",        defense_bonus=22, hp_bonus=40),
    "mithril_plate":  Item("mithril_plate", "Мітрилові латні",    "armor",  220, "💙", "+18 захист, +30 HP",        defense_bonus=18, hp_bonus=30),
    "bone_armor":     Item("bone_armor",    "Кісткова броня",     "armor",  70,  "🦴", "+8 захист",                 defense_bonus=8),
    "silver_mail":    Item("silver_mail",   "Срібна кольчуга",    "armor",  150, "⚪", "+12 захист, +1% крит",      defense_bonus=12, crit_bonus=0.01),
}


# ══════════════════════════════════════════
#  КРЕСЛЕННИКИ
# ══════════════════════════════════════════
# Структура: tier 1 (базові) → tier 2 (середні) → tier 3 (рідкісні) → tier 4 (епічні) → tier 5 (легендарні)

BLUEPRINTS = {

    # ════════════════════════════════
    #  ЗБРОЯ
    # ════════════════════════════════

    # ── Tier 1: Залізна лінійка ──────────────────────────────────
    "bp_dagger": Blueprint(
        "bp_dagger", "Кресленик: Кинджал", "dagger", "Кинджал",
        9, "🗡", "Швидкий клинок з тонким лезом",
        {"wood": 2, "iron_bar": 1}, 12,
        result_attack=9,
        rarity="common"),
    "bp_iron_sword": Blueprint(
        "bp_iron_sword", "Кресленик: Залізний меч", "iron_sword", "Залізний меч",
        13, "⚔", "Збалансована зброя ближнього бою",
        {"iron_bar": 3, "wood": 1}, 20,
        result_attack=13,
        rarity="common"),
    "bp_battle_axe": Blueprint(
        "bp_battle_axe", "Кресленик: Бойова сокира", "battle_axe", "Бойова сокира",
        17, "🪓", "Важка та потужна. Трощить броню",
        {"iron_bar": 4, "wood": 2, "leather": 1}, 30,
        result_attack=17,
        rarity="common"),
    "bp_war_hammer": Blueprint(
        "bp_war_hammer", "Кресленик: Бойовий молот", "war_hammer", "Бойовий молот",
        18, "🔨", "Дробить щити та кістки однаково",
        {"iron_bar": 5, "hardwood": 2}, 32,
        result_attack=18, bonus_material="hardwood",
        rarity="common"),

    # ── Tier 1: Кісткова/шкіряна ─────────────────────────────────
    "bp_bone_club": Blueprint(
        "bp_bone_club", "Кресленик: Кісткова булава", "bone_club", "Кісткова булава",
        12, "🦴", "Груба зброя з кісток ворогів",
        {"bone": 5, "bone_dust": 2, "leather": 1}, 18,
        result_attack=12, bonus_material="bone_dust",
        rarity="common"),
    "bp_bone_spear": Blueprint(
        "bp_bone_spear", "Кресленик: Кістяний спис", "bone_spear", "Кістяний спис",
        15, "🦴", "Довгий спис з загостреної кістки",
        {"bone": 6, "bone_dust": 3, "wood": 2}, 22,
        result_attack=15, bonus_materials=("bone_dust"),
        rarity="common"),

    # ── Tier 2: Срібна лінійка ───────────────────────────────────
    "bp_silver_dagger": Blueprint(
        "bp_silver_dagger", "Кресленик: Срібний кинджал", "silver_dagger", "Срібний кинджал",
        14, "🥈", "Легкий та гострий. Добрий шанс критів",
        {"silver_bar": 2, "leather": 1}, 25,
        result_attack=14, bonus_material="silver_bar",
        rarity="uncommon"),
    "bp_silver_sword": Blueprint(
        "bp_silver_sword", "Кресленик: Срібний меч", "silver_sword", "Срібний меч",
        19, "⚔", "Блискучий клинок з відмінним балансом",
        {"silver_bar": 3, "enchanted_wood": 1}, 35,
        result_attack=19, bonus_materials=("silver_bar", "enchanted_wood"),
        rarity="uncommon"),
    "bp_quartz_blade": Blueprint(
        "bp_quartz_blade", "Кресленик: Кварцовий клинок", "quartz_blade", "Кварцовий клинок",
        16, "🔷", "Прозорий клинок що ловить світло",
        {"silver_bar": 2, "quartz": 3, "leather": 1}, 28,
        result_attack=16, bonus_materials=("silver_bar", "quartz"),
        rarity="uncommon"),
    "bp_frost_blade": Blueprint(
        "bp_frost_blade", "Кресленик: Морозний клинок", "frost_blade", "Морозний клинок",
        20, "❄", "Вкритий вічним льодом. Морозить ворогів",
        {"iron_bar": 3, "frost_crystal": 2}, 38,
        result_attack=20, bonus_material="frost_crystal",
        rarity="uncommon"),

    # ── Tier 3: Темна/магічна лінійка ────────────────────────────
    "bp_dark_blade": Blueprint(
        "bp_dark_blade", "Кресленик: Темний клинок", "dark_blade", "Темний клинок",
        22, "🌑", "Магічний клинок що п'є душі",
        {"dark_steel": 3, "magic_core": 1, "leather": 2}, 50,
        result_attack=22, bonus_materials=("dark_steel", "magic_core"),
        rarity="rare"),
    "bp_shadow_blade": Blueprint(
        "bp_shadow_blade", "Кресленик: Тіньовий клинок", "shadow_blade", "Тіньовий клинок",
        25, "🩶", "Зброя тіней. Часто б'є критично",
        {"dark_steel": 2, "shadow_cloth": 3, "magic_core": 1}, 60,
        result_attack=25, bonus_materials=("magic_core", "shadow_cloth"),
        rarity="rare"),
    "bp_fire_sword": Blueprint(
        "bp_fire_sword", "Кресленик: Вогняний меч", "fire_sword", "Вогняний меч",
        27, "🔥", "Леза горять вічним вогнем",
        {"iron_bar": 3, "fire_gem": 2, "magic_core": 1}, 65,
        result_attack=27, bonus_materials=("fire_gem", "magic_core"),
        rarity="rare"),
    "bp_storm_blade": Blueprint(
        "bp_storm_blade", "Кресленик: Клинок бурі", "storm_blade", "Клинок бурі",
        26, "⚡", "Кожен удар супроводжується тріском",
        {"dark_steel": 2, "storm_shard": 2, "magic_core": 1}, 62,
        result_attack=26, bonus_materials=("storm_shard", "magic_core"),
        rarity="rare"),
    "bp_blood_sword": Blueprint(
        "bp_blood_sword", "Кресленик: Кривавий меч", "blood_sword", "Кривавий меч",
        28, "🔴", "Живиться кров'ю ворогів",
        {"blood_crystal": 2, "iron_bar": 2, "leather": 2}, 70,
        result_attack=28, bonus_material="blood_crystal",
        rarity="rare"),
    "bp_runic_sword": Blueprint(
        "bp_runic_sword", "Кресленик: Рунічний меч", "runic_sword", "Рунічний меч",
        30, "🪨", "Вкритий рунами давніх магів",
        {"runic_stone": 2, "dark_steel": 2, "magic_core": 1}, 72,
        result_attack=30, bonus_materials=("runic_stone", "dark_steel"),
        rarity="rare"),

    # ── Tier 4: Мітрилова/void лінійка ───────────────────────────
    "bp_mithril_sword": Blueprint(
        "bp_mithril_sword", "Кресленик: Мітриловий меч", "mithril_sword", "Мітриловий меч",
        32, "💙", "Надлегкий та надміцний",
        {"mithril_bar": 3, "enchanted_wood": 1, "magic_core": 1}, 80,
        result_attack=32, bonus_materials=("mithril_bar", "magic_core"),
        rarity="epic"),
    "bp_void_blade": Blueprint(
        "bp_void_blade", "Кресленик: Клинок пустоти", "void_blade", "Клинок пустоти",
        30, "🌀", "Розриває простір між ударами",
        {"void_essence": 2, "dark_steel": 2, "magic_core": 2}, 75,
        result_attack=30, bonus_materials=("void_essence", "magic_core"),
        rarity="epic"),
    "bp_shadow_reaper": Blueprint(
        "bp_shadow_reaper", "Кресленик: Коса тіней", "shadow_reaper", "Коса тіней",
        33, "🌑", "Жне душі в темряві",
        {"shadow_essence": 2, "void_essence": 1, "dark_steel": 3}, 85,
        result_attack=33, bonus_materials=("shadow_essence", "void_essence"),
        rarity="epic"),
    "bp_phoenix_sword": Blueprint(
        "bp_phoenix_sword", "Кресленик: Меч Фенікса", "phoenix_sword", "Меч Фенікса",
        34, "🪶", "Відроджується з попелу битв",
        {"phoenix_feather": 2, "fire_gem": 2, "mithril_bar": 2}, 88,
        result_attack=34, bonus_materials=("phoenix_feather", "fire_gem"),
        rarity="epic"),

    # ── Tier 5: Легендарна лінійка ───────────────────────────────
    "bp_dragon_sword": Blueprint(
        "bp_dragon_sword", "Кресленик: Меч дракона", "dragon_sword", "Меч дракона",
        38, "🐉", "Легендарна зброя кована з луски",
        {"dragon_scale": 2, "dark_steel": 2, "magic_core": 2}, 90,
        result_attack=38, bonus_materials=("dragon_scale"),
        rarity="legendary"),
    "bp_star_blade": Blueprint(
        "bp_star_blade", "Кресленик: Зірковий клинок", "star_blade", "Зірковий клинок",
        40, "⭐", "Кований із зіркової сталі",
        {"star_metal": 3, "magic_core": 2, "enchanted_wood": 1}, 100,
        result_attack=40, bonus_materials=("star_metal"),
        rarity="legendary"),
    "bp_void_dragon": Blueprint(
        "bp_void_dragon", "Кресленик: Дракон Пустоти", "void_dragon_sword", "Дракон Пустоти",
        45, "🌌", "Найсильніша зброя відомих земель",
        {"dragon_scale": 3, "void_essence": 3, "magic_core": 3, "dark_steel": 2}, 120,
        result_attack=45, bonus_materials=("dragon_scale", "void_essence", "magic_core"),
        rarity="legendary"),
    "bp_ancient_sword": Blueprint(
        "bp_ancient_sword", "Кресленик: Клинок Вічності", "ancient_sword", "Клинок Вічності",
        50, "🌐", "Зброя до якої доторкнулись боги",
        {"ancient_core": 2, "star_metal": 2, "dragon_scale": 2, "void_essence": 2}, 150,
        result_attack=50, bonus_materials=("ancient_core", "star_metal"),
        rarity="legendary"),

    # ════════════════════════════════
    #  БРОНЯ
    # ════════════════════════════════

    # ── Tier 1: Легка броня ──────────────────────────────────────
    "bp_leather_armor": Blueprint(
        "bp_leather_armor", "Кресленик: Шкіряна броня+", "crafted_leather", "Шкіряна броня+",
        50, "🥋", "Покращена шкіряна броня мисливця",
        {"leather": 4, "bone": 2}, 15,
        result_type="armor", result_defense=7,
        rarity="common"),
    "bp_bone_armor": Blueprint(
        "bp_bone_armor", "Кресленик: Кісткова броня", "crafted_bone_armor", "Кісткова броня",
        65, "🦴", "Броня з кісток. Легка і міцна",
        {"bone": 6, "bone_dust": 3, "leather": 2}, 22,
        result_type="armor", result_defense=8, bonus_material="bone_dust",
        rarity="common"),
    "bp_hardwood_shield": Blueprint(
        "bp_hardwood_shield", "Кресленик: Дерев'яний щит", "hardwood_shield", "Дерев'яний щит",
        55, "🌳", "Щит з твердого дерева",
        {"hardwood": 4, "iron_bar": 1, "leather": 2}, 20,
        result_type="armor", result_defense=9, result_hp=10, bonus_material="hardwood",
        rarity="common"),

    # ── Tier 2: Середня броня ────────────────────────────────────
    "bp_chainmail_plus": Blueprint(
        "bp_chainmail_plus", "Кресленик: Посилена кольчуга", "chainmail_plus", "Посилена кольчуга",
        100, "🛡", "+13 захист, надійна броня",
        {"iron_bar": 5, "iron_chain": 3, "leather": 2}, 35,
        result_type="armor", result_defense=13, bonus_material="iron_chain",
        rarity="uncommon"),
    "bp_silver_mail": Blueprint(
        "bp_silver_mail", "Кресленик: Срібна кольчуга", "crafted_silver_mail", "Срібна кольчуга",
        150, "⚪", "+12 захист, +1% крит. удар",
        {"silver_bar": 4, "leather": 2, "quartz": 1}, 50,
        result_type="armor", result_defense=12, bonus_materials=("silver_bar", "quartz"),
        rarity="uncommon"),
    "bp_frost_armor": Blueprint(
        "bp_frost_armor", "Кресленик: Крижана броня", "frost_armor", "Крижана броня",
        130, "❄", "+15 захист, +20 HP — вкрита льодом",
        {"frost_crystal": 3, "iron_bar": 4, "leather": 2}, 55,
        result_type="armor", result_defense=15, result_hp=20, bonus_material="frost_crystal",
        rarity="uncommon"),

    # ── Tier 3: Важка броня ──────────────────────────────────────
    "bp_shadow_vest": Blueprint(
        "bp_shadow_vest", "Кресленик: Тіньовий жилет", "crafted_shadow_vest", "Тіньовий жилет",
        120, "🩶", "+14 захист, +20 HP — броня тіней",
        {"shadow_cloth": 4, "leather": 2, "dark_steel": 1}, 45,
        result_type="armor", result_defense=14, result_hp=20, bonus_materials=("shadow_cloth", "dark_steel"),
        rarity="rare"),
    "bp_runic_armor": Blueprint(
        "bp_runic_armor", "Кресленик: Рунічна броня", "runic_armor", "Рунічна броня",
        175, "🪨", "+16 захист, +25 HP, руни захисту",
        {"runic_stone": 2, "iron_bar": 4, "enchanted_wood": 2}, 65,
        result_type="armor", result_defense=16, result_hp=25, bonus_materials=("runic_stone", "enchanted_wood"),
        rarity="rare"),
    "bp_shadow_armor": Blueprint(
        "bp_shadow_armor", "Кресленик: Броня тіней", "shadow_armor", "Броня тіней",
        190, "🌑", "+17 захист, +15 HP, +крит тіні",
        {"shadow_essence": 2, "dark_steel": 3, "shadow_cloth": 2}, 70,
        result_type="armor", result_defense=17, result_hp=15, bonus_materials=("shadow_essence", "dark_steel"),
        rarity="rare"),

    # ── Tier 4-5: Легендарна броня ───────────────────────────────
    "bp_mithril_plate": Blueprint(
        "bp_mithril_plate", "Кресленик: Мітрилові латні", "crafted_mithril_plate", "Мітрилові латні",
        220, "💙", "+18 захист, +30 HP — найміцніший метал",
        {"mithril_bar": 4, "enchanted_wood": 2, "iron_chain": 2}, 75,
        result_type="armor", result_defense=18, result_hp=30, bonus_materials=("mithril_bar"),
        rarity="epic"),
    "bp_phoenix_armor": Blueprint(
        "bp_phoenix_armor", "Кресленик: Броня Фенікса", "phoenix_armor", "Броня Фенікса",
        260, "🪶", "+20 захист, +35 HP — відроджує власника",
        {"phoenix_feather": 3, "mithril_bar": 3, "magic_core": 2}, 90,
        result_type="armor", result_defense=20, result_hp=35, bonus_materials=("phoenix_feather", "mithril_bar"),
        rarity="epic"),
    "bp_dragon_armor": Blueprint(
        "bp_dragon_armor", "Кресленик: Броня дракона", "crafted_dragon_armor", "Броня дракона",
        300, "💎", "+22 захист, +40 HP — легендарна луска",
        {"dragon_scale": 3, "mithril_bar": 2, "magic_core": 2}, 100,
        result_type="armor", result_defense=22, result_hp=40, bonus_materials=("dragon_scale", "mithril_bar"),
        rarity="legendary"),
    "bp_ancient_armor": Blueprint(
        "bp_ancient_armor", "Кресленик: Броня Вічності", "ancient_armor", "Броня Вічності",
        380, "🌐", "+28 захист, +50 HP — благословення богів",
        {"ancient_core": 2, "dragon_scale": 2, "star_metal": 2, "magic_core": 2}, 140,
        result_type="armor", result_defense=28, result_hp=50, bonus_materials=("ancient_core", "star_metal", "dragon_scale"),
        rarity="legendary"),

    # ── Інструменти шахтаря ───────────────────────────────────────
    "bp_pickaxe": Blueprint(
        "bp_pickaxe", "Кресленик: Кайло", "pickaxe", "Кайло",
        20, "⛏", "Обов'язковий інструмент шахтаря",
        {"iron_bar": 3, "wood": 2}, 15,
        result_type="tool",
        rarity="common"),

    "bp_shovel": Blueprint(
        "bp_shovel", "Кресленик: Лопата", "shovel", "Лопата",
        15, "🪣", "Прискорює копання на 10%",
        {"iron_bar": 2, "wood": 2, "leather": 1}, 12,
        result_type="tool",
        rarity="common"),
}


def make_weapon_from_blueprint(bp: Blueprint) -> Item:
    """Створює Item зі зброї/броні/інструменту з кресленника."""
    bonuses = bp.calc_bonuses()
    if bp.result_type == "armor":
        return Item(
            bp.result_id, bp.result_name, "armor", bp.result_value,
            bp.result_icon, bp.result_desc,
            defense_bonus=bonuses["defense"],
            hp_bonus=bonuses["hp"],
            crit_bonus=bonuses["crit"],
        )
    elif bp.result_type == "tool":
        return Item(
            bp.result_id, bp.result_name, "tool", bp.result_value,
            bp.result_icon, bp.result_desc,
        )
    else:
        return Item(
            bp.result_id, bp.result_name, "weapon", bp.result_value,
            bp.result_icon, bp.result_desc,
            attack_bonus=bonuses["attack"],
            crit_bonus=bonuses["crit"],
        )


# ══════════════════════════════════════════
#  ТУТОРІАЛИ
# ══════════════════════════════════════════

TUTORIALS = {
    "tut_welcome": {
        "id": "tut_welcome",
        "title": "⚔ Ласкаво просимо!",
        "pages": [
            ["Ти — мандрівний герой у світі, де зброю", "не купують — її кують власноруч."],
            ["🗺 КАРТА СВІТУ", "", "🏘 Село → 🌲 Ліс → 🏰 Вежа/🗿 Руїни → 🐉 Дракон"],
            ["📋 КОМАНДИ", "", "ЛКМ — взаємодія", "ESC — вихід/назад", "F5 — збереження", "F12 — адмін-панель"],
        ],
    },
    "tut_shop": {
        "id": "tut_shop",
        "title": "🏪 Крамниця",
        "pages": [
            ["У крамниці НЕ продають зброю.", "Тут можна купити зілля та броню."],
            ["📜 КРЕСЛЕННИКИ — найважливіше!", "", "Купи кресленик → іди до майстерні → куй!"],
        ],
    },
    "tut_workshop": {
        "id": "tut_workshop",
        "title": "🔨 Майстерня",
        "pages": [
            ["Тут куються всі клинки.", "Потрібно: кресленик + матеріали."],
            ["🪨 ПЕРЕПЛАВКА", "", "2 залізні руди → 1 залізний зливок",
             "2 срібні руди → 1 срібний зливок", "2 мітрилові руди → 1 мітриловий зливок"],
        ],
    },
    "tut_first_battle": {
        "id": "tut_first_battle",
        "title": "⚔ Перший бій",
        "pages": [
            ["Зараз відбудеться твій перший бій.", "", "⚔ Атакувати | 🧪 Зілля | 🏃 Втеча"],
        ],
    },
    "tut_first_craft": {
        "id": "tut_first_craft",
        "title": "🔨 Перший крафт",
        "pages": [
            ["Ти отримав матеріали!", "Йди до майстерні та скуй зброю."],
        ],
    },
    "tut_level2": {
        "id": "tut_level2",
        "title": "⬆ Рівень 2",
        "pages": [
            ["Вітаємо з підвищенням рівня!", "Тепер ти сильніший."],
        ],
    },
    "tut_level3": {
        "id": "tut_level3",
        "title": "⬆ Рівень 3",
        "pages": [
            ["Ти вже досвідчений герой.", "Готуйся до фінальних боїв!"],
        ],
    },
}