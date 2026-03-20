"""
Рендерер для BestiaryScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/bestiary.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets


class BestiaryRenderer(BaseRenderer):
    """
    Малює BestiaryScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        self._draw_header(screen)
        self._draw_list_panel(screen)
        self._draw_detail_panel(screen)
        self.scene.close_button.draw(screen)

    def _draw_header(self, screen):
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_sub   = assets.get_font(FONT_SIZE_SMALL)

        title  = font_title.render("📖 Бестіарій", True, COLOR_GOLD)
        shadow = font_title.render("📖 Бестіарій", True, (0, 0, 0))
        cx = SCREEN_WIDTH // 2
        screen.blit(shadow, (cx - title.get_width() // 2 + 2, 22))
        screen.blit(title,  (cx - title.get_width() // 2,     20))

        seen_count = sum(1 for e in ENEMY_REGISTRY if self.scene._is_seen(e))
        sub = font_sub.render(
            f"Виявлено: {seen_count} / {len(ENEMY_REGISTRY)}",
            True, COLOR_TEXT_DIM
        )
        screen.blit(sub, (cx - sub.get_width() // 2, 76))

    def _draw_list_panel(self, screen):
        panel_h = PANELS_BOT - PANELS_TOP
        pygame.draw.rect(screen, (22, 18, 30), (8, PANELS_TOP, LIST_W, panel_h), border_radius=14)
        pygame.draw.rect(screen, (80, 70, 100), (8, PANELS_TOP, LIST_W, panel_h), 2, border_radius=14)

        item_h   = 68
        list_top = PANELS_TOP + 8

        for i, entry in enumerate(ENEMY_REGISTRY):
            y    = list_top + i * item_h
            rect = pygame.Rect(10, y, LIST_W - 10, item_h - 6)
            seen = self.scene._is_seen(entry)

            # Фон рядка
            selected = (i == self.scene.selected_idx)
            if selected:
                bg = (50, 40, 70)
            elif rect.collidepoint(pygame.mouse.get_pos()):
                bg = (35, 28, 50)
            else:
                bg = (28, 22, 38)

            pygame.draw.rect(screen, bg, rect, border_radius=8)
            if selected:
                diff_color = DIFFICULTY_COLOR.get(entry["difficulty"], COLOR_GOLD)
                pygame.draw.rect(screen, diff_color, rect, 2, border_radius=8)

            if seen:
                self._draw_list_item_seen(screen, entry, rect, i)
            else:
                self._draw_list_item_unknown(screen, rect)

    def _draw_list_item_seen(self, screen, entry, rect, idx):
        font_name = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_sm   = assets.get_font(FONT_SIZE_SMALL)

        # Іконка
        icon_surf = assets.get_font(FONT_SIZE_LARGE).render(entry["icon"], True, COLOR_TEXT)
        screen.blit(icon_surf, (rect.x + 8, rect.y + rect.h // 2 - icon_surf.get_height() // 2))

        # Назва
        name_surf = font_name.render(entry["name"], True, COLOR_TEXT)
        screen.blit(name_surf, (rect.x + 52, rect.y + 8))

        # Локація
        loc_surf = font_sm.render(entry["location"], True, COLOR_TEXT_DIM)
        screen.blit(loc_surf, (rect.x + 52, rect.y + 34))

        # Ефективний рівень для поточного гравця
        from game.enemy_scaling import enemy_level, level_color
        eff_lvl = enemy_level(entry["sprite_name"], self.player.level)
        lvl_clr = level_color(eff_lvl, self.player.level)
        lvl_surf = font_sm.render(f"Рівень {eff_lvl}", True, lvl_clr)
        screen.blit(lvl_surf, (rect.x + 52, rect.y + 52))

        # Зірки складності (праворуч)
        stars = DIFFICULTY_STARS.get(entry["difficulty"], "")
        diff_color = DIFFICULTY_COLOR.get(entry["difficulty"], COLOR_TEXT_DIM)
        stars_surf = font_sm.render(stars, True, diff_color)
        screen.blit(stars_surf, (rect.right - stars_surf.get_width() - 8, rect.y + 8))

        # К-сть вбитих
        kills = self.scene._kill_count(entry)
        kill_surf = font_sm.render(f"☠ {kills}", True, (180, 180, 180))
        screen.blit(kill_surf, (rect.right - kill_surf.get_width() - 8, rect.y + 34))

    def _draw_list_item_unknown(self, screen, rect):
        font = assets.get_font(FONT_SIZE_NORMAL)
        surf = font.render("??? Невідомий ворог", True, (80, 70, 90))
        screen.blit(surf, (rect.x + 14, rect.y + rect.h // 2 - surf.get_height() // 2))

    def _draw_detail_panel(self, screen):
        cx     = LIST_W + 20
        panel_w = SCREEN_WIDTH - cx - 12
        panel_h = PANELS_BOT - PANELS_TOP

        pygame.draw.rect(screen, (18, 22, 18), (cx, PANELS_TOP, panel_w, panel_h), border_radius=14)
        pygame.draw.rect(screen, (70, 90, 70), (cx, PANELS_TOP, panel_w, panel_h), 2, border_radius=14)

        entry = ENEMY_REGISTRY[self.scene.selected_idx]
        if not self.scene._is_seen(entry):
            self._draw_unknown_detail(screen, cx, panel_w, panel_h)
        else:
            self._draw_known_detail(screen, entry, cx, panel_w, panel_h)

    def _draw_unknown_detail(self, screen, cx, panel_w, panel_h):
        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_sub = assets.get_font(FONT_SIZE_NORMAL)
        cy = PANELS_TOP + panel_h // 2

        q = font.render("???", True, (80, 70, 90))
        screen.blit(q, (cx + panel_w // 2 - q.get_width() // 2, cy - 40))

        sub = font_sub.render("Зустрінь цього ворога, щоб дізнатись більше", True, (70, 60, 80))
        screen.blit(sub, (cx + panel_w // 2 - sub.get_width() // 2, cy + 10))

    def _draw_known_detail(self, screen, entry, cx, panel_w, panel_h):
        font_huge  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_large = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_med   = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)
        font_norm  = assets.get_font(FONT_SIZE_NORMAL)

        pad = 20
        x   = cx + pad
        y   = PANELS_TOP + pad

        # ── Заголовок ──
        icon_surf = font_huge.render(entry["icon"], True, COLOR_TEXT)
        screen.blit(icon_surf, (x, y))

        name_surf = font_large.render(entry["name"], True, COLOR_GOLD)
        screen.blit(name_surf, (x + icon_surf.get_width() + 12, y + 4))

        diff_color = DIFFICULTY_COLOR.get(entry["difficulty"], COLOR_TEXT_DIM)
        stars_surf = font_sm.render(
            DIFFICULTY_STARS.get(entry["difficulty"], ""), True, diff_color
        )
        screen.blit(stars_surf, (x + icon_surf.get_width() + 12,
                                  y + 4 + name_surf.get_height() + 2))

        loc_surf = font_sm.render(entry["location"], True, COLOR_TEXT_DIM)
        screen.blit(loc_surf, (cx + panel_w - loc_surf.get_width() - pad, y + 8))

        y += max(icon_surf.get_height(), name_surf.get_height()) + 16

        # ── Опис ──
        desc_lines = self.scene._wrap_text(entry["description"], font_norm,
                                      panel_w - pad * 2 - 10)
        for line in desc_lines:
            surf = font_norm.render(line, True, COLOR_TEXT_DIM)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 2
        y += 12

        # ── Розділювач ──
        pygame.draw.line(screen, (60, 80, 60), (x, y), (cx + panel_w - pad, y), 1)
        y += 12

        # ── Стати (ліва колонка) + Нагороди (права колонка) ──
        col_w    = (panel_w - pad * 2) // 2 - 10
        stats_x  = x
        rewards_x = x + col_w + 20

        # Статистика
        stat_title = font_med.render("📊 Характеристики", True, COLOR_GOLD)
        screen.blit(stat_title, (stats_x, y))
        sy = y + stat_title.get_height() + 8

        stats = [
            ("❤ HP",      str(entry["hp"])),
            ("⚔ Атака",   entry["attack"]),
            ("🛡 Захист",  str(entry["defense"])),
            ("✨ XP",      str(entry["xp_reward"])),
            ("💰 Золото",  str(entry["gold_reward"])),
            ("☠ Вбито",   str(self.scene._kill_count(entry))),
        ]
        for lbl, val in stats:
            lbl_s = font_sm.render(lbl,  True, COLOR_TEXT_DIM)
            val_s = font_norm.render(val, True, COLOR_TEXT)
            screen.blit(lbl_s, (stats_x, sy))
            screen.blit(val_s, (stats_x + 130, sy))
            sy += lbl_s.get_height() + 8

        # Нагороди — скрол-зона
        rew_title = font_med.render("🎁 Лут", True, COLOR_GOLD)
        screen.blit(rew_title, (rewards_x, y))

        loot_area_top = y + rew_title.get_height() + 8
        loot_area_bot = PANELS_BOT - 10
        loot_area_h   = loot_area_bot - loot_area_top

        loot_lines = self.scene._build_loot_lines(entry, font_sm, font_norm)
        row_h = font_norm.get_height() + 6
        total_loot_h = len(loot_lines) * row_h
        max_scroll = max(0, total_loot_h - loot_area_h)
        self.scene._loot_max_scroll = max_scroll
        scroll = min(self.scene.loot_scroll, max_scroll)

        clip = pygame.Rect(rewards_x, loot_area_top, col_w, loot_area_h)
        screen.set_clip(clip)

        ry = loot_area_top - scroll
        for icon_s, text_s in loot_lines:
            if ry + row_h >= loot_area_top and ry <= loot_area_bot:
                screen.blit(icon_s, (rewards_x, ry))
                screen.blit(text_s, (rewards_x + icon_s.get_width() + 6, ry))
            ry += row_h

        screen.set_clip(None)

        # Смуга скролу
        if max_scroll > 0:
            sb_x = cx + panel_w - 14
            pygame.draw.rect(screen, (40, 55, 40),
                              (sb_x, loot_area_top, 5, loot_area_h), border_radius=3)
            ratio   = loot_area_h / total_loot_h
            thumb_h = max(20, int(loot_area_h * ratio))
            thumb_y = loot_area_top + int((loot_area_h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(screen, COLOR_GOLD,
                              (sb_x, thumb_y, 5, thumb_h), border_radius=3)