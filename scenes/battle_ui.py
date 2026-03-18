"""
Малювання UI для сцени бою (HP бари, пауза, налаштування, результати).
"""

import pygame
from ui.assets import assets
from ui.components import Button, Panel, ProgressBar
from ui.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_HP, COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_ERROR, COLOR_SUCCESS, COLOR_BTN_HOVER,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, FONT_SIZE_HUGE,
)
from game.sound_manager import sounds


class BattleUIMixin:
    """Міксін з усією логікою малювання для FightingBattleScene."""

    def _create_ui(self):
        """Створює UI елементи."""
        self.player_hp_bar = ProgressBar(50, 30, 400, 30, COLOR_HP, show_text=False)
        self.enemy_hp_bar = ProgressBar(SCREEN_WIDTH - 450, 30, 400, 30, COLOR_HP, show_text=False)

        self.controls_panel = Panel(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 80, 500, 60, alpha=True)

        # ── Action Bar (панель дій) ──────────────────────────────
        # 4 кнопки: Атака(J) / Сильна(I) / Блок(K) / Зілля(Q)
        self._action_bar = [
            {"key": "J",  "icon": "⚔",  "label": "Атака",       "color": (220,160,80),  "cd_attr": "attack_cooldown",  "cd_max": 0.6},
            {"key": "I",  "icon": "💥", "label": "Сильна",       "color": (255,80,80),   "cd_attr": "attack_cooldown",  "cd_max": 1.0},
            {"key": "K",  "icon": "🛡", "label": "Блок",         "color": (80,150,255),  "cd_attr": "block_cooldown",   "cd_max": 0.5},
            {"key": "Q",  "icon": "🧪", "label": "Зілля",        "color": (80,220,120),  "cd_attr": None,               "cd_max": 0},
        ]
        self._ab_w  = 120
        self._ab_h  = 64
        self._ab_y  = SCREEN_HEIGHT - self._ab_h - 12
        ab_total    = len(self._action_bar) * (self._ab_w + 8) - 8
        self._ab_x0 = SCREEN_WIDTH // 2 - ab_total // 2

        self.paused = False
        self.pause_panel = Panel(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 200, 400, 420, alpha=True)
        self.pause_buttons = [
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100, 300, 50,
                   "▶ Продовжити", lambda: self._unpause()),
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 30, 300, 50,
                   "🧪 Використати зілля", lambda: self._use_potion()),
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 40, 300, 50,
                   "⚙ Налаштування", lambda: self._open_settings()),
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 110, 300, 50,
                   "🏃 Втекти з бою", lambda: self._try_flee()),
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 170, 300, 40,
                   "🏘 Вийти до села", lambda: self._exit_to_village()),
        ]
        self.show_settings = False
        self.loot_scroll_y = 0  # скрол панелі нагород

    def _build_result_buttons(self):
        """Створює кнопки екрану результатів."""
        self.result_buttons = [
            Button(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT - 130, 300, 52,
                   "🏘 Повернутись до села", lambda: self.game.change_scene("village")),
            Button(SCREEN_WIDTH // 2 + 160, SCREEN_HEIGHT - 130, 200, 52,
                   "📜 Журнал бою", lambda: self.game.push_scene("battle_log")),
        ]

    def _draw_ui(self, screen):
        """Малює HP бари, таймер, статус-ефекти та Action Bar."""
        font_name = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        font_sm   = assets.get_font(FONT_SIZE_SMALL)

        # ── Гравець (ліворуч) ───────────────────────────────────
        player_name = font_name.render(self.player.name, True, COLOR_GOLD)
        screen.blit(player_name, (50, 5))
        self.player_hp_bar.draw(screen, self.player_fighter.hp, self.player_fighter.max_hp)

        # HP числами
        hp_txt = font_sm.render(
            f"{max(0, self.player_fighter.hp)} / {self.player_fighter.max_hp}",
            True, COLOR_TEXT)
        screen.blit(hp_txt, (50, 62))

        # Статус-ефекти гравця
        self._draw_status_icons(screen, self.player_fighter, x=50, y=80)

        # ── Ворог (праворуч) ────────────────────────────────────
        from game.enemy_scaling import level_color
        enemy_lvl  = getattr(self.enemy_data, "level", 1)
        lvl_clr    = level_color(enemy_lvl, self.player.level)
        enemy_name = font_name.render(self.enemy_data.name, True, COLOR_ERROR)
        screen.blit(enemy_name, (SCREEN_WIDTH - 450, 5))
        lvl_surf   = font_sm.render(f"Рівень {enemy_lvl}", True, lvl_clr)
        screen.blit(lvl_surf, (SCREEN_WIDTH - 450, 30))
        self.enemy_hp_bar.draw(screen, self.enemy_fighter.hp, self.enemy_fighter.max_hp)

        # HP числами
        ehp_txt = font_sm.render(
            f"{max(0, self.enemy_fighter.hp)} / {self.enemy_fighter.max_hp}",
            True, COLOR_TEXT)
        screen.blit(ehp_txt, (SCREEN_WIDTH - 450, 62))

        # Статус-ефекти ворога
        self._draw_status_icons(screen, self.enemy_fighter,
                                x=SCREEN_WIDTH - 450, y=80, align_right=False)

        # ── Таймер по центру ────────────────────────────────────
        time_left = max(0, self.battle_time_limit - self.battle_elapsed)
        seconds   = int(time_left)
        import math
        if time_left <= 15:
            # Пульсуючий червоний + тремтіння
            pulse     = abs(math.sin(time_left * math.pi * (2 if time_left <= 10 else 1.2)))
            size      = int(52 + 14 * pulse)
            font_timer = assets.get_font(size, bold=True)
            r = int(255)
            g = int(60 * (1 - pulse))
            timer_surf = font_timer.render(str(seconds), True, (r, g, 60))
            # Попереджувальний фон
            warn_bg = pygame.Surface((60, 60), pygame.SRCALPHA)
            warn_bg.fill((180, 0, 0, int(80 * pulse)))
            screen.blit(warn_bg, (SCREEN_WIDTH // 2 - 30, 4))
        elif time_left <= 30:
            font_timer = assets.get_font(FONT_SIZE_LARGE, bold=True)
            timer_surf = font_timer.render(str(seconds), True, COLOR_GOLD)
        else:
            font_timer = assets.get_font(FONT_SIZE_LARGE, bold=True)
            timer_surf = font_timer.render(str(seconds), True, COLOR_TEXT)
        screen.blit(timer_surf, (SCREEN_WIDTH // 2 - timer_surf.get_width() // 2, 8))

        # ── DPS (урон за секунду) ────────────────────────────────
        elapsed = max(1.0, self.battle_elapsed)
        dps = self.stat_damage_dealt / elapsed
        if dps >= 1.0:
            font_dps = assets.get_font(FONT_SIZE_SMALL)
            dps_surf = font_dps.render(f"DPS: {dps:.1f}", True, (200, 160, 80))
            screen.blit(dps_surf, (SCREEN_WIDTH // 2 - dps_surf.get_width() // 2, 52))

        # ── Action Bar ──────────────────────────────────────────
        self._draw_action_bar(screen)

    def _draw_status_icons(self, screen, fighter, x: int, y: int, align_right: bool = False):
        """Малює іконки активних статусів (burn, stun) над HP баром."""
        font = assets.get_font(FONT_SIZE_SMALL)
        icons = []
        if fighter.burn_timer > 0:
            icons.append(("🔥", f"{fighter.burn_timer:.1f}с", (255, 120, 40)))
        if fighter.stun_timer > 0:
            icons.append(("⚡", f"{fighter.stun_timer:.1f}с", (200, 180, 255)))
        if fighter.rage_mode:
            icons.append(("😡", "RAGE", (255, 60, 40)))
        if fighter.is_blocking:
            icons.append(("🛡", "БЛОК", (80, 150, 255)))

        cx = x
        for ico, label, color in icons:
            # Плашка
            bg = pygame.Surface((54, 20), pygame.SRCALPHA)
            bg.fill((20, 16, 10, 180))
            screen.blit(bg, (cx, y))
            pygame.draw.rect(screen, color, (cx, y, 54, 20), 1, border_radius=3)
            txt = font.render(f"{ico}{label}", True, color)
            screen.blit(txt, (cx + 3, y + 2))
            cx += 58

    def _draw_action_bar(self, screen):
        """Малює панель дій з cooldown-кільцями і підсвіченням."""
        import math
        font_key  = assets.get_font(FONT_SIZE_SMALL)
        font_lbl  = assets.get_font(FONT_SIZE_SMALL)
        font_ico  = assets.get_font(28)

        pf = self.player_fighter
        has_potion = any(i.item_type == "potion" for i in self.player.inventory)

        for idx, action in enumerate(self._action_bar):
            ax = self._ab_x0 + idx * (self._ab_w + 8)
            ay = self._ab_y
            W, H = self._ab_w, self._ab_h

            # Стан кнопки
            on_cooldown = False
            cd_frac = 0.0
            if action["cd_attr"]:
                cd_val = getattr(pf, action["cd_attr"], 0.0)
                cd_max = action["cd_max"]
                if cd_val > 0:
                    on_cooldown = True
                    cd_frac = min(1.0, cd_val / cd_max)

            # Спеціальні стани
            is_blocking = (idx == 2 and pf.is_blocking)
            no_potion   = (idx == 3 and not has_potion)
            disabled    = on_cooldown or no_potion

            # Фон
            bg_color = (16, 12, 8, 220)
            if is_blocking:
                bg_color = (20, 30, 60, 230)
            bg = pygame.Surface((W, H), pygame.SRCALPHA)
            bg.fill(bg_color)
            screen.blit(bg, (ax, ay))

            # Рамка
            border = action["color"] if is_blocking else (
                (60, 50, 40) if disabled else (90, 75, 55))
            pygame.draw.rect(screen, border, (ax, ay, W, H), 2, border_radius=8)

            # Cooldown overlay
            if on_cooldown and cd_frac > 0:
                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, int(160 * cd_frac)))
                screen.blit(overlay, (ax, ay))

                # Cooldown arc (рисуємо через лінії)
                cx_c = ax + W // 2
                cy_c = ay + H // 2
                r = min(W, H) // 2 - 4
                steps = 32
                angle_start = -math.pi / 2
                angle_end   = angle_start + 2 * math.pi * cd_frac
                points = [(cx_c, cy_c)]
                for s in range(steps + 1):
                    a = angle_start + (angle_end - angle_start) * s / steps
                    points.append((cx_c + r * math.cos(a), cy_c + r * math.sin(a)))
                if len(points) > 2:
                    pygame.draw.polygon(screen, (*action["color"], 60), points)

            # Іконка
            ico_surf = font_ico.render(action["icon"], True,
                                       (120, 110, 100) if disabled else action["color"])
            screen.blit(ico_surf, (ax + W // 2 - ico_surf.get_width() // 2,
                                   ay + 6))

            # Підпис
            lbl_color = (100, 90, 80) if disabled else (200, 190, 170)
            lbl = font_lbl.render(action["label"], True, lbl_color)
            screen.blit(lbl, (ax + W // 2 - lbl.get_width() // 2, ay + H - 22))

            # Клавіша (зверху-зліва)
            key_s = font_key.render(f"[{action['key']}]", True,
                                    (100, 90, 80) if disabled else COLOR_GOLD)
            screen.blit(key_s, (ax + 4, ay + 4))

    def _draw_pause_menu(self, screen):
        """Малює меню паузи."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        self.pause_panel.draw(screen)

        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("ПАУЗА", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))

        for btn in self.pause_buttons:
            btn.draw(screen)

    def _draw_settings(self, screen):
        """Малює вікно налаштувань."""
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(cx - 220, cy - 180, 440, 410)
        pygame.draw.rect(screen, (30, 25, 40), panel_rect, border_radius=16)
        pygame.draw.rect(screen, COLOR_GOLD, panel_rect, 2, border_radius=16)

        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font = assets.get_font(FONT_SIZE_NORMAL)
        font_sm = assets.get_font(FONT_SIZE_SMALL)

        title = font_title.render("⚙ Налаштування", True, COLOR_GOLD)
        screen.blit(title, (cx - title.get_width() // 2, cy - 160))

        # Музика
        screen.blit(font.render("🎵 Музика", True, COLOR_TEXT), (cx - 150, cy - 62))
        music_cb = pygame.Rect(cx + 170, cy - 58, 24, 24)
        pygame.draw.rect(screen, (50, 50, 60), music_cb, border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, music_cb, 2, border_radius=4)
        if sounds.music_enabled:
            screen.blit(font.render("✓", True, COLOR_GOLD), (music_cb.x + 3, music_cb.y - 2))

        music_track = pygame.Rect(cx - 150, cy - 30, 300, 12)
        pygame.draw.rect(screen, (50, 50, 60), music_track, border_radius=6)
        fill_w = int(music_track.width * sounds.music_volume)
        if fill_w > 0:
            pygame.draw.rect(screen, COLOR_GOLD,
                pygame.Rect(music_track.x, music_track.y, fill_w, 12), border_radius=6)
        pygame.draw.circle(screen, COLOR_GOLD, (music_track.x + fill_w, music_track.centery), 9)
        screen.blit(font_sm.render(f"{int(sounds.music_volume * 100)}%", True, COLOR_TEXT_DIM),
                    (cx + 162, cy - 35))

        # Звуки
        screen.blit(font.render("🔊 Звуки", True, COLOR_TEXT), (cx - 150, cy + 18))
        sfx_cb = pygame.Rect(cx + 170, cy + 22, 24, 24)
        pygame.draw.rect(screen, (50, 50, 60), sfx_cb, border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, sfx_cb, 2, border_radius=4)
        if sounds.enabled:
            screen.blit(font.render("✓", True, COLOR_GOLD), (sfx_cb.x + 3, sfx_cb.y - 2))

        sfx_track = pygame.Rect(cx - 150, cy + 50, 300, 12)
        pygame.draw.rect(screen, (50, 50, 60), sfx_track, border_radius=6)
        fill_w2 = int(sfx_track.width * sounds.sfx_volume)
        if fill_w2 > 0:
            pygame.draw.rect(screen, (100, 180, 255),
                pygame.Rect(sfx_track.x, sfx_track.y, fill_w2, 12), border_radius=6)
        pygame.draw.circle(screen, (100, 180, 255), (sfx_track.x + fill_w2, sfx_track.centery), 9)
        screen.blit(font_sm.render(f"{int(sounds.sfx_volume * 100)}%", True, COLOR_TEXT_DIM),
                    (cx + 162, cy + 45))

        # Числа шкоди
        screen.blit(font.render("💢 Числа шкоди", True, COLOR_TEXT), (cx - 150, cy + 88))
        dmg_cb = pygame.Rect(cx + 170, cy + 92, 24, 24)
        pygame.draw.rect(screen, (50, 50, 60), dmg_cb, border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, dmg_cb, 2, border_radius=4)
        if sounds.show_damage_numbers:
            screen.blit(font.render("✓", True, COLOR_GOLD), (dmg_cb.x + 3, dmg_cb.y - 2))

        # Кнопка назад
        back_rect = pygame.Rect(cx - 100, cy + 150, 200, 45)
        mouse_pos = pygame.mouse.get_pos()
        back_color = COLOR_BTN_HOVER if back_rect.collidepoint(mouse_pos) else (50, 40, 65)
        pygame.draw.rect(screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, back_rect, 2, border_radius=10)
        back_lbl = font.render("← Назад", True, COLOR_TEXT)
        screen.blit(back_lbl, (cx - back_lbl.get_width() // 2, back_rect.y + 10))

    def _draw_result_screen(self, screen: pygame.Surface):
        """Малює повний екран результатів бою."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        font_huge  = assets.get_font(72, bold=True)
        font_large = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_med   = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)

        # ── Заголовок ──
        if self.player_won:
            title      = font_huge.render("ПЕРЕМОГА!", True, COLOR_SUCCESS)
            title_glow = font_huge.render("ПЕРЕМОГА!", True, (100, 255, 130))
        else:
            title      = font_huge.render("ПОРАЗКА", True, COLOR_ERROR)
            title_glow = font_huge.render("ПОРАЗКА", True, (255, 100, 100))

        ty = 18
        screen.blit(title_glow, (cx - title.get_width() // 2 + 2, ty + 2))
        screen.blit(title,      (cx - title.get_width() // 2,     ty))

        enemy_lbl = font_med.render(
            f"{'vs' if self.player_won else 'програш проти'} {self.enemy_data.name}",
            True, COLOR_TEXT_DIM
        )
        screen.blit(enemy_lbl, (cx - enemy_lbl.get_width() // 2, ty + 82))

        elapsed = int(self.battle_elapsed)
        time_surf = font_med.render(f"⏱ {elapsed // 60}:{elapsed % 60:02d}", True, COLOR_TEXT)
        screen.blit(time_surf, (cx - time_surf.get_width() // 2, ty + 112))

        # ── Геометрія двох панелей ──
        panels_top  = 160
        panels_bot  = SCREEN_HEIGHT - 110   # над кнопкою
        panels_h    = panels_bot - panels_top
        gap         = 14
        stat_w      = 430
        rew_w       = SCREEN_WIDTH - 80 - stat_w - gap
        stat_x      = 40
        rew_x       = stat_x + stat_w + gap

        # ── Ліва панель: Статистика ──
        stat_rect = pygame.Rect(stat_x, panels_top, stat_w, panels_h)
        pygame.draw.rect(screen, (25, 20, 35), stat_rect, border_radius=14)
        pygame.draw.rect(screen, COLOR_GOLD, stat_rect, 2, border_radius=14)

        stat_title = font_large.render("📊 Статистика", True, COLOR_GOLD)
        screen.blit(stat_title, (stat_x + stat_w // 2 - stat_title.get_width() // 2,
                                  panels_top + 12))

        stats = [
            ("⚔ Завдано шкоди",    str(self.stat_damage_dealt)),
            ("💔 Отримано шкоди",  str(self.stat_damage_taken)),
            ("🎯 Влучань",         str(self.stat_hits_landed)),
            ("😵 Отримано ударів", str(self.stat_hits_taken)),
            ("🛡 Заблоковано",     str(self.stat_blocks_done)),
            ("❤ HP залишилось",   str(max(0, self.player_fighter.hp))),
        ]
        row_y = panels_top + 58
        val_x = stat_x + stat_w - 90
        for lbl, val in stats:
            screen.blit(font_sm.render(lbl,  True, COLOR_TEXT_DIM), (stat_x + 18, row_y))
            screen.blit(font_med.render(val, True, COLOR_TEXT),     (val_x,       row_y))
            row_y += 44

        # ── Права панель: Нагороди ──
        rew_rect = pygame.Rect(rew_x, panels_top, rew_w, panels_h)
        pygame.draw.rect(screen, (20, 28, 20), rew_rect, border_radius=14)
        rew_border = COLOR_GOLD if self.player_won else (80, 80, 80)
        pygame.draw.rect(screen, rew_border, rew_rect, 2, border_radius=14)

        rew_title = font_large.render("🎁 Нагороди", True, COLOR_GOLD)
        screen.blit(rew_title, (rew_x + rew_w // 2 - rew_title.get_width() // 2,
                                 panels_top + 12))

        if self.player_won:
            # XP + золото
            xp_surf   = font_med.render(f"✨ +{self.enemy_data.xp_reward} XP", True, (120, 220, 255))
            gold_surf = font_med.render(f"💰 +{self.enemy_data.gold_reward} золота", True, COLOR_GOLD)
            screen.blit(xp_surf,   (rew_x + 18, panels_top + 58))
            screen.blit(gold_surf, (rew_x + 18, panels_top + 90))

            # Лут список зі скролом
            loot_lines = []
            for entry in self.loot_gained:
                kind, icon, name, qty = entry
                if kind == "mat":
                    loot_lines.append((icon, f"{name}  ×{qty}", (180, 230, 255)))
                else:
                    loot_lines.append((icon, name, (255, 220, 120)))

            loot_area_top  = panels_top + 130
            loot_area_bot  = panels_bot - 8
            loot_area_h    = loot_area_bot - loot_area_top
            row_h          = 32
            total_loot_h   = len(loot_lines) * row_h
            max_scroll     = max(0, total_loot_h - loot_area_h)
            self._loot_max_scroll = max_scroll
            scroll_y       = min(getattr(self, "loot_scroll_y", 0), max_scroll)

            # Clip до зони луту
            clip = pygame.Rect(rew_x + 4, loot_area_top, rew_w - 8, loot_area_h)
            screen.set_clip(clip)

            if loot_lines:
                for i, (icon, label, color) in enumerate(loot_lines):
                    iy = loot_area_top + i * row_h - scroll_y
                    icon_s  = font_sm.render(icon,  True, color)
                    label_s = font_sm.render(label, True, color)
                    screen.blit(icon_s,  (rew_x + 18, iy))
                    screen.blit(label_s, (rew_x + 18 + icon_s.get_width() + 6, iy))
            else:
                no_s = font_sm.render("Додаткового луту не було", True, COLOR_TEXT_DIM)
                screen.blit(no_s, (rew_x + rew_w // 2 - no_s.get_width() // 2,
                                    loot_area_top + 10))

            screen.set_clip(None)

            # Смуга скролу (якщо потрібна)
            if max_scroll > 0:
                sb_x   = rew_x + rew_w - 10
                sb_top = loot_area_top
                sb_h   = loot_area_h
                pygame.draw.rect(screen, (40, 50, 40),
                                  (sb_x, sb_top, 5, sb_h), border_radius=3)
                ratio     = loot_area_h / total_loot_h
                thumb_h   = max(20, int(sb_h * ratio))
                thumb_y   = sb_top + int((sb_h - thumb_h) * scroll_y / max_scroll)
                pygame.draw.rect(screen, COLOR_GOLD,
                                  (sb_x, thumb_y, 5, thumb_h), border_radius=3)
        else:
            no_s = font_med.render("Нагород немає", True, COLOR_TEXT_DIM)
            screen.blit(no_s, (rew_x + rew_w // 2 - no_s.get_width() // 2,
                                panels_top + panels_h // 2 - 10))

        # ── Кнопка ──
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.result_buttons:
            btn.update(mouse_pos, False)
            btn.draw(screen)

    def _draw_battle_end(self, screen):
        """Малює перехідний екран завершення бою."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        font_huge = assets.get_font(80, bold=True)
        text = font_huge.render(
            "ПЕРЕМОГА!" if self.player_won else "ПОРАЗКА",
            True,
            COLOR_SUCCESS if self.player_won else COLOR_ERROR
        )
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))