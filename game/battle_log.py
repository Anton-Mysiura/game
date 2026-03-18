"""
Журнал бою — збирає події під час битви, зберігає для перегляду після.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class EventType(Enum):
    HIT         = "hit"
    CRIT        = "crit"
    BLOCK       = "block"
    MISS        = "miss"
    ENEMY_HIT   = "enemy_hit"
    BURN        = "burn"
    STUN        = "stun"
    LIFESTEAL   = "lifesteal"
    HEAL        = "heal"
    KILL        = "kill"
    DEATH       = "death"
    COMBO       = "combo"


# Іконки і кольори для кожного типу події
EVENT_META = {
    EventType.HIT:       ("⚔",  (220, 200, 180), "Удар"),
    EventType.CRIT:      ("💥", (255, 200,  50), "Критичний удар"),
    EventType.BLOCK:     ("🛡",  (100, 180, 255), "Блок"),
    EventType.MISS:      ("💨", (150, 150, 150), "Промах"),
    EventType.ENEMY_HIT: ("🩸", (220,  80,  80), "Отримано удар"),
    EventType.BURN:      ("🔥", (255, 140,  30), "Підпал"),
    EventType.STUN:      ("⚡", (220, 220,  80), "Оглушення"),
    EventType.LIFESTEAL: ("💚", ( 80, 220, 120), "Крадіжка здоров'я"),
    EventType.HEAL:      ("❤",  ( 80, 220, 120), "Зцілення"),
    EventType.KILL:      ("💀", (255, 215,   0), "Ворог переможений"),
    EventType.DEATH:     ("☠",  (220,  60,  60), "Герой загинув"),
    EventType.COMBO:     ("🔥", (255, 160,  40), "Комбо"),
}


@dataclass
class BattleEvent:
    etype:   EventType
    turn:    int           # номер кроку (удар N)
    actor:   str           # "Гравець" або ім'я ворога
    value:   int = 0       # числове значення (дамаг, хіл тощо)
    note:    str = ""      # додаткова примітка

    @property
    def icon(self) -> str:
        return EVENT_META[self.etype][0]

    @property
    def color(self) -> tuple:
        return EVENT_META[self.etype][1]

    @property
    def label(self) -> str:
        return EVENT_META[self.etype][2]

    def to_text(self) -> str:
        """Людиночитабельний рядок події."""
        v = self.value
        t = self.turn
        if self.etype == EventType.HIT:
            return f"[{t}] {self.actor} завдав {v} шкоди"
        if self.etype == EventType.CRIT:
            return f"[{t}] {self.actor} — КРИТИЧНИЙ УДАР! {v} шкоди"
        if self.etype == EventType.BLOCK:
            return f"[{t}] {self.actor} заблокував удар"
        if self.etype == EventType.MISS:
            return f"[{t}] {self.actor} промахнувся"
        if self.etype == EventType.ENEMY_HIT:
            return f"[{t}] {self.actor} отримав {v} шкоди від ворога"
        if self.etype == EventType.BURN:
            return f"[{t}] Ворог підпалений! (перк)"
        if self.etype == EventType.STUN:
            return f"[{t}] Ворог оглушений! (перк)"
        if self.etype == EventType.LIFESTEAL:
            return f"[{t}] Крадіжка здоров'я: +{v} HP"
        if self.etype == EventType.HEAL:
            return f"[{t}] {self.actor} зцілився на {v} HP"
        if self.etype == EventType.KILL:
            return f"[{t}] {self.note} — переможений!"
        if self.etype == EventType.DEATH:
            return f"[{t}] {self.actor} загинув..."
        if self.etype == EventType.COMBO:
            return f"[{t}] КОМБО x{v}!"
        return f"[{t}] {self.label}"


@dataclass
class BattleRecord:
    """Повний запис одного бою."""
    enemy_name:    str
    enemy_icon:    str
    player_won:    bool
    duration_sec:  float
    events:        List[BattleEvent] = field(default_factory=list)

    # Підсумкові стати
    damage_dealt:  int = 0
    damage_taken:  int = 0
    hits_landed:   int = 0
    hits_taken:    int = 0
    crits:         int = 0
    blocks:        int = 0
    xp_gained:     int = 0
    gold_gained:   int = 0
    loot:          list = field(default_factory=list)  # (icon, name, qty)


class BattleLogger:
    """Записує події під час одного бою."""

    def __init__(self, player_name: str, enemy_name: str, enemy_icon: str):
        self.player_name = player_name
        self.enemy_name  = enemy_name
        self.enemy_icon  = enemy_icon
        self._events: List[BattleEvent] = []
        self._turn = 0
        self._start_time = 0.0
        self._time = 0.0

    def tick(self, dt: float):
        self._time += dt

    def _next_turn(self) -> int:
        self._turn += 1
        return self._turn

    def hit(self, damage: int, is_crit: bool = False):
        t = self._next_turn()
        if is_crit:
            self._events.append(BattleEvent(EventType.CRIT, t, self.player_name, damage))
        else:
            self._events.append(BattleEvent(EventType.HIT, t, self.player_name, damage))

    def block(self):
        self._events.append(BattleEvent(EventType.BLOCK, self._turn, self.player_name))

    def enemy_hit(self, damage: int):
        t = self._next_turn()
        self._events.append(BattleEvent(EventType.ENEMY_HIT, t, self.player_name, damage))

    def burn(self):
        self._events.append(BattleEvent(EventType.BURN, self._turn, self.player_name))

    def stun(self):
        self._events.append(BattleEvent(EventType.STUN, self._turn, self.player_name))

    def lifesteal(self, amount: int):
        self._events.append(BattleEvent(EventType.LIFESTEAL, self._turn, self.player_name, amount))

    def combo(self, count: int):
        self._events.append(BattleEvent(EventType.COMBO, self._turn, self.player_name, count))

    def kill(self):
        self._events.append(BattleEvent(
            EventType.KILL, self._turn, self.player_name, note=self.enemy_name))

    def death(self):
        self._events.append(BattleEvent(EventType.DEATH, self._turn, self.player_name))

    def build_record(self, player_won: bool,
                     damage_dealt: int, damage_taken: int,
                     hits_landed: int, hits_taken: int,
                     crits: int, blocks: int,
                     xp_gained: int, gold_gained: int,
                     loot: list) -> BattleRecord:
        return BattleRecord(
            enemy_name   = self.enemy_name,
            enemy_icon   = self.enemy_icon,
            player_won   = player_won,
            duration_sec = self._time,
            events       = list(self._events),
            damage_dealt = damage_dealt,
            damage_taken = damage_taken,
            hits_landed  = hits_landed,
            hits_taken   = hits_taken,
            crits        = crits,
            blocks       = blocks,
            xp_gained    = xp_gained,
            gold_gained  = gold_gained,
            loot         = loot,
        )