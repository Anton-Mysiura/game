"""
Сцена села Пригорщина (стартова локація).
"""

import logging

log = logging.getLogger(__name__)

import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel, ProgressBar
from ui.constants import *
from ui.assets import assets
from game.save_manager import autosave
from game.tutorial_manager import TutorialManager
from game.animation import AnimationController, Animation, AnimationLoader
from scenes.main_menu import _build_menu_character
from game.sound_manager import sounds


class VillageScene(SceneWithBackground, SceneWithButtons):
    """Село Пригорщина."""

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "village")
        SceneWithButtons.__init__(self, game)

        # Ініціалізуємо всі атрибути ДО будь-яких ранніх повернень
        self.show_settings   = False
        self._offline_msg    = ""
        self._offline_msg_t  = 0.0
        self._char_ctrl      = None
        self._char_float_t   = 0.0
        self._char_shadow    = pygame.Surface((120, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(self._char_shadow, (0, 0, 0, 70), self._char_shadow.get_rect())

        # Якщо є невибрані перки — одразу на екран вибору
        if self.player and self.player.pending_perk_choices:
            game.change_scene("level_up")
            return
        offline = self.game.scene_data.pop("offline_crafted", [])
        if offline:
            names = ", ".join(i.name for i in offline[:3])
            if len(offline) > 3:
                names += f" та ще {len(offline) - 3}"
            self._offline_msg   = f"📦 Готово поки тебе не було: {names}!"
            self._offline_msg_t = 6.0

        # ── Онбординг ─────────────────────────────────────────────
        self._ob_village = (self.game.scene_data.get("onboarding_step") == "village")
        self._ob_anim    = 0.0

        # Перевіряємо туторіали
        self._check_tutorials()

        # Створюємо кнопки
        self._create_buttons()

        # UI панель зі статами
        self.stats_panel = Panel(20, 20, 360, 180, alpha=True)
        self.hp_bar = ProgressBar(50, 50, 300, 30, COLOR_HP)
        self.xp_bar = ProgressBar(50, 90, 300, 30, COLOR_XP)

        # ── Анімований персонаж гравця ──
        # Беремо активного героя з roster
        hero = self.player.hero_roster.active_hero if self.player else None
        char_id = hero.hero_id if hero else "gangster_1"
        try:
            self._char_ctrl = _build_menu_character(char_id, scale=3.0)
        except Exception:
            self._char_ctrl = None

        # ── Погода / час доби ──────────────────────────────────
        import random as _rnd, datetime
        _hour = datetime.datetime.now().hour
        if   6  <= _hour < 12: self._time_of_day = "ранок"
        elif 12 <= _hour < 18: self._time_of_day = "день"
        elif 18 <= _hour < 22: self._time_of_day = "вечір"
        else:                   self._time_of_day = "ніч"
        _weathers = ["ясно", "хмарно", "туман", "вітер", "дощ"]
        _weights  = [40, 25, 15, 12, 8]
        self._weather = _rnd.choices(_weathers, _weights)[0]
        self._weather_t = 0.0   # анімаційний таймер

    def _check_tutorials(self):
        """Перевіряє чи є туторіали для показу."""
        tutorials = TutorialManager.flush_tutorial_queue(self.player)
        if tutorials:
            self.game.change_scene("tutorial",
                                   tutorial_data=tutorials,
                                   next_scene="village")

    def _create_buttons(self):
        """Створює кнопки для локацій та дій."""
        # Основні локації
        self.buttons = [
            Button(30,  600, 155, 50, "🏪 Крамниця",
                   lambda: self._go_to_shop()),
            Button(200, 600, 155, 50, "🔨 Майстерня",
                   lambda: self._go_to_workshop()),
            Button(370, 600, 155, 50, "🏴 Ринок",
                   lambda: self.game.change_scene("market")),
            Button(540, 600, 155, 50, "🗣 Голова села",
                   lambda: self._talk_to_elder()),
            Button(710, 600, 155, 50, "🌲 До лісу",
                   lambda: self._go_to_forest()),
            Button(880, 600, 155, 50, "🗺 Карта світу",
                   lambda: self.game.change_scene("world_map")),
        ]

        # Кнопки управління
        self.buttons.extend([
            Button(SCREEN_WIDTH - 230, 20, 200, 40, "📊 Характеристики",
                   lambda: self.game.push_scene("stats")),
            Button(SCREEN_WIDTH - 230, 70, 200, 40, "🎒 Інвентар",
                   lambda: self.game.push_scene("inventory")),
            Button(SCREEN_WIDTH - 230, 120, 200, 40, "💾 Зберегти",
                   lambda: self._save_game()),
        ])
        # Кнопки управління
        self.buttons.extend([
            Button(SCREEN_WIDTH - 230, 20, 200, 40, "📊 Характеристики",
                   lambda: self.game.push_scene("stats")),
            Button(SCREEN_WIDTH - 230, 70, 200, 40, "🎒 Інвентар",
                   lambda: self.game.push_scene("inventory")),
            Button(SCREEN_WIDTH - 230, 120, 200, 40, "🏆 Досягнення",
                   lambda: self.game.push_scene("achievements")),
            Button(SCREEN_WIDTH - 230, 170, 200, 40, "✨ Перки",
                   lambda: self.game.push_scene("perks")),
            Button(SCREEN_WIDTH - 230, 220, 200, 40, "🌳 Дерево навичок",
                   lambda: self.game.push_scene("skill_tree")),
            Button(SCREEN_WIDTH - 230, 270, 200, 40, "💎 Крамниця перків",
                   lambda: self.game.push_scene("perk_shop")),
            Button(SCREEN_WIDTH - 230, 320, 200, 40, "📖 Бестіарій",
                   lambda: self.game.push_scene("bestiary")),
            Button(SCREEN_WIDTH - 230, 370, 200, 40, "📋 Завдання дня",
                   lambda: self.game.push_scene("daily_quests")),
            Button(SCREEN_WIDTH - 230, 420, 200, 40, "⚔ Герої",
                   lambda: self.game.push_scene("hero_slots")),
            Button(SCREEN_WIDTH - 230, 470, 200, 40, "💾 Зберегти",
                   lambda: self._save_game()),
            Button(SCREEN_WIDTH - 230, 520, 200, 40, "⚙ Налаштування",
                   lambda: self._open_settings()),
        ])
        self.show_settings = False

    def _go_to_shop(self):
        """Перехід до крамниці."""
        tutorial = TutorialManager.maybe_tutorial(self.player, "tut_shop")
        if tutorial:
            self.game.change_scene("tutorial",
                                   tutorial_data=[{
                                       "id": "tut_shop",
                                       "title": "🏪 Крамниця",
                                       "pages": tutorial
                                   }],
                                   next_scene="shop")
        else:
            self.game.change_scene("shop")

    def _go_to_workshop(self):
        """Перехід до майстерні."""
        tutorial = TutorialManager.maybe_tutorial(self.player, "tut_workshop")
        if tutorial:
            self.game.change_scene("tutorial",
                                   tutorial_data=[{
                                       "id": "tut_workshop",
                                       "title": "🔨 Майстерня",
                                       "pages": tutorial
                                   }],
                                   next_scene="workshop")
        else:
            self.game.change_scene("workshop")

    def _talk_to_elder(self):
        """Розмова з головою села — відкриває сцену квестів."""
        # Перший раз — дає стартове золото
        if self.player.level < 2 and not self.player.quests_active and not self.player.quests_done:
            self.player.gold += 30
            autosave(self.player)
            self._show_message("Голова села дав тобі 30 золота на старт!")
        self.game.change_scene("elder")

    def _go_to_forest(self):
        """Перехід до лісу."""
        # Онбординг — знімаємо стрілку і визначаємо return_scene
        if self._ob_village and not getattr(self.player, "onboarding_done", False):
            self._ob_village = False
            self.game.scene_data.pop("onboarding_step", None)
            trips = getattr(self.player, "_ob_forest_trips", 0) + 1
            self.player._ob_forest_trips = trips
            if trips == 1:
                # Перший похід у ліс після онбордингу — другий бій з гобліном
                from game.enemy import make_goblin
                from scenes.onboarding import BATTLE2_XP
                enemy = make_goblin()
                enemy.level = 1
                enemy.hp    = enemy.max_hp = 40
                self.game.scene_data["onboarding_after_battle"] = "perk_pick"
                self.game.scene_data["onboarding_battle2_xp"]   = BATTLE2_XP
                self.game.change_scene("battle", enemy=enemy,
                                       return_scene="onboarding_perk",
                                       background_name="forest")
                return
        self.game.change_scene("forest")

    def _open_settings(self):
        self.show_settings = True

    def _close_settings(self):
        self.show_settings = False

    def _save_game(self):
        """Збереження гри."""
        autosave(self.player)
        self._show_message("💾 Гру збережено!", kind="save")

    def _show_message(self, text: str, kind: str = "info"):
        """Показує тост-сповіщення."""
        from ui.notifications import notify
        notify(text, kind=kind, duration=2.5)
        log.info("%s", text)

    def handle_event(self, event: pygame.event.Event):
        if self.show_settings:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_settings_click(pygame.mouse.get_pos())
            return
        super().handle_event(event)

    def update(self, dt: float):
        if not self.show_settings:
            super().update(dt) if hasattr(super(), "update") else None
        if self._char_ctrl:
            self._char_ctrl.update(dt)
            self._char_float_t += dt
        self._weather_t += dt
        if self._offline_msg_t > 0:
            self._offline_msg_t -= dt
        if self._ob_village:
            self._ob_anim += dt

        # Оновлюємо підказку на кнопці голови якщо є квести до здачі
        from game.quests import get_completable_quests
        completable = get_completable_quests(self.player)
        for btn in self.buttons:
            if "Голова" in btn.text or "Здати" in btn.text:
                if completable:
                    btn.text = f"🧓 Здати ({len(completable)})"
                else:
                    btn.text = "🗣 Голова села"
                break

    def _handle_settings_click(self, mouse_pos):
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        back_rect = pygame.Rect(cx - 100, cy + 200, 200, 45)
        if back_rect.collidepoint(mouse_pos):
            self._close_settings()
            return
        music_track = pygame.Rect(cx - 150, cy - 30, 300, 12)
        if music_track.collidepoint(mouse_pos):
            val = (mouse_pos[0] - music_track.x) / music_track.width
            sounds.set_music_volume(max(0.0, min(1.0, val)))
            return
        sfx_track = pygame.Rect(cx - 150, cy + 50, 300, 12)
        if sfx_track.collidepoint(mouse_pos):
            val = (mouse_pos[0] - sfx_track.x) / sfx_track.width
            sounds.set_sfx_volume(max(0.0, min(1.0, val)))
            return
        music_cb = pygame.Rect(cx + 170, cy - 38, 24, 24)
        if music_cb.collidepoint(mouse_pos):
            sounds.music_enabled = not sounds.music_enabled
            if not sounds.music_enabled:
                sounds.stop_music()
            return
        sfx_cb = pygame.Rect(cx + 170, cy + 42, 24, 24)
        if sfx_cb.collidepoint(mouse_pos):
            sounds.enabled = not sounds.enabled
            return
        dmg_cb = pygame.Rect(cx + 170, cy + 112, 24, 24)
        if dmg_cb.collidepoint(mouse_pos):
            sounds.show_damage_numbers = not sounds.show_damage_numbers
            return
        fs_cb = pygame.Rect(cx + 170, cy + 162, 24, 24)
        if fs_cb.collidepoint(mouse_pos):
            self.game.toggle_fullscreen()
            return

    def _draw_village_character(self, screen: pygame.Surface):
        """Малює анімованого персонажа гравця в селі (правіше центру)."""
        if not self._char_ctrl:
            return
        frame = self._char_ctrl.get_current_frame()
        if not frame:
            return

        import math
        float_y = math.sin(self._char_float_t * 1.6) * 4

        # Праворуч від центральної панелі опису
        char_x = SCREEN_WIDTH // 2 + 320
        char_y = int(SCREEN_HEIGHT - 55 - frame.get_height() + float_y)

        # Тінь
        sx = char_x + frame.get_width() // 2 - self._char_shadow.get_width() // 2
        screen.blit(self._char_shadow, (sx, SCREEN_HEIGHT - 47))

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
        self.stats_panel.draw(screen)

        # HP бар
        self.hp_bar.draw(screen, self.player.hp, self.player.max_hp, "HP")

        # XP бар
        self.xp_bar.draw(screen, self.player.xp, self.player.xp_next, "XP")

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
        self.draw_buttons(screen)

        # ── Бейдж "завдання дня" на кнопці ──────────────────────
        self._draw_daily_badge(screen)

        # ── Погода / час доби ────────────────────────────────────
        self._draw_weather(screen)

        # ── Останній бій ────────────────────────────────────────
        self._draw_last_battle(screen)

        # Налаштування (поверх всього)
        if self.show_settings:
            self._draw_settings(screen)

        self._draw_offline_msg(screen)
        if self._ob_village:
            self._draw_ob_forest_arrow(screen)

    def _draw_ob_forest_arrow(self, screen: pygame.Surface):
        """Стрілка + підсвітка кнопки 'Ліс' під час онбордингу."""
        import math
        pulse = 0.5 + 0.5 * abs(math.sin(self._ob_anim * 2.5))
        hl_col = tuple(int(c * pulse) for c in (255, 220, 60))

        forest_btn = None
        for btn in self.buttons:
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
        for btn in self.buttons:
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
        w_icon, w_col = ICONS.get(self._weather, ("?", (200, 200, 200)))
        t_icon, t_col = TIME_ICONS.get(self._time_of_day, ("?", (200, 200, 200)))

        font = assets.get_font(FONT_SIZE_SMALL)
        # Легке мерехтіння
        pulse = 0.85 + 0.15 * abs(math.sin(self._weather_t * 0.8))
        w_surf = font.render(f"{w_icon} {self._weather.capitalize()}", True, w_col)
        t_surf = font.render(f"{t_icon} {self._time_of_day.capitalize()}", True, t_col)
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
        if self._offline_msg_t <= 0:
            return
        alpha = min(255, int(self._offline_msg_t * 60))
        font  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        surf  = font.render(self._offline_msg, True, (100, 220, 100))
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