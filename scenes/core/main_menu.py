"""
Головне меню + вибір/створення збережень.
"""

import pygame
import random
from datetime import datetime
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel, TextBox, ScrollableList
from ui.constants import *
from ui.assets import assets
from game.save_manager import SaveManager
from game.animation import AnimationController, Animation, AnimationLoader


def _build_menu_character(character_id: str = "player", scale: float = 3.5) -> AnimationController:
    """
    Будує AnimationController для персонажа в головному меню / селі.
    Підтримує як нових героїв (heroes.py AnimConfig) так і legacy папки.
    """
    from game.heroes import HEROES

    ctrl = AnimationController()

    # Нова система — hero_id з каталогу
    hero = HEROES.get(character_id)
    if hero:
        cfg = hero.anim
        base_path = cfg.path()
        fh = cfg.frame_h

        # Idle
        fname, count = cfg.idle
        if fname and count:
            path = base_path / f"{fname}.png"
            if not path.exists():
                # case-insensitive fallback
                for p in base_path.iterdir():
                    if p.stem.lower() == fname.lower() and p.suffix.lower() == '.png':
                        path = p
                        break
            idle_frames = AnimationLoader.load_spritesheet(
                path, frame_width=fh, frame_height=fh, frame_count=count, scale=scale)
            ctrl.add_animation("idle", Animation("idle", idle_frames, frame_duration=0.12, loop=True))

        # Idle2
        fname2, count2 = cfg.idle2
        if fname2 and count2:
            path2 = base_path / f"{fname2}.png"
            if path2.exists():
                v_frames = AnimationLoader.load_spritesheet(
                    path2, frame_width=fh, frame_height=fh, frame_count=count2, scale=scale)
                ctrl.add_animation("idle2", Animation("idle2", v_frames, frame_duration=0.12, loop=False))

        ctrl.play("idle")
        return ctrl

    # Legacy fallback (старі character2/3/4/player або enemy)
    base_path = ANIMATIONS_DIR / character_id
    frame_count = {"player": 13, "character2": 6, "character3": 7, "character4": 6}.get(character_id, 6)
    idle_frames = AnimationLoader.load_spritesheet(
        base_path / "idle.png",
        frame_width=128, frame_height=128,
        frame_count=frame_count, scale=scale
    )
    ctrl.add_animation("idle", Animation("idle", idle_frames, frame_duration=0.12, loop=True))
    variant_path = base_path / "idle2.png"
    if variant_path.exists():
        v_frames = AnimationLoader.load_spritesheet(
            variant_path, frame_width=128, frame_height=128,
            frame_count=AnimationLoader.count_frames(variant_path, 128), scale=scale)
        ctrl.add_animation("idle2", Animation("idle2", v_frames, frame_duration=0.12, loop=False))
    ctrl.play("idle")
    return ctrl


