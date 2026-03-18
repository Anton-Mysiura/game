"""
Черга крафту з офлайн-прогресом.
Кожне замовлення зберігає unix timestamp коли воно завершиться.
При запуску гри — всі завершені замовлення обробляються автоматично.
"""
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CraftOrder:
    blueprint_id: str
    finish_at:    float   # unix timestamp
    # Серіалізована копія предмета (вже з мутацією, матеріальними бонусами)
    item_data:    dict    = field(default_factory=dict)

    def is_done(self) -> bool:
        return time.time() >= self.finish_at

    def seconds_left(self) -> float:
        return max(0.0, self.finish_at - time.time())

    def to_dict(self) -> dict:
        return {
            "blueprint_id": self.blueprint_id,
            "finish_at":    self.finish_at,
            "item_data":    self.item_data,
        }

    @staticmethod
    def from_dict(d: dict) -> "CraftOrder":
        return CraftOrder(
            blueprint_id = d["blueprint_id"],
            finish_at    = d["finish_at"],
            item_data    = d.get("item_data", {}),
        )


# ── Час крафту для кожного кресленника (секунди) ──────────────────
# Tier 1 — 30–90с,  Tier 2 — 2–5хв,  Tier 3 — 6–12хв,
# Tier 4 — 15–20хв, Tier 5 — 25–30хв (легендарні)

CRAFT_TIMES: dict[str, int] = {
    # ── Зброя: базова залізна лінійка ────
    "bp_dagger":        30,
    "bp_iron_sword":    60,
    "bp_battle_axe":    90,
    "bp_war_hammer":    90,
    "bp_bone_club":     45,
    "bp_bone_spear":    60,

    # ── Зброя: срібна лінійка ────────────
    "bp_silver_dagger": 120,
    "bp_silver_sword":  150,
    "bp_quartz_blade":  180,
    "bp_frost_blade":   200,

    # ── Зброя: темна/магічна лінійка ─────
    "bp_dark_blade":    300,
    "bp_shadow_blade":  360,
    "bp_fire_sword":    420,
    "bp_storm_blade":   420,
    "bp_blood_sword":   480,
    "bp_runic_sword":   540,

    # ── Зброя: рідкісна лінійка ──────────
    "bp_mithril_sword": 600,
    "bp_void_blade":    660,
    "bp_shadow_reaper": 720,
    "bp_phoenix_sword": 780,

    # ── Зброя: легендарна лінійка ────────
    "bp_dragon_sword":  900,
    "bp_star_blade":    1080,
    "bp_void_dragon":   1200,
    "bp_ancient_sword": 1500,

    # ── Броня: легка лінійка ─────────────
    "bp_leather_armor": 45,
    "bp_bone_armor":    60,
    "bp_hardwood_shield":75,
    "bp_shadow_vest":   180,

    # ── Броня: середня лінійка ───────────
    "bp_chainmail_plus":120,
    "bp_silver_mail":   180,
    "bp_frost_armor":   240,
    "bp_runic_armor":   360,
    "bp_shadow_armor":  420,

    # ── Броня: важка лінійка ─────────────
    "bp_mithril_plate": 600,
    "bp_phoenix_armor": 720,
    "bp_dragon_armor":  900,
    "bp_ancient_armor": 1500,
}

DEFAULT_CRAFT_TIME = 120   # якщо кресленника нема в таблиці


def get_craft_time(blueprint_id: str) -> int:
    """Повертає час крафту в секундах."""
    return CRAFT_TIMES.get(blueprint_id, DEFAULT_CRAFT_TIME)


def fmt_time(seconds: float) -> str:
    """Форматує секунди у читабельний рядок."""
    s = int(seconds)
    if s < 60:
        return f"{s}с"
    if s < 3600:
        return f"{s // 60}хв {s % 60:02d}с"
    h = s // 3600
    m = (s % 3600) // 60
    return f"{h}г {m:02d}хв"


