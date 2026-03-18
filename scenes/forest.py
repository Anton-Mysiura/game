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
        super().draw(screen)

        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("🌲 Темний Ліс", True, COLOR_GOLD)
        screen.blit(font_title.render("🌲 Темний Ліс", True, (0, 0, 0)),
                    (SCREEN_WIDTH // 2 - title.get_width() // 2 + 2, 52))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # Лічильник вбивств у free_roam
        if self.stage == "free_roam":
            font_s = assets.get_font(FONT_SIZE_SMALL)
            kills  = font_s.render(
                f"⚔ Вбито: {self.player.enemies_killed}   "
                f"👺 Гоблінів: {self.player.goblins_killed}   "
                f"👹 Орків: {self.player.orcs_killed}",
                True, COLOR_TEXT_DIM)
            screen.blit(kills, (40, 96))

            # Показуємо інформацію про поточного ворога
            if self._next_enemy:
                self._draw_enemy_card(screen)

        self.dialog_panel.draw(screen)
        self.text_box.draw(screen)
        self.draw_buttons(screen)

        if self._confirm_callback is not None:
            self._draw_low_hp_confirm(screen)

    def _draw_enemy_card(self, screen):
        """Міні-картка ворога у правому куті."""
        enemy = self._next_enemy
        if not enemy:
            return
        from game.enemy_scaling import level_color

        cx = SCREEN_WIDTH - 210
        cy = 110
        cw, ch = 190, 100

        surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        surf.fill((18, 14, 10, 210))
        lclr = level_color(enemy.level, self.player.level)
        pygame.draw.rect(surf, lclr, surf.get_rect(), 2, border_radius=8)
        screen.blit(surf, (cx, cy))

        font  = assets.get_font(FONT_SIZE_SMALL)
        font_h = assets.get_font(FONT_SIZE_NORMAL, bold=True)

        screen.blit(font_h.render(enemy.name, True, COLOR_TEXT), (cx + 8, cy + 6))
        screen.blit(font.render(f"Рівень {enemy.level}", True, lclr), (cx + 8, cy + 26))
        screen.blit(font.render(f"❤ {enemy.hp}   ⚔ {enemy.attack}   🛡 {enemy.defense}",
                                True, COLOR_TEXT_DIM), (cx + 8, cy + 46))
        # Очікуваний лут
        if enemy.loot_materials:
            mats = [k for k, v in enemy.loot_materials.items() if v > 0]
            from game.data import MATERIALS
            icons = "".join(MATERIALS[m].icon for m in mats[:4] if m in MATERIALS)
            screen.blit(font.render(f"Лут: {icons}", True, COLOR_GOLD), (cx + 8, cy + 66))

    def _draw_low_hp_confirm(self, screen: pygame.Surface):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(cx - 220, cy - 110, 440, 210)
        pygame.draw.rect(screen, (45, 20, 20), panel_rect, border_radius=14)
        pygame.draw.rect(screen, COLOR_ERROR, panel_rect, 2, border_radius=14)
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        warn = font_title.render("⚠ Небезпечно низьке HP!", True, COLOR_ERROR)
        screen.blit(warn, (cx - warn.get_width() // 2, cy - 95))
        font = assets.get_font(FONT_SIZE_NORMAL)
        hp_text = font.render(
            f"У тебе лише {self.player.hp} / {self.player.max_hp} HP.",
            True, COLOR_TEXT)
        screen.blit(hp_text, (cx - hp_text.get_width() // 2, cy - 48))
        question = font.render("Все одно йти в бій?", True, COLOR_TEXT_DIM)
        screen.blit(question, (cx - question.get_width() // 2, cy - 18))
        mouse_pos = pygame.mouse.get_pos()
        yes_rect = pygame.Rect(cx - 160, cy + 60, 140, 44)
        no_rect  = pygame.Rect(cx + 20,  cy + 60, 140, 44)
        yes_color = (160, 40, 40) if yes_rect.collidepoint(mouse_pos) else (120, 30, 30)
        no_color  = COLOR_BTN_HOVER if no_rect.collidepoint(mouse_pos) else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, yes_color, yes_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_ERROR, yes_rect, 2, border_radius=10)
        pygame.draw.rect(screen, no_color,  no_rect,  border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, no_rect,  2, border_radius=10)
        yes_lbl = font.render("⚔ Так, вперед!", True, COLOR_TEXT)
        no_lbl  = font.render("↩ Назад",        True, COLOR_TEXT)
        screen.blit(yes_lbl, (yes_rect.centerx - yes_lbl.get_width() // 2,
                               yes_rect.centery - yes_lbl.get_height() // 2))
        screen.blit(no_lbl,  (no_rect.centerx  - no_lbl.get_width()  // 2,
                               no_rect.centery  - no_lbl.get_height()  // 2))


def _color_name(clr: tuple) -> str:
    r, g, b = clr[:3]
    if r > 180 and g < 100:  return "небезпечний"
    if r > 180 and g > 100:  return "сильніший"
    if g > 180:               return "слабший"
    return "рівний"