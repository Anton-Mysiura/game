"""
HeroRoster — система героїв гравця.

Зберігає:
  - відкриту колекцію героїв (list[OwnedHero])
  - слоти (1–4), активний слот
  - запас спінів рулетки
  - прапорець "перший спін зроблено"
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .heroes import Hero, HEROES


# Рівні для розблокування слотів
SLOT_UNLOCK_LEVELS = {2: 15, 3: 30}   # slot_index → min_level
SLOT_UNLOCK_GOLD   = {4: 500}          # slot_index → gold cost


@dataclass
class OwnedHero:
    """Герой у колекції гравця."""
    hero_id:   str
    obtained_at: int = 0   # timestamp

    @property
    def hero(self) -> Hero:
        return HEROES[self.hero_id]


@dataclass
class HeroRoster:
    """
    Управляє героями гравця:
      collection    — всі відкриті герої
      slots         — до 4 слотів, кожен = hero_id або None
      active_slot   — індекс активного слоту (0-based)
      spins_left    — залишок спінів рулетки
      first_spin_done — чи зроблений перший обов'язковий спін
    """
    collection:      list[OwnedHero] = field(default_factory=list)
    slots:           list[Optional[str]] = field(default_factory=lambda: [None, None, None, None])
    active_slot:     int = 0
    spins_left:      int = 3       # початковий запас
    first_spin_done: bool = False

    # Кількість доступних слотів (1-4, розблоковуються за рівнем і золотом)
    slots_unlocked:  int = 1

    # ── Поточний активний герой ──────────────────────────────────
    @property
    def active_hero_id(self) -> Optional[str]:
        if self.active_slot < len(self.slots):
            return self.slots[self.active_slot]
        return None

    @property
    def active_hero(self) -> Optional[Hero]:
        hid = self.active_hero_id
        return HEROES.get(hid) if hid else None

    # ── Перемикання між слотами ──────────────────────────────────
    def switch_slot(self, slot_index: int) -> bool:
        """Перемикає активний слот. Повертає True якщо успішно."""
        if 0 <= slot_index < self.slots_unlocked and self.slots[slot_index] is not None:
            self.active_slot = slot_index
            return True
        return False

    def set_hero_in_slot(self, hero_id: str, slot_index: int) -> bool:
        """Призначає героя в слот. Герой має бути в колекції."""
        if not self.has_hero(hero_id):
            return False
        if slot_index < 0 or slot_index >= self.slots_unlocked:
            return False
        self.slots[slot_index] = hero_id
        return True

    # ── Колекція ─────────────────────────────────────────────────
    def has_hero(self, hero_id: str) -> bool:
        return any(oh.hero_id == hero_id for oh in self.collection)

    def add_hero(self, hero_id: str) -> OwnedHero:
        """Додає героя в колекцію (дублікати дозволені — можна мати 2 копії)."""
        import time as _t
        oh = OwnedHero(hero_id=hero_id, obtained_at=int(_t.time()))
        self.collection.append(oh)
        # Якщо перший слот порожній — автоматично ставимо
        if self.slots[0] is None:
            self.slots[0] = hero_id
        return oh

    # ── Спіни ────────────────────────────────────────────────────
    def can_spin(self) -> bool:
        return self.spins_left > 0

    def spin(self) -> Optional[Hero]:
        """
        Крутить рулетку. Повертає Hero або None якщо немає спінів.
        НЕ додає автоматично в колекцію — це робить сцена після підтвердження.
        """
        if not self.can_spin():
            return None
        from .heroes import roll_hero
        self.spins_left -= 1
        self.first_spin_done = True
        return roll_hero()

    def add_spins(self, count: int) -> None:
        self.spins_left += count

    # ── Слоти ────────────────────────────────────────────────────
    def unlock_slot_by_level(self, player_level: int) -> bool:
        """Перевіряє і розблоковує слоти за рівнем. Повертає True якщо щось відкрилось."""
        unlocked = False
        for slot_idx, req_level in SLOT_UNLOCK_LEVELS.items():
            if self.slots_unlocked < slot_idx and player_level >= req_level:
                self.slots_unlocked = slot_idx
                unlocked = True
        return unlocked

    def can_unlock_gold_slot(self, player_gold: int) -> bool:
        cost = SLOT_UNLOCK_GOLD.get(4, 9999)
        return self.slots_unlocked < 4 and player_gold >= cost

    def unlock_gold_slot(self) -> int:
        """Розблоковує 4-й слот. Повертає вартість (0 якщо вже відкрито/немає)."""
        cost = SLOT_UNLOCK_GOLD.get(4, 500)
        if self.slots_unlocked < 4:
            self.slots_unlocked = 4
            return cost
        return 0

    # ── Серіалізація ─────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "collection": [{"id": oh.hero_id, "at": oh.obtained_at} for oh in self.collection],
            "slots": self.slots,
            "active_slot": self.active_slot,
            "spins_left": self.spins_left,
            "first_spin_done": self.first_spin_done,
            "slots_unlocked": self.slots_unlocked,
        }

    @staticmethod
    def from_dict(data: dict) -> "HeroRoster":
        r = HeroRoster()
        for entry in data.get("collection", []):
            hid = entry.get("id", "")
            if hid in HEROES:
                r.collection.append(OwnedHero(hero_id=hid, obtained_at=entry.get("at", 0)))
        slots_raw = data.get("slots", [None, None, None, None])
        r.slots = [s if s in HEROES else None for s in slots_raw]
        while len(r.slots) < 4:
            r.slots.append(None)
        r.active_slot = data.get("active_slot", 0)
        r.spins_left = data.get("spins_left", 3)
        r.first_spin_done = data.get("first_spin_done", False)
        r.slots_unlocked = data.get("slots_unlocked", 1)
        return r

    @staticmethod
    def new_game() -> "HeroRoster":
        """Початковий стан для нової гри."""
        return HeroRoster(spins_left=3, first_spin_done=False, slots_unlocked=1)