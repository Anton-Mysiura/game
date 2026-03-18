"""
Мутації зброї та броні.
Випадають при крафті з певним шансом.
Кожна дає унікальні бонуси до параметрів.
"""
import random
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Mutation:
    mutation_id:   str
    name:          str
    icon:          str
    color:         tuple     # RGB для відображення
    rarity:        str       # common | uncommon | rare | epic | legendary
    drop_weight:   int       # відносна вага (більше = частіше)
    # Бонуси — стосуються предмета на якому мутація
    atk_bonus:     int   = 0
    def_bonus:     int   = 0
    hp_bonus:      int   = 0
    crit_bonus:    float = 0.0
    atk_pct:       float = 0.0   # % від поточного attack_bonus предмета
    def_pct:       float = 0.0
    desc:          str   = ""


MUTATIONS: dict[str, Mutation] = {
    # ── Common ─────────────────────────────────────────────────
    "sharp": Mutation(
        "sharp", "Гострий", "🔪", (180, 200, 220), "common", 30,
        atk_bonus=3,
        desc="+3 до атаки"
    ),
    "sturdy": Mutation(
        "sturdy", "Міцний", "🪨", (160, 140, 110), "common", 30,
        def_bonus=2, hp_bonus=10,
        desc="+2 захист, +10 HP"
    ),
    "balanced": Mutation(
        "balanced", "Збалансований", "⚖", (180, 180, 160), "common", 25,
        atk_bonus=2, def_bonus=1,
        desc="+2 ATK, +1 DEF"
    ),
    "heavy": Mutation(
        "heavy", "Важкий", "⚓", (140, 130, 120), "common", 20,
        atk_bonus=5, atk_pct=-0.05,
        desc="+5 ATK, -5% базової атаки (важко носити)"
    ),
    "light": Mutation(
        "light", "Легкий", "🍃", (160, 210, 160), "common", 20,
        crit_bonus=0.03,
        desc="+3% шанс крит. удару"
    ),

    # ── Uncommon ───────────────────────────────────────────────
    "golden": Mutation(
        "golden", "Золотий", "🌟", (255, 215, 0), "uncommon", 15,
        atk_bonus=4, def_bonus=2, hp_bonus=15,
        desc="+4 ATK, +2 DEF, +15 HP"
    ),
    "icy": Mutation(
        "icy", "Крижаний", "❄", (140, 200, 255), "uncommon", 14,
        atk_bonus=3, crit_bonus=0.05,
        desc="+3 ATK, +5% крит. удар"
    ),
    "venomous": Mutation(
        "venomous", "Отруйний", "🐍", (120, 200, 80), "uncommon", 14,
        atk_pct=0.08, crit_bonus=0.03,
        desc="+8% базової атаки, +3% крит"
    ),
    "reinforced": Mutation(
        "reinforced", "Посилений", "🔩", (160, 160, 180), "uncommon", 12,
        def_bonus=4, hp_bonus=20,
        desc="+4 DEF, +20 HP"
    ),
    "lucky": Mutation(
        "lucky", "Щасливий", "🍀", (100, 220, 100), "uncommon", 12,
        crit_bonus=0.08, atk_bonus=2,
        desc="+8% крит, +2 ATK"
    ),

    # ── Rare ───────────────────────────────────────────────────
    "magma": Mutation(
        "magma", "Магмовий", "🌋", (255, 100, 30), "rare", 8,
        atk_bonus=7, atk_pct=0.10,
        desc="+7 ATK, +10% базової атаки"
    ),
    "shadow": Mutation(
        "shadow", "Тіньовий", "🌑", (100, 80, 160), "rare", 8,
        atk_pct=0.12, crit_bonus=0.08,
        desc="+12% базової атаки, +8% крит"
    ),
    "arcane": Mutation(
        "arcane", "Магічний", "✨", (180, 120, 255), "rare", 7,
        atk_bonus=5, crit_bonus=0.06, hp_bonus=25,
        desc="+5 ATK, +6% крит, +25 HP"
    ),
    "titanium": Mutation(
        "titanium", "Титановий", "🔷", (100, 160, 220), "rare", 6,
        def_bonus=7, hp_bonus=35, atk_bonus=2,
        desc="+7 DEF, +35 HP, +2 ATK"
    ),
    "berserker": Mutation(
        "berserker", "Берсерк", "💢", (220, 60, 60), "rare", 6,
        atk_pct=0.18, def_bonus=-2,
        desc="+18% базової атаки, -2 DEF (нестримна лють)"
    ),

    # ── Epic ───────────────────────────────────────────────────
    "diamond": Mutation(
        "diamond", "Діамантовий", "💎", (160, 240, 255), "epic", 4,
        atk_bonus=8, def_bonus=6, hp_bonus=40,
        desc="+8 ATK, +6 DEF, +40 HP"
    ),
    "soul": Mutation(
        "soul", "Душелов", "👁", (220, 180, 255), "epic", 3,
        atk_pct=0.15, crit_bonus=0.12, hp_bonus=30,
        desc="+15% ATK, +12% крит, +30 HP"
    ),
    "storm": Mutation(
        "storm", "Штормовий", "⚡", (255, 240, 100), "epic", 3,
        atk_bonus=10, crit_bonus=0.10, atk_pct=0.08,
        desc="+10 ATK, +8% ATK, +10% крит"
    ),
    "void": Mutation(
        "void", "Пустотний", "🌀", (80, 60, 120), "epic", 3,
        atk_pct=0.20, crit_bonus=0.10, def_bonus=-3,
        desc="+20% ATK, +10% крит, -3 DEF (сила пустоти)"
    ),

    # ── Legendary ──────────────────────────────────────────────
    "celestial": Mutation(
        "celestial", "Небесний", "🌠", (255, 255, 180), "legendary", 1,
        atk_bonus=12, def_bonus=8, hp_bonus=60, crit_bonus=0.10,
        desc="+12 ATK, +8 DEF, +60 HP, +10% крит"
    ),
    "dragonborn": Mutation(
        "dragonborn", "Дракона кров", "🐉", (220, 80, 40), "legendary", 1,
        atk_pct=0.25, atk_bonus=10, crit_bonus=0.15,
        desc="+25% ATK, +10 ATK, +15% крит"
    ),
    "ancient": Mutation(
        "ancient", "Стародавній", "🏛", (200, 180, 100), "legendary", 1,
        atk_bonus=8, def_bonus=10, hp_bonus=80, crit_bonus=0.08,
        desc="+8 ATK, +10 DEF, +80 HP, +8% крит"
    ),
}

