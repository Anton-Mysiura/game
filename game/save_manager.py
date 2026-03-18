"""
Система збережень гри.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from .player import Player
from .data import ITEMS, BLUEPRINTS, Item, make_weapon_from_blueprint, OwnedBlueprint


def _serialize_item(item: "Item") -> dict:
    """Серіалізує Item у словник (зберігає мутацію і всі стати)."""
    return {
        "item_id":      item.item_id,
        "name":         item.name,
        "item_type":    item.item_type,
        "value":        item.value,
        "icon":         item.icon,
        "description":  item.description,
        "attack_bonus":  item.attack_bonus,
        "defense_bonus": item.defense_bonus,
        "hp_bonus":      item.hp_bonus,
        "hp_restore":    item.hp_restore,
        "crit_bonus":    item.crit_bonus,
        "mutation":      getattr(item, "mutation", ""),
    }


def _deserialize_item(raw) -> Optional["Item"]:
    """Відновлює Item зі словника або старого рядкового формату."""
    if raw is None:
        return None
    # Старий формат — просто рядок з item_id
    if isinstance(raw, str):
        return ITEMS.get(raw)
    # Новий формат — словник
    if isinstance(raw, dict):
        item_id = raw.get("item_id", "")
        # Якщо є в базових ITEMS і без мутації — повертаємо базовий (щоб не дублювати)
        base = ITEMS.get(item_id)
        mutation = raw.get("mutation", "")
        if base and not mutation and raw.get("attack_bonus") == base.attack_bonus:
            return base
        # Інакше — відновлюємо повністю (мутований або крафтований)
        return Item(
            item_id       = item_id,
            name          = raw.get("name", item_id),
            item_type     = raw.get("item_type", "weapon"),
            value         = raw.get("value", 0),
            icon          = raw.get("icon", "⚔"),
            description   = raw.get("description", ""),
            attack_bonus  = raw.get("attack_bonus", 0),
            defense_bonus = raw.get("defense_bonus", 0),
            hp_bonus      = raw.get("hp_bonus", 0),
            hp_restore    = raw.get("hp_restore", 0),
            crit_bonus    = raw.get("crit_bonus", 0.0),
            mutation      = mutation,
        )
    return None

# Шлях до збережень
SAVES_DIR = Path.home() / ".dark_kingdom_saves"
SAVES_DIR.mkdir(exist_ok=True)


class SaveManager:
    """Менеджер збережень гри."""

    @staticmethod
    def get_all_saves() -> list[dict]:
        """Повертає список всіх збережень з метаданими."""
        saves = []
        for fpath in SAVES_DIR.glob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saves.append({
                        "filename": fpath.stem,
                        "filepath": fpath,
                        "player_name": data.get("name", "???"),
                        "level": data.get("level", 1),
                        "gold": data.get("gold", 0),
                        "modified": datetime.fromtimestamp(fpath.stat().st_mtime),
                        "valid": True,
                    })
            except Exception:  # Пошкоджений JSON файл
                saves.append({
                    "filename": fpath.stem,
                    "filepath": fpath,
                    "player_name": "ПОШКОДЖЕНО",
                    "level": 0,
                    "gold": 0,
                    "modified": datetime.fromtimestamp(fpath.stat().st_mtime),
                    "valid": False,
                })
        return sorted(saves, key=lambda s: s["modified"], reverse=True)

    @staticmethod
    def save_exists(save_name: str) -> bool:
        """Перевіряє чи існує збереження."""
        return (SAVES_DIR / f"{save_name}.json").exists()

    @staticmethod
    def get_unique_name(base: str) -> str:
        """Генерує унікальне ім'я якщо base вже зайнято."""
        if not SaveManager.save_exists(base):
            return base
        i = 1
        while SaveManager.save_exists(f"{base}_{i}"):
            i += 1
        return f"{base}_{i}"

    @staticmethod
    def save_game(player: Player, save_name: str):
        """Зберігає стан гравця."""
        data = {
            "name": player.name,
            "level": player.level,
            "xp": player.xp,
            "xp_next": player.xp_next,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.attack,
            "defense": player.defense,
            "gold": player.gold,
            "bonus_attack": player.bonus_attack,
            "hero_roster": player.hero_roster.to_dict(),
            "inventory": [_serialize_item(item) for item in player.inventory],
            "materials": player.materials,
            "blueprints": [{"id": ob.blueprint_id, "uses": ob.uses_left}
                           for ob in player.blueprints],
            "equipped_weapon": _serialize_item(player.equipped_weapon) if player.equipped_weapon else None,
            "equipped_armor":  _serialize_item(player.equipped_armor)  if player.equipped_armor  else None,
            "tutorial_seen": list(player.tutorial_seen),
            "achievements_unlocked": list(player.achievements_unlocked),
            "perks": player.perks,
            "skill_points": player.skill_points,
            "skill_nodes":  list(player.skill_nodes),
            "quests_active": list(player.quests_active),
            "quests_done":   list(player.quests_done),
            "crafting_queue":  player.crafting_queue.to_list(),
            "dismantle_queue": player.dismantle_queue.to_list(),
            "market": player.market.to_dict(),
            "daily_quests": player.daily_quests.to_dict(),
            "locations_visited": list(player.locations_visited),
            "enemies_killed": player.enemies_killed,
            "goblins_killed": player.goblins_killed,
            "orcs_killed": player.orcs_killed,
            "knights_killed": player.knights_killed,
            "dragons_killed": player.dragons_killed,
            "items_crafted": player.items_crafted,
            "total_gold_earned": player.total_gold_earned,
            "gold_spent": player.gold_spent,
            "deaths": player.deaths,
            "survived_at_1hp": player.survived_at_1hp,
            "enemies_seen": list(player.enemies_seen),
            "perk_shop_extra_bought": player.perk_shop_extra_bought,
            "perk_shop_reroll_bought": player.perk_shop_reroll_bought,
            "total_playtime":     getattr(player, "total_playtime", 0.0),
            "onboarding_done":    getattr(player, "onboarding_done", False),
            "ob_forest_trips":    getattr(player, "_ob_forest_trips", 0),
            "saved_at": datetime.now().isoformat(),
        }

        fpath = SAVES_DIR / f"{save_name}.json"
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_game(save_name: str) -> Optional[Player]:
        """Завантажує гравця зі збереження."""
        fpath = SAVES_DIR / f"{save_name}.json"
        if not fpath.exists():
            return None

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:  # Пошкоджений або недоступний файл збереження
            return None


        # Реконструюємо об'єкт Player
        player = Player(data["name"])
        player.level = data.get("level", 1)
        from .hero_roster import HeroRoster
        raw_roster = data.get("hero_roster")
        if raw_roster:
            player.hero_roster = HeroRoster.from_dict(raw_roster)
        elif data.get("character_id"):
            # Міграція старого формату — перший спін ще не зроблено
            player.hero_roster = HeroRoster.new_game()
        player.xp = data.get("xp", 0)
        player.xp_next = data.get("xp_next", 50)
        player.hp = data.get("hp", 100)
        player.max_hp = data.get("max_hp", 100)
        player.attack = data.get("attack", 8)
        player.defense = data.get("defense", 3)
        player.gold = data.get("gold", 15)
        player.bonus_attack = data.get("bonus_attack", 0)
        print(f"[LOAD] Базові стати: lvl={player.level} xp={player.xp}/{player.xp_next}")

        # Інвентар
        player.inventory = []
        for raw in data.get("inventory", []):
            item = _deserialize_item(raw)
            if item:
                player.inventory.append(item)

        # Матеріали
        player.materials = data.get("materials", {})

        # Кресленники
        player.blueprints = []
        for entry in data.get("blueprints", []):
            # Підтримка старого формату (просто рядок) і нового (dict з uses)
            if isinstance(entry, str):
                bp_id, uses = entry, None
            else:
                bp_id = entry.get("id", "")
                uses  = entry.get("uses")
            if bp_id in BLUEPRINTS:
                ob = OwnedBlueprint.new(BLUEPRINTS[bp_id])
                if uses is not None:
                    ob.uses_left = uses
                player.blueprints.append(ob)

        # Екіпірована зброя
        raw_w = data.get("equipped_weapon")
        player.equipped_weapon = _deserialize_item(raw_w) if raw_w else None

        # Екіпірована броня
        raw_a = data.get("equipped_armor")
        player.equipped_armor = _deserialize_item(raw_a) if raw_a else None


        # Туторіали
        player.tutorial_seen = set(data.get("tutorial_seen", []))
        player.tutorial_queue = []

        # Перки
        saved_perks = data.get("perks", [])
        player.perks = []
        player.pending_perk_choices = []
        # Відновлюємо множники з перків (ітеруємось по копії, не по player.perks)
        from .perk_system import PERKS
        for perk_id in saved_perks:
            if perk_id in PERKS:
                # Застосовуємо тільки множники, без додавання в список
                perk = PERKS[perk_id]
                p = perk.perk_id
                m = player.perk_multipliers
                if p == "dmg_5":        m["dmg"] += 0.05
                elif p == "dmg_12":     m["dmg"] += 0.12
                elif p == "atk_speed_5":  m["atk_speed"] += 0.05
                elif p == "atk_speed_15": m["atk_speed"] += 0.15
                elif p == "crit_chance_7":  m["crit_chance"] += 7.0
                elif p == "crit_chance_12": m["crit_chance"] += 12.0
                elif p == "move_speed_5": m["move_speed"] += 0.05
                elif p == "range_5":    m["range"] += 0.05
        player.perks = saved_perks  # відновлюємо список як є
        print(f"[LOAD] Перки відновлено ({len(player.perks)} шт.)")

        player.locations_visited = set(data.get("locations_visited", ["village"]))

        # Досягнення
        player.achievements_unlocked = set(data.get("achievements_unlocked", []))
        player.achievements_new = []
        player.enemies_killed = data.get("enemies_killed", 0)
        player.goblins_killed = data.get("goblins_killed", 0)
        player.orcs_killed = data.get("orcs_killed", 0)
        player.knights_killed = data.get("knights_killed", 0)
        player.dragons_killed = data.get("dragons_killed", 0)
        player.items_crafted = data.get("items_crafted", 0)
        player.total_gold_earned = data.get("total_gold_earned", 0)
        player.gold_spent = data.get("gold_spent", 0)
        player.deaths = data.get("deaths", 0)
        player.survived_at_1hp = data.get("survived_at_1hp", False)
        player.enemies_seen = set(data.get("enemies_seen", []))
        player.perk_shop_extra_bought  = data.get("perk_shop_extra_bought", 0)
        player.perk_shop_reroll_bought = data.get("perk_shop_reroll_bought", 0)
        player.total_playtime    = data.get("total_playtime", 0.0)
        player.onboarding_done   = data.get("onboarding_done", False)
        player._ob_forest_trips  = data.get("ob_forest_trips", 0)
        player.skill_points = data.get("skill_points", 0)
        player.skill_nodes  = set(data.get("skill_nodes", []))
        player.quests_active = set(data.get("quests_active", []))
        player.quests_done   = set(data.get("quests_done",   []))

        # Черга крафту — офлайн прогрес: готові предмети збираємо одразу
        from .crafting_queue import CraftingQueue, DismantleQueue
        player.crafting_queue  = CraftingQueue()
        player.crafting_queue.load_list(data.get("crafting_queue", []))
        player.dismantle_queue = DismantleQueue()
        player.dismantle_queue.load_list(data.get("dismantle_queue", []))

        # Ринок — офлайн оновлення якщо час минув
        from .market import Market
        player.market = Market()
        player.market.load_dict(data.get("market", {}))
        player.daily_quests.from_dict(data.get("daily_quests", {}))
        player.market.ensure_fresh()   # оновлюємо якщо вийшов час


        return player

    @staticmethod
    def delete_save(save_name: str):
        """Видаляє збереження."""
        fpath = SAVES_DIR / f"{save_name}.json"
        if fpath.exists():
            fpath.unlink()


def autosave(player: Player):
    """Автоматичне збереження після зміни стану."""
    try:
        SaveManager.save_game(player, player.save_name)
        # Сигналізуємо менеджеру збережень що відбулось збереження
        from game.save_indicator import signal_saved
        signal_saved()
    except Exception:
        pass