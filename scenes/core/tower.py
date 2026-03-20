"""
Сцена Вежі Темного Лицаря.
Перший візит — бос. Повторні — вільний спавн з таблиці вежі.
"""
import pygame
from .base import DungeonScene, SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets
from game.enemy import make_dark_knight
from game.spawn_table import pick_enemy, get_encounter_pool
from game.enemy_scaling import level_color
from game.save_manager import autosave


class TowerScene(DungeonScene):
    """Вежа Темного Лицаря — бос при першому візиті, потім вільний спавн."""

    BACKGROUND   = "tower"
    TITLE        = "🏰 Вежа Темного Лицаря"
    RETURN_SCENE = "tower_after_battle"
    GOLD_REWARD  = 20
    FIGHT_LABEL  = "⚔ У бій!"
    ENEMY_FACTORY = staticmethod(make_dark_knight)

    INTRO_TEXT = (
        "Вежа височить над лісом. Темний Лицар чекає на тебе.\n"
        "Це буде важкий бій — переконайся що у тебе є зілля!"
    )
    AFTER_TEXT = (
        "Темний Лицар переможений!\n\n"
        "Отримано: +20 золота\n\n"
        "Вежа тепер відкрита для патрулювання.\n"
        "Поверхи вежі охороняють різні страхіття."
    )

    def __init__(self, game):
        # Якщо вежу вже пройшли — вільний режим
        self._free_roam = "tower_after_battle" in game.player.locations_visited
        self._next_enemy = None
        if self._free_roam:
            # Ініціалізуємо як звичайну сцену, не DungeonScene
            SceneWithBackground.__init__(self, game, self.BACKGROUND)
            SceneWithButtons.__init__(self, game)
            self.dialog_panel = Panel(SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT - 300, 800, 250, alpha=True)
            self.text_box = TextBox(SCREEN_WIDTH // 2 - 370, SCREEN_HEIGHT - 270, 740, FONT_SIZE_NORMAL)
            self._refresh_encounter()
            self._show_free_roam()
        else:
            super().__init__(game)

        # Підключаємо renderer (малювання)
        from scenes.ui.tower_renderer import TowerRenderer
        self._renderer = TowerRenderer(self)
    def _refresh_encounter(self):
        self._next_enemy = pick_enemy("tower", self.player.level)

    def _reroll(self):
        self._refresh_encounter()
        self._show_free_roam()

    def _show_free_roam(self):
        enemy = self._next_enemy
        pool  = get_encounter_pool("tower", self.player.level)
        if enemy:
            self.text_box.set_text(
                f"Вежа повна небезпек навіть без свого господаря.\n"
                f"Попереду: {enemy.name}  (Рів. {enemy.level}  "
                f"❤{enemy.hp}  ⚔{enemy.attack}  🛡{enemy.defense})\n"
                f"Можливі вороги: {', '.join(pool[:4])}"
            )
        else:
            self.text_box.set_text("Вежа тихо... поки що.")

        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 310, SCREEN_HEIGHT - 100, 180, 50,
                   "⚔ В бій!", self._fight_random),
            Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50,
                   "🔀 Інший ворог", self._reroll),
            Button(SCREEN_WIDTH // 2 + 120, SCREEN_HEIGHT - 100, 180, 50,
                   "🏘 До села", lambda: self.game.change_scene("village")),
        ]

    def _fight_random(self):
        if not self._next_enemy:
            self._refresh_encounter()
        enemy = self._next_enemy
        self._next_enemy = None
        if enemy:
            self.game.change_scene(
                "battle", enemy=enemy,
                return_scene="tower_free", background_name="tower"
            )

    def on_enter(self):
        if self._free_roam:
            if self.game.scene_data.get("from_battle") == "tower_free":
                self.game.scene_data.pop("from_battle", None)
                self._refresh_encounter()
                self._show_free_roam()
        else:
            super().on_enter()
            # Перевіряємо чи щойно перемогли боса
            if "tower_after_battle" in self.player.locations_visited and not self._free_roam:
                self._free_roam = True
                self._refresh_encounter()
                self._show_free_roam()

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)