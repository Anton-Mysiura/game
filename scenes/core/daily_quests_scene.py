"""
Сцена щоденних завдань.
Відображає 3 завдання з прогресом і кнопкою «Забрати».
"""
import pygame
from .base import Scene
from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TEXT, COLOR_TEXT_DIM
from ui.components import Button


class DailyQuestsScene(Scene):
    """Вікно щоденних завдань."""

    def __init__(self, game):
        super().__init__(game)
        self.player = game.player
        self.player.daily_quests.refresh_if_needed()
        self._claim_btns: list[tuple] = []   # (quest_id, Button)
        self._build_buttons()
        self._feedback: str  = ""
        self._fb_timer: float = 0.0

        # Підключаємо renderer (малювання)
        from scenes.ui.daily_quests_renderer import DailyQuestsRenderer
        self._renderer = DailyQuestsRenderer(self)
    def _build_buttons(self):
        self._claim_btns = []
        quests = self.player.daily_quests.quests
        for i, q in enumerate(quests):
            y = 180 + i * 160
            btn = Button(SCREEN_WIDTH // 2 + 100, y + 90, 160, 38, "✅ Забрати",
                         lambda qid=q.quest_id: self._claim(qid))
            self._claim_btns.append((q.quest_id, btn))

        self.close_btn = Button(SCREEN_WIDTH // 2 - 80, 620, 160, 42, "← Назад",
                                lambda: self.game.pop_scene())

    def _claim(self, quest_id: str):
        ok = self.player.daily_quests.claim(quest_id, self.player)
        if ok:
            self._feedback = "🎉 Нагороду отримано!"
            self._fb_timer  = 2.0
            self._build_buttons()
        else:
            self._feedback = "Завдання ще не виконано."
            self._fb_timer  = 1.5

    # ── Events ─────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.pop_scene()
        mp = pygame.mouse.get_pos()
        click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        for _, btn in self._claim_btns:
            btn.update(mp, click)
        self.close_btn.update(mp, click)

    def update(self, dt: float):
        if self._fb_timer > 0:
            self._fb_timer -= dt
        mp = pygame.mouse.get_pos()
        for _, btn in self._claim_btns:
            btn.update(mp, False)
        self.close_btn.update(mp, False)

    # ── Draw ────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)