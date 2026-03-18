"""
Система вільного крафту.

Гравець сам обирає матеріали для двох слотів:
  • Лезо / Основа  — тільки металеві матеріали (is_metal=True)
  • Рукоятка / Підкладка — будь-які матеріали

Фінальний множник = зважене середнє множників усіх використаних матеріалів.
Бафи матеріалів застосовуються 1 раз на тип, незалежно від кількості.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple
import math


# ── Базові характеристики по типу зброї ───────────────────────────────
BASE_WEAPON_ATK  = 20   # base before multiplier
BASE_ARMOR_DEF   = 15
BASE_ARMOR_HP    = 30

# Мінімальна кількість матеріалів для крафту
MIN_TOTAL_MATS   = 3


@dataclass
class SlotIngredients:
    """Вміст одного слоту крафту: {material_id: quantity}."""
    mats: Dict[str, int] = field(default_factory=dict)

    def total_qty(self) -> int:
        return sum(self.mats.values())

    def is_empty(self) -> bool:
        return self.total_qty() == 0

    def add(self, mat_id: str, qty: int = 1):
        self.mats[mat_id] = self.mats.get(mat_id, 0) + qty

    def remove(self, mat_id: str, qty: int = 1):
        cur = self.mats.get(mat_id, 0)
        new = max(0, cur - qty)
        if new == 0:
            self.mats.pop(mat_id, None)
        else:
            self.mats[mat_id] = new

    def clear(self):
        self.mats.clear()


@dataclass
class FreeCraftRecipe:
    """Повний рецепт вільного крафту."""
    result_type: str                    # "weapon" | "armor"
    blade:   SlotIngredients = field(default_factory=SlotIngredients)   # тільки метали
    handle:  SlotIngredients = field(default_factory=SlotIngredients)   # будь-які

    def all_mats(self) -> Dict[str, int]:
        """Об'єднує обидва слоти."""
        combined: Dict[str, int] = {}
        for mid, qty in self.blade.mats.items():
            combined[mid] = combined.get(mid, 0) + qty
        for mid, qty in self.handle.mats.items():
            combined[mid] = combined.get(mid, 0) + qty
        return combined

    def total_qty(self) -> int:
        return self.blade.total_qty() + self.handle.total_qty()

    def is_valid(self) -> bool:
        return self.total_qty() >= MIN_TOTAL_MATS

    def can_afford(self, player_mats: Dict[str, int]) -> Tuple[bool, str]:
        """Перевіряє чи вистачає матеріалів у гравця."""
        for mid, need in self.all_mats().items():
            have = player_mats.get(mid, 0)
            if have < need:
                from .data import MATERIALS
                mat = MATERIALS.get(mid)
                name = mat.name if mat else mid
                return False, f"Не вистачає: {name} ({have}/{need})"
        return True, ""


def calc_multiplier(recipe: FreeCraftRecipe) -> float:
    """
    Зважене середнє множників усіх матеріалів.
    Multiplier = Σ(mult_i × qty_i) / Σ(qty_i)
    """
    from .data import MATERIALS
    total_weighted = 0.0
    total_qty      = 0
    for mid, qty in recipe.all_mats().items():
        mat = MATERIALS.get(mid)
        if mat:
            total_weighted += mat.multiplier * qty
            total_qty      += qty
    if total_qty == 0:
        return 1.0
    return round(total_weighted / total_qty, 3)


def calc_bonuses(recipe: FreeCraftRecipe) -> dict:
    """
    Бафи від унікальних типів матеріалів (1 раз на тип).
    Повертає {attack, defense, hp, crit}.
    """
    from .data import MATERIALS
    atk  = 0
    defs = 0
    hp   = 0
    crit = 0.0
    seen: set = set()
    for mid in recipe.all_mats():
        if mid in seen:
            continue
        seen.add(mid)
        mat = MATERIALS.get(mid)
        if mat:
            atk  += mat.bonus_attack
            defs += mat.bonus_defense
            hp   += mat.bonus_hp
            crit += mat.bonus_crit
    return {"attack": atk, "defense": defs, "hp": hp, "crit": round(crit, 4)}


