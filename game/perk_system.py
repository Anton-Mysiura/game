"""
Система перків (карток бонусів при підвищенні рівня).
"""

import random
from dataclasses import dataclass, field


# ══════════════════════════════════════════
#  РІДКОСТІ
# ══════════════════════════════════════════

RARITY_WEIGHTS = {
    "common":    50.0,
    "uncommon":  25.0,
    "rare":      12.0,
    "epic":       7.0,
    "mythic":     3.0,
    "legendary":  1.5,
    "god":        0.5,
}

RARITY_NAMES = {
    "common":    "Звичайна",
    "uncommon":  "Незвичайна",
    "rare":      "Рідкісна",
    "epic":      "Епічна",
    "mythic":    "Міфічна",
    "legendary": "Легендарна",
    "god":       "GOD",
}

RARITY_COLORS = {
    "common":    (200, 200, 200),
    "uncommon":  (80,  200, 80),
    "rare":      (80,  120, 255),
    "epic":      (180, 80,  255),
    "mythic":    (255, 80,  80),
    "legendary": (255, 200, 0),
    "god":       (255, 255, 255),
}


# ══════════════════════════════════════════
#  ДАТАКЛАС ПЕРКУ
# ══════════════════════════════════════════

@dataclass
class Perk:
    perk_id: str
    name: str
    description: str
    rarity: str
    icon: str

    @property
    def color(self):
        return RARITY_COLORS[self.rarity]

    @property
    def rarity_name(self):
        return RARITY_NAMES[self.rarity]


# ══════════════════════════════════════════
#  СПИСОК УСІХ ПЕРКІВ
# ══════════════════════════════════════════

