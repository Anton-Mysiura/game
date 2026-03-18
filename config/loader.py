"""
╔══════════════════════════════════════════╗
║  ЗАВАНТАЖУВАЧ КОНФІГІВ                   ║
║  Перетворює config/*.py → об'єкти гри    ║
╚══════════════════════════════════════════╝

Цей файл НЕ потрібно редагувати для додавання контенту.
Редагуй config/enemies.py, config/loot.py, config/heroes.py.

Використання:
    from config.loader import load_all
    MATERIALS, ITEMS, BLUEPRINTS, HEROES, SPAWN_TABLES = load_all()
"""
from __future__ import annotations
import random
from pathlib import Path
from typing import Optional

# ── Імпорт конфіг-даних ──────────────────────────────────────────
from config.enemies import ENEMY_DEFINITIONS, SPAWN_TABLES as _SPAWN_TABLES_RAW
from config.loot    import MATERIALS_DATA, ITEMS_DATA, BLUEPRINTS_DATA
from config.heroes  import HEROES_DATA, RARITY_WEIGHTS

# ── Імпорт класів гри ─────────────────────────────────────────────
from game.data    import Material, Item, Blueprint, OwnedBlueprint, BP_RARITY_USES
from game.enemy   import Enemy
from game.enemy_scaling import scale_enemy
from game.heroes  import Hero, HeroSkill, AnimConfig
from game.spawn_table import SpawnEntry


# ══════════════════════════════════════════
#  МАТЕРІАЛИ
# ══════════════════════════════════════════

def _build_materials() -> dict[str, Material]:
    result = {}
    for mat_id, row in MATERIALS_DATA.items():
        name, icon, desc, rarity, atk, dfs, hp, crit, mult, is_metal = row
        result[mat_id] = Material(
            material_id    = mat_id,
            name           = name,
            icon           = icon,
            description    = desc,
            rarity         = rarity,
            bonus_attack   = atk,
            bonus_defense  = dfs,
            bonus_hp       = hp,
            bonus_crit     = crit,
            multiplier     = mult,
            is_metal       = is_metal,
        )
    return result


# ══════════════════════════════════════════
#  ПРЕДМЕТИ
# ══════════════════════════════════════════

def _build_items() -> dict[str, Item]:
    result = {}
    for item_id, row in ITEMS_DATA.items():
        name, typ, val, icon, desc, atk, dfs, hp, hp_restore, crit = row
        result[item_id] = Item(
            item_id       = item_id,
            name          = name,
            item_type     = typ,
            value         = val,
            icon          = icon,
            description   = desc,
            attack_bonus  = atk,
            defense_bonus = dfs,
            hp_bonus      = hp,
            hp_restore    = hp_restore,
            crit_bonus    = crit,
        )
    return result


# ══════════════════════════════════════════
#  КРЕСЛЕННИКИ
# ══════════════════════════════════════════

def _build_blueprints() -> dict[str, Blueprint]:
    result = {}
    for bp_id, d in BLUEPRINTS_DATA.items():
        res_id, res_name, res_val, res_icon, res_desc = d["result"]
        bonus_mats = tuple(d.get("bonus_materials", []))
        bp = Blueprint(
            blueprint_id   = bp_id,
            name           = d["name"],
            result_id      = res_id,
            result_name    = res_name,
            result_value   = res_val,
            result_icon    = res_icon,
            result_desc    = res_desc,
            recipe         = d["recipe"],
            unlock_cost    = d["unlock_cost"],
            result_type    = d.get("type", "weapon"),
            result_attack  = d.get("attack", 0),
            result_defense = d.get("defense", 0),
            result_hp      = d.get("hp", 0),
            bonus_materials= bonus_mats,
            rarity         = d.get("rarity", "common"),
        )
        result[bp_id] = bp
    return result


# ══════════════════════════════════════════
#  ВОРОГИ
# ══════════════════════════════════════════

def _resolve_loot_amount(val) -> int:
    """Перетворює (мін, макс) або число в конкретне значення."""
    if isinstance(val, tuple):
        return random.randint(val[0], val[1])
    return int(val)


