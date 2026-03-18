"""
Чорний ринок — випадкові пропозиції що оновлюються кожні N секунд.
Може продавати: зілля, матеріали, кресленники, готову зброю/броню (з мутаціями).
Зберігається у save-файлі разом з timestamp наступного оновлення.
"""
import random
import time
from dataclasses import dataclass, field
from typing import Optional

# ── Типи лотів ────────────────────────────────────────────────────

SLOT_COUNT   = 6     # лотів на ринку одночасно
REFRESH_SEC  = 300   # 5 хвилин між оновленнями (реальний час)

# ── Рідкісність лота і її вага появи ─────────────────────────────
RARITY_WEIGHTS = {
    "common":    50,
    "uncommon":  28,
    "rare":      14,
    "epic":       6,
    "legendary":  2,
}

RARITY_COLOR = {
    "common":    (180, 180, 180),
    "uncommon":  (100, 210, 100),
    "rare":      (80,  150, 255),
    "epic":      (190, 100, 255),
    "legendary": (255, 185,  40),
}

RARITY_UA = {
    "common":    "Звичайне",
    "uncommon":  "Незвичайне",
    "rare":      "Рідкісне",
    "epic":      "Епічне",
    "legendary": "Легендарне",
}


@dataclass
class MarketLot:
    lot_type:  str    # "potion" | "material" | "blueprint" | "weapon" | "armor"
    rarity:    str
    price:     int
    sold:      bool = False
    # Для зілля/матеріалів
    item_id:   str  = ""
    qty:       int  = 1
    # Для кресленників
    bp_id:     str  = ""
    # Для зброї/броні (повна серіалізована копія)
    item_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "lot_type":  self.lot_type,
            "rarity":    self.rarity,
            "price":     self.price,
            "sold":      self.sold,
            "item_id":   self.item_id,
            "qty":       self.qty,
            "bp_id":     self.bp_id,
            "item_data": self.item_data,
        }

    @staticmethod
    def from_dict(d: dict) -> "MarketLot":
        return MarketLot(
            lot_type  = d.get("lot_type",  "potion"),
            rarity    = d.get("rarity",    "common"),
            price     = d.get("price",     10),
            sold      = d.get("sold",      False),
            item_id   = d.get("item_id",   ""),
            qty       = d.get("qty",       1),
            bp_id     = d.get("bp_id",     ""),
            item_data = d.get("item_data", {}),
        )


# ── Пули для генерації ────────────────────────────────────────────

# Зілля: (item_id, рідкісність, ціна_за_1)
POTION_POOL = [
    ("small_potion",  "common",   12),
    ("big_potion",    "uncommon", 30),
    ("power_potion",  "uncommon", 35),
]

# Інструменти шахтаря: (item_id, name, icon, рідкісність, ціна)
TOOL_POOL = [
    ("pickaxe",        "Кайло",   "⛏", "common",   16),
    ("shovel",         "Лопата",  "🪣", "common",   12),
]

# Матеріали: (mat_id, рідкісність, ціна_за_1)
MATERIAL_POOL = [
    ("wood",           "common",    3),
    ("leather",        "common",    5),
    ("bone",           "common",    4),
    ("iron_ore",       "common",    6),
    ("iron_bar",       "common",    10),
    ("bone_dust",      "common",    8),
    ("silver_ore",     "uncommon",  15),
    ("silver_bar",     "uncommon",  25),
    ("enchanted_wood", "uncommon",  20),
    ("shadow_cloth",   "uncommon",  22),
    ("quartz",         "uncommon",  18),
    ("hardwood",       "uncommon",  16),
    ("iron_chain",     "uncommon",  20),
    ("dark_steel",     "rare",      45),
    ("magic_core",     "rare",      50),
    ("fire_gem",       "rare",      55),
    ("frost_crystal",  "rare",      55),
    ("storm_shard",    "rare",      60),
    ("blood_crystal",  "rare",      65),
    ("mithril_ore",    "rare",      40),
    ("mithril_bar",    "rare",      70),
    ("dragon_scale",   "epic",     120),
    ("void_essence",   "epic",     130),
    ("phoenix_feather","epic",     140),
    ("shadow_essence", "epic",     125),
    ("runic_stone",    "epic",     110),
    ("star_metal",     "legendary",250),
    ("ancient_core",   "legendary",300),
]

