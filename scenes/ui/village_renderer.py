"""
Рендерер для VillageScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/village.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

import logging
from ui.components import Button, Panel, ProgressBar
from ui.constants import *
from ui.assets import assets


class VillageRenderer(BaseRenderer):
    """
    Малює VillageScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def _draw_village_character(self, screen: pygame.Surface):
        """Малює анімованого персонажа гравця в селі (правіше центру)."""
        if not self.scene._char_ctrl:
            return
        frame = self.scene._char_ctrl.get_current_frame()
        if not frame:
            return

        import math
        float_y = math.sin(self.scene._char_float_t * 1.6) * 4

        # Праворуч від центральної панелі опису
        char_x = SCREEN_WIDTH // 2 + 320
        char_y = int(SCREEN_HEIGHT - 55 - frame.get_height() + float_y)

        # Тінь
        sx = char_x + frame.get_width() // 2 - self.scene._char_shadow.get_width() // 2
        screen.blit(self.scene._char_shadow, (sx, SCREEN_HEIGHT - 47))

        # Персонаж дивиться вліво (в бік центру)
        flipped = pygame.transform.flip(frame, True, False)
        screen.blit(flipped, (char_x, char_y))

    def _draw_settings(self, screen):
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(cx - 220, cy - 180, 440, 460)
        pygame.draw.rect(screen, (30, 25, 40), panel_rect, border_radius=16)
        pygame.draw.rect(screen, COLOR_GOLD, panel_rect, 2, border_radius=16)
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font = assets.get_font(FONT_SIZE_NORMAL)
        font_sm = assets.get_font(FONT_SIZE_SMALL)
        title = font_title.render("⚙ Налаштування", True, COLOR_GOLD)
        screen.blit(title, (cx - title.get_width() // 2, cy - 160))
        # Музика
        lbl = font.render("🎵 Музика", True, COLOR_TEXT)
        screen.blit(lbl, (cx - 150, cy - 62))
        music_cb = pygame.Rect(cx + 170, cy - 58, 24, 24)
        pygame.draw.rect(screen, (50, 50, 60), music_cb, border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, music_cb, 2, border_radius=4)
        if sounds.music_enabled:
            screen.blit(font.render("✓", True, COLOR_GOLD), (music_cb.x + 3, music_cb.y - 2))
        music_track = pygame.Rect(cx - 150, cy - 30, 300, 12)
        pygame.draw.rect(screen, (50, 50, 60), music_track, border_radius=6)
        fill_w = int(music_track.width * sounds.music_volume)
        if fill_w > 0:
            pygame.draw.rect(screen, COLOR_GOLD, pygame.Rect(music_track.x, music_track.y, fill_w, 12), border_radius=6)
        pygame.draw.circle(screen, COLOR_GOLD, (music_track.x + fill_w, music_track.centery), 9)
        screen.blit(font_sm.render(f"{int(sounds.music_volume * 100)}%", True, COLOR_TEXT_DIM), (cx + 162, cy - 35))
        # Звуки
        lbl2 = font.render("🔊 Звуки", True, COLOR_TEXT)
        screen.blit(lbl2, (cx - 150, cy + 18))
        sfx_cb = pygame.Rect(cx + 170, cy + 22, 24, 24)
        pygame.draw.rect(screen, (50, 50, 60), sfx_cb, border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, sfx_cb, 2, border_radius=4)
        if sounds.enabled:
            screen.blit(font.render("✓", True, COLOR_GOLD), (sfx_cb.x + 3, sfx_cb.y - 2))
        sfx_track = pygame.Rect(cx - 150, cy + 50, 300, 12)
        pygame.draw.rect(screen, (50, 50, 60), sfx_track, border_radius=6)
        fill_w2 = int(sfx_track.width * sounds.sfx_volume)
        if fill_w2 > 0:
            pygame.draw.rect(screen, (100, 180, 255), pygame.Rect(sfx_track.x, sfx_track.y, fill_w2, 12), border_radius=6)
        pygame.draw.circle(screen, (100, 180, 255), (sfx_track.x + fill_w2, sfx_track.centery), 9)
        screen.blit(font_sm.render(f"{int(sounds.sfx_volume * 100)}%", True, COLOR_TEXT_DIM), (cx + 162, cy + 45))
        # Числа шкоди
        lbl3 = font.render('💢 Числа шкоди', True, COLOR_TEXT)
        screen.blit(lbl3, (cx - 150, cy + 88))
        dmg_cb = pygame.Rect(cx + 170, cy + 92, 24, 24)
        pygame.draw.rect(screen, (50, 50, 60), dmg_cb, border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, dmg_cb, 2, border_radius=4)
        if sounds.show_damage_numbers:
            screen.blit(font.render('✓', True, COLOR_GOLD), (dmg_cb.x + 3, dmg_cb.y - 2))

        # Повний екран
        lbl4 = font.render('🖥 Повний екран', True, COLOR_TEXT)
        screen.blit(lbl4, (cx - 150, cy + 138))
        fs_cb = pygame.Rect(cx + 170, cy + 142, 24, 24)
        pygame.draw.rect(screen, (50, 50, 60), fs_cb, border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, fs_cb, 2, border_radius=4)
        if self.game.is_fullscreen:
            screen.blit(font.render('✓', True, COLOR_GOLD), (fs_cb.x + 3, fs_cb.y - 2))
        hint_fs = font_sm.render('або F11', True, COLOR_TEXT_DIM)
        screen.blit(hint_fs, (cx + 170 + 30, cy + 147))

        # Назад
        back_rect = pygame.Rect(cx - 100, cy + 200, 200, 45)
        back_color = COLOR_BTN_HOVER if back_rect.collidepoint(pygame.mouse.get_pos()) else (50, 40, 65)
        pygame.draw.rect(screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, back_rect, 2, border_radius=10)
        back_lbl = font.render("← Назад", True, COLOR_TEXT)
        screen.blit(back_lbl, (cx - back_lbl.get_width() // 2, back_rect.y + 10))

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # Фон
        super().draw(screen)

        # Анімований персонаж (малюємо ДО панелей щоб вони були поверх)
        self._draw_village_character(screen)

        # Панель зі статами
        self.scene.stats_panel.draw(screen)

        # HP бар
        self.scene.hp_bar.draw(screen, self.player.hp, self.player.max_hp, "HP")

        # XP бар
        self.scene.xp_bar.draw(screen, self.player.xp, self.player.xp_next, "XP")

        # Золото та рівень
        font = assets.get_font(FONT_SIZE_NORMAL)
        gold_text = font.render(f"💰 {self.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold_text, (50, 130))

        level_text = font.render(f"⬆ Рівень {self.player.level}", True, COLOR_TEXT)
        screen.blit(level_text, (230, 130))

        # Час у грі
        font_small = assets.get_font(FONT_SIZE_SMALL)
        pt = getattr(self.player, "total_playtime", 0.0)
        total_s = int(pt)
        h = total_s // 3600; m = (total_s % 3600) // 60; s = total_s % 60
        if h > 0:
            pt_str = f"{h}г {m:02d}хв"
        elif m > 0:
            pt_str = f"{m}хв {s:02d}с"
        else:
            pt_str = f"{s}с"
        time_text = font_small.render(f"🕐 {pt_str}", True, COLOR_TEXT_DIM)
        screen.blit(time_text, (420, 133))

        # Атака та захист
        font_small = assets.get_font(FONT_SIZE_SMALL)
        atk_text = font_small.render(f"⚔ {self.player.total_attack} ATK", True, COLOR_TEXT)
        screen.blit(atk_text, (50, 160))

        def_text = font_small.render(f"🛡 {self.player.total_defense} DEF", True, COLOR_TEXT)
        screen.blit(def_text, (200, 160))

        # Опис локації (по центру)
        desc_panel = Panel(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 100, 600, 200, alpha=True)
        desc_panel.draw(screen)

        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = font_title.render("🏘 Село Пригорщина", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

        font_desc = assets.get_font(FONT_SIZE_NORMAL)
        desc_lines = [
            "Невелике село огорнуте тривогою.",
            "Монстри наближаються. Зброю тут більше не продають,",
            "але є майстерня та крамниця з кресленниками.",
        ]

        y = SCREEN_HEIGHT // 2 - 20
        for line in desc_lines:
            text = font_desc.render(line, True, COLOR_TEXT)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 30

        # Кнопки
        self.scene.draw_buttons(screen)

        # ── Бейдж "завдання дня" на кнопці ──────────────────────
        self._draw_daily_badge(screen)

        # ── Погода / час доби ────────────────────────────────────
        self._draw_weather(screen)

        # ── Останній бій ────────────────────────────────────────
        self._draw_last_battle(screen)

        # Налаштування (поверх всього)
        if self.scene.show_settings:
            self._draw_settings(screen)

        self._draw_offline_msg(screen)
        if self.scene._ob_village:
            self._draw_ob_forest_arrow(screen)

    def _draw_ob_forest_arrow(self, screen: pygame.Surface):
        """Стрілка + підсвітка кнопки 'Ліс' під час онбордингу."""
        import math
        pulse = 0.5 + 0.5 * abs(math.sin(self.scene._ob_anim * 2.5))
        hl_col = tuple(int(c * pulse) for c in (255, 220, 60))

        forest_btn = None
        for btn in self.scene.buttons:
            if "Ліс" in btn.text or "ліс" in btn.text.lower():
                forest_btn = btn
                break
        if not forest_btn:
            return

        # Підсвітка рамки
        r = pygame.Rect(forest_btn.x - 4, forest_btn.y - 4,
                        forest_btn.width + 8, forest_btn.height + 8)
        pygame.draw.rect(screen, hl_col, r, 3, border_radius=10)

        # Стрілка зверху кнопки
        cx   = forest_btn.x + forest_btn.width // 2
        ay   = forest_btn.y - 14
        size = int(12 + 4 * pulse)
        pts  = [(cx, ay + size), (cx - size, ay - size//2), (cx + size, ay - size//2)]
        pygame.draw.polygon(screen, hl_col, pts)

        # Текст
        fn  = assets.get_font(FONT_SIZE_SMALL, bold=True)
        tip = fn.render("Іди у ліс!", True, hl_col)
        tip.set_alpha(int(210 * pulse))
        screen.blit(tip, (cx - tip.get_width() // 2, ay - size//2 - 22))

    def _draw_daily_badge(self, screen: pygame.Surface):
        """Бейдж кількості виконаних завдань на кнопці 'Завдання дня'."""
        if not self.player:
            return
        dq = self.player.daily_quests
        dq.refresh_if_needed()
        done  = sum(1 for q in dq.quests if q.done and not q.claimed)
        total = len(dq.quests)
        if total == 0:
            return
        # Шукаємо кнопку "Завдання дня"
        for btn in self.scene.buttons:
            if "Завдання" in btn.text:
                # Оновлюємо текст кнопки з лічильником
                claimed = sum(1 for q in dq.quests if q.claimed)
                all_done = done + claimed
                if done > 0:
                    btn.text = f"📋 Завдання ({done} готово!)"
                elif all_done == total:
                    btn.text = "📋 Завдання (✓ всі!)"
                else:
                    btn.text = f"📋 Завдання ({all_done}/{total})"
                break

    def _draw_weather(self, screen: pygame.Surface):
        """Смужка погоди і часу доби у верхньому правому куті."""
        import math
        ICONS = {
            "ясно":    ("☀", (255, 220, 80)),
            "хмарно":  ("⛅", (180, 190, 200)),
            "туман":   ("🌫", (160, 160, 170)),
            "вітер":   ("💨", (140, 200, 220)),
            "дощ":     ("🌧", (100, 140, 200)),
        }
        TIME_ICONS = {
            "ранок": ("🌅", (255, 200, 120)),
            "день":  ("🌞", (255, 230, 80)),
            "вечір": ("🌆", (220, 160, 80)),
            "ніч":   ("🌙", (140, 140, 220)),
        }
        w_icon, w_col = ICONS.get(self.scene._weather, ("?", (200, 200, 200)))
        t_icon, t_col = TIME_ICONS.get(self.scene._time_of_day, ("?", (200, 200, 200)))

        font = assets.get_font(FONT_SIZE_SMALL)
        # Легке мерехтіння
        pulse = 0.85 + 0.15 * abs(math.sin(self.scene._weather_t * 0.8))
        w_surf = font.render(f"{w_icon} {self.scene._weather.capitalize()}", True, w_col)
        t_surf = font.render(f"{t_icon} {self.scene._time_of_day.capitalize()}", True, t_col)
        w_surf.set_alpha(int(255 * pulse))
        x = SCREEN_WIDTH - 230
        y = SCREEN_HEIGHT - 640
        screen.blit(t_surf, (x, y))
        screen.blit(w_surf, (x, y + 22))

    def _draw_last_battle(self, screen: pygame.Surface):
        """Міні-статистика останнього бою під панеллю статів."""
        rec = getattr(self.game, "last_battle_record", None)
        if not rec:
            return
        font  = assets.get_font(FONT_SIZE_SMALL)
        font_b = assets.get_font(FONT_SIZE_SMALL, bold=True)
        x, y  = 30, 210
        result_col = (100, 220, 100) if rec.player_won else (220, 80, 80)
        result_txt = "✓ Перемога" if rec.player_won else "✗ Поразка"
        title = font_b.render(f"Останній бій: {rec.enemy_icon} {rec.enemy_name}", True, (180, 160, 100))
        screen.blit(title, (x, y)); y += 20
        res   = font.render(result_txt, True, result_col)
        screen.blit(res, (x, y)); y += 18
        for label, val in [
            (f"⚔ Урон: {rec.damage_dealt}", (220, 180, 100)),
            (f"🩸 Отримано: {rec.damage_taken}", (200, 100, 100)),
            (f"🎯 Критів: {rec.crits}", (140, 200, 255)),
        ]:
            screen.blit(font.render(label, True, val), (x, y)); y += 16

    def _draw_offline_msg(self, screen):
        """Банер про готові предмети офлайн-крафту."""
        if self.scene._offline_msg_t <= 0:
            return
        alpha = min(255, int(self.scene._offline_msg_t * 60))
        font  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        surf  = font.render(self.scene._offline_msg, True, (100, 220, 100))
        pad   = 12
        w, h  = surf.get_width() + pad * 2, surf.get_height() + pad * 2
        bg    = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((10, 30, 10, 200))
        pygame.draw.rect(bg, (80, 200, 80), bg.get_rect(), 2, border_radius=8)
        bg.set_alpha(alpha)
        surf.set_alpha(alpha)
        bx = SCREEN_WIDTH // 2 - w // 2
        by = SCREEN_HEIGHT - 140
        screen.blit(bg, (bx, by))
        screen.blit(surf, (bx + pad, by + pad))