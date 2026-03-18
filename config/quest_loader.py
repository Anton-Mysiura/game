"""
Перетворює config/quests.py → об'єкти Quest і DailyQuest.
Цей файл не потрібно редагувати.
"""
from __future__ import annotations
from typing import Callable


def _build_unlock_cond(when: str) -> Callable:
    """Перетворює рядок умови на лямбду."""
    if when == "always":
        return lambda p: True

    if when.startswith("quest:"):
        qid = when[6:]
        return lambda p, q=qid: q in p.quests_done

    if when.startswith("level:"):
        lvl = int(when[6:])
        return lambda p, l=lvl: p.level >= l

    if when.startswith("lambda "):
        return eval(when)  # noqa: S307

    return lambda p: True


def _build_complete_cond(when: str) -> Callable:
    """Перетворює рядок умови виконання на лямбду."""
    if when.startswith("kills:"):
        _, target, count = when.split(":")
        count = int(count)
        if target == "any":
            return lambda p, c=count: p.enemies_killed >= c
        if target == "goblin":
            return lambda p, c=count: p.goblins_killed >= c
        if target == "orc":
            return lambda p, c=count: p.orcs_killed >= c
        if target == "dark_knight":
            return lambda p, c=count: p.dark_knights_killed >= c
        if target == "cursed_knight":
            return lambda p, c=count: p.cursed_knights_killed >= c
        if target == "dragon":
            return lambda p, c=count: p.dragons_killed >= c
        # fallback — шукаємо в kills_by_type якщо є
        return lambda p, t=target, c=count: (
            getattr(p, "kills_by_type", {}).get(t, 0) >= c
        )

    if when.startswith("material:"):
        _, mat_id, count = when.split(":")
        count = int(count)
        return lambda p, m=mat_id, c=count: p.materials.get(m, 0) >= c

    if when.startswith("gold:"):
        amount = int(when[5:])
        return lambda p, a=amount: p.gold >= a

    if when.startswith("weapon_attack:"):
        atk = int(when[14:])
        return lambda p, a=atk: (
            any(getattr(i, "attack_bonus", 0) >= a for i in p.inventory)
            or (p.equipped_weapon and p.equipped_weapon.attack_bonus >= a)
        )

    if when.startswith("wins:"):
        count = int(when[5:])
        return lambda p, c=count: p.battles_won >= c

    if when.startswith("lambda "):
        return eval(when)  # noqa: S307

    return lambda p: False


def build_quests() -> dict:
    """Будує словник Quest об'єктів з config/quests.py."""
    from config.quests import QUESTS_DATA
    from game.quests import Quest

    result = {}
    for d in QUESTS_DATA:
        q = Quest(
            quest_id       = d["id"],
            title          = d["title"],
            icon           = d["icon"],
            story_lines    = d.get("story", []),
            unlock_cond    = _build_unlock_cond(d.get("unlock_when", "always")),
            complete_cond  = _build_complete_cond(d.get("complete_when", "always")),
            objective      = d.get("objective", ""),
            reward_gold    = d.get("reward_gold", 0),
            reward_xp      = d.get("reward_xp", 0),
            reward_mats    = d.get("reward_mats", {}),
            reward_item_id = d.get("reward_item_id", ""),
            reward_spins   = d.get("reward_spins", 0),
            unlocks        = d.get("unlocks", ""),
            repeatable     = d.get("repeatable", False),
        )
        result[d["id"]] = q
    return result


def build_daily_pool() -> list:
    """Будує пул щоденних завдань з config/quests.py."""
    from config.quests import DAILY_QUESTS_POOL
    return [
        (d["id"], d["title"], d["icon"], d["desc"],
         d["type"], d["target"], d["gold"], d["xp"])
        for d in DAILY_QUESTS_POOL
    ]
