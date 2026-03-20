"""
Рендерер для PerksScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/perks.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets


class PerksRenderer(BaseRenderer):
    """
    Малює PerksScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        # Затемнення під панель
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self.scene.main_panel.draw(screen)

        self._draw_header(screen)
        self._draw_summary_bar(screen)
        self._draw_cards(screen)
        self._draw_scrollbar(screen)

        if self.scene._hovered_perk and not self.scene._ob_tutorial:
            self._draw_tooltip(screen, *self.scene._hovered_perk)

        self.scene.close_button.draw(screen)

        # Онбординг оверлей
        if self.scene._ob_tutorial:
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

        step  = min(self.scene._ob_step, len(STEPS) - 1)
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
        pulse = 0.85 + 0.15 * abs(math.sin(self.scene._ob_anim * 1.5))
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
            cnt = len(self.scene._grouped[rarity])
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
        if not self.scene._flat_cards:
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

        for i, (perk, cnt) in enumerate(self.scene._flat_cards):
            y = list_top + i * (CARD_H + CARD_GAP) - self.scene.scroll_y

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
        hovered = (self.scene._hovered_perk is not None and
                   self.scene._hovered_perk[0].perk_id == perk.perk_id)

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
        if self.scene.max_scroll <= 0:
            return
        list_top = 138
        list_h = SCREEN_HEIGHT - list_top - 90
        bar_x = SCREEN_WIDTH - 55
        bar_h = list_h
        bar_y = list_top

        # Track
        pygame.draw.rect(screen, (40, 35, 50), (bar_x, bar_y, 8, bar_h), border_radius=4)

        # Thumb
        ratio = list_h / (list_h + self.scene.max_scroll)
        thumb_h = max(30, int(bar_h * ratio))
        thumb_y = bar_y + int((bar_h - thumb_h) * self.scene.scroll_y / self.scene.max_scroll)
        pygame.draw.rect(screen, COLOR_GOLD, (bar_x, thumb_y, 8, thumb_h), border_radius=4)