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
from scenes.core.main_menu import _build_menu_character
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

        # Підключаємо renderer (малювання)
        from scenes.ui.village_renderer import VillageRenderer
        self._renderer = VillageRenderer(self)
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
                from scenes.core.onboarding import BATTLE2_XP
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

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)