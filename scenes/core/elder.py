"""
Сцена розмови з Головою села.
Три режими:
  "hub"      — список доступних/активних/виконаних квестів
  "dialog"   — сюжетний діалог перед прийняттям квесту
  "complete" — завершення квесту з показом нагород
"""
import math
import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.quests import (
    QUESTS, get_available_quests, get_active_quests, get_completable_quests,
    accept_quest, complete_quest,
)
from game.data import MATERIALS
from game.save_manager import autosave
from game.reputation import add_reputation, get_tier, get_next_tier, REP_QUEST_COMPLETE

# ── Кольори статусів ──────────────────────────────────────────────
CLR_AVAILABLE  = (100, 220, 255)   # можна взяти
CLR_ACTIVE     = (255, 200, 80)    # активний
CLR_DONE       = (120, 200, 120)   # завершено
CLR_COMPLETABLE = (80, 255, 140)   # готово здати — яскраво-зелений

ROW_H    = 68
LIST_X   = 60
LIST_Y   = 130
LIST_W   = 540
VISIBLE  = 7
INFO_X   = LIST_X + LIST_W + 30
INFO_W   = SCREEN_WIDTH - INFO_X - 40


class ElderScene(SceneWithBackground, SceneWithButtons):

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "village")
        SceneWithButtons.__init__(self, game)

        self.mode      = "hub"      # hub | dialog | complete
        self.sel       = -1
        self.scroll    = 0
        self._anim_t   = 0.0

        # Для режиму dialog
        self._dialog_quest  = None   # Quest
        self._dialog_page   = 0

        # Для режиму complete
        self._complete_quest = None  # Quest (вже завершений)
        self._reward_shown   = False

        self._build_buttons()
        self.main_panel = Panel(30, 30, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60, alpha=True)

    # ── Кнопки ────────────────────────────────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.elder_renderer import ElderRenderer
        self._renderer = ElderRenderer(self)
    def _build_buttons(self):
        self.btn_exit    = Button(40, SCREEN_HEIGHT - 80, 160, 50,
                                  "← Вийти", lambda: self.game.change_scene("village"))
        self.btn_action  = Button(INFO_X, SCREEN_HEIGHT - 90, INFO_W, 50,
                                  "Взяти квест", self._do_action)
        self.btn_next    = Button(SCREEN_WIDTH // 2 + 80, SCREEN_HEIGHT - 90, 200, 50,
                                  "Далі →", self._dialog_next)
        self.btn_prev    = Button(SCREEN_WIDTH // 2 - 290, SCREEN_HEIGHT - 90, 200, 50,
                                  "← Назад", self._dialog_prev)
        self.buttons = [self.btn_exit, self.btn_action, self.btn_next, self.btn_prev]

    # ── Головний хаб ──────────────────────────────────────────────

    def _all_rows(self):
        """Повний список рядків: [('completable'|'active'|'available'|'done', quest)]"""
        rows = []
        completable = {q.quest_id for q in get_completable_quests(self.player)}
        active      = {q.quest_id for q in get_active_quests(self.player)}
        available   = {q.quest_id for q in get_available_quests(self.player)}

        # Порядок: здати > активні > доступні > виконані
        for q in get_completable_quests(self.player):
            rows.append(("completable", q))
        for q in get_active_quests(self.player):
            if q.quest_id not in completable:
                rows.append(("active", q))
        for q in get_available_quests(self.player):
            if q.quest_id not in active and q.quest_id not in completable:
                rows.append(("available", q))
        for qid in sorted(self.player.quests_done):
            q = QUESTS.get(qid)
            if q:
                rows.append(("done", q))
        return rows

    def _selected_quest_and_status(self):
        rows = self._all_rows()
        idx  = self.scroll + self.sel
        if self.sel < 0 or idx >= len(rows):
            return None, None
        return rows[idx][1], rows[idx][0]

    # ── Дії ───────────────────────────────────────────────────────

    def _do_action(self):
        quest, status = self._selected_quest_and_status()
        if not quest:
            return
        if status == "completable":
            self._try_complete(quest)
        elif status == "available":
            self._open_dialog(quest)

    def _open_dialog(self, quest):
        self._dialog_quest = quest
        self._dialog_page  = 0
        self.mode = "dialog"

    def _dialog_next(self):
        if self.mode == "dialog":
            pages = self._dialog_quest.story_lines
            if self._dialog_page < len(pages) - 1:
                self._dialog_page += 1
            else:
                # Остання сторінка — приймаємо квест
                accept_quest(self.player, self._dialog_quest.quest_id)
                autosave(self.player)
                from ui.notifications import notify
                notify(f"📜 Квест прийнято: {self._dialog_quest.title}",
                       kind="quest", duration=3.0)
                self.mode = "hub"
                self.sel  = -1
        elif self.mode == "complete":
            self.mode = "hub"
            self.sel  = -1

    def _dialog_prev(self):
        if self.mode == "dialog" and self._dialog_page > 0:
            self._dialog_page -= 1

    def _try_complete(self, quest):
        result = complete_quest(self.player, quest.quest_id)
        if result:
            # Репутація за квест
            leveled = add_reputation(self.player, REP_QUEST_COMPLETE)
            autosave(self.player)
            from ui.notifications import notify
            parts = []
            if result.reward_gold: parts.append(f"💰+{result.reward_gold}")
            if result.reward_xp:   parts.append(f"⭐+{result.reward_xp}")
            parts.append(f"⭐ Репутація +{REP_QUEST_COMPLETE}")
            notify(f"✦ {result.title} — виконано!",
                   kind="quest", duration=4.0,
                   subtitle="  ".join(parts) if parts else "")
            self._complete_quest = result
            self.mode = "complete"

    # ── Події ─────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and self.mode == "hub":
            mp  = pygame.mouse.get_pos()
            rows = self._all_rows()
            if event.button == 1:
                for i in range(min(VISIBLE, len(rows) - self.scroll)):
                    r = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)
                    if r.collidepoint(mp):
                        self.sel = i; break
            elif event.button == 4:
                self.scroll = max(0, self.scroll - 1); self.sel = -1
            elif event.button == 5:
                mx = max(0, len(rows) - VISIBLE)
                self.scroll = min(mx, self.scroll + 1); self.sel = -1
        # Клавіша Escape
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.mode != "hub":
                self.mode = "hub"
            else:
                self.game.change_scene("village")

    def update(self, dt: float):
        super().update(dt)
        self._anim_t += dt

    # ── Малювання ─────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)