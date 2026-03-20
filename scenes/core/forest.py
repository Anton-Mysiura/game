"""
Сцена Темного Лісу.
Після первинного сюжету (гоблін → орк) переходить у режим
вільного фарму з випадковим спавном ворогів.
"""
import random
import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets
from game.enemy import make_goblin, make_orc
from game.spawn_table import pick_enemy, get_encounter_pool
from game.save_manager import autosave

LOW_HP_THRESHOLD = 0.30


class ForestScene(SceneWithBackground, SceneWithButtons):

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "forest")
        SceneWithButtons.__init__(self, game)

        self._confirm_callback = None
        self.player.locations_visited.add("forest")

        lv = self.player.locations_visited
        if "orc" in lv:
            self.stage = "free_roam"
        elif "goblin" in lv:
            self.stage = "after_goblin"
        else:
            self.stage = "intro"

        # Зворотна сумісність
        if hasattr(self.game, 'forest_progress'):
            fp = self.game.forest_progress
            if fp in ("after_orc", "fighting_orc"):
                self.stage = "free_roam"
            elif fp in ("after_goblin", "fighting_goblin"):
                self.stage = "after_goblin"

        self.dialog_panel = Panel(SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT - 300, 800, 250, alpha=True)
        self.text_box = TextBox(SCREEN_WIDTH // 2 - 370, SCREEN_HEIGHT - 270, 740, FONT_SIZE_NORMAL)
        self.buttons = []

        # Поточний ворог для free_roam (оновлюється при вході)
        self._next_enemy = None
        self._setup_stage()

    # ── Ініціалізація стадій ──────────────────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.forest_renderer import ForestRenderer
        self._renderer = ForestRenderer(self)
    def _setup_stage(self):
        if self.stage == "intro":
            self._show_intro()
        elif self.stage == "after_goblin":
            self._show_after_goblin()
        elif self.stage == "free_roam":
            self._refresh_encounter()
            self._show_free_roam()

    def _show_intro(self):
        from game.enemy_scaling import enemy_level
        plvl  = self.player.level
        g_lvl = enemy_level("goblin", plvl)
        o_lvl = enemy_level("orc", plvl)
        self.text_box.set_text(
            f"Дерева закривають небо. Тут панує вічна тінь.\n"
            f"Убивай ворогів — збирай матеріали — куй зброю!\n"
            f"👺 Гоблін  Рівень {g_lvl}   👹 Орк  Рівень {o_lvl}"
        )
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50,
                   "Продовжити", self._fight_goblin),
        ]

    def _show_after_goblin(self):
        self.text_box.set_text(
            "Гоблін повержений! Зібрано матеріали.\n"
            "Але попереду — великий орк!"
        )
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50,
                   "Продовжити", self._fight_orc),
        ]

    def _show_free_roam(self):
        """Вільне дослідження лісу — випадковий ворог кожен раз."""
        enemy = self._next_enemy
        pool  = get_encounter_pool("forest", self.player.level)

        if enemy:
            from game.enemy_scaling import level_color
            lvl_clr_name = _color_name(level_color(enemy.level, self.player.level))
            self.text_box.set_text(
                f"Ліс не спить — небезпека завжди поруч.\n"
                f"Попереду: {enemy.name}  (Рів. {enemy.level}  "
                f"❤{enemy.hp}  ⚔{enemy.attack}  🛡{enemy.defense})\n"
                f"Можливі зустрічі: {', '.join(pool[:5])}"
            )
        else:
            self.text_box.set_text("Ліс спокійний... поки що.")

        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 310, SCREEN_HEIGHT - 100, 180, 50,
                   "⚔ В бій!", self._fight_random),
            Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50,
                   "🔀 Інший ворог", self._reroll_enemy),
            Button(SCREEN_WIDTH // 2 + 120, SCREEN_HEIGHT - 100, 180, 50,
                   "🏘 До села", lambda: self.game.change_scene("village")),
            Button(SCREEN_WIDTH // 2 - 310, SCREEN_HEIGHT - 160, 180, 50,
                   "🏰 До вежі", lambda: self.game.change_scene("tower")),
            Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 160, 200, 50,
                   "🗿 До руїн", lambda: self.game.change_scene("ruins")),
        ]

    # ── Спавн ────────────────────────────────────────────────────

    def _refresh_encounter(self):
        """Генерує нового випадкового ворога."""
        self._next_enemy = pick_enemy("forest", self.player.level)

    def _reroll_enemy(self):
        """Перекидає ворога і оновлює UI."""
        self._refresh_encounter()
        self._show_free_roam()

    # ── Бої ──────────────────────────────────────────────────────

    def _try_fight(self, battle_callback):
        hp_ratio = self.player.hp / self.player.max_hp if self.player.max_hp > 0 else 1.0
        if hp_ratio < LOW_HP_THRESHOLD:
            self._confirm_callback = battle_callback
        else:
            battle_callback()

    def _confirm_fight(self):
        cb = self._confirm_callback
        self._confirm_callback = None
        if cb:
            cb()

    def _cancel_fight(self):
        self._confirm_callback = None

    def _fight_goblin(self):
        lvl = self.player.level
        self._try_fight(lambda: self.game.change_scene(
            "battle", enemy=make_goblin(lvl),
            return_scene="forest", background_name="forest_battle"
        ))

    def _fight_orc(self):
        lvl = self.player.level
        self._try_fight(lambda: self.game.change_scene(
            "battle", enemy=make_orc(lvl),
            return_scene="forest", background_name="forest_battle"
        ))

    def _fight_random(self):
        if not self._next_enemy:
            self._refresh_encounter()
        enemy = self._next_enemy
        self._next_enemy = None   # після бою — новий ворог
        if enemy:
            self._try_fight(lambda: self.game.change_scene(
                "battle", enemy=enemy,
                return_scene="forest_free", background_name="forest_battle"
            ))

    # ── Події ────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if self._confirm_callback is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                yes_rect = pygame.Rect(cx - 160, cy + 60, 140, 44)
                no_rect  = pygame.Rect(cx + 20,  cy + 60, 140, 44)
                if yes_rect.collidepoint(mx, my):
                    self._confirm_fight()
                elif no_rect.collidepoint(mx, my):
                    self._cancel_fight()
            return
        super().handle_event(event)

    def on_enter(self):
        super().on_enter()
        lv = self.player.locations_visited

        # Повернення після сюжетного бою з гобліном
        if self.stage == "intro":
            if hasattr(self.game, 'forest_progress') and \
               self.game.forest_progress == "fighting_goblin":
                self.player.locations_visited.add("goblin")
                self.stage = "after_goblin"
                self._setup_stage()
                autosave(self.player)

        # Повернення після сюжетного бою з орком
        elif self.stage == "after_goblin":
            if hasattr(self.game, 'forest_progress') and \
               self.game.forest_progress == "fighting_orc":
                self.player.locations_visited.add("orc")
                self.stage = "free_roam"
                self._setup_stage()
                autosave(self.player)

        # Повернення після вільного бою
        elif self.stage == "free_roam":
            if self.game.scene_data.get("from_battle") == "forest_free":
                self.game.scene_data.pop("from_battle", None)
                self._refresh_encounter()
                self._show_free_roam()

    # ── Малювання ────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)
def _color_name(clr: tuple) -> str:
    r, g, b = clr[:3]
    if r > 180 and g < 100:  return "небезпечний"
    if r > 180 and g > 100:  return "сильніший"
    if g > 180:               return "слабший"
    return "рівний"