class MainMenuScene(SceneWithBackground, SceneWithButtons):
    """Головне меню гри."""

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "main_menu_bg")
        SceneWithButtons.__init__(self, game)

        center_x = SCREEN_WIDTH // 2

        self.buttons = [
            Button(center_x - 100, 300, 200, 60, "Нова гра",
                   lambda: self.show_new_game_menu()),
            Button(center_x - 100, 380, 200, 60, "Завантажити",
                   lambda: self.show_load_menu()),
            Button(center_x - 100, 460, 200, 60, "Вихід",
                   lambda: self.game.quit_game()),
        ]

        self.state = "main"
        self.saves_list = []
        self.selected_save_index = -1
        self.name_input = ""
        self.save_name_input = ""

        self.load_buttons = []
        self.new_game_buttons = []
        self.overwrite_buttons = []

        # ── Анімовані персонажі (4 штуки, рандомні з каталогу) ──
        import random as _rnd
        from game.heroes import HEROES

        # Беремо 4 різних рандомних героя
        all_ids = list(HEROES.keys())
        chosen = _rnd.sample(all_ids, min(4, len(all_ids)))

        # Позиції: 2 зліва (дивляться вправо), 2 справа (дивляться вліво)
        positions = [
            (20,                   False),
            (190,                  False),
            (SCREEN_WIDTH - 548,   True),
            (SCREEN_WIDTH - 378,   True),
        ]

        self._chars = []
        for hero_id, (x, flip) in zip(chosen, positions):
            try:
                ctrl = _build_menu_character(hero_id, scale=2.8)
            except Exception:
                ctrl = None
            self._chars.append({"ctrl": ctrl, "x": x, "flip": flip})

        self._float_t = 0.0

        # Тінь
        self._shadow = pygame.Surface((120, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(self._shadow, (0, 0, 0, 70), self._shadow.get_rect())

        # Підключаємо renderer (малювання)
        from scenes.ui.main_menu_renderer import MainMenuRenderer
        self._renderer = MainMenuRenderer(self)
    def show_new_game_menu(self):
        """Показує меню створення нової гри."""
        self.saves_list = SaveManager.get_all_saves()

        if not self.saves_list:
            # Немає збережень — одразу до введення імені
            self.state = "name_input"
            self.save_name_input = "Default"
        else:
            # Є збереження — показуємо вибір
            self.state = "new_game"
            self._create_new_game_buttons()

    def show_load_menu(self):
        """Показує меню завантаження."""
        self.saves_list = SaveManager.get_all_saves()

        if not self.saves_list:
            # Немає збережень
            self.state = "main"
            return

        self.state = "load"
        self.selected_save_index = -1
        self._create_load_buttons()

    def _create_new_game_buttons(self):
        """Створює кнопки для меню нової гри."""
        self.new_game_buttons = [
            Button(SCREEN_WIDTH // 2 - 200, 250, 400, 60, "Перезаписати існуюче",
                   lambda: self._switch_to_overwrite()),
            Button(SCREEN_WIDTH // 2 - 200, 330, 400, 60, "Створити новий світ",
                   lambda: self._create_new_world()),
            Button(SCREEN_WIDTH // 2 - 100, 450, 200, 50, "Назад",
                   lambda: self._back_to_main()),
        ]

    def _create_load_buttons(self):
        """Створює кнопки для меню завантаження."""
        self.load_buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 600, 200, 50, "Назад",
                   lambda: self._back_to_main())
        ]

    def _create_overwrite_buttons(self):
        """Створює кнопки для меню перезапису."""
        self.overwrite_buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 600, 200, 50, "Назад",
                   lambda: self._switch_to_new_game())
        ]

    def _switch_to_overwrite(self):
        """Перехід до вибору збереження для перезапису."""
        self.state = "overwrite"
        self._create_overwrite_buttons()

    def _create_new_world(self):
        """Створює новий світ."""
        self.state = "name_input"
        self.save_name_input = SaveManager.get_unique_name(
            f"Save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    def _back_to_main(self):
        """Повернення до головного меню."""
        self.state = "main"

    def _switch_to_new_game(self):
        """Повернення до меню нової гри."""
        self.state = "new_game"

    def handle_event(self, event: pygame.event.Event):
        """Обробка подій."""
        if self.state == "main":
            super().handle_event(event)

        elif self.state == "load":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # Кнопки управління
                for btn in self.load_buttons:
                    btn.update(mouse_pos, True)

                # Клік по списку збережень
                y = 200
                for i, save in enumerate(self.saves_list):
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, y, 600, 60)
                    if btn_rect.collidepoint(mouse_pos):
                        if save["valid"]:
                            self.game.load_game(save["filename"])
                        break
                    y += 70

        elif self.state == "new_game":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for btn in self.new_game_buttons:
                    btn.update(mouse_pos, True)

        elif self.state == "overwrite":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # Кнопки управління
                for btn in self.overwrite_buttons:
                    btn.update(mouse_pos, True)

                # Клік по списку
                y = 200
                for i, save in enumerate(self.saves_list):
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, y, 600, 60)
                    if btn_rect.collidepoint(mouse_pos):
                        # Перезаписуємо це збереження
                        SaveManager.delete_save(save["filename"])
                        self.save_name_input = save["filename"]
                        self.state = "name_input"
                        break
                    y += 70

        elif self.state == "name_input":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.name_input.strip():
                    # Зберігаємо ім'я і переходимо до рулетки героїв
                    name = self.name_input.strip()
                    save = self.save_name_input
                    self.game.scene_data["pending_player_name"] = name
                    self.game.scene_data["pending_save_name"] = save
                    # Створюємо гравця одразу, щоб hero_roulette мав доступ до roster
                    self.game.start_new_game_silent(name, save)
                    self.game.change_scene("hero_roulette")
                elif event.key == pygame.K_BACKSPACE:
                    self.name_input = self.name_input[:-1]
                elif event.unicode.isprintable() and len(self.name_input) < 20:
                    self.name_input += event.unicode

    def update(self, dt: float):
        """Оновлення."""
        mouse_pos = pygame.mouse.get_pos()

        if self.state == "main":
            for btn in self.buttons:
                btn.update(mouse_pos, False)
        elif self.state == "new_game":
            for btn in self.new_game_buttons:
                btn.update(mouse_pos, False)
        elif self.state == "load":
            for btn in self.load_buttons:
                btn.update(mouse_pos, False)
        elif self.state == "overwrite":
            for btn in self.overwrite_buttons:
                btn.update(mouse_pos, False)

        # Анімація всіх персонажів
        self._float_t += dt
        for c in self._chars:
            if c["ctrl"]:
                c["ctrl"].update(dt)

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)