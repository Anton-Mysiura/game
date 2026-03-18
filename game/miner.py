"""
Логіка шахтаря — стан, тарифи, генерація руд, ризики.
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import Optional

# ── Константи інструментів (для імпорту в інших модулях) ─────────
PICKAXE_ID        = "pickaxe"
BROKEN_PICKAXE_ID = "broken_pickaxe"
SHOVEL_ID         = "shovel"
REPAIR_RECIPE     = {"iron_bar": 3}
REPAIR_GOLD_COST  = 15

# ── Тарифи ───────────────────────────────────────────────────────
@dataclass
class MiningTier:
    tier_id:     str
    name:        str
    icon:        str
    description: str
    cost:        int          # монети за роботу
    duration:    int          # секунди реального часу
    min_ores:    int          # мінімум руд
    max_ores:    int          # максимум руд
    ore_pool:    list[str]    # можливі руди (material_id)
    depth_label: str          # "Поверхня" / "Середина" / "Глибина"

TIERS: dict[str, MiningTier] = {
    "surface": MiningTier(
        tier_id     = "surface",
        name        = "Поверхня",
        icon        = "🪨",
        description = "Швидко та дешево. Базові руди.",
        cost        = 10,
        duration    = 10 * 60,   # 10 хвилин
        min_ores    = 3,
        max_ores    = 6,
        depth_label = "Поверхня",
        ore_pool    = [
            "coal_ore", "copper_ore", "flint_ore", "graphite_ore",
            "sulfur_ore", "bronze_ore", "pyrite_ore", "obsidian_ore",
            "iron_ore",
        ],
    ),
    "middle": MiningTier(
        tier_id     = "middle",
        name        = "Середній рівень",
        icon        = "⛏",
        description = "Більше часу, кращі руди.",
        cost        = 25,
        duration    = 20 * 60,   # 20 хвилин
        min_ores    = 4,
        max_ores    = 8,
        depth_label = "Середина",
        ore_pool    = [
            "silver_ore", "gold_ore", "amber_ore", "amethyst_ore",
            "aquamarine_ore", "cobalt_ore", "emerald_ore", "garnet_ore",
            "sapphire_ore", "topaz_ore", "moonstone_ore", "onyx_ore",
            # рідко — з поверхні
            "iron_ore", "copper_ore",
        ],
    ),
    "deep": MiningTier(
        tier_id     = "deep",
        name        = "Глибина",
        icon        = "💎",
        description = "Довго та дорого. Рідкісні та епічні руди.",
        cost        = 60,
        duration    = 35 * 60,   # 35 хвилин
        min_ores    = 5,
        max_ores    = 10,
        depth_label = "Глибина",
        ore_pool    = [
            "mithril_ore", "ruby_ore", "dark_crystal_ore", "bloodstone_ore",
            "amethyst_crystal_ore", "steel_ore", "spinel_ore", "nephrite_ore",
            "astral_ore", "fire_ore", "storm_ore", "magma_ore",
            "toxic_ore", "lava_ore", "volcanic_ore",
            # рідко — з середини
            "gold_ore", "amethyst_ore",
        ],
    ),
}

# ── Ймовірності ризиків ───────────────────────────────────────────
RISK_PICKAXE_BREAK   = 0.20   # 20% — кайло ламається
RISK_CAVE_IN         = 0.10   # 10% — обвал (менше руд)
RISK_MINER_LOST      = 0.03   # 3%  — шахтар не повертається
SHOVEL_TIME_BONUS    = 0.10   # 10% зменшення часу від лопати

# ── Стан шахтаря ─────────────────────────────────────────────────
class MinerState:
    """Стан шахтаря, зберігається у save."""

    STATUS_IDLE       = "idle"        # вільний, чекає
    STATUS_WORKING    = "working"     # в шахті
    STATUS_DONE       = "done"        # повернувся, руди чекають
    STATUS_LOST       = "lost"        # не повернувся

    # Рівні втоми
    FATIGUE_NONE   = 0
    FATIGUE_TIRED  = 3   # після 3 походів — втомлений (+20% ціна)
    FATIGUE_EXHAUSTED = 5  # після 5 — виснажений (+50%, відмовляється при >3 tiers)

    def __init__(self):
        self.status:      str            = self.STATUS_IDLE
        self.tier_id:     Optional[str]  = None
        self.start_time:  Optional[float]= None   # unix timestamp
        self.end_time:    Optional[float]= None   # unix timestamp
        self.ores_ready:   dict[str, int] = {}     # руди що чекають забору
        self.had_cave_in:  bool           = False  # чи був обвал
        self.bonus_gold:   int            = 0      # знайдені монети
        self.bonus_items:  list[str]      = []     # знайдені item_id
        self.trips_since_rest: int        = 0      # походів без відпочинку
        self.resting_until:   Optional[float] = None

    @property
    def fatigue_level(self) -> int:
        """0 = свіжий, 1 = втомлений, 2 = виснажений."""
        t = self.trips_since_rest
        if t >= self.FATIGUE_EXHAUSTED:
            return 2
        if t >= self.FATIGUE_TIRED:
            return 1
        return 0

    @property
    def cost_multiplier(self) -> float:
        """Множник ціни від втоми."""
        return {0: 1.0, 1: 1.20, 2: 1.50}.get(self.fatigue_level, 1.0)

    @property
    def is_resting(self) -> bool:
        if self.resting_until is None:
            return False
        return time.time() < self.resting_until

    def rest_time_left(self) -> int:
        if not self.is_resting:
            return 0
        return max(0, int(self.resting_until - time.time()))

    def start_rest(self) -> None:
        """Відпочинок 10 хвилин — скидає втому."""
        self.resting_until    = time.time() + 10 * 60
        self.trips_since_rest = 0
        self.status           = self.STATUS_IDLE

    # ── Відправка ────────────────────────────────────────────────
    def send(self, tier_id: str, has_shovel: bool,
             weather: str = "ясно") -> None:
        """Відправляє шахтаря. Знімає лопату якщо є."""
        tier = TIERS[tier_id]
        duration = tier.duration
        if has_shovel:
            duration = int(duration * (1.0 - SHOVEL_TIME_BONUS))
        # Погода впливає на час
        if weather == "ясно":
            duration = int(duration * 0.95)   # -5% при ясній погоді
        elif weather == "дощ":
            duration = int(duration * 1.10)   # +10% при дощі
        elif weather == "туман":
            duration = int(duration * 1.05)   # +5% при тумані
        self.status     = self.STATUS_WORKING
        self.tier_id    = tier_id
        self.weather    = weather
        self.start_time = time.time()
        self.end_time   = self.start_time + duration
        self.ores_ready = {}
        self.had_cave_in= False

    # ── Перевірка чи час вийшов ──────────────────────────────────
    def check_return(self) -> bool:
        """
        Перевіряє чи шахтар повернувся.
        Якщо так — генерує руди і застосовує ризики.
        Повертає True якщо статус щойно змінився.
        """
        if self.status != self.STATUS_WORKING:
            return False
        if time.time() < self.end_time:
            return False

        # Час вийшов — визначаємо результат
        # Погода впливає на ризики
        weather = getattr(self, "weather", "ясно")
        risk_lost   = RISK_MINER_LOST
        risk_cave   = RISK_CAVE_IN
        if weather == "дощ":
            risk_cave += 0.05    # +5% обвал при дощі
            risk_lost += 0.01    # +1% зникнення
        elif weather == "туман":
            risk_cave += 0.03
        elif weather == "ясно":
            risk_cave = max(0, risk_cave - 0.02)  # -2% при ясній погоді

        # Ризик зникнення
        if random.random() < risk_lost:
            self.status = self.STATUS_LOST
            return True

        # Ризик обвалу
        cave_in = random.random() < risk_cave
        self.had_cave_in = cave_in

        # Генеруємо руди
        tier = TIERS[self.tier_id]
        min_o = tier.min_ores
        max_o = tier.max_ores
        if cave_in:
            max_o = max(min_o, max_o // 2)   # вдвічі менше при обвалі

        count = random.randint(min_o, max_o)
        ores: dict[str, int] = {}
        for _ in range(count):
            ore = random.choice(tier.ore_pool)
            ores[ore] = ores.get(ore, 0) + 1

        self.ores_ready        = ores
        self.status            = self.STATUS_DONE
        self.trips_since_rest += 1

        # Бонусні знахідки
        self.bonus_gold  = 0
        self.bonus_items = []
        tier = TIERS[self.tier_id]

        # Монети — частіше на глибині
        gold_chance = {"surface": 0.25, "middle": 0.40, "deep": 0.60}.get(self.tier_id, 0.3)
        if random.random() < gold_chance:
            gold_range = {"surface": (2, 8), "middle": (5, 20), "deep": (10, 40)}.get(self.tier_id, (2, 10))
            self.bonus_gold = random.randint(*gold_range)

        # Предмети — рідко, тільки на середньому і глибокому рівнях
        if self.tier_id in ("middle", "deep") and random.random() < 0.15:
            item_pool = {
                "middle": ["bone", "leather", "bone_dust", "quartz"],
                "deep":   ["magic_core", "runic_stone", "iron_chain", "shadow_cloth"],
            }
            self.bonus_items = [random.choice(item_pool.get(self.tier_id, ["bone"]))]

        return True

    # ── Час що залишився ────────────────────────────────────────
    def time_left(self) -> int:
        """Секунди до повернення (0 якщо вже готово)."""
        if self.status != self.STATUS_WORKING or self.end_time is None:
            return 0
        return max(0, int(self.end_time - time.time()))

    # ── Серіалізація ─────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "status":      self.status,
            "tier_id":     self.tier_id,
            "start_time":  self.start_time,
            "end_time":    self.end_time,
            "ores_ready":  self.ores_ready,
            "had_cave_in": self.had_cave_in,
            "weather":           getattr(self, "weather", "ясно"),
            "bonus_gold":        self.bonus_gold,
            "bonus_items":       self.bonus_items,
            "trips_since_rest":  self.trips_since_rest,
            "resting_until":     self.resting_until,
        }

    def from_dict(self, d: dict) -> None:
        self.status      = d.get("status",      self.STATUS_IDLE)
        self.tier_id     = d.get("tier_id",     None)
        self.start_time  = d.get("start_time",  None)
        self.end_time    = d.get("end_time",    None)
        self.ores_ready  = d.get("ores_ready",  {})
        self.had_cave_in = d.get("had_cave_in", False)
        self.weather          = d.get("weather",    "ясно")
        self.bonus_gold       = d.get("bonus_gold",  0)
        self.bonus_items      = d.get("bonus_items", [])
        self.trips_since_rest = d.get("trips_since_rest", 0)
        self.resting_until    = d.get("resting_until",    None)