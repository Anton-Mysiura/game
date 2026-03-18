"""
Дерево навичок — 3 гілки, кожна по 5 вузлів.
Очки нараховуються при підвищенні рівня.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

# ── Визначення вузлів ──────────────────────────────────────────────
# Кожен вузол: id, назва, опис, який стат і на скільки збільшує

@dataclass(frozen=True)
class SkillNode:
    node_id:    str
    name:       str
    desc:       str
    icon:       str
    stat:       str     # "attack" | "defense" | "max_hp" | "crit_chance" | "atk_speed" | "move_speed"
    value:      float   # абсолютне значення бонусу
    branch:     str     # "strength" | "endurance" | "agility"
    tier:       int     # 1..5 — рівень в гілці
    requires:   Optional[str] = None  # node_id попереднього вузла


# ── Гілка 1: Сила (червона) ──────────────────────────────────────────
SKILL_NODES: Dict[str, SkillNode] = {}

def _reg(node: SkillNode):
    SKILL_NODES[node.node_id] = node

# Сила
_reg(SkillNode("str_1", "Гостре лезо",    "+5 до атаки",             "⚔", "attack",      5,   "strength", 1))
_reg(SkillNode("str_2", "Важкий удар",    "+8 до атаки",             "🗡", "attack",      8,   "strength", 2, "str_1"))
_reg(SkillNode("str_3", "Точний удар",    "+5% шанс крит. удару",   "🎯", "crit_chance", 0.05,"strength", 3, "str_2"))
_reg(SkillNode("str_4", "Руйнівник",      "+12 до атаки",            "💢","attack",      12,  "strength", 4, "str_3"))
_reg(SkillNode("str_5", "Берсерк",        "+15 до атаки, +10% крит","🔥", "attack",      15,  "strength", 5, "str_4"))
# str_5 також дає crit_chance — обробляємо окремо нижче

# Витривалість
_reg(SkillNode("end_1", "Загартування",   "+20 до макс. HP",         "❤", "max_hp",      20,  "endurance", 1))
_reg(SkillNode("end_2", "Товста шкіра",   "+3 до захисту",           "🛡","defense",     3,   "endurance", 2, "end_1"))
_reg(SkillNode("end_3", "Стійкість",      "+30 до макс. HP",         "💪","max_hp",      30,  "endurance", 3, "end_2"))
_reg(SkillNode("end_4", "Броня воїна",    "+5 до захисту",           "⛨", "defense",     5,   "endurance", 4, "end_3"))
_reg(SkillNode("end_5", "Незламний",      "+50 до макс. HP, +5 DEF","🏛", "max_hp",      50,  "endurance", 5, "end_4"))

# Спритність
_reg(SkillNode("agi_1", "Легкий крок",    "+5% швидкість атаки",     "💨","atk_speed",   0.05,"agility", 1))
_reg(SkillNode("agi_2", "Реакція",        "+10% швидкість атаки",    "⚡","atk_speed",   0.10,"agility", 2, "agi_1"))
_reg(SkillNode("agi_3", "Тіньовий удар",  "+7% шанс крит. удару",   "🌑","crit_chance", 0.07,"agility", 3, "agi_2"))
_reg(SkillNode("agi_4", "Вихор",          "+15% швидкість атаки",    "🌀","atk_speed",   0.15,"agility", 4, "agi_3"))
_reg(SkillNode("agi_5", "Майстер бою",    "+20% шв. атаки, +5% крит","👁","atk_speed",   0.20,"agility", 5, "agi_4"))

# Групування по гілках для зручності
BRANCHES = {
    "strength":  {"name": "Сила",        "icon": "⚔", "color": (220, 80,  60),  "nodes": ["str_1","str_2","str_3","str_4","str_5"]},
    "endurance": {"name": "Витривалість", "icon": "🛡","color": (60,  160, 220), "nodes": ["end_1","end_2","end_3","end_4","end_5"]},
    "agility":   {"name": "Спритність",   "icon": "⚡","color": (80,  200, 100), "nodes": ["agi_1","agi_2","agi_3","agi_4","agi_5"]},
}

# Додаткові бонуси для вузлів з двома ефектами
EXTRA_BONUS: Dict[str, tuple] = {
    "str_5": ("crit_chance", 0.10),
    "end_5": ("defense", 5),
    "agi_5": ("crit_chance", 0.05),
}


def apply_skill_node(player, node_id: str):
    """Застосовує бонус вузла до гравця."""
    node = SKILL_NODES.get(node_id)
    if not node:
        return
    _apply_stat(player, node.stat, node.value)
    if node_id in EXTRA_BONUS:
        stat, val = EXTRA_BONUS[node_id]
        _apply_stat(player, stat, val)


def _apply_stat(player, stat: str, value: float):
    if stat == "attack":
        player.attack += int(value)
    elif stat == "defense":
        player.defense += int(value)
    elif stat == "max_hp":
        player.max_hp += int(value)
        player.hp = min(player.hp + int(value), player.max_hp)
    elif stat == "crit_chance":
        player.perk_multipliers["crit_chance"] = \
            round(player.perk_multipliers.get("crit_chance", 0.0) + value, 4)
    elif stat == "atk_speed":
        player.perk_multipliers["atk_speed"] = \
            round(player.perk_multipliers.get("atk_speed", 1.0) + value, 4)


def can_unlock(player, node_id: str) -> bool:
    """Чи можна розблокувати цей вузол."""
    if node_id in player.skill_nodes:
        return False
    node = SKILL_NODES.get(node_id)
    if not node:
        return False
    if node.requires and node.requires not in player.skill_nodes:
        return False
    return player.skill_points > 0