"""
Клас гравця з усією ігровою логікою.
"""

import random
from typing import Optional
from .data import Item, Blueprint, OwnedBlueprint, ITEMS, make_weapon_from_blueprint
from .hero_roster import HeroRoster
from .perk_system import Perk, roll_perks
from .location_bonuses import calc_bonus_total
from .daily_quests import DailyQuestManager


class Player:
    """Гравець з усіма характеристиками та інвентарем."""

    def __init__(self, name: str):
        self.name = name
        self.level = 1
        self.xp = 0
        self.xp_next = 50
        self.hp = 100
        self.max_hp = 100
        self.attack = 8
        self.defense = 3
        self.gold = 15
        self.bonus_attack = 0

        # Інвентар
        self.inventory: list[Item] = [ITEMS["rusty_sword"], ITEMS["small_potion"]]
        self.materials: dict[str, int] = {"wood": 2, "iron_ore": 1}
        self.blueprints: list[OwnedBlueprint] = []

        # Екіпірування
        self.equipped_weapon: Optional[Item] = ITEMS["rusty_sword"]
        self.equipped_armor: Optional[Item] = None

        # Навчання
        self.tutorial_seen: set[str] = set()
        self.tutorial_queue: list[str] = []

        # Збереження
        self.save_name: str = "Default"
        self.hero_roster: HeroRoster = HeroRoster.new_game()

        @property
        def character_id(self) -> str:
            """Зворотна сумісність — повертає hero_id активного героя."""
            h = self.hero_roster.active_hero
            return h.hero_id if h else "player"

        # ── Прогрес локацій ──
        self.locations_visited: set[str] = {"village"}  # село відкрито одразу
        self.perks: list[str] = []              # список отриманих perk_id
        self.pending_perk_choices: list[Perk] = []  # картки що очікують вибору
        self.perk_multipliers = {               # накопичені множники від перків
            "dmg":        1.0,
            "atk_speed":  1.0,
            "crit_chance": 0.0,
            "move_speed": 1.0,
            "range":      1.0,
        }

        # ── Дерево навичок ──
        self.skill_points: int = 0           # очки для розподілу
        self.skill_nodes:  set[str] = set()  # розблоковані вузли

        # ── Квести ──
        self.quests_active: set[str] = set()   # взяті, ще не здані
        self.quests_done:   set[str] = set()   # завершені

        # ── Черга крафту ──
        from .crafting_queue import CraftingQueue, DismantleQueue
        self.crafting_queue  = CraftingQueue()
        self.dismantle_queue = DismantleQueue()

        # ── Ринок ──
        from .market import Market
        self.market = Market()
        self.daily_quests = DailyQuestManager()
        self.daily_quests.refresh_if_needed()

        # ── Досягнення ──
        self.achievements_unlocked: set[str] = set()  # Розблоковані
        self.achievements_new: list[str] = []  # Нові (для показу)

        # ── Статистика для досягнень ──
        self.enemies_killed: int = 0
        self.goblins_killed: int = 0
        self.orcs_killed: int = 0
        self.knights_killed: int = 0
        self.dragons_killed: int = 0
        self.items_crafted: int = 0
        self.total_gold_earned: int = 0
        self.gold_spent: int = 0
        self.deaths: int = 0
        self.survived_at_1hp: bool = False

        # ── Бестіарій ──
        self.enemies_seen: set[str] = set()  # sprite_name ворогів яких зустрічали

        # ── Крамниця перків ──
        self.perk_shop_extra_bought: int = 0   # к-сть куплених бонусних карток
        self.perk_shop_reroll_bought: int = 0  # к-сть зроблених ролів заміни

        # ── Час у грі ──
        self.total_playtime: float = 0.0

        # ── Онбординг ──
        self.onboarding_done:  bool = False
        self._ob_forest_trips: int  = 0

    # ── Властивості ──

    @property
    def total_attack(self) -> int:
        base = self.attack + self.bonus_attack
        weapon = self.equipped_weapon.attack_bonus if self.equipped_weapon else 0
        loc_bonus = int(calc_bonus_total(self.locations_visited, "attack"))
        return base + weapon + loc_bonus

    @property
    def total_defense(self) -> int:
        armor = self.equipped_armor.defense_bonus if self.equipped_armor else 0
        loc_bonus = int(calc_bonus_total(self.locations_visited, "defense"))
        return self.defense + armor + loc_bonus

    @property
    def total_max_hp(self) -> int:
        """Макс. HP з урахуванням бонусів локацій."""
        return self.max_hp + int(calc_bonus_total(self.locations_visited, "max_hp"))

    @property
    def total_crit_chance(self) -> float:
        """Шанс крит. удару: перки + локації + дерево навичок."""
        return round(
            self.perk_multipliers.get("crit_chance", 0.0)
            + calc_bonus_total(self.locations_visited, "crit_chance"),
            4
        )

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    # ── Бойові методи ──

    def deal_damage(self) -> int:
        return self.total_attack + random.randint(-2, 4)

    def take_damage(self, damage: int) -> int:
        actual = max(1, damage - self.total_defense)
        self.hp = max(0, self.hp - actual)
        # Перевірка виживання на 1 HP
        if self.hp == 1:
            self.survived_at_1hp = True
        return actual

    # ── Прогрес ──

    def gain_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.xp_next:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_next
        self.xp_next = int(self.xp_next * 1.5)
        self.max_hp += 15
        self.hp = self.max_hp
        self.attack += 2
        self.defense += 1
        self.skill_points += 1   # +1 очко дерева навичок

        # Перевіряємо чи відкрились нові слоти героїв
        self.hero_roster.unlock_slot_by_level(self.level)

        # Генеруємо 3 картки для вибору
        self.pending_perk_choices = roll_perks(3)

        # Тригери туторіалів
        if self.level == 2 and "tut_level2" not in self.tutorial_seen:
            self.tutorial_queue.append("tut_level2")
        elif self.level == 3 and "tut_level3" not in self.tutorial_seen:
            self.tutorial_queue.append("tut_level3")

    def apply_perk(self, perk: Perk):
        """Застосовує вибраний перк до гравця."""
        self.perks.append(perk.perk_id)
        self.pending_perk_choices = []

        p = perk.perk_id
        m = self.perk_multipliers

        # ── Прості числові бонуси ──
        if p == "dmg_5":
            m["dmg"] += 0.05
        elif p == "dmg_12":
            m["dmg"] += 0.12
        elif p == "atk_speed_5":
            m["atk_speed"] += 0.05
        elif p == "atk_speed_15":
            m["atk_speed"] += 0.15
        elif p == "crit_chance_7":
            m["crit_chance"] += 7.0
        elif p == "crit_chance_12":
            m["crit_chance"] += 12.0
        elif p == "move_speed_5":
            m["move_speed"] += 0.05
        elif p == "range_5":
            m["range"] += 0.05
        elif p == "stamina_up":
            m["max_energy"] = m.get("max_energy", 0) + 30
        elif p == "fast_regen":
            m["energy_regen"] = m.get("energy_regen", 1.0) + 0.50
        # Решта складних перків (dodge_attack, parry_heal, shadow_step тощо)
        # обробляються в battle_fighting.py через has_perk()

    def has_perk(self, perk_id: str) -> bool:
        """Перевіряє чи є перк у гравця."""
        return perk_id in self.perks

    def perk_count(self, perk_id: str) -> int:
        """Повертає скільки разів вибрано даний перк (стекування)."""
        return self.perks.count(perk_id)

    # ── Матеріали ──

    def add_material(self, mat_id: str, qty: int = 1):
        self.materials[mat_id] = self.materials.get(mat_id, 0) + qty

    def has_materials(self, recipe: dict[str, int]) -> bool:
        return all(self.materials.get(m, 0) >= q for m, q in recipe.items())

    def consume_materials(self, recipe: dict[str, int]):
        for m, q in recipe.items():
            self.materials[m] -= q

    # ── Предмети ──

    def equip_item(self, item: Item):
        if item.item_type == "weapon":
            if self.equipped_weapon and self.equipped_weapon not in self.inventory:
                self.inventory.append(self.equipped_weapon)
            self.equipped_weapon = item
            if item in self.inventory:
                self.inventory.remove(item)
        elif item.item_type == "armor":
            if self.equipped_armor:
                self.inventory.append(self.equipped_armor)
            self.equipped_armor = item
            if item in self.inventory:
                self.inventory.remove(item)

    def use_potion(self, potion: Item) -> str:
        """Використовує зілля. Повертає повідомлення."""
        if potion not in self.inventory:
            return "Зілля немає в інвентарі"

        self.inventory.remove(potion)

        messages = []

        if potion.attack_bonus:
            self.bonus_attack += potion.attack_bonus
            messages.append(f"Атака +{potion.attack_bonus}")

        if potion.hp_restore:
            healed = min(potion.hp_restore, self.max_hp - self.hp)
            self.hp += healed
            messages.append(f"Відновлено {healed} HP")

        return ", ".join(messages) if messages else "Зілля використано"

    # ── Крафт ──

    def craft_weapon(self, owned_bp: "OwnedBlueprint") -> Optional["CraftOrder"]:
        """
        Починає крафт — витрачає матеріали, зменшує uses_left кресленика.
        Якщо uses_left досягає 0 — кресленик видаляється з інвентаря.
        Повертає CraftOrder якщо успішно, None якщо щось не так.
        """
        blueprint = owned_bp.blueprint
        if not blueprint.can_craft(self.materials):
            return None
        if len(self.crafting_queue.orders) >= self.crafting_queue.MAX_SLOTS:
            return None
        if owned_bp.is_broken:
            return None

        bonuses = blueprint.calc_bonuses(self.materials)
        self.consume_materials(blueprint.recipe)

        # Зменшуємо uses_left і видаляємо зламаний кресленик
        owned_bp.use_one()
        if owned_bp.is_broken:
            try:
                self.blueprints.remove(owned_bp)
            except ValueError:
                pass

        from .data import Item
        if blueprint.result_type == "armor":
            item = Item(
                blueprint.result_id, blueprint.result_name, "armor", blueprint.result_value,
                blueprint.result_icon, blueprint.result_desc,
                defense_bonus=bonuses["defense"],
                hp_bonus=bonuses["hp"],
                crit_bonus=bonuses["crit"],
            )
        else:
            item = Item(
                blueprint.result_id, blueprint.result_name, "weapon", blueprint.result_value,
                blueprint.result_icon, blueprint.result_desc,
                attack_bonus=bonuses["attack"],
                crit_bonus=bonuses["crit"],
            )

        from .mutations import roll_mutation, apply_mutation
        mut_id = roll_mutation(blueprint.result_type)
        if mut_id:
            apply_mutation(item, mut_id)

        from .save_manager import _serialize_item
        item_data = _serialize_item(item)

        order = self.crafting_queue.start(blueprint.blueprint_id, item_data)
        return order if order else None

    def free_craft_weapon(self, recipe: "FreeCraftRecipe") -> "CraftOrder | None":
        """
        Вільний крафт — гравець сам обирає матеріали.
        Витрачає матеріали, будує предмет і додає в чергу.
        """
        from .free_craft import (
            FreeCraftRecipe, build_item, calc_craft_time, calc_item_stats
        )
        from .save_manager import _serialize_item

        ok, err = recipe.can_afford(self.materials)
        if not ok:
            return None
        if len(self.crafting_queue.orders) >= self.crafting_queue.MAX_SLOTS:
            return None

        # Будуємо предмет і серіалізуємо
        item = build_item(recipe, self)
        item_data = _serialize_item(item)

        # Витрачаємо матеріали
        self.consume_materials(recipe.all_mats())

        # Визначаємо час крафту і стартуємо
        seconds = calc_craft_time(recipe)
        import time as _t
        finish_at = _t.time() + seconds

        from .crafting_queue import CraftOrder
        order = CraftOrder(
            blueprint_id="free_craft",
            finish_at=finish_at,
            item_data=item_data,
        )
        self.crafting_queue.orders.append(order)
        return order

    def collect_crafted(self) -> list:
        """
        Забирає готові предмети з черги → додає в інвентар.
        Повертає список Item що щойно завершились.
        """
        from .save_manager import _deserialize_item
        done_data = self.crafting_queue.collect_done()
        items = []
        for d in done_data:
            item = _deserialize_item(d)
            if item:
                self.inventory.append(item)
                items.append(item)
        return items

    def start_dismantle(self, item) -> tuple[bool, str]:
        """
        Починає розбирання предмета.
        Знімає монети і видаляє предмет з інвентарю.
        Повертає (ok, повідомлення).
        """
        from .crafting_queue import dismantle_cost, dismantle_time, fmt_time
        from .save_manager import _serialize_item

        if item not in self.inventory:
            return False, "Предмет не в інвентарі"
        if item.item_type not in ("weapon", "armor"):
            return False, "Можна розбирати лише зброю та броню"
        if len(self.dismantle_queue.orders) >= self.dismantle_queue.MAX_SLOTS:
            return False, "Черга розбирання повна (макс. 2)"

        cost = dismantle_cost(item)
        if self.gold < cost:
            return False, f"Потрібно {cost} 🪙 для розбирання"

        self.gold -= cost
        self.inventory.remove(item)
        # Якщо екіпірована — знімаємо
        if self.equipped_weapon is item:
            self.equipped_weapon = None
        if self.equipped_armor is item:
            self.equipped_armor = None

        item_data = _serialize_item(item)
        self.dismantle_queue.start(item, item_data)
        t = fmt_time(dismantle_time(item))
        return True, f"🔧 Розбирання почато ({t})"

    def collect_dismantled(self) -> list[tuple]:
        """
        Збирає готові розбирання.
        Повертає список (item_name, {mat_id: qty}) для кожного завершеного.
        """
        from .save_manager import _deserialize_item
        from .crafting_queue import roll_dismantle_materials
        done_data = self.dismantle_queue.collect_done()
        results = []
        for d in done_data:
            item = _deserialize_item(d)
            if not item:
                continue
            mats = roll_dismantle_materials(item)
            for mat_id, qty in mats.items():
                self.add_material(mat_id, qty)
            results.append((item.name, mats))
        return results