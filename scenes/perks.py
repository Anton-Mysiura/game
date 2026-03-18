"""
Екран перегляду отриманих перків гравця.
"""

import pygame
from .base import Scene
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.perk_system import PERKS, RARITY_COLORS, RARITY_NAMES


# Порядок відображення рідкостей (від звичайних до GOD)
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "mythic", "legendary", "god"]

# Розміри картки перку
CARD_W = 340
CARD_H = 80
CARD_GAP = 10
CARDS_PER_COL = 7
COL_GAP = 30


class PerksScene(Scene):
    """Екран перегляду всіх отриманих перків."""

    def __init__(self, game):
        super().__init__(game)

        self.close_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70, 200, 46,
            "← Закрити", lambda: game.pop_scene()
        )

        self.main_panel = Panel(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 100, alpha=True)

        # Скролінг
        self.scroll_y = 0
        self.max_scroll = 0

        # Підготовка згрупованих перків
        self._grouped = self._build_grouped()
        self._flat_cards = self._build_flat_cards()

        # Рахуємо загальну висоту і max_scroll
        total_h = len(self._flat_cards) * (CARD_H + CARD_GAP)
        visible_h = SCREEN_HEIGHT - 210
        self.max_scroll = max(0, total_h - visible_h)

        # Tooltip
        self._hovered_perk = None

        # Онбординг-туторіал
        self._ob_tutorial = self.game.scene_data.pop("onboarding_perk_tutorial", False)
        self._ob_step     = 0    # 0=пояснення що таке перки, 1=рідкості, 2=де купити, 3=готово
        self._ob_anim     = 0.0
        self._ob_done     = False

        if self._ob_tutorial:
            # Міняємо кнопку закриття — після туторіалу виходимо у вільну гру
            self.close_button = Button(
                SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70, 200, 46,
                "Далі →", self._ob_next
            )

    # ──────────────────────────────────────────
    #  Підготовка даних
    # ──────────────────────────────────────────

    def _build_grouped(self) -> dict:
        """Групує perk_id гравця за рідкістю, рахує дублікати."""
        counts: dict[str, int] = {}
        for pid in self.player.perks:
            counts[pid] = counts.get(pid, 0) + 1

        grouped: dict[str, list[tuple]] = {r: [] for r in RARITY_ORDER}
        for pid, cnt in counts.items():
            perk = PERKS.get(pid)
            if perk:
                grouped[perk.rarity].append((perk, cnt))

        # Сортуємо всередині рідкості за назвою
        for r in grouped:
            grouped[r].sort(key=lambda x: x[0].name)

        return grouped

    def _build_flat_cards(self) -> list:
        """Повертає плоский список (perk, count) у порядку рідкостей."""
        result = []
        for rarity in RARITY_ORDER:
            result.extend(self._grouped[rarity])
        return result

    # ──────────────────────────────────────────
    #  Логіка
    # ──────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if self._ob_tutorial:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._ob_next()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mp = pygame.mouse.get_pos()
                self.close_button.update(mp, True)
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.close_button.update(pygame.mouse.get_pos(), True)
            elif event.button == 4:  # scroll up
                self.scroll_y = max(0, self.scroll_y - 40)
            elif event.button == 5:  # scroll down
                self.scroll_y = min(self.max_scroll, self.scroll_y + 40)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                self.game.pop_scene()
            elif event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 40)
            elif event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 40)

    def _ob_next(self):
        """Наступний крок туторіалу перків."""
        if self._ob_step < 3:
            self._ob_step += 1
            self._ob_anim  = 0.0
            if self._ob_step == 3:
                self.close_button.text = "← Готово"
                self.close_button.callback = self._ob_finish
        else:
            self._ob_finish()

    def _ob_finish(self):
        """Завершення туторіалу — вільна гра."""
        self.player.onboarding_done = True
        from game.save_manager import autosave
        autosave(self.player)
        self.game.pop_scene()
        self.game.change_scene("village")

    def update(self, dt: float):
        if self._ob_tutorial:
            self._ob_anim += dt
        self.close_button.update(pygame.mouse.get_pos(), False)
        self._hovered_perk = self._get_hovered_perk()

    def _get_hovered_perk(self):
        mx, my = pygame.mouse.get_pos()
        list_top = 130
        for i, (perk, cnt) in enumerate(self._flat_cards):
            y = list_top + i * (CARD_H + CARD_GAP) - self.scroll_y
            if y + CARD_H < 120 or y > SCREEN_HEIGHT - 100:
                continue
            rect = pygame.Rect(SCREEN_WIDTH // 2 - CARD_W // 2, y, CARD_W, CARD_H)
            if rect.collidepoint(mx, my):
                return (perk, rect)
        return None

    # ──────────────────────────────────────────
    #  Малювання
    # ──────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        # Затемнення під панель
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self.main_panel.draw(screen)

        self._draw_header(screen)
        self._draw_summary_bar(screen)
        self._draw_cards(screen)
        self._draw_scrollbar(screen)

        if self._hovered_perk and not self._ob_tutorial:
            self._draw_tooltip(screen, *self._hovered_perk)

        self.close_button.draw(screen)

        # Онбординг оверлей
        if self._ob_tutorial:
            self._draw_ob_overlay(screen)

    def _draw_ob_overlay(self, screen: pygame.Surface):
        """Покроковий туторіал по перках."""
        import math
        from ui.components import Panel

        STEPS = [
            (
                "✨ Це твої перки",
                [
                    "Перки — постійні покращення твого персонажа.",
                    "Після кожного підвищення рівня ти отримуєш",
                    "вибір з трьох карток. Обираєш одну — вона залишається.",
                    "",
                    "Щойно ти вибрав свій перший перк.",
                    "Він слабкий — але це не назавжди.",
                ],
            ),
            (
                "🎴 Рідкості перків",
                [
                    "Перки мають 5 рідкостей:",
                    "⬜ Звичайний  —  невеликий бонус",
                    "🟩 Незвичайний  —  помітний ефект",
                    "🟦 Рідкісний  —  сильний бонус",
                    "🟪 Епічний  —  дуже потужний",
                    "🟡 Легендарний  —  змінює геймплей",
                    "",
                    "Чим вищий рівень — тим частіше випадають кращі.",
                ],
            ),
            (
                "🔄 Як змінити перк",
                [
                    "Тобі дістався слабкий перк?",
                    "Зайди в Крамницю перків (кнопка в селі).",
                    "",
                    "Там можна:",
                    "• Замінити перк на кращий за золото",
                    "• Перекинути всі картки заново",
                    "",
                    "При першій заміні гарантовано випаде",
                    "перк не нижче Епічного!",
                ],
            ),
            (
                "🎉 Готово!",
                [
                    "Тепер ти знаєш основи.",
                    "",
                    "Наставник іще повернеться —",
                    "є ще багато чого вивчити.",
                    "",
                    "А поки — досліджуй світ.",
                    "Удачі, мандрівнику! ⚔",
                ],
            ),
        ]

        step  = min(self._ob_step, len(STEPS) - 1)
        title_text, lines = STEPS[step]

        # Напівпрозорий оверлей
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        # Панель
        pw, ph = 580, 360
        px = SCREEN_WIDTH  // 2 - pw // 2
        py = SCREEN_HEIGHT // 2 - ph // 2

        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((14, 11, 8, 240))
        pulse = 0.85 + 0.15 * abs(math.sin(self._ob_anim * 1.5))
        border_col = tuple(int(c * pulse) for c in (220, 180, 60))
        pygame.draw.rect(bg, border_col, bg.get_rect(), 2, border_radius=12)
        screen.blit(bg, (px, py))

        fn  = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fsm = assets.get_font(FONT_SIZE_NORMAL)
        fxs = assets.get_font(FONT_SIZE_SMALL)

        # Заголовок
        title_s = fn.render(title_text, True, COLOR_GOLD)
        screen.blit(title_s, (SCREEN_WIDTH // 2 - title_s.get_width() // 2, py + 18))

        # Рядки
        cy = py + 66
        for line in lines:
            if line == "":
                cy += 10
                continue
            col = COLOR_TEXT if not line.startswith("•") else (160, 200, 140)
            if any(line.startswith(c) for c in ("⬜","🟩","🟦","🟪","🟡")):
                col = (200, 180, 120)
            s = fsm.render(line, True, col)
            screen.blit(s, (px + 24, cy))
            cy += 26

        # Лічильник кроків
        steps_total = len(STEPS)
        for i in range(steps_total):
            dot_col = COLOR_GOLD if i == step else (60, 55, 45)
            pygame.draw.circle(screen, dot_col,
                               (SCREEN_WIDTH // 2 - (steps_total - 1) * 12 + i * 24,
                                py + ph - 30), 6)

        # Підказка
        next_lbl = "← Готово" if step == len(STEPS) - 1 else "Далі →"
        hint_s = fxs.render(f"[ {next_lbl} ]", True, (120, 110, 90))
        screen.blit(hint_s,
                    (SCREEN_WIDTH // 2 - hint_s.get_width() // 2, py + ph - 14))

    def _draw_header(self, screen: pygame.Surface):
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("✨ Мої перки", True, COLOR_GOLD)
        shadow = font_title.render("✨ Мої перки", True, (0, 0, 0))
        cx = SCREEN_WIDTH // 2
        screen.blit(shadow, (cx - title.get_width() // 2 + 2, 57))
        screen.blit(title,  (cx - title.get_width() // 2,     55))

        total = len(self.player.perks)
        font_sub = assets.get_font(FONT_SIZE_SMALL)
        sub = font_sub.render(f"Всього отримано: {total}", True, COLOR_TEXT_DIM)
        screen.blit(sub, (cx - sub.get_width() // 2, 100))

    def _draw_summary_bar(self, screen: pygame.Surface):
        """Мінірядок зі зведенням по рідкостях."""
        font = assets.get_font(FONT_SIZE_SMALL)
        cx = SCREEN_WIDTH // 2
        total_w = 0
        parts = []
        for rarity in RARITY_ORDER:
            cnt = len(self._grouped[rarity])
            if cnt:
                label = f"{RARITY_NAMES[rarity]}: {cnt}"
                surf = font.render(label, True, RARITY_COLORS[rarity])
                parts.append(surf)
                total_w += surf.get_width() + 20

        x = cx - total_w // 2
        y = 118
        for surf in parts:
            screen.blit(surf, (x, y))
            x += surf.get_width() + 20

    def _draw_cards(self, screen: pygame.Surface):
        if not self._flat_cards:
            font = assets.get_font(FONT_SIZE_LARGE)
            msg = font.render("Перків поки немає. Підвищуй рівень!", True, COLOR_TEXT_DIM)
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                               SCREEN_HEIGHT // 2 - 20))
            return

        list_top = 138
        clip_rect = pygame.Rect(60, list_top, SCREEN_WIDTH - 120, SCREEN_HEIGHT - list_top - 90)
        screen.set_clip(clip_rect)

        cx = SCREEN_WIDTH // 2
        prev_rarity = None

        for i, (perk, cnt) in enumerate(self._flat_cards):
            y = list_top + i * (CARD_H + CARD_GAP) - self.scroll_y

            # Пропускаємо поза зоною
            if y + CARD_H < list_top or y > SCREEN_HEIGHT - 90:
                continue

            # Розділювач між рідкостями
            if perk.rarity != prev_rarity:
                prev_rarity = perk.rarity
                self._draw_rarity_divider(screen, cx, y - 4, perk.rarity)

            self._draw_perk_card(screen, perk, cnt, cx - CARD_W // 2, y)

        screen.set_clip(None)

    def _draw_rarity_divider(self, screen, cx, y, rarity):
        color = RARITY_COLORS[rarity]
        label = RARITY_NAMES[rarity].upper()
        font = assets.get_font(FONT_SIZE_SMALL, bold=True)
        surf = font.render(label, True, color)
        lw = surf.get_width()
        line_y = y + surf.get_height() // 2
        pygame.draw.line(screen, (*color, 120), (cx - CARD_W // 2, line_y),
                         (cx - lw // 2 - 8, line_y), 1)
        pygame.draw.line(screen, (*color, 120), (cx + lw // 2 + 8, line_y),
                         (cx + CARD_W // 2, line_y), 1)
        screen.blit(surf, (cx - lw // 2, y))

    def _draw_perk_card(self, screen, perk, cnt, x, y):
        color = perk.color
        hovered = (self._hovered_perk is not None and
                   self._hovered_perk[0].perk_id == perk.perk_id)

        # Фон картки
        bg_color = (
            min(color[0] // 5 + 30, 80),
            min(color[1] // 5 + 20, 60),
            min(color[2] // 5 + 25, 70),
        )
        if hovered:
            bg_color = tuple(min(c + 20, 255) for c in bg_color)

        card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        card_surf.fill((*bg_color, 220))
        screen.blit(card_surf, (x, y))

        # Рамка (кольорова за рідкістю)
        border_w = 2 if not hovered else 3
        pygame.draw.rect(screen, color, (x, y, CARD_W, CARD_H), border_w, border_radius=8)

        # Ліва кольорова смужка
        pygame.draw.rect(screen, color, (x, y, 5, CARD_H), border_radius=4)

        font_icon = assets.get_font(FONT_SIZE_LARGE)
        font_name = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_rare = assets.get_font(FONT_SIZE_SMALL)

        # Іконка
        icon_surf = font_icon.render(perk.icon, True, color)
        screen.blit(icon_surf, (x + 14, y + CARD_H // 2 - icon_surf.get_height() // 2))

        # Назва
        name_surf = font_name.render(perk.name, True, COLOR_TEXT)
        screen.blit(name_surf, (x + 58, y + 14))

        # Рідкість
        rare_surf = font_rare.render(perk.rarity_name, True, color)
        screen.blit(rare_surf, (x + 58, y + 44))

        # Кількість (якщо > 1)
        if cnt > 1:
            badge_text = f"×{cnt}"
            badge_surf = font_name.render(badge_text, True, COLOR_GOLD)
            bx = x + CARD_W - badge_surf.get_width() - 12
            screen.blit(badge_surf, (bx, y + CARD_H // 2 - badge_surf.get_height() // 2))

    def _draw_tooltip(self, screen, perk, card_rect):
        """Спливаючий опис при наведенні."""
        font = assets.get_font(FONT_SIZE_SMALL)
        desc_surf = font.render(perk.description, True, COLOR_TEXT)
        pad = 10
        tw = desc_surf.get_width() + pad * 2
        th = desc_surf.get_height() + pad * 2

        tx = card_rect.right + 8
        ty = card_rect.centery - th // 2
        # Не виходити за межі екрана
        if tx + tw > SCREEN_WIDTH - 10:
            tx = card_rect.left - tw - 8
        ty = max(10, min(ty, SCREEN_HEIGHT - th - 10))

        tip_surf = pygame.Surface((tw, th), pygame.SRCALPHA)
        tip_surf.fill((20, 15, 30, 230))
        screen.blit(tip_surf, (tx, ty))
        pygame.draw.rect(screen, perk.color, (tx, ty, tw, th), 1, border_radius=6)
        screen.blit(desc_surf, (tx + pad, ty + pad))

    def _draw_scrollbar(self, screen: pygame.Surface):
        if self.max_scroll <= 0:
            return
        list_top = 138
        list_h = SCREEN_HEIGHT - list_top - 90
        bar_x = SCREEN_WIDTH - 55
        bar_h = list_h
        bar_y = list_top

        # Track
        pygame.draw.rect(screen, (40, 35, 50), (bar_x, bar_y, 8, bar_h), border_radius=4)

        # Thumb
        ratio = list_h / (list_h + self.max_scroll)
        thumb_h = max(30, int(bar_h * ratio))
        thumb_y = bar_y + int((bar_h - thumb_h) * self.scroll_y / self.max_scroll)
        pygame.draw.rect(screen, COLOR_GOLD, (bar_x, thumb_y, 8, thumb_h), border_radius=4)