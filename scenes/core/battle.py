"""
Сцена бою (гравець проти ворога).
"""

import pygame
import random
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel, ProgressBar, TextBox
from ui.constants import *
from ui.assets import assets
from game.save_manager import autosave
from game.enemy import Enemy


class BattleScene(SceneWithBackground, SceneWithButtons):
    """Сцена бою."""

    def __init__(self, game, enemy: Enemy, return_scene: str = "village"):
        SceneWithBackground.__init__(self, game, "forest")
        SceneWithButtons.__init__(self, game)

        self.enemy = enemy
        self.return_scene = return_scene
        self.battle_log = []
        self.battle_over = False
        self.player_won = False
        self.animation_timer = 0.0

        # Кнопки дій
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 250, 600, 150, 50, "⚔ Атака",
                   lambda: self._player_attack(), enabled=True),
            Button(SCREEN_WIDTH // 2 - 75, 600, 150, 50, "🧪 Зілля",
                   lambda: self._use_potion(), enabled=True),
            Button(SCREEN_WIDTH // 2 + 100, 600, 150, 50, "🏃 Втеча",
                   lambda: self._try_flee(), enabled=True),
        ]

        # UI елементи
        self.battle_panel = Panel(100, 50, SCREEN_WIDTH - 200, 500, alpha=True)
        self.player_hp_bar = ProgressBar(150, 430, 200, 30, COLOR_HP)
        self.enemy_hp_bar = ProgressBar(SCREEN_WIDTH - 350, 430, 200, 30, COLOR_HP)

        # Лог
        self.log_box = TextBox(150, 480, SCREEN_WIDTH - 300, FONT_SIZE_SMALL)

        # Початкове повідомлення
        self._add_log(f"{enemy.name} з'являється перед тобою!")

        # Підключаємо renderer (малювання)
        from scenes.ui.battle_renderer import BattleRenderer
        self._renderer = BattleRenderer(self)
    def _add_log(self, message: str):
        """Додає повідомлення до логу."""
        self.battle_log.append(message)
        if len(self.battle_log) > 5:
            self.battle_log.pop(0)

        # Оновлюємо текстовий блок
        log_text = "\n".join(self.battle_log)
        self.log_box.set_text(log_text)

    def _player_attack(self):
        """Гравець атакує."""
        if self.battle_over:
            return

        # Гравець б'є
        dmg = self.player.deal_damage()
        taken = self.enemy.take_damage(dmg)
        self._add_log(f"Ти завдаєш {taken} шкоди!")

        # Перевірка смерті ворога
        if not self.enemy.is_alive:
            self._end_battle(won=True)
            return

        # Хід ворога
        self._enemy_turn()

    def _enemy_turn(self):
        """Хід ворога."""
        if self.battle_over:
            return

        dmg = self.enemy.deal_damage()
        taken = self.player.take_damage(dmg)
        self._add_log(f"{self.enemy.name} завдає {taken} шкоди!")

        # Перевірка смерті гравця
        if not self.player.is_alive:
            self._end_battle(won=False)

    def _use_potion(self):
        """Використання зілля."""
        if self.battle_over:
            return

        # Знаходимо зілля в інвентарі
        potions = [item for item in self.player.inventory if item.item_type == "potion"]

        if not potions:
            self._add_log("Немає зілля!")
            return

        # Використовуємо перше зілля
        potion = potions[0]
        msg = self.player.use_potion(potion)
        self._add_log(msg)

        # Хід ворога
        self._enemy_turn()

    def _try_flee(self):
        """Спроба втечі."""
        if self.battle_over:
            return

        if random.random() < 0.5:
            self._add_log("Вдалося втекти!")
            self.battle_over = True
            self.animation_timer = 1.5
        else:
            self._add_log("Не вдалося втекти!")
            self._enemy_turn()

    def _end_battle(self, won: bool):
        """Завершення бою."""
        self.battle_over = True
        self.player_won = won
        self.animation_timer = 2.5

        # Вимикаємо кнопки
        for btn in self.buttons:
            btn.enabled = False

        if won:
            self._add_log(f"{self.enemy.name} переможено!")

            # Нагороди
            self.player.gain_xp(self.enemy.xp_reward)
            self.player.gold += self.enemy.gold_reward

            # Лут предмети
            for item in self.enemy.loot_items:
                if random.random() < 0.55:
                    self.player.inventory.append(item)
                    self._add_log(f"Отримано: {item.name}")

            # Лут матеріали
            for mat_id, qty in self.enemy.loot_materials.items():
                self.player.add_material(mat_id, qty)
                from game.data import MATERIALS
                mat_name = MATERIALS[mat_id].name
                self._add_log(f"Отримано: {mat_name} x{qty}")

            # Автозбереження
            autosave(self.player)
            # Трекінг досягнень
            self.player.enemies_killed += 1

            # Підрахунок за типом ворога
            enemy_name = self.enemy.name.lower()
            if "гоблін" in enemy_name:
                self.player.goblins_killed += 1
            elif "орк" in enemy_name:
                self.player.orcs_killed += 1
            elif "лицар" in enemy_name:
                self.player.knights_killed += 1
            elif "дракон" in enemy_name:
                self.player.dragons_killed += 1

            # Перевірка досягнень
            from game.achievements import AchievementManager
            newly_unlocked = AchievementManager.check_all(self.player)
            # Показуємо сповіщення
            for ach_id in newly_unlocked:
                self.game.show_achievement(ach_id)
        else:
            self._add_log("Ти загинув...")
            autosave(self.player)
            self.player.deaths += 1
            autosave(self.player)

    def update(self, dt: float):
        """Оновлення."""
        super().update(dt)

        # Таймер завершення бою
        if self.battle_over:
            self.animation_timer -= dt
            if self.animation_timer <= 0:
                if self.player_won:
                    # Перевірка туторіалу після першого бою
                    from game.tutorial_manager import TutorialManager
                    tutorial = TutorialManager.maybe_tutorial(self.player, "tut_first_craft")
                    if tutorial:
                        self.game.change_scene("tutorial",
                                               tutorial_data=[{
                                                   "id": "tut_first_craft",
                                                   "title": "🔨 Перший крафт",
                                                   "pages": tutorial
                                               }],
                                               next_scene=self.return_scene)
                    elif self.return_scene == "forest":
                        # Шанс на рандомну подію після бою в лісі
                        from game.forest_events import roll_event
                        event = roll_event(chance=0.45)
                        if event:
                            self.game.change_scene(
                                "forest_event",
                                forest_event=event,
                                return_scene="forest",
                            )
                        else:
                            self.game.change_scene(self.return_scene)
                    else:
                        self.game.change_scene(self.return_scene)
                else:
                    # Смерть гравця
                    self.game.change_scene("death")

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)