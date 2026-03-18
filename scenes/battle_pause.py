"""
Логіка паузи, налаштувань та дій під час паузи у бою.
"""

import logging
import random
import pygame
log = logging.getLogger(__name__)
from game.save_manager import autosave
from game.sound_manager import sounds


class BattlePauseMixin:
    """Міксін з логікою паузи для FightingBattleScene."""

    def _pause(self):
        """Пауза."""
        self.paused = True
        sounds.pause_music()

    def _unpause(self):
        """Зняття паузи."""
        self.paused = False
        sounds.unpause_music()

    def _open_settings(self):
        """Відкриває налаштування."""
        self.show_settings = True

    def _close_settings(self):
        """Закриває налаштування."""
        self.show_settings = False

    def _use_potion(self):
        """Використання зілля під час паузи."""
        potions = [item for item in self.player.inventory if item.item_type == "potion"]

        if not potions:
            log.info("Гравець спробував використати зілля — інвентар порожній")
            return

        potion = potions[0]
        msg = self.player.use_potion(potion)

        # Оновлюємо HP бійця
        self.player_fighter.hp = self.player.hp

        autosave(self.player)
        log.info("%s", msg)
        self._unpause()

    def _try_flee(self):
        """Спроба втечі з бою."""
        if random.random() < 0.5:
            log.info("Гравець втік з бою")
            self.player.hp = self.player_fighter.hp
            autosave(self.player)
            self.game.change_scene(self.return_scene)
        else:
            log.info("Спроба втечі невдала")
            self._unpause()

    def _exit_to_village(self):
        """Прямий вихід до села (зберегти прогрес, бій незакінчений)."""
        from ui.confirm_dialog import ConfirmDialog
        def confirmed():
            self.player.hp = self.player_fighter.hp
            autosave(self.player)
            self.game._pending_battle = self
            self.game.change_scene("village")
        self._confirm_exit = ConfirmDialog(
            "Вийти до села?",
            "Прогрес бою буде втрачено.",
            on_yes=confirmed,
            yes_lbl="🏘 Вийти",
            no_lbl="Залишитись",
            danger=True,
        )

    def _handle_settings_click(self, mouse_pos):
        """Обробляє кліки у вікні налаштувань."""
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Кнопка назад
        back_rect = pygame.Rect(cx - 100, cy + 150, 200, 45)
        if back_rect.collidepoint(mouse_pos):
            self._close_settings()
            return

        # Слайдер музики
        music_track = pygame.Rect(cx - 150, cy - 30, 300, 12)
        if music_track.collidepoint(mouse_pos):
            val = (mouse_pos[0] - music_track.x) / music_track.width
            sounds.set_music_volume(max(0.0, min(1.0, val)))
            return

        # Слайдер звуків
        sfx_track = pygame.Rect(cx - 150, cy + 50, 300, 12)
        if sfx_track.collidepoint(mouse_pos):
            val = (mouse_pos[0] - sfx_track.x) / sfx_track.width
            sounds.set_sfx_volume(max(0.0, min(1.0, val)))
            return

        # Чекбокс музики
        music_cb = pygame.Rect(cx + 170, cy - 38, 24, 24)
        if music_cb.collidepoint(mouse_pos):
            sounds.music_enabled = not sounds.music_enabled
            if sounds.music_enabled:
                sounds.play_music("battle music loop.flac")
            else:
                sounds.stop_music()
            return

        # Чекбокс звуків
        sfx_cb = pygame.Rect(cx + 170, cy + 42, 24, 24)
        if sfx_cb.collidepoint(mouse_pos):
            sounds.enabled = not sounds.enabled
            return

        # Чекбокс чисел шкоди
        dmg_cb = pygame.Rect(cx + 170, cy + 112, 24, 24)
        if dmg_cb.collidepoint(mouse_pos):
            sounds.show_damage_numbers = not sounds.show_damage_numbers


# Імпорт констант тут щоб уникнути циклічних залежностей
from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT  # noqa: E402