"""
Сцена досягнень зі скролом.
"""

import pygame
from .base import Scene
from ui.components import Button, Panel, ProgressBar
from ui.constants import *
from ui.assets import assets
from game.achievements import ACHIEVEMENTS, AchievementManager

# Розміри зони списку
LIST_X      = 60
LIST_Y      = 210
LIST_W      = 520
LIST_H      = SCREEN_HEIGHT - 290   # висота видимої зони
ITEM_H      = 78
ITEM_GAP    = 6
SCROLL_SPD  = 40


class AchievementsScene(Scene):
    """Екран досягнень."""

    def __init__(self, game):
        super().__init__(game)

        self.close_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 68, 200, 50,
            "Закрити", lambda: game.pop_scene()
        )
        self.main_panel = Panel(30, 30, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 70, alpha=True)
        self.progress   = AchievementManager.get_progress(self.player)

        # Тільки видимі досягнення
        self.achievement_list = [
            (aid, ach) for aid, ach in ACHIEVEMENTS.items()
            if not ach.hidden or aid in self.player.achievements_unlocked
        ]

        self.selected_index = -1
        self.scroll_y       = 0       # поточний зсув скролу (пікселі)
        self.scroll_target  = 0       # плавний скрол
        self._max_scroll     = max(0, len(self.achievement_list) * (ITEM_H + ITEM_GAP) - LIST_H)

        # Clip rect для списку
        self.list_clip = pygame.Rect(LIST_X, LIST_Y, LIST_W, LIST_H)

    # ─────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Скрол колесом
            if event.button == 4:   # вгору
                self.scroll_target = max(0, self.scroll_target - SCROLL_SPD * 3)
            elif event.button == 5: # вниз
                self.scroll_target = min(self._max_scroll, self.scroll_target + SCROLL_SPD * 3)

            elif event.button == 1:
                self.close_button.update(mouse_pos, True)

                # Клік по досягненню (тільки якщо в зоні списку)
                if self.list_clip.collidepoint(mouse_pos):
                    rel_y = mouse_pos[1] - LIST_Y + self.scroll_y
                    idx = int(rel_y // (ITEM_H + ITEM_GAP))
                    if 0 <= idx < len(self.achievement_list):
                        self.selected_index = idx

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.scroll_target = min(self._max_scroll, self.scroll_target + SCROLL_SPD)
            elif event.key == pygame.K_UP:
                self.scroll_target = max(0, self.scroll_target - SCROLL_SPD)
            elif event.key == pygame.K_ESCAPE:
                self.game.pop_scene()

    # ─────────────────────────────────────────
    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.close_button.update(mouse_pos, False)

        # Плавний скрол
        diff = self.scroll_target - self.scroll_y
        self.scroll_y += diff * min(1.0, dt * 14)

    # ─────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        # Затемнення
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        self.main_panel.draw(screen)

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("🏆 Досягнення", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 45))

        # Прогрес
        font_prog = assets.get_font(FONT_SIZE_MEDIUM)
        prog_text = f"{self.progress['unlocked']}/{self.progress['total']} ({self.progress['percentage']}%)"
        prog_surf = font_prog.render(prog_text, True, COLOR_TEXT)
        screen.blit(prog_surf, (SCREEN_WIDTH // 2 - prog_surf.get_width() // 2, 115))

        pb = ProgressBar(SCREEN_WIDTH // 2 - 300, 148, 600, 22, COLOR_XP, show_text=False)
        pb.draw(screen, self.progress['unlocked'], self.progress['total'])

        # ── Список зі скролом ──
        # Малюємо у Surface-буфер, потім blit з clip
        total_h   = len(self.achievement_list) * (ITEM_H + ITEM_GAP)
        list_surf = pygame.Surface((LIST_W, max(total_h, LIST_H)), pygame.SRCALPHA)
        list_surf.fill((0, 0, 0, 0))

        font_name = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_desc = assets.get_font(FONT_SIZE_SMALL)
        font_icon = assets.get_font(38)
        mouse_pos = pygame.mouse.get_pos()

        for i, (ach_id, ach) in enumerate(self.achievement_list):
            unlocked = ach_id in self.player.achievements_unlocked
            iy = i * (ITEM_H + ITEM_GAP)
            item_rect = pygame.Rect(0, iy, LIST_W - 16, ITEM_H)

            # Перевіряємо hover (у координатах екрану)
            screen_item = pygame.Rect(LIST_X, LIST_Y + iy - self.scroll_y, LIST_W - 16, ITEM_H)
            hovered = screen_item.collidepoint(mouse_pos) and self.list_clip.collidepoint(mouse_pos)

            if i == self.selected_index:
                bg = COLOR_BTN_PRESSED
            elif hovered:
                bg = COLOR_BTN_HOVER
            elif unlocked:
                bg = (45, 38, 55)
            else:
                bg = (28, 23, 18)

            pygame.draw.rect(list_surf, bg, item_rect, border_radius=8)
            border = COLOR_GOLD if unlocked else (70, 60, 80)
            pygame.draw.rect(list_surf, border, item_rect, 2, border_radius=8)

            # Іконка
            icon_surf = font_icon.render(ach.icon, True, COLOR_TEXT if unlocked else COLOR_TEXT_DIM)
            list_surf.blit(icon_surf, (12, iy + 16))

            # Назва
            nc = COLOR_GOLD if unlocked else COLOR_TEXT_DIM
            list_surf.blit(font_name.render(ach.name, True, nc), (62, iy + 8))

            # Опис
            dc = COLOR_TEXT if unlocked else COLOR_TEXT_DIM
            list_surf.blit(font_desc.render(ach.description, True, dc), (62, iy + 32))

            # Нагорода
            if ach.reward_gold > 0:
                rc = COLOR_GOLD if unlocked else COLOR_TEXT_DIM
                list_surf.blit(font_desc.render(f"+{ach.reward_gold} 🪙", True, rc), (62, iy + 52))

        # Blit видимої частини
        screen.blit(list_surf, (LIST_X, LIST_Y),
                    area=pygame.Rect(0, int(self.scroll_y), LIST_W, LIST_H))

        # Смуга скролу
        self._draw_scrollbar(screen)

        # ── Права панель (деталі) ──
        info_x = LIST_X + LIST_W + 20
        info_w = SCREEN_WIDTH - info_x - 50
        info_panel = Panel(info_x, LIST_Y, info_w, LIST_H, alpha=True)
        info_panel.draw(screen)

        if self.selected_index != -1 and self.selected_index < len(self.achievement_list):
            ach_id, ach = self.achievement_list[self.selected_index]
            unlocked = ach_id in self.player.achievements_unlocked

            font_big_icon = assets.get_font(72)
            font_big_name = assets.get_font(FONT_SIZE_LARGE, bold=True)
            font_big_desc = assets.get_font(FONT_SIZE_NORMAL)

            cx = info_x + info_w // 2
            big_icon = font_big_icon.render(ach.icon, True, COLOR_TEXT if unlocked else COLOR_TEXT_DIM)
            screen.blit(big_icon, (cx - big_icon.get_width() // 2, LIST_Y + 30))

            big_name = font_big_name.render(ach.name, True, COLOR_GOLD if unlocked else COLOR_TEXT_DIM)
            screen.blit(big_name, (cx - big_name.get_width() // 2, LIST_Y + 130))

            # Опис з переносом
            words = ach.description.split()
            lines, line = [], ""
            for w in words:
                test = (line + " " + w).strip()
                if font_big_desc.size(test)[0] < info_w - 30:
                    line = test
                else:
                    lines.append(line)
                    line = w
            if line:
                lines.append(line)

            ty = LIST_Y + 175
            for ln in lines:
                ls = font_big_desc.render(ln, True, COLOR_TEXT)
                screen.blit(ls, (cx - ls.get_width() // 2, ty))
                ty += 28

            status_text  = "✅ Розблоковано" if unlocked else "🔒 Заблоковано"
            status_color = COLOR_SUCCESS if unlocked else COLOR_ERROR
            ss = font_big_desc.render(status_text, True, status_color)
            screen.blit(ss, (cx - ss.get_width() // 2, ty + 10))

            if ach.reward_gold > 0:
                rl = font_big_desc.render("Нагорода:", True, COLOR_TEXT)
                screen.blit(rl, (cx - rl.get_width() // 2, ty + 45))
                rv = font_big_name.render(f"+{ach.reward_gold} 🪙", True, COLOR_GOLD)
                screen.blit(rv, (cx - rv.get_width() // 2, ty + 75))
        else:
            font_hint = assets.get_font(FONT_SIZE_SMALL)
            hint = font_hint.render("← Вибери досягнення", True, COLOR_TEXT_DIM)
            screen.blit(hint, (info_x + info_w // 2 - hint.get_width() // 2,
                                LIST_Y + LIST_H // 2))

        self.close_button.draw(screen)

    def _draw_scrollbar(self, screen: pygame.Surface):
        """Малює смугу прокрутки."""
        if self._max_scroll <= 0:
            return

        bar_x     = LIST_X + LIST_W - 10
        bar_track = pygame.Rect(bar_x, LIST_Y, 8, LIST_H)
        pygame.draw.rect(screen, (40, 35, 50), bar_track, border_radius=4)

        # Розмір повзунка
        visible_ratio = LIST_H / (LIST_H + self._max_scroll)
        thumb_h = max(30, int(LIST_H * visible_ratio))
        thumb_y = LIST_Y + int((LIST_H - thumb_h) * (self.scroll_y / max(1, self._max_scroll)))
        thumb   = pygame.Rect(bar_x, thumb_y, 8, thumb_h)
        pygame.draw.rect(screen, COLOR_GOLD, thumb, border_radius=4)