RARITY_COLOR = {
    "common":    (180, 180, 180),
    "uncommon":  (100, 200, 100),
    "rare":      (80,  140, 255),
    "epic":      (180, 100, 255),
    "legendary": (255, 180,  40),
}

RARITY_NAME_UA = {
    "common":    "Звичайна",
    "uncommon":  "Незвичайна",
    "rare":      "Рідкісна",
    "epic":      "Епічна",
    "legendary": "Легендарна",
}

# Базовий шанс отримати хоч якусь мутацію при крафті
BASE_MUTATION_CHANCE = 0.40   # 40%


def roll_mutation(item_rarity: str = "common") -> Optional[str]:
    """
    Кидає кубик на мутацію при крафті.
    Повертає mutation_id або None.
    item_rarity — рідкісність кресленника (впливає на шанс).
    """
    rarity_boost = {"common": 0.0, "uncommon": 0.05, "rare": 0.10,
                    "epic": 0.15, "legendary": 0.20}
    chance = BASE_MUTATION_CHANCE + rarity_boost.get(item_rarity, 0.0)

    if random.random() > chance:
        return None

    # Зважена вибірка
    pool   = list(MUTATIONS.values())
    weights = [m.drop_weight for m in pool]
    chosen  = random.choices(pool, weights=weights, k=1)[0]
    return chosen.mutation_id


def apply_mutation(item, mutation_id: str) -> None:
    """Застосовує мутацію до Item. Змінює item на місці."""
    mut = MUTATIONS.get(mutation_id)
    if not mut:
        return

    item.mutation = mutation_id

    # Абсолютні бонуси
    item.attack_bonus  += mut.atk_bonus
    item.defense_bonus += mut.def_bonus
    item.hp_bonus      += mut.hp_bonus
    item.crit_bonus    = round(item.crit_bonus + mut.crit_bonus, 4)

    # Відсоткові бонуси від базової атаки/захисту предмета
    if mut.atk_pct:
        item.attack_bonus  = int(item.attack_bonus * (1 + mut.atk_pct))
    if mut.def_pct:
        item.defense_bonus = int(item.defense_bonus * (1 + mut.def_pct))

    # Мутована назва
    item.name = f"{mut.name} {item.name}"


def get_mutation(item) -> Optional[Mutation]:
    """Повертає Mutation об'єкт для предмета або None."""
    mid = getattr(item, "mutation", "")
    return MUTATIONS.get(mid) if mid else None