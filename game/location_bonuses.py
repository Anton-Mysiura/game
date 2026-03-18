"""
Пасивні бонуси від відвіданих локацій.
Бонуси рахуються динамічно — достатньо мати location_id в player.locations_visited.
"""
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class LocationBonus:
    location_id: str
    name:        str        # назва локації
    icon:        str
    stat:        str        # "attack" | "defense" | "max_hp" | "crit_chance" | "xp_mult"
    value:       float
    desc:        str        # людиночитабельний опис бонусу
    color:       tuple      # колір для UI


LOCATION_BONUSES: Dict[str, LocationBonus] = {
    "village": LocationBonus(
        "village", "Пригорщина", "🏘",
        "max_hp", 10,
        "+10 до макс. HP (рідне місто)",
        (120, 200, 100),
    ),
    "forest": LocationBonus(
        "forest", "Темний Ліс", "🌲",
        "attack", 3,
        "+3 до атаки (загартований боями)",
        (60, 180, 60),
    ),
    "ruins": LocationBonus(
        "ruins", "Стародавні Руїни", "🗿",
        "crit_chance", 0.05,
        "+5% шанс крит. удару (таємниче знання)",
        (160, 140, 80),
    ),
    "tower": LocationBonus(
        "tower", "Вежа Лицаря", "🏰",
        "defense", 4,
        "+4 до захисту (лицарська виправка)",
        (180, 120, 60),
    ),
    "dragon": LocationBonus(
        "dragon", "Лігво Дракона", "🐉",
        "max_hp", 30,
        "+30 до макс. HP (кров дракона)",
        (220, 80, 60),
    ),
    # Під-локації лісу
    "goblin": LocationBonus(
        "goblin", "Місце гоблінів", "👺",
        "attack", 2,
        "+2 до атаки (рефлекси після боїв)",
        (100, 180, 60),
    ),
    "orc": LocationBonus(
        "orc", "Табір орків", "👹",
        "defense", 2,
        "+2 до захисту (трофейна броня)",
        (180, 100, 60),
    ),
}


def get_active_bonuses(locations_visited: set) -> List[LocationBonus]:
    """Повертає список активних бонусів для поточного гравця."""
    return [
        b for loc_id, b in LOCATION_BONUSES.items()
        if loc_id in locations_visited
    ]


def calc_bonus_total(locations_visited: set, stat: str) -> float:
    """Сума бонусів для конкретного стату."""
    return sum(
        b.value for b in get_active_bonuses(locations_visited)
        if b.stat == stat
    )