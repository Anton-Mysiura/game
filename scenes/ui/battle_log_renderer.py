"""
Рендерер для BattleLogScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/battle_log_scene.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets


class BattleLogRenderer(BaseRenderer):
    """
    Малює BattleLogScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        # Затемнення
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        Panel(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80, alpha=True).draw(screen)

        if not self.scene.record:
            self._draw_empty(screen)
            self.scene.close_btn.draw(screen)
            return

        self._draw_header(screen)
        self._draw_summary(screen)
        self._draw_filter_btns(screen)
        self._draw_event_list(screen)
        self._draw_loot(screen)
        self.scene.close_btn.draw(screen)

    def _draw_empty(self, screen):
        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        t = font.render("Журнал порожній — зіграй битву!", True, COLOR_TEXT_DIM)
        screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2))

    def _draw_header(self, screen):
        r = self.scene.record
        result_txt = "⚔ ПЕРЕМОГА" if r.player_won else "💀 ПОРАЗКА"
        result_clr = (100, 220, 100) if r.player_won else (220, 80, 80)

        font_big  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_med  = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm   = assets.get_font(FONT_SIZE_SMALL)

        # Результат
        res_surf = font_big.render(result_txt, True, result_clr)
        screen.blit(res_surf, (LIST_X, 55))

        # Ворог
        enemy_txt = font_med.render(
            f"vs  {r.enemy_icon}  {r.enemy_name}", True, COLOR_GOLD)
        screen.blit(enemy_txt, (LIST_X + res_surf.get_width() + 30, 68))

        # Час
        secs = int(r.duration_sec)
        time_txt = font_sm.render(
            f"⏱ {secs // 60:02d}:{secs % 60:02d}", True, COLOR_TEXT_DIM)
        screen.blit(time_txt, (SCREEN_WIDTH - 200, 68))

        pygame.draw.line(screen, COLOR_GOLD, (LIST_X, 115), (SCREEN_WIDTH - LIST_X, 115), 1)

    def _draw_summary(self, screen):
        """Рядок підсумкових стат прямо під заголовком."""
        r = self.scene.record
        font = assets.get_font(FONT_SIZE_SMALL)

        stats = [
            ("⚔ Завдано",  f"{r.damage_dealt}",  (220, 200, 100)),
            ("🩸 Отримано", f"{r.damage_taken}",  (220, 100, 100)),
            ("🎯 Попадань", f"{r.hits_landed}",   COLOR_TEXT),
            ("💥 Критів",   f"{r.crits}",          (255, 200, 50)),
            ("🛡 Блоків",   f"{r.blocks}",          (100, 180, 255)),
            ("✨ XP",        f"+{r.xp_gained}",     (180, 130, 255)),
            ("💰 Золото",   f"+{r.gold_gained}",   COLOR_GOLD),
        ]

        col_w = (SCREEN_WIDTH - LIST_X * 2) // len(stats)
        for i, (lbl, val, clr) in enumerate(stats):
            x = LIST_X + i * col_w

            # Значення — велике і кольорове
            v_surf = assets.get_font(FONT_SIZE_MEDIUM, bold=True).render(val, True, clr)
            screen.blit(v_surf, (x, 122))

            # Підпис — маленький і сірий
            l_surf = font.render(lbl, True, COLOR_TEXT_DIM)
            screen.blit(l_surf, (x, 148))

        pygame.draw.line(screen, (60, 55, 50),
                         (LIST_X, 170), (SCREEN_WIDTH - LIST_X, 170), 1)

    def _draw_filter_btns(self, screen):
        for i, btn in enumerate(self.scene._filter_btns):
            # Активний фільтр — підсвічуємо рамкою
            btn.draw(screen)
            if i == self.scene._filter_idx:
                r = pygame.Rect(btn.rect.x - 2, btn.rect.y - 2,
                                btn.rect.width + 4, btn.rect.height + 4)
                pygame.draw.rect(screen, COLOR_GOLD, r, 2, border_radius=6)

        count_txt = assets.get_font(FONT_SIZE_SMALL).render(
            f"{len(self.scene._filtered)} подій", True, COLOR_TEXT_DIM)
        screen.blit(count_txt, (LIST_X + len(FILTERS) * 138 + 10, 159))

    def _draw_event_list(self, screen):
        """Скролабельний список подій."""
        clip_rect = pygame.Rect(LIST_X, LIST_Y, LIST_W, VISIBLE_H)
        screen.set_clip(clip_rect)

        font     = assets.get_font(FONT_SIZE_SMALL)
        font_ico = assets.get_font(FONT_SIZE_NORMAL)

        y_base = LIST_Y - self.scene._scroll_y
        for i, ev in enumerate(self.scene._filtered):
            y = y_base + i * ROW_H
            if y + ROW_H < LIST_Y or y > LIST_Y + VISIBLE_H:
                continue

            # Рядок з чергуванням фону
            row_surf = pygame.Surface((LIST_W, ROW_H - 2), pygame.SRCALPHA)
            row_surf.fill((40, 35, 30, 180) if i % 2 == 0 else (30, 27, 24, 120))
            screen.blit(row_surf, (LIST_X, y))

            # Іконка
            ico = font_ico.render(ev.icon, True, ev.color)
            screen.blit(ico, (LIST_X + 6, y + 4))

            # Текст події
            txt = font.render(ev.to_text(), True, ev.color)
            screen.blit(txt, (LIST_X + 36, y + 9))

        screen.set_clip(None)

        # Рамка списку
        pygame.draw.rect(screen, (80, 70, 60), clip_rect, 1, border_radius=4)

        # Скролбар
        if self.scene._max_scroll > 0:
            track_h = VISIBLE_H
            thumb_h = max(30, int(track_h * VISIBLE_H / (VISIBLE_H + self.scene._max_scroll)))
            thumb_y = LIST_Y + int((track_h - thumb_h) * self.scene._scroll_y / self.scene._max_scroll)
            bar_x   = LIST_X + LIST_W + 6
            pygame.draw.rect(screen, (50, 45, 40),
                             pygame.Rect(bar_x, LIST_Y, 8, VISIBLE_H), border_radius=4)
            pygame.draw.rect(screen, COLOR_GOLD,
                             pygame.Rect(bar_x, thumb_y, 8, thumb_h), border_radius=4)

            hint = assets.get_font(FONT_SIZE_SMALL).render("↑↓ або колесо миші", True, COLOR_TEXT_DIM)
            screen.blit(hint, (LIST_X, LIST_Y + VISIBLE_H + 6))

    def _draw_loot(self, screen):
        """Здобич внизу праворуч."""
        r = self.scene.record
        if not r.loot:
            return

        loot_x = SCREEN_WIDTH - 300
        loot_y = LIST_Y

        font_h = assets.get_font(FONT_SIZE_SMALL, bold=True)
        font   = assets.get_font(FONT_SIZE_SMALL)

        screen.blit(font_h.render("🎁 Здобич:", True, COLOR_GOLD), (loot_x, loot_y))
        loot_y += 24

        for icon, name, qty in r.loot:
            qty_txt = f" x{qty}" if qty > 1 else ""
            row = font.render(f"{icon} {name}{qty_txt}", True, COLOR_TEXT)
            screen.blit(row, (loot_x, loot_y))
            loot_y += 22