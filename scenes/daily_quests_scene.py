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
        # Темний overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 8, 6, 220))
        screen.blit(overlay, (0, 0))

        # Панель
        pw, ph = 740, 560
        px, py = (SCREEN_WIDTH - pw) // 2, (SCREEN_HEIGHT - ph) // 2
        pygame.draw.rect(screen, (28, 22, 16), (px, py, pw, ph), border_radius=14)
        pygame.draw.rect(screen, (120, 100, 60), (px, py, pw, ph), 2, border_radius=14)

        # Заголовок
        font_title = pygame.font.Font(None, 46)
        title = font_title.render("📋 Щоденні завдання", True, (220, 200, 100))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, py + 18))

        from datetime import date
        font_sub = pygame.font.Font(None, 22)
        today = font_sub.render(f"Оновлення: {date.today().strftime('%d.%m.%Y')}",
                                True, (120, 110, 80))
        screen.blit(today, (SCREEN_WIDTH // 2 - today.get_width() // 2, py + 58))

        # Квести
        quests = self.player.daily_quests.quests
        font_name = pygame.font.Font(None, 30)
        font_desc = pygame.font.Font(None, 22)
        font_prog = pygame.font.Font(None, 24)

        for i, q in enumerate(quests):
            card_y = py + 90 + i * 150
            card_x = px + 30

            # Карточка
            card_color = (38, 30, 20) if not q.claimed else (20, 38, 20)
            border_col = (80, 180, 80) if q.done and not q.claimed else \
                         (60, 60, 40) if not q.done else (40, 80, 40)
            pygame.draw.rect(screen, card_color, (card_x, card_y, pw - 60, 130), border_radius=10)
            pygame.draw.rect(screen, border_col, (card_x, card_y, pw - 60, 130), 2, border_radius=10)

            # Іконка + назва
            icon_surf = font_name.render(q.icon, True, (220, 200, 120))
            screen.blit(icon_surf, (card_x + 14, card_y + 12))
            name_col = (160, 220, 100) if q.done else (220, 200, 140)
            name_surf = font_name.render(q.title, True, name_col)
            screen.blit(name_surf, (card_x + 48, card_y + 12))

            # Опис
            desc_surf = font_desc.render(q.description, True, (160, 150, 120))
            screen.blit(desc_surf, (card_x + 14, card_y + 46))

            # Прогрес
            bar_x, bar_y = card_x + 14, card_y + 76
            bar_w, bar_h  = pw - 200, 12
            pygame.draw.rect(screen, (40, 40, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            fill_w = int(bar_w * q.progress_pct)
            bar_fill = (80, 200, 80) if q.done else (80, 140, 200)
            if fill_w > 0:
                pygame.draw.rect(screen, bar_fill, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
            pygame.draw.rect(screen, (80, 70, 50), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=6)
            prog_text = font_prog.render(f"{min(q.progress, q.target)}/{q.target}", True, (200, 190, 150))
            screen.blit(prog_text, (bar_x + bar_w + 8, bar_y - 2))

            # Нагороди
            rew_text = font_desc.render(f"💰 {q.reward_gold}  ⭐ {q.reward_xp} XP",
                                        True, (180, 170, 100))
            screen.blit(rew_text, (card_x + 14, card_y + 98))

            # Кнопка
            qid, btn = self._claim_btns[i]
            btn.rect.y = card_y + 78
            btn.rect.x = card_x + pw - 195
            if q.claimed:
                done_surf = font_desc.render("✓ Виконано", True, (80, 200, 80))
                screen.blit(done_surf, (btn.rect.x + 20, btn.rect.y + 10))
            elif q.done:
                btn.draw(screen)
            else:
                # Сірий placeholder
                pygame.draw.rect(screen, (40, 40, 35), btn.rect, border_radius=6)
                nd_surf = font_desc.render("Не виконано", True, (80, 80, 70))
                screen.blit(nd_surf, (btn.rect.x + 12, btn.rect.y + 11))

        # Feedback
        if self._fb_timer > 0 and self._feedback:
            fb_font = pygame.font.Font(None, 32)
            fb_col  = (100, 230, 100) if "🎉" in self._feedback else (220, 160, 80)
            fb_surf = fb_font.render(self._feedback, True, fb_col)
            screen.blit(fb_surf, (SCREEN_WIDTH // 2 - fb_surf.get_width() // 2, py + ph - 60))

        self.close_btn.draw(screen)