class CraftingQueue:
    """Черга крафту — прив'язана до гравця."""

    MAX_SLOTS = 3   # скільки предметів можна крафтити одночасно

    def __init__(self):
        self.orders: List[CraftOrder] = []

    # ── Додавання замовлення ──────────────────────────────────────

    def start(self, blueprint_id: str, item_data: dict) -> bool:
        """Додає нове замовлення. Повертає True якщо успішно."""
        if len(self.orders) >= self.MAX_SLOTS:
            return False
        duration  = get_craft_time(blueprint_id)
        finish_at = time.time() + duration
        self.orders.append(CraftOrder(blueprint_id, finish_at, item_data))
        return True

    # ── Перевірка і збирання готових ──────────────────────────────

    def collect_done(self) -> List[dict]:
        """
        Повертає список item_data завершених замовлень і видаляє їх з черги.
        Викликається при запуску гри і в майстерні.
        """
        done   = [o for o in self.orders if o.is_done()]
        self.orders = [o for o in self.orders if not o.is_done()]
        return [o.item_data for o in done]

    # ── Серіалізація ──────────────────────────────────────────────

    def to_list(self) -> list:
        return [o.to_dict() for o in self.orders]

    def load_list(self, raw: list):
        self.orders = [CraftOrder.from_dict(d) for d in raw]


# ══════════════════════════════════════════════════════════════════
#  ЧЕРГА РОЗБИРАННЯ
# ══════════════════════════════════════════════════════════════════

import random as _random

# Відсоток повернення матеріалів залежно від рідкісності предмета
# (базова ймовірність на КОЖЕН матеріал у рецепті)
DISMANTLE_RETURN: dict[str, float] = {
    "common":    0.55,   # 55% кожного матеріалу
    "uncommon":  0.50,
    "rare":      0.45,
    "epic":      0.40,
    "legendary": 0.35,
}

# Вартість розбирання = value * множник
DISMANTLE_COST_MULT: dict[str, float] = {
    "common":    0.10,
    "uncommon":  0.12,
    "rare":      0.15,
    "epic":      0.20,
    "legendary": 0.25,
}

# Час розбирання (секунди) — швидше ніж крафт
DISMANTLE_TIMES: dict[str, int] = {
    "common":    20,
    "uncommon":  40,
    "rare":      75,
    "epic":      120,
    "legendary": 200,
}

# Рідкісність предмета за attack/defense — для визначення tier
def _item_tier(item) -> str:
    power = getattr(item, "attack_bonus", 0) + getattr(item, "defense_bonus", 0)
    if power >= 38:  return "legendary"
    if power >= 28:  return "epic"
    if power >= 18:  return "rare"
    if power >= 10:  return "uncommon"
    return "common"


def dismantle_cost(item) -> int:
    """Ціна розбирання в золоті."""
    tier = _item_tier(item)
    base = max(5, getattr(item, "value", 10))
    return max(3, int(base * DISMANTLE_COST_MULT[tier]))


def dismantle_time(item) -> int:
    """Час розбирання в секундах."""
    tier = _item_tier(item)
    return DISMANTLE_TIMES[tier]


def dismantle_preview(item) -> dict[str, int]:
    """
    Рахує очікуваний вихід матеріалів (середнє).
    Повертає {mat_id: очікувана_кількість_float}.
    """
    from game.data import BLUEPRINTS
    tier = _item_tier(item)
    rate = DISMANTLE_RETURN[tier]
    recipe = _find_recipe(item)
    if not recipe:
        return {}
    return {mat_id: qty * rate for mat_id, qty in recipe.items()}


def _find_recipe(item) -> dict | None:
    """Шукає рецепт для предмета за result_id."""
    from game.data import BLUEPRINTS
    item_id = getattr(item, "item_id", "")
    for bp in BLUEPRINTS.values():
        if bp.result_id == item_id:
            return bp.recipe
    return None


def roll_dismantle_materials(item) -> dict[str, int]:
    """
    Кидає кубики — повертає реальний вихід матеріалів.
    Кожна одиниця матеріалу повертається окремим кидком.
    """
    recipe = _find_recipe(item)
    if not recipe:
        # Немає рецепту — повертаємо щось базове
        return _fallback_materials(item)

    tier = _item_tier(item)
    rate = DISMANTLE_RETURN[tier]
    result: dict[str, int] = {}
    for mat_id, qty in recipe.items():
        returned = sum(1 for _ in range(qty) if _random.random() < rate)
        if returned > 0:
            result[mat_id] = returned
    return result