PERKS = {
    # ── Звичайні ──
    "dmg_5": Perk(
        "dmg_5", "+5% шкоди", "Всі удари наносять на 5% більше шкоди",
        "common", "⚔"
    ),
    "atk_speed_5": Perk(
        "atk_speed_5", "+5% швидкість атаки", "Атаки виконуються на 5% швидше",
        "common", "⚡"
    ),
    "crit_chance_7": Perk(
        "crit_chance_7", "+7% шанс крит. удару", "Збільшує шанс критичного удару на 7%",
        "common", "🎯"
    ),
    "move_speed_5": Perk(
        "move_speed_5", "+5% швидкість руху", "Персонаж рухається на 5% швидше",
        "common", "💨"
    ),
    "range_5": Perk(
        "range_5", "+5% дальність ударів", "Хітбокс атак збільшується на 5%",
        "common", "📏"
    ),

    # ── Незвичайні ──
    "dmg_12": Perk(
        "dmg_12", "+12% шкоди", "Всі удари наносять на 12% більше шкоди",
        "uncommon", "⚔"
    ),
    "atk_speed_15": Perk(
        "atk_speed_15", "+15% швидкість атаки", "Атаки виконуються на 15% швидше",
        "uncommon", "⚡"
    ),
    "crit_chance_12": Perk(
        "crit_chance_12", "+12% шанс крит. удару", "Збільшує шанс критичного удару на 12%",
        "uncommon", "🎯"
    ),

    # ── Рідкісні ──
    "crit_knockback": Perk(
        "crit_knockback", "Крит відштовхує", "Критичні удари відштовхують ворога",
        "rare", "💥"
    ),
    "stun_10": Perk(
        "stun_10", "10% оглушення", "Удари мають 10% шанс оглушити ворога на 0.7 сек",
        "rare", "😵"
    ),
    "block_pierce": Perk(
        "block_pierce", "Пробиття блоку", "Атаки проходять крізь блок ворога",
        "rare", "🛡"
    ),
    "first_hit_combo": Perk(
        "first_hit_combo", "Перший удар комбо +50%",
        "Перший удар у кожному комбо наносить на 50% більше шкоди",
        "rare", "1️⃣"
    ),

    # ── Епічні ──
    "combo_on_block": Perk(
        "combo_on_block", "Комбо крізь блок",
        "Комбо не переривається при отриманні удару в блок",
        "epic", "🔥"
    ),
    "crit_burn": Perk(
        "crit_burn", "Крити підпалюють",
        "Критичні удари підпалюють ворога — він горить 2 сек",
        "epic", "🔥"
    ),

    # ── Міфічні ──
    "every_5th_crit": Perk(
        "every_5th_crit", "Кожен 5-й = крит",
        "Кожен 5-й удар гарантовано є критичним",
        "mythic", "⭐"
    ),

    # ── Легендарні ──
    "double_hit": Perk(
        "double_hit", "Подвійний удар",
        "Кожна атака завдає удар двічі",
        "legendary", "⚔⚔"
    ),
    "combo_no_break": Perk(
        "combo_no_break", "Невразливе комбо",
        "Комбо не обривається від отриманих атак",
        "legendary", "♾"
    ),
    "shockwave": Perk(
        "shockwave", "Ударна хвиля",
        "Удари створюють хвилю, яка підкидає ворога",
        "legendary", "🌊"
    ),
    "air_attack_200": Perk(
        "air_attack_200", "Повітряні атаки +200%",
        "Атаки у стрибку наносять утричі більше шкоди",
        "legendary", "🦅"
    ),

    # ── GOD ──
    "perfect_block_slow": Perk(
        "perfect_block_slow", "Ідеальний блок = стоп-час",
        "Час сповільнюється на 1 сек після ідеального блоку",
        "god", "⏱"
    ),
    "every_3rd_crit": Perk(
        "every_3rd_crit", "Кожен 3-й = крит",
        "Кожен 3-й удар гарантовано є критичним",
        "god", "💫"
    ),
    "auto_knockback": Perk(
        "auto_knockback", "Кожен удар відштовхує",
        "Кожен удар трохи відштовхує ворога",
        "god", "💪"
    ),
    "lifesteal": Perk(
        "lifesteal", "Крадіжка здоров'я",
        "Повертає 20% отриманої шкоди у вигляді HP",
        "god", "❤"
    ),

    # ── Нові перки: ухилення / парирування / енергія ──

    # Uncommon
    "stamina_up": Perk(
        "stamina_up", "+30 енергії",
        "Максимальна енергія збільшується на 30 одиниць",
        "uncommon", "🔋"
    ),
    "fast_regen": Perk(
        "fast_regen", "Швидка регенерація",
        "Енергія відновлюється на 50% швидше",
        "uncommon", "⚡"
    ),

    # Rare
    "dodge_attack": Perk(
        "dodge_attack", "Ухилення → удар",
        "Перша атака після ухилення наносить +40% шкоди",
        "rare", "💨"
    ),
    "parry_heal": Perk(
        "parry_heal", "Парирування лікує",
        "Вдале парирування відновлює 8% максимального HP",
        "rare", "⚔"
    ),

    # Epic
    "shadow_step": Perk(
        "shadow_step", "Тіньовий крок",
        "Ухилення не витрачає енергію (перекат безкоштовний)",
        "epic", "🌑"
    ),
    "counter_bleed": Perk(
        "counter_bleed", "Контратака кровоточить",
        "Удар після парирування накладає кровотечу на 5 сек",
        "epic", "🩸"
    ),

    # Legendary
    "infinite_combo": Perk(
        "infinite_combo", "Нескінченне комбо",
        "Ухилення не перериває комбо лічильник",
        "legendary", "∞"
    ),

    # God
    "ghost_dodge": Perk(
        "ghost_dodge", "Примарне ухилення",
        "Під час ухилення наступний удар — гарантований крит",
        "god", "👻"
    ),
}


# ══════════════════════════════════════════
#  ВИБІРКА КАРТОК
# ══════════════════════════════════════════

def _roll_rarity() -> str:
    """Визначає рідкість картки за вагами."""
    rarities = list(RARITY_WEIGHTS.keys())
    weights  = list(RARITY_WEIGHTS.values())
    return random.choices(rarities, weights=weights, k=1)[0]


def roll_perks(count: int = 3) -> list[Perk]:
    """
    Тягне count карток для вибору.
    Гарантує що всі 3 картки різні (різний perk_id).
    """
    result = []
    used_ids = set()
    attempts = 0

    while len(result) < count and attempts < 100:
        attempts += 1
        rarity = _roll_rarity()
        candidates = [p for p in PERKS.values()
                      if p.rarity == rarity and p.perk_id not in used_ids]

        # Якщо для цієї рідкості немає невикористаних — беремо будь-яку
        if not candidates:
            candidates = [p for p in PERKS.values() if p.perk_id not in used_ids]

        if not candidates:
            break

        perk = random.choice(candidates)
        result.append(perk)
        used_ids.add(perk.perk_id)

    return result