def _build_enemy_factory(key: str, items_dict: dict[str, Item]):
    """Повертає фабричну функцію для ворога з конфіга."""
    d = ENEMY_DEFINITIONS[key]

    def factory(player_level: int = 1) -> Enemy:
        # Лут-предмети
        loot_items = [items_dict[iid] for iid in d.get("loot_items", [])
                      if iid in items_dict]
        # Лут-матеріали
        chances = d.get("loot_chance", {})
        loot_mats: dict[str, int] = {}
        for mat_id, val in d.get("loot_materials", {}).items():
            amount = _resolve_loot_amount(val)
            # перевірка шансу
            chance = chances.get(mat_id, 1.0)
            if random.random() < chance and amount > 0:
                loot_mats[mat_id] = amount

        e = Enemy(
            name           = d["name"],
            hp             = d["hp"],
            attack         = d["attack"],
            defense        = d["defense"],
            xp_reward      = d["xp"],
            gold_reward    = d["gold"],
            loot_items     = loot_items,
            loot_materials = loot_mats,
            sprite_name    = d.get("sprite", "goblin"),
            behavior       = d.get("behavior", "balanced"),
        )
        e.level = d.get("level", 1)
        scale_enemy(e, player_level)
        return e

    factory.__name__ = f"make_{key}"
    return factory


def _build_spawn_tables(items_dict: dict[str, Item]) -> dict[str, list[SpawnEntry]]:
    factories = {key: _build_enemy_factory(key, items_dict)
                 for key in ENEMY_DEFINITIONS}

    result: dict[str, list[SpawnEntry]] = {}
    for location, entries in _SPAWN_TABLES_RAW.items():
        table = []
        for (enemy_key, weight, min_level) in entries:
            if enemy_key not in factories:
                continue
            table.append(SpawnEntry(
                factory   = factories[enemy_key],
                weight    = weight,
                min_level = min_level,
                label     = ENEMY_DEFINITIONS[enemy_key]["name"],
            ))
        result[location] = table
    return result


# ══════════════════════════════════════════
#  ГЕРОЇ
# ══════════════════════════════════════════

def _build_skills(skills_data: list) -> list[HeroSkill]:
    result = []
    for s in skills_data:
        skill = HeroSkill(
            name           = s["name"],
            desc           = s["desc"],
            is_passive     = s.get("passive", True),
            bonus_hp       = s.get("hp", 0),
            bonus_attack   = s.get("attack", 0),
            bonus_defense  = s.get("defense", 0),
            bonus_crit     = s.get("crit", 0.0),
            bonus_dodge    = s.get("dodge", 0.0),
            bonus_parry    = s.get("parry", 0.0),
            active_id      = s.get("active_id", ""),
        )
        result.append(skill)
    return result


def _build_heroes(anim_base_dir: Path) -> dict[str, Hero]:
    from ui.constants import ANIMATIONS_DIR
    result = {}
    for hero_id, d in HEROES_DATA.items():
        anim_raw = d.get("anim", {})
        fh       = d.get("frame_h", 128)

        def _get(key):
            return anim_raw.get(key, (None, 0))

        anim = AnimConfig(
            folder   = d["anim_folder"],
            frame_h  = fh,
            idle     = _get("idle"),
            idle2    = _get("idle2"),
            attack1  = _get("attack1"),
            attack2  = _get("attack2"),
            attack3  = _get("attack3"),
            hurt     = _get("hurt"),
            dead     = _get("dead"),
            run      = _get("run"),
            walk     = _get("walk"),
            jump     = _get("jump"),
            block    = _get("block"),
            special1 = _get("special1"),
            special2 = _get("special2"),
        )

        base = d.get("base", {})
        hero = Hero(
            hero_id      = hero_id,
            name         = d["name"],
            group        = d["group"],
            rarity       = d["rarity"],
            icon         = d["icon"],
            lore         = d["lore"],
            anim         = anim,
            skills       = _build_skills(d.get("skills", [])),
            base_hp      = base.get("hp", 0),
            base_attack  = base.get("attack", 0),
            base_defense = base.get("defense", 0),
            base_crit    = base.get("crit", 0.0),
            base_dodge   = base.get("dodge", 0.0),
        )
        result[hero_id] = hero
    return result


# ══════════════════════════════════════════
#  ПУБЛІЧНИЙ API
# ══════════════════════════════════════════

_cache: dict = {}


def load_all():
    """
    Завантажує всі конфіги і повертає готові словники.
    Результат кешується — викликай скільки завгодно разів.

    Повертає:
        (MATERIALS, ITEMS, BLUEPRINTS, HEROES, SPAWN_TABLES)
    """
    if _cache:
        return (_cache["materials"], _cache["items"],
                _cache["blueprints"], _cache["heroes"],
                _cache["spawn_tables"])

    mats      = _build_materials()
    items     = _build_items()
    bps       = _build_blueprints()
    heroes    = _build_heroes(Path("."))
    spawns    = _build_spawn_tables(items)

    _cache.update(materials=mats, items=items,
                  blueprints=bps, heroes=heroes,
                  spawn_tables=spawns)

    return mats, items, bps, heroes, spawns


def reload():
    """Очищає кеш і перезавантажує всі конфіги (для live-edit)."""
    _cache.clear()
    return load_all()
