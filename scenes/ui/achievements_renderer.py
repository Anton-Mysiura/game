"""
Рендерер для AchievementsScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/achievements.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel, ProgressBar
from ui.constants import *
from ui.assets import assets


class AchievementsRenderer(BaseRenderer):
    """
    Малює AchievementsScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        # Затемнення
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        self.scene.main_panel.draw(screen)

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("🏆 Досягнення", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 45))

        # Прогрес
        font_prog = assets.get_font(FONT_SIZE_MEDIUM)
        prog_text = f"{self.scene.progress['unlocked']}/{self.scene.progress['total']} ({self.scene.progress['percentage']}%)"
        prog_surf = font_prog.render(prog_text, True, COLOR_TEXT)
        screen.blit(prog_surf, (SCREEN_WIDTH // 2 - prog_surf.get_width() // 2, 115))

        pb = ProgressBar(SCREEN_WIDTH // 2 - 300, 148, 600, 22, COLOR_XP, show_text=False)
        pb.draw(screen, self.scene.progress['unlocked'], self.scene.progress['total'])

        # ── Список зі скролом ──
        # Малюємо у Surface-буфер, потім blit з clip
        total_h   = len(self.scene.achievement_list) * (ITEM_H + ITEM_GAP)
        list_surf = pygame.Surface((LIST_W, max(total_h, LIST_H)), pygame.SRCALPHA)
        list_surf.fill((0, 0, 0, 0))

        font_name = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_desc = assets.get_font(FONT_SIZE_SMALL)
        font_icon = assets.get_font(38)
        mouse_pos = pygame.mouse.get_pos()

        for i, (ach_id, ach) in enumerate(self.scene.achievement_list):
            unlocked = ach_id in self.player.achievements_unlocked
            iy = i * (ITEM_H + ITEM_GAP)
            item_rect = pygame.Rect(0, iy, LIST_W - 16, ITEM_H)

            # Перевіряємо hover (у координатах екрану)
            screen_item = pygame.Rect(LIST_X, LIST_Y + iy - self.scene.scroll_y, LIST_W - 16, ITEM_H)
            hovered = screen_item.collidepoint(mouse_pos) and self.scene.list_clip.collidepoint(mouse_pos)

            if i == self.scene.selected_index:
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
                    area=pygame.Rect(0, int(self.scene.scroll_y), LIST_W, LIST_H))

        # Смуга скролу
        self._draw_scrollbar(screen)

        # ── Права панель (деталі) ──
        info_x = LIST_X + LIST_W + 20
        info_w = SCREEN_WIDTH - info_x - 50
        info_panel = Panel(info_x, LIST_Y, info_w, LIST_H, alpha=True)
        info_panel.draw(screen)

        if self.scene.selected_index != -1 and self.scene.selected_index < len(self.scene.achievement_list):
            ach_id, ach = self.scene.achievement_list[self.scene.selected_index]
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

        self.scene.close_button.draw(screen)

    def _draw_scrollbar(self, screen: pygame.Surface):
        """Малює смугу прокрутки."""
        if self.scene._max_scroll <= 0:
            return

        bar_x     = LIST_X + LIST_W - 10
        bar_track = pygame.Rect(bar_x, LIST_Y, 8, LIST_H)
        pygame.draw.rect(screen, (40, 35, 50), bar_track, border_radius=4)

        # Розмір повзунка
        visible_ratio = LIST_H / (LIST_H + self.scene._max_scroll)
        thumb_h = max(30, int(LIST_H * visible_ratio))
        thumb_y = LIST_Y + int((LIST_H - thumb_h) * (self.scene.scroll_y / max(1, self.scene._max_scroll)))
        thumb   = pygame.Rect(bar_x, thumb_y, 8, thumb_h)
        pygame.draw.rect(screen, COLOR_GOLD, thumb, border_radius=4)