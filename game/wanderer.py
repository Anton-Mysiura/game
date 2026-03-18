"""
Торговець-мандрівник — з'являється раз на день у селі.
Продає унікальні товари яких немає в крамниці чи на ринку.
Зникає через 10 хвилин після першого відвідування.
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import Optional

# Інтервал появи (секунди) — 1 раз на 24 години реального часу
WANDERER_INTERVAL = 24 * 60 * 60
# Скільки часу стоїть у селі після появи
WANDERER_STAY     = 10 * 60   # 10 хвилин
# Кількість товарів
SLOT_COUNT = 4

RARITY_COLORS = {
    "common":    (180, 180, 180),
    "uncommon":  (100, 210, 100),
    "rare":      ( 80, 150, 255),
    "epic":      (190, 100, 255),
    "legendary": (255, 185,  40),
}


@dataclass
class WandererLot:
    item_id:   str
    name:      str
    icon:      str
    item_type: str        # "material" | "tool" | "potion" | "blueprint"
    rarity:    str
    price:     int
    qty:       int   = 1
    bp_id:     str   = ""
    sold:      bool  = False

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @staticmethod
    def from_dict(d: dict) -> "WandererLot":
        return WandererLot(**{k: d.get(k, v)
                              for k, v in WandererLot.__dataclass_fields__.items()})


# ── Пул унікальних товарів ────────────────────────────────────────
# (item_id, name, icon, item_type, rarity, base_price, qty_range)
WANDERER_POOL = [
    # Рідкісні руди — дорожче ніж у крамниці
    ("astral_ore",    "Астральна руда",    "✨", "material", "epic",      70, (1, 3)),
    ("volcanic_ore",  "Вулканічна руда",   "🌋", "material", "legendary",150, (1, 2)),
    ("dark_crystal_ore","Темний кристал",  "🖤", "material", "rare",      35, (1, 4)),
    ("ruby_ore",      "Рубін",             "❤",  "material", "rare",      38, (1, 4)),
    ("fire_ore",      "Вогняна руда",      "🔥", "material", "epic",      75, (1, 3)),
    ("storm_ore",     "Штормова руда",     "⚡", "material", "epic",      75, (1, 3)),
    # Унікальні матеріали
    ("magic_core",    "Магічне ядро",      "✨", "material", "rare",      65, (1, 3)),
    ("dragon_scale",  "Луска дракона",     "💎", "material", "epic",     140, (1, 2)),
    ("void_essence",  "Есенція пустоти",   "🌀", "material", "epic",     150, (1, 2)),
    ("ancient_core",  "Древнє ядро",       "🌐", "material", "legendary",280, (1, 1)),
    # Інструменти — дешевше ніж скрізь
    ("pickaxe",       "Кайло",             "⛏", "tool",     "common",    14, (1, 2)),
    ("shovel",        "Лопата",            "🪣", "tool",     "common",    10, (1, 2)),
    # Зілля — більші пачки
    ("big_potion",    "Велике зілля",      "🍶", "potion",   "uncommon",  20, (3, 7)),
    ("power_potion",  "Зілля сили",        "💪", "potion",   "uncommon",  24, (2, 5)),
    # Ексклюзивні кресленики (рандомні)
    ("bp_void_blade",   "Кресленик: Клинок пустоти", "🌀", "blueprint", "epic",    60, (1, 1)),
    ("bp_shadow_reaper","Кресленик: Коса тіней",     "🌑", "blueprint", "epic",    68, (1, 1)),
    ("bp_ancient_sword","Кресленик: Клинок Вічності","🌐", "blueprint", "legendary",120,(1, 1)),
    ("bp_phoenix_armor","Кресленик: Броня Фенікса",  "🪶", "blueprint", "epic",    72, (1, 1)),
]


def generate_lots() -> list[WandererLot]:
    """Генерує SLOT_COUNT унікальних товарів."""
    chosen = random.sample(WANDERER_POOL, min(SLOT_COUNT, len(WANDERER_POOL)))
    lots = []
    for item_id, name, icon, itype, rarity, base_price, qty_range in chosen:
        qty   = random.randint(*qty_range)
        price = int(base_price * qty * random.uniform(0.90, 1.20))
        bp_id = item_id if itype == "blueprint" else ""
        lots.append(WandererLot(
            item_id=item_id, name=name, icon=icon,
            item_type=itype, rarity=rarity,
            price=price, qty=qty, bp_id=bp_id,
        ))
    return lots


class WandererState:
    """Стан торговця-мандрівника."""

    def __init__(self):
        self.next_arrival: float      = time.time() + 60   # перша поява через хвилину
        self.departs_at:   Optional[float] = None
        self.lots:         list[WandererLot] = []
        self.visited:      bool        = False   # чи гравець вже заходив

    @property
    def is_present(self) -> bool:
        """Чи торговець зараз у селі."""
        if self.departs_at is None:
            return False
        return time.time() < self.departs_at

    @property
    def time_left(self) -> int:
        if not self.is_present:
            return 0
        return max(0, int(self.departs_at - time.time()))

    @property
    def arrives_in(self) -> int:
        return max(0, int(self.next_arrival - time.time()))

    def check_arrival(self) -> bool:
        """Перевіряє чи прийшов торговець. True = щойно з'явився."""
        if self.is_present:
            return False
        if time.time() >= self.next_arrival:
            self.lots       = generate_lots()
            self.departs_at = time.time() + WANDERER_STAY
            self.visited    = False
            self.next_arrival = self.departs_at + WANDERER_INTERVAL
            return True
        return False

    def buy(self, idx: int, player) -> tuple[bool, str]:
        if idx < 0 or idx >= len(self.lots):
            return False, "Немає такого товару"
        lot = self.lots[idx]
        if lot.sold:
            return False, "Вже продано"
        if player.gold < lot.price:
            return False, "Недостатньо золота"

        player.gold       -= lot.price
        player.gold_spent += lot.price

        if lot.item_type == "material":
            player.materials[lot.item_id] = \
                player.materials.get(lot.item_id, 0) + lot.qty
        elif lot.item_type in ("tool", "potion"):
            from game.data import Item
            import copy
            item = Item(lot.item_id, lot.name, lot.item_type,
                        lot.price // lot.qty, lot.icon, "")
            for _ in range(lot.qty):
                player.inventory.append(copy.copy(item))
        elif lot.item_type == "blueprint":
            from game.data import BLUEPRINTS, OwnedBlueprint
            bp = BLUEPRINTS.get(lot.bp_id)
            if bp:
                player.blueprints.append(OwnedBlueprint.new(bp))

        lot.sold = True
        return True, "✓ Куплено!"

    def to_dict(self) -> dict:
        return {
            "next_arrival": self.next_arrival,
            "departs_at":   self.departs_at,
            "visited":      self.visited,
            "lots":         [l.to_dict() for l in self.lots],
        }

    def from_dict(self, d: dict) -> None:
        self.next_arrival = d.get("next_arrival", time.time() + 60)
        self.departs_at   = d.get("departs_at",   None)
        self.visited      = d.get("visited",       False)
        self.lots         = [WandererLot.from_dict(l) for l in d.get("lots", [])]