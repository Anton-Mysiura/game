"""
Система навчання (туторіалів).
"""

from typing import Optional
from .data import TUTORIALS


class TutorialManager:
    """Менеджер туторіалів."""

    @staticmethod
    def run_tutorial(player, tutorial_id: str) -> Optional[list]:
        """
        Повертає сторінки туторіалу якщо він ще не переглядався.
        Повертає None якщо вже бачили.
        """
        if tutorial_id in player.tutorial_seen:
            return None

        tut = TUTORIALS.get(tutorial_id)
        if not tut:
            return None

        player.tutorial_seen.add(tutorial_id)
        return tut["pages"]

    @staticmethod
    def flush_tutorial_queue(player) -> list:
        """
        Повертає всі туторіали що накопичились у черзі.
        Очищає чергу після витягування.
        """
        tutorials_to_show = []

        while player.tutorial_queue:
            tid = player.tutorial_queue.pop(0)
            pages = TutorialManager.run_tutorial(player, tid)
            if pages:
                tutorials_to_show.append({
                    "id": tid,
                    "title": TUTORIALS[tid]["title"],
                    "pages": pages
                })

        return tutorials_to_show

    @staticmethod
    def maybe_tutorial(player, tutorial_id: str) -> Optional[list]:
        """
        Зручна обгортка: показує туторіал якщо ще не бачили.
        Повертає сторінки або None.
        """
        if tutorial_id not in player.tutorial_seen:
            return TutorialManager.run_tutorial(player, tutorial_id)
        return None

    @staticmethod
    def trigger_tutorial(player, tutorial_id: str):
        """
        Додає туторіал в чергу (для показу пізніше).
        Використовується коли туторіал треба показати не зараз.
        """
        if tutorial_id not in player.tutorial_seen and tutorial_id not in player.tutorial_queue:
            player.tutorial_queue.append(tutorial_id)