"""
Система щоденних завдань.
3 завдання оновлюються щодня о 00:00.
Прогрес скидається при новому дні.
"""
import random
from datetime import date
from dataclasses import dataclass, field


@dataclass
class DailyQuest:
    quest_id:    str
    title:       str
    icon:        str
    description: str
    # Тип: "kill_enemy", "kill_crits", "win_nodamage", "use_dodge",
    #       "use_parry", "deal_damage", "win_battles", "use_potion"
    quest_type:  str
    target:      int        # скільки треба
    reward_gold: int
    reward_xp:   int
    progress:    int = 0
    claimed:     bool = False

    @property
    def done(self) -> bool:
        return self.progress >= self.target

    @property
    def progress_pct(self) -> float:
        return min(1.0, self.progress / max(1, self.target))


# ── Пул завдань ────────────────────────────────────────────────
_POOL = [
    # kill enemies
    ("kill_goblin",    "Мисливець на гоблінів", "🗡",
     "Вбий гоблінів",                "kill_goblin",    5,  80, 120),
    ("kill_orc",       "Ворог орків",           "⚔",
     "Переможи орків",               "kill_orc",       3, 120, 180),
    ("kill_knight",    "Лицарська честь",       "🛡",
     "Здолай темних лицарів",        "kill_knight",    2, 200, 280),
    # combat mechanics
    ("deal_500",       "Розрив шкоди",          "💥",
     "Нанеси 500 урону за один бій", "deal_damage",  500, 100, 150),
    ("crit_3",         "Снайпер",               "🎯",
     "Влучи крит. ударом 3 рази",    "crit_hit",       3,  90, 130),
    ("dodge_5",        "Тінь вітру",            "💨",
     "Ухились 5 разів",              "use_dodge",      5,  90, 120),
    ("parry_2",        "Майстер блоку",         "⚔",
     "Виконай 2 парирування",        "use_parry",      2, 150, 200),
    ("win_nodmg",      "Бездоганний",           "✨",
     "Виграй бій без отримання шкоди","win_nodamage",  1, 250, 350),
    ("win_3",          "Переможець",            "🏆",
     "Виграй 3 бої підряд",          "win_battles",    3, 130, 180),
    ("potion_use",     "Алхімік",               "🧪",
     "Використай 2 зілля в бою",     "use_potion",     2,  70, 100),
    ("heavy_kill",     "Нищівний удар",         "💪",
     "Вбий ворога зарядженим ударом","heavy_kill",     1, 180, 240),
    ("bleed_3",        "Кривавий шлях",         "🩸",
     "Накладіть кровотечу 3 рази",   "apply_bleed",    3, 110, 160),
]


def _make_quest(entry) -> DailyQuest:
    qid, title, icon, desc, qtype, target, gold, xp = entry
    return DailyQuest(
        quest_id=qid, title=title, icon=icon, description=desc,
        quest_type=qtype, target=target,
        reward_gold=gold, reward_xp=xp
    )


class DailyQuestManager:
    """Зберігається у player.daily_quests."""

    def __init__(self):
        self.today_str:  str              = ""
        self.quests:     list[DailyQuest] = []
        self._refreshed: bool             = False

    def refresh_if_needed(self):
        """Перегенерує завдання якщо новий день."""
        today = date.today().isoformat()
        if self.today_str == today and self.quests:
            return
        self.today_str = today
        # Беремо 3 різні
        sample = random.sample(_POOL, 3)
        self.quests = [_make_quest(e) for e in sample]

    # ── Оновлення прогресу ─────────────────────────────────────
    def on_battle_end(self, result: dict):
        """Викликати після кожного бою.
        result: {won, enemy_name, damage_dealt, crits, dodges,
                  parries, potions_used, no_damage_taken,
                  heavy_kill, bleed_applied}
        """
        self.refresh_if_needed()
        won         = result.get("won", False)
        enemy       = result.get("enemy_name", "").lower()

        for q in self.quests:
            if q.claimed:
                continue
            qt = q.quest_type
            if qt == "kill_goblin" and won and "гоблін" in enemy:
                q.progress += 1
            elif qt == "kill_orc" and won and "орк" in enemy:
                q.progress += 1
            elif qt == "kill_knight" and won and "лицар" in enemy:
                q.progress += 1
            elif qt == "deal_damage":
                q.progress += result.get("damage_dealt", 0)
            elif qt == "crit_hit":
                q.progress += result.get("crits", 0)
            elif qt == "use_dodge":
                q.progress += result.get("dodges", 0)
            elif qt == "use_parry":
                q.progress += result.get("parries", 0)
            elif qt == "win_nodamage" and won and result.get("no_damage_taken"):
                q.progress += 1
            elif qt == "win_battles" and won:
                q.progress += 1
            elif qt == "use_potion":
                q.progress += result.get("potions_used", 0)
            elif qt == "heavy_kill" and won and result.get("heavy_kill"):
                q.progress += 1
            elif qt == "apply_bleed":
                q.progress += result.get("bleed_applied", 0)
            # Обрізаємо до ліміту
            q.progress = min(q.progress, q.target)

    def claim(self, quest_id: str, player) -> bool:
        """Забирає нагороду. Повертає True якщо успішно."""
        for q in self.quests:
            if q.quest_id == quest_id and q.done and not q.claimed:
                q.claimed = True
                player.gold += q.reward_gold
                player.gain_xp(q.reward_xp)
                return True
        return False

    # ── Серіалізація ───────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "today": self.today_str,
            "quests": [
                {"id": q.quest_id, "progress": q.progress, "claimed": q.claimed}
                for q in self.quests
            ]
        }

    def from_dict(self, data: dict):
        saved_today = data.get("today", "")
        today       = date.today().isoformat()
        if saved_today != today:
            # Новий день — скидаємо
            self.today_str = ""
            self.quests    = []
            self.refresh_if_needed()
            return
        self.today_str = today
        # Підтягуємо прогрес зі збереження
        progress_map = {
            e["id"]: (e["progress"], e["claimed"])
            for e in data.get("quests", [])
        }
        # Генеруємо ті ж завдання (з тим самим seed)
        rng = random.Random(saved_today)
        sample = rng.sample(_POOL, 3)
        self.quests = [_make_quest(e) for e in sample]
        for q in self.quests:
            if q.quest_id in progress_map:
                q.progress, q.claimed = progress_map[q.quest_id]