def calc_item_stats(recipe: FreeCraftRecipe) -> dict:
    """
    Фінальні характеристики предмета:
      base × multiplier + бафи від матеріалів
    """
    mult    = calc_multiplier(recipe)
    bonuses = calc_bonuses(recipe)

    if recipe.result_type == "weapon":
        raw_atk = BASE_WEAPON_ATK * mult
        atk     = math.ceil(raw_atk) + bonuses["attack"]
        return {"attack": atk, "defense": 0, "hp": 0,
                "crit": bonuses["crit"], "multiplier": mult}
    else:
        raw_def = BASE_ARMOR_DEF * mult
        raw_hp  = BASE_ARMOR_HP  * mult
        defs    = math.ceil(raw_def) + bonuses["defense"]
        hp      = math.ceil(raw_hp)  + bonuses["hp"]
        return {"attack": 0, "defense": defs, "hp": hp,
                "crit": bonuses["crit"], "multiplier": mult}


def calc_item_value(recipe: FreeCraftRecipe) -> int:
    """Ціна предмета — сума вартості матеріалів × 1.5."""
    from .data import MATERIALS, RARITY_COLOR
    RARITY_PRICE = {"common": 3, "uncommon": 8, "rare": 20, "epic": 50, "legendary": 120}
    total = 0
    for mid, qty in recipe.all_mats().items():
        mat = MATERIALS.get(mid)
        if mat:
            total += RARITY_PRICE.get(mat.rarity, 3) * qty
    return max(5, int(total * 1.5))


def calc_craft_time(recipe: FreeCraftRecipe) -> float:
    """Час крафту в секундах — залежить від кількості і рідкісності матеріалів."""
    from .data import MATERIALS
    RARITY_TIME = {"common": 4, "uncommon": 8, "rare": 18, "epic": 35, "legendary": 70}
    total = 0.0
    for mid, qty in recipe.all_mats().items():
        mat = MATERIALS.get(mid)
        if mat:
            total += RARITY_TIME.get(mat.rarity, 4) * qty
    return max(10.0, total)


def generate_item_name(recipe: FreeCraftRecipe) -> Tuple[str, str]:
    """
    Генерує назву і іконку предмета на основі домінуючого матеріалу.
    Повертає (name, icon).
    """
    from .data import MATERIALS
    RARITY_ORDER = ["legendary", "epic", "rare", "uncommon", "common"]

    # Знаходимо матеріал з найвищою рідкісністю (при рівності — з найбільшою кількістю)
    best_mat_id  = None
    best_rarity  = 6
    best_qty     = 0
    for mid, qty in recipe.all_mats().items():
        mat = MATERIALS.get(mid)
        if not mat:
            continue
        r_idx = RARITY_ORDER.index(mat.rarity) if mat.rarity in RARITY_ORDER else 6
        if r_idx < best_rarity or (r_idx == best_rarity and qty > best_qty):
            best_mat_id = mid
            best_rarity = r_idx
            best_qty    = qty

    mat = MATERIALS.get(best_mat_id) if best_mat_id else None
    prefix = mat.name if mat else "Невідомий"

    if recipe.result_type == "weapon":
        # Тип зброї залежить від кількості матеріалів у лезі
        blade_qty = recipe.blade.total_qty()
        if blade_qty >= 10:
            suffix, icon = "Дворучний меч", "🗡"
        elif blade_qty >= 5:
            suffix, icon = "Меч", "⚔"
        else:
            suffix, icon = "Кинджал", "🗡"
    else:
        # Тип броні
        handle_qty = recipe.handle.total_qty()
        if handle_qty >= 8:
            suffix, icon = "Важкі латні", "🛡"
        elif handle_qty >= 4:
            suffix, icon = "Нагрудник", "🛡"
        else:
            suffix, icon = "Жилет", "🩶"

    return f"{prefix} {suffix}", icon


def build_item(recipe: FreeCraftRecipe, player) -> "Item":
    """Будує Item з вільного рецепту."""
    from .data import Item, MATERIALS
    from .mutations import roll_mutation, apply_mutation

    stats = calc_item_stats(recipe)
    value = calc_item_value(recipe)
    name, icon = generate_item_name(recipe)

    # Унікальний ID
    import time as _t
    item_id = f"free_{recipe.result_type}_{int(_t.time())}"

    if recipe.result_type == "weapon":
        item = Item(item_id, name, "weapon", value, icon,
                    f"Виковано власноруч (×{stats['multiplier']:.2f})",
                    attack_bonus=stats["attack"],
                    crit_bonus=stats["crit"])
    else:
        item = Item(item_id, name, "armor", value, icon,
                    f"Виковано власноруч (×{stats['multiplier']:.2f})",
                    defense_bonus=stats["defense"],
                    hp_bonus=stats["hp"],
                    crit_bonus=stats["crit"])

    # Мутація
    mut_id = roll_mutation(recipe.result_type)
    if mut_id:
        apply_mutation(item, mut_id)

    return item