def _fallback_materials(item) -> dict[str, int]:
    """Якщо рецепту немає (базовий предмет) — шматочок металу."""
    tier = _item_tier(item)
    mapping = {
        "common":    {"iron_bar": 1},
        "uncommon":  {"iron_bar": 2},
        "rare":      {"dark_steel": 1, "iron_bar": 1},
        "epic":      {"mithril_bar": 1, "dark_steel": 1},
        "legendary": {"mithril_bar": 2, "magic_core": 1},
    }
    base = mapping.get(tier, {"iron_bar": 1})
    rate = DISMANTLE_RETURN[tier]
    return {k: v for k, v in base.items() if _random.random() < rate}


@dataclass
class DismantleOrder:
    item_data:  dict    # серіалізований Item
    finish_at:  float

    def is_done(self) -> bool:
        return time.time() >= self.finish_at

    def seconds_left(self) -> float:
        return max(0.0, self.finish_at - time.time())

    def to_dict(self) -> dict:
        return {"item_data": self.item_data, "finish_at": self.finish_at}

    @staticmethod
    def from_dict(d: dict) -> "DismantleOrder":
        return DismantleOrder(item_data=d["item_data"], finish_at=d["finish_at"])


class DismantleQueue:
    MAX_SLOTS = 2

    def __init__(self):
        self.orders: List[DismantleOrder] = []

    def start(self, item, item_data: dict) -> bool:
        if len(self.orders) >= self.MAX_SLOTS:
            return False
        duration  = dismantle_time(item)
        finish_at = time.time() + duration
        self.orders.append(DismantleOrder(item_data, finish_at))
        return True

    def collect_done(self) -> List[dict]:
        done = [o for o in self.orders if o.is_done()]
        self.orders = [o for o in self.orders if not o.is_done()]
        return [o.item_data for o in done]

    def to_list(self) -> list:
        return [o.to_dict() for o in self.orders]

    def load_list(self, raw: list):
        self.orders = [DismantleOrder.from_dict(d) for d in raw]

# ══════════════════════════════════════════════════════════════════
#  ЧЕРГА ПЕРЕПЛАВКИ
# ══════════════════════════════════════════════════════════════════

# Час переплавки (секунди) за 1 партію
SMELT_TIME: dict[str, int] = {
    "iron_ore":    30,
    "silver_ore":  60,
    "mithril_ore": 120,
}
SMELT_DEFAULT_TIME = 45


def get_smelt_time(from_mat: str) -> int:
    return SMELT_TIME.get(from_mat, SMELT_DEFAULT_TIME)


@dataclass
class SmeltOrder:
    from_mat:   str
    from_qty:   int
    to_mat:     str
    to_qty:     int
    batches:    int
    finish_at:  float

    def is_done(self) -> bool:
        return time.time() >= self.finish_at

    def seconds_left(self) -> float:
        return max(0.0, self.finish_at - time.time())

    def to_dict(self) -> dict:
        return {
            "from_mat":  self.from_mat,
            "from_qty":  self.from_qty,
            "to_mat":    self.to_mat,
            "to_qty":    self.to_qty,
            "batches":   self.batches,
            "finish_at": self.finish_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "SmeltOrder":
        return SmeltOrder(
            from_mat  = d["from_mat"],
            from_qty  = d["from_qty"],
            to_mat    = d["to_mat"],
            to_qty    = d["to_qty"],
            batches   = d.get("batches", 1),
            finish_at = d["finish_at"],
        )


class SmeltQueue:
    """Черга переплавки — 2 слоти одночасно, офлайн-прогрес."""

    MAX_SLOTS = 2

    def __init__(self):
        self.orders: List[SmeltOrder] = []

    def start(self, from_mat: str, from_qty: int,
              to_mat: str, to_qty: int, batches: int) -> bool:
        if len(self.orders) >= self.MAX_SLOTS:
            return False
        duration  = get_smelt_time(from_mat) * batches
        finish_at = time.time() + duration
        self.orders.append(SmeltOrder(
            from_mat, from_qty, to_mat, to_qty, batches, finish_at))
        return True

    def collect_done(self) -> list:
        done        = [o for o in self.orders if o.is_done()]
        self.orders = [o for o in self.orders if not o.is_done()]
        return done

    def to_list(self) -> list:
        return [o.to_dict() for o in self.orders]

    def load_list(self, raw: list):
        self.orders = [SmeltOrder.from_dict(d) for d in raw]