# Кресленники: (bp_id, рідкісність)  — ціна = unlock_cost * 1.5
BP_POOL = [
    ("bp_dagger",        "common"),
    ("bp_iron_sword",    "common"),
    ("bp_battle_axe",    "common"),
    ("bp_bone_club",     "common"),
    ("bp_bone_spear",    "common"),
    ("bp_leather_armor", "common"),
    ("bp_bone_armor",    "common"),
    ("bp_silver_dagger", "uncommon"),
    ("bp_silver_sword",  "uncommon"),
    ("bp_quartz_blade",  "uncommon"),
    ("bp_frost_blade",   "uncommon"),
    ("bp_war_hammer",    "uncommon"),
    ("bp_hardwood_shield","uncommon"),
    ("bp_chainmail_plus","uncommon"),
    ("bp_silver_mail",   "uncommon"),
    ("bp_shadow_vest",   "uncommon"),
    ("bp_dark_blade",    "rare"),
    ("bp_shadow_blade",  "rare"),
    ("bp_fire_sword",    "rare"),
    ("bp_blood_sword",   "rare"),
    ("bp_storm_blade",   "rare"),
    ("bp_runic_sword",   "rare"),
    ("bp_frost_armor",   "rare"),
    ("bp_runic_armor",   "rare"),
    ("bp_shadow_armor",  "rare"),
    ("bp_mithril_sword", "epic"),
    ("bp_void_blade",    "epic"),
    ("bp_shadow_reaper", "epic"),
    ("bp_phoenix_sword", "epic"),
    ("bp_mithril_plate", "epic"),
    ("bp_phoenix_armor", "epic"),
    ("bp_dragon_sword",  "legendary"),
    ("bp_star_blade",    "legendary"),
    ("bp_void_dragon",   "legendary"),
    ("bp_ancient_sword", "legendary"),
    ("bp_dragon_armor",  "legendary"),
    ("bp_ancient_armor", "legendary"),
]

# Базові предмети зброї/броні для ринку (може мати мутацію)
# (bp_id_щоб_згенерувати, рідкісність_лота, множник_ціни)
GEAR_POOL = [
    ("bp_dagger",        "common",    1.2),
    ("bp_iron_sword",    "common",    1.2),
    ("bp_battle_axe",    "uncommon",  1.4),
    ("bp_bone_club",     "common",    1.1),
    ("bp_silver_dagger", "uncommon",  1.4),
    ("bp_silver_sword",  "uncommon",  1.5),
    ("bp_leather_armor", "common",    1.2),
    ("bp_bone_armor",    "common",    1.2),
    ("bp_dark_blade",    "rare",      1.6),
    ("bp_fire_sword",    "rare",      1.7),
    ("bp_shadow_blade",  "rare",      1.7),
    ("bp_shadow_vest",   "rare",      1.6),
    ("bp_chainmail_plus","uncommon",  1.4),
    ("bp_mithril_sword", "epic",      2.0),
    ("bp_void_blade",    "epic",      2.0),
    ("bp_shadow_reaper", "epic",      2.2),
    ("bp_mithril_plate", "epic",      2.0),
    ("bp_phoenix_sword", "epic",      2.3),
    ("bp_dragon_sword",  "legendary", 3.0),
    ("bp_void_dragon",   "legendary", 3.5),
    ("bp_dragon_armor",  "legendary", 3.0),
    ("bp_ancient_sword", "legendary", 4.0),
]

# Шанс появи мутації на готовій зброї/броні на ринку (вищий ніж при крафті)
MARKET_MUTATION_CHANCE = 0.65


def _pick_rarity(allow: list[str] | None = None) -> str:
    pool = {k: v for k, v in RARITY_WEIGHTS.items()
            if allow is None or k in allow}
    keys   = list(pool.keys())
    weights = list(pool.values())
    return random.choices(keys, weights=weights, k=1)[0]


def generate_lots() -> list[MarketLot]:
    """Генерує SLOT_COUNT випадкових лотів."""
    from game.data import MATERIALS, BLUEPRINTS, Item
    from game.mutations import roll_mutation, apply_mutation, MUTATIONS
    from game.save_manager import _serialize_item

    lots   = []
    # Гарантуємо хоча б 1 зілля, 1 матеріал, 1 кресленник
    # решта — повністю випадково
    type_pool = (
        ["potion", "material", "blueprint"] +
        random.choices(
            ["potion", "material", "blueprint", "weapon", "armor", "tool"],
            weights=[14, 23, 23, 18, 14, 8],
            k=SLOT_COUNT - 3
        )
    )
    random.shuffle(type_pool)

    for lot_type in type_pool:

        # ── Зілля ────────────────────────────────────────────────
        if lot_type == "potion":
            item_id, rar, base_price = random.choice(POTION_POOL)
            qty   = random.randint(1, 5)
            price = int(base_price * qty * random.uniform(0.85, 1.25))
            lots.append(MarketLot("potion", rar, price,
                                  item_id=item_id, qty=qty))

        # ── Матеріали ────────────────────────────────────────────
        elif lot_type == "material":
            rar   = _pick_rarity()
            pool  = [m for m in MATERIAL_POOL if m[1] == rar]
            if not pool:
                pool = MATERIAL_POOL
            mat_id, mat_rar, base_price = random.choice(pool)
            qty   = random.randint(1, max(1, 8 - RARITY_WEIGHTS.get(mat_rar, 1) // 10))
            price = int(base_price * qty * random.uniform(0.80, 1.30))
            lots.append(MarketLot("material", mat_rar, price,
                                  item_id=mat_id, qty=qty))

        # ── Кресленники ──────────────────────────────────────────
        elif lot_type == "blueprint":
            rar  = _pick_rarity()
            pool = [b for b in BP_POOL if b[1] == rar]
            if not pool:
                pool = BP_POOL
            bp_id, bp_rar = random.choice(pool)
            bp    = BLUEPRINTS.get(bp_id)
            if not bp:
                continue
            price = int(bp.unlock_cost * random.uniform(1.3, 2.0))
            lots.append(MarketLot("blueprint", bp_rar, price, bp_id=bp_id))

        # ── Інструменти шахтаря ──────────────────────────────────
        elif lot_type == "tool":
            item_id, name, icon, rar, base_price = random.choice(TOOL_POOL)
            price = int(base_price * random.uniform(0.75, 0.95))  # дешевше ніж в крамниці
            from game.data import Item
            tool_item = Item(item_id, name, "tool", base_price, icon,
                             "Інструмент шахтаря.")
            from game.save_manager import _serialize_item
            lots.append(MarketLot("tool", rar, price,
                                  item_id=item_id, qty=1,
                                  item_data=_serialize_item(tool_item)))

        # ── Зброя / Броня ────────────────────────────────────────
        else:
            need_type = lot_type  # "weapon" або "armor"
            pool = [(b, r, m) for b, r, m in GEAR_POOL]
            # Фільтруємо за типом
            from game.data import BLUEPRINTS as BPS
            typed = [(b, r, m) for b, r, m in pool
                     if BPS.get(b) and BPS[b].result_type == need_type]
            if not typed:
                typed = pool

            rar   = _pick_rarity()
            close = [(b, r, m) for b, r, m in typed if r == rar]
            bp_id, bp_rar, price_mult = random.choice(close if close else typed)

            bp = BLUEPRINTS.get(bp_id)
            if not bp:
                continue

            # Будуємо предмет
            from game.data import Item
            bonuses = bp.calc_bonuses()
            if bp.result_type == "armor":
                item = Item(
                    bp.result_id, bp.result_name, "armor", bp.result_value,
                    bp.result_icon, bp.result_desc,
                    defense_bonus=bonuses["defense"],
                    hp_bonus=bonuses["hp"],
                    crit_bonus=bonuses["crit"],
                )
            else:
                item = Item(
                    bp.result_id, bp.result_name, "weapon", bp.result_value,
                    bp.result_icon, bp.result_desc,
                    attack_bonus=bonuses["attack"],
                    crit_bonus=bonuses["crit"],
                )

            # Мутація з підвищеним шансом
            if random.random() < MARKET_MUTATION_CHANCE:
                mut_id = roll_mutation(bp_rar)
                if mut_id:
                    apply_mutation(item, mut_id)
                    # Підвищуємо рідкісність лота якщо мутація рідша
                    mut = MUTATIONS.get(mut_id)
                    if mut:
                        rar_order = list(RARITY_WEIGHTS.keys())
                        lot_idx = rar_order.index(rar) if rar in rar_order else 0
                        mut_idx = rar_order.index(mut.rarity) if mut.rarity in rar_order else 0
                        rar = rar_order[max(lot_idx, mut_idx)]

            base_price = bp.result_value * 3
            price = int(base_price * price_mult * random.uniform(0.9, 1.3))
            lots.append(MarketLot(
                need_type, rar, price,
                item_data=_serialize_item(item),
            ))

    return lots


def fmt_time_market(seconds: float) -> str:
    """Форматує секунди у рядок для таймера ринку."""
    s = int(seconds)
    if s <= 0:    return "зараз!"
    if s < 60:    return f"{s}с"
    if s < 3600:  return f"{s // 60}хв {s % 60:02d}с"
    return f"{s // 3600}г {(s % 3600) // 60:02d}хв"


class Market:
    """Стан ринку — зберігається у save-файлі."""

    def __init__(self):
        self.lots:        list[MarketLot] = []
        self.next_refresh: float = 0.0   # unix timestamp

    def needs_refresh(self) -> bool:
        return time.time() >= self.next_refresh or not self.lots

    def time_to_refresh(self) -> float:
        return max(0.0, self.next_refresh - time.time())

    def refresh(self):
        self.lots        = generate_lots()
        self.next_refresh = time.time() + REFRESH_SEC

    def ensure_fresh(self):
        """Оновлює якщо час вийшов (офлайн-прогрес)."""
        if self.needs_refresh():
            self.refresh()

    def buy(self, idx: int, player) -> tuple[bool, str]:
        """
        Купує лот. Повертає (ok, повідомлення).
        """
        if idx < 0 or idx >= len(self.lots):
            return False, "Немає такого лота"
        lot = self.lots[idx]
        if lot.sold:
            return False, "Вже продано"
        if player.gold < lot.price:
            return False, "Недостатньо золота"

        player.gold       -= lot.price
        player.gold_spent += lot.price

        from game.data import ITEMS, MATERIALS, BLUEPRINTS
        from game.save_manager import _deserialize_item

        if lot.lot_type == "potion":
            item = ITEMS.get(lot.item_id)
            if item:
                for _ in range(lot.qty):
                    player.inventory.append(item)

        elif lot.lot_type == "material":
            player.add_material(lot.item_id, lot.qty)

        elif lot.lot_type == "blueprint":
            bp = BLUEPRINTS.get(lot.bp_id)
            if bp and bp not in player.blueprints:
                player.blueprints.append(bp)
            elif bp in player.blueprints:
                # Повертаємо золото
                player.gold       += lot.price
                player.gold_spent -= lot.price
                return False, "Цей кресленник вже є у тебе"

        elif lot.lot_type in ("weapon", "armor"):
            item = _deserialize_item(lot.item_data)
            if item:
                player.inventory.append(item)

        elif lot.lot_type == "tool":
            item = _deserialize_item(lot.item_data)
            if item:
                import copy
                player.inventory.append(copy.copy(item))

        lot.sold = True
        return True, "✓ Куплено!"

    # ── Серіалізація ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "lots":         [l.to_dict() for l in self.lots],
            "next_refresh": self.next_refresh,
        }

    def load_dict(self, d: dict):
        self.lots         = [MarketLot.from_dict(l) for l in d.get("lots", [])]
        self.next_refresh = d.get("next_refresh", 0.0)