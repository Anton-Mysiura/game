"""
Система досягнень (achievements).
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Achievement:
    """Досягнення."""
    achievement_id: str
    name: str
    description: str
    icon: str
    reward_gold: int = 0
    hidden: bool = False  # Приховане до розблокування

    # Умови для розблокування (буде перевірятись програмно)
    def check_unlock(self, player) -> bool:
        """Перевіряє чи досягнення розблоковано. Переопределяється в підкласах."""
        return False


# ══════════════════════════════════════════
#  ДОСЯГНЕННЯ
# ══════════════════════════════════════════

ACHIEVEMENTS = {
    # ── Бойові ──
    "first_blood": Achievement(
        "first_blood",
        "Перша кров",
        "Переможи свого першого ворога",
        "⚔",
        reward_gold=10
    ),
    "goblin_slayer": Achievement(
        "goblin_slayer",
        "Винищувач гоблінів",
        "Переможи гобліна",
        "👺",
        reward_gold=15
    ),
    "orc_hunter": Achievement(
        "orc_hunter",
        "Мисливець на орків",
        "Переможи орка",
        "🧟",
        reward_gold=20
    ),
    "knight_killer": Achievement(
        "knight_killer",
        "Вбивця лицарів",
        "Переможи Темного Лицаря",
        "🏰",
        reward_gold=30
    ),
    "dragon_slayer": Achievement(
        "dragon_slayer",
        "Драконобійця",
        "Переможи дракона Морвета",
        "🐉",
        reward_gold=100,
        hidden=True
    ),

    # ── Прогрес ──
    "level_5": Achievement(
        "level_5",
        "Досвідчений воїн",
        "Досягни 5 рівня",
        "⬆",
        reward_gold=25
    ),
    "level_10": Achievement(
        "level_10",
        "Ветеран",
        "Досягни 10 рівня",
        "🌟",
        reward_gold=50,
        hidden=True
    ),

    # ── Багатство ──
    "rich": Achievement(
        "rich",
        "Багатій",
        "Накопич 500 золота",
        "💰",
        reward_gold=50
    ),
    "very_rich": Achievement(
        "very_rich",
        "Дуже багатій",
        "Накопич 1000 золота",
        "💎",
        reward_gold=100,
        hidden=True
    ),

    # ── Крафт ──
    "first_craft": Achievement(
        "first_craft",
        "Перший крафт",
        "Створи свою першу зброю",
        "🔨",
        reward_gold=20
    ),
    "blacksmith": Achievement(
        "blacksmith",
        "Коваль",
        "Створи 5 предметів",
        "⚒",
        reward_gold=50
    ),
    "master_blacksmith": Achievement(
        "master_blacksmith",
        "Майстер-коваль",
        "Створи 10 предметів",
        "🛠",
        reward_gold=100,
        hidden=True
    ),

    # ── Колекціонування ──
    "collector": Achievement(
        "collector",
        "Колекціонер",
        "Отримай всі кресленники",
        "📜",
        reward_gold=75
    ),
    "hoarder": Achievement(
        "hoarder",
        "Накопичувач",
        "Маю 20 предметів в інвентарі",
        "🎒",
        reward_gold=30
    ),

    # ── Шопінг ──
    "shopaholic": Achievement(
        "shopaholic",
        "Шопоголік",
        "Витрать 300 золота в крамниці",
        "🏪",
        reward_gold=40
    ),

    # ── Виживання ──
    "survivor": Achievement(
        "survivor",
        "Виживальник",
        "Вижий з 1 HP",
        "💚",
        reward_gold=25
    ),
    "immortal": Achievement(
        "immortal",
        "Безсмертний",
        "Пройди гру без смертей",
        "👑",
        reward_gold=200,
        hidden=True
    ),

    # ── Шахта ──────────────────────────────────────────────────────
    "mine_first": Achievement(
        "mine_first",
        "Перший спуск",
        "Відправ шахтаря вперше",
        "⛏",
        reward_gold=20,
    ),
    "mine_collector": Achievement(
        "mine_collector",
        "Збирач руд",
        "Отримай 50 руд від шахтаря",
        "🪨",
        reward_gold=40,
    ),
    "mine_deep": Achievement(
        "mine_deep",
        "В надра землі",
        "Відправ шахтаря на Глибину",
        "💎",
        reward_gold=60,
    ),
    "mine_accident": Achievement(
        "mine_accident",
        "Нещасний випадок",
        "Шахтар не повернувся...",
        "💀",
        reward_gold=0,
        hidden=True,
    ),
    "mine_lucky": Achievement(
        "mine_lucky",
        "Щасливчик",
        "Отримай легендарну руду від шахтаря",
        "🌋",
        reward_gold=100,
        hidden=True,
    ),
}


class AchievementManager:
    """Менеджер досягнень."""

    @staticmethod
    def check_and_unlock(player, achievement_id: str) -> bool:
        """
        Перевіряє і розблоковує досягнення.
        Повертає True якщо досягнення щойно розблоковано.
        """
        if achievement_id in player.achievements_unlocked:
            return False  # Вже розблоковано

        achievement = ACHIEVEMENTS.get(achievement_id)
        if not achievement:
            return False

        # Перевірка умов (програмно)
        unlocked = False

        if achievement_id == "first_blood":
            unlocked = player.enemies_killed >= 1
        elif achievement_id == "goblin_slayer":
            unlocked = player.goblins_killed >= 1
        elif achievement_id == "orc_hunter":
            unlocked = player.orcs_killed >= 1
        elif achievement_id == "knight_killer":
            unlocked = player.knights_killed >= 1
        elif achievement_id == "dragon_slayer":
            unlocked = player.dragons_killed >= 1
        elif achievement_id == "level_5":
            unlocked = player.level >= 5
        elif achievement_id == "level_10":
            unlocked = player.level >= 10
        elif achievement_id == "rich":
            unlocked = player.total_gold_earned >= 500
        elif achievement_id == "very_rich":
            unlocked = player.total_gold_earned >= 1000
        elif achievement_id == "first_craft":
            unlocked = player.items_crafted >= 1
        elif achievement_id == "blacksmith":
            unlocked = player.items_crafted >= 5
        elif achievement_id == "master_blacksmith":
            unlocked = player.items_crafted >= 10
        elif achievement_id == "collector":
            from .data import BLUEPRINTS
            unlocked = len({ob.blueprint_id for ob in player.blueprints}) >= len(BLUEPRINTS)
        elif achievement_id == "hoarder":
            unlocked = len(player.inventory) >= 20
        elif achievement_id == "shopaholic":
            unlocked = player.gold_spent >= 300
        elif achievement_id == "survivor":
            unlocked = player.survived_at_1hp
        elif achievement_id == "immortal":
            unlocked = player.deaths == 0 and player.dragons_killed >= 1

        # ── Шахта ────────────────────────────────────────────────
        elif achievement_id == "mine_first":
            unlocked = getattr(player, "mine_trips", 0) >= 1
        elif achievement_id == "mine_collector":
            unlocked = getattr(player, "mine_ores_collected", 0) >= 50
        elif achievement_id == "mine_deep":
            unlocked = getattr(player, "mine_deep_trips", 0) >= 1
        elif achievement_id == "mine_accident":
            unlocked = getattr(player, "mine_accidents", 0) >= 1
        elif achievement_id == "mine_lucky":
            unlocked = getattr(player, "mine_legendary_found", False)

        if unlocked:
            player.achievements_unlocked.add(achievement_id)
            player.achievements_new.append(achievement_id)

            # Нагорода
            if achievement.reward_gold > 0:
                player.gold += achievement.reward_gold

            return True

        return False

    @staticmethod
    def check_all(player):
        """Перевіряє всі досягнення."""
        newly_unlocked = []
        for achievement_id in ACHIEVEMENTS.keys():
            if AchievementManager.check_and_unlock(player, achievement_id):
                newly_unlocked.append(achievement_id)
        return newly_unlocked

    @staticmethod
    def get_progress(player) -> dict:
        """Повертає прогрес по досягненнях."""
        total = len(ACHIEVEMENTS)
        unlocked = len(player.achievements_unlocked)
        return {
            "total": total,
            "unlocked": unlocked,
            "percentage": int((unlocked / total) * 100) if total > 0 else 0
        }