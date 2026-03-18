"""
Система репутації гравця в селі.

Репутація зростає від:
  - виконання квестів
  - перемог над ворогами
  - крафту предметів
  - відправки шахтаря
  - витрат у крамниці/ринку

Рівні репутації і їхні бонуси:
  0   — Невідомий    (нейтрал)
  100 — Знайомий     (-3% ціни)
  250 — Друг         (-7% ціни, нові діалоги)
  500 — Союзник      (-12% ціни, ексклюзивні товари)
  900 — Герой        (-18% ціни, макс. знижка)
 1500 — Легенда      (-25% ціни, особливий статус)
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RepTier:
    tier_id:   str
    name:      str
    icon:      str
    min_rep:   int
    discount:  float   # множник ціни, напр. 0.93 = -7%
    color:     tuple


TIERS: list[RepTier] = [
    RepTier("unknown",  "Невідомий", "❓",  0,    1.00, (160, 160, 160)),
    RepTier("familiar", "Знайомий",  "🙂",  100,  0.97, (180, 200, 140)),
    RepTier("friend",   "Друг",      "😊",  250,  0.93, (100, 220, 120)),
    RepTier("ally",     "Союзник",   "🤝",  500,  0.88, ( 80, 160, 255)),
    RepTier("hero",     "Герой",     "⚔",   900,  0.82, (220, 160,  60)),
    RepTier("legend",   "Легенда",   "👑",  1500, 0.75, (255, 200,  40)),
]

# ── Скільки репутації дає кожна дія ──────────────────────────────
REP_QUEST_COMPLETE  = 30   # виконано квест
REP_ENEMY_KILL      = 1    # вбито ворога
REP_ITEM_CRAFT      = 5    # скрафтовано предмет
REP_MINE_TRIP       = 8    # шахтар повернувся
REP_SHOP_SPEND_10   = 1    # кожні 10 монет витрачених у крамниці


def get_tier(reputation: int) -> RepTier:
    """Повертає поточний рівень репутації."""
    result = TIERS[0]
    for tier in TIERS:
        if reputation >= tier.min_rep:
            result = tier
    return result


def get_next_tier(reputation: int) -> RepTier | None:
    """Повертає наступний рівень або None якщо максимум."""
    current = get_tier(reputation)
    for i, tier in enumerate(TIERS):
        if tier.tier_id == current.tier_id and i + 1 < len(TIERS):
            return TIERS[i + 1]
    return None


def apply_discount(price: int, reputation: int) -> int:
    """Застосовує знижку від репутації до ціни."""
    tier = get_tier(reputation)
    return max(1, int(price * tier.discount))


def add_reputation(player, amount: int, reason: str = "") -> bool:
    """
    Додає репутацію гравцю.
    Повертає True якщо рівень підвищився.
    """
    old_tier = get_tier(player.reputation)
    player.reputation = getattr(player, "reputation", 0) + amount
    new_tier = get_tier(player.reputation)

    leveled_up = old_tier.tier_id != new_tier.tier_id
    if leveled_up:
        from ui.notifications import notify
        notify(
            f"⭐ Репутація: {new_tier.icon} {new_tier.name}! "
            f"Знижка -{int((1 - new_tier.discount) * 100)}%",
            kind="item", duration=4.0
        )
    return leveled_up