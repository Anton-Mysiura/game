"""
Сцена вибору персонажа з анімованими idle превью.
"""

import pygame
from .base import Scene
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.animation import AnimationController, Animation, AnimationLoader

CHARACTERS = [
    {
        "id": "player",
        "name": "Аркан",
        "description": "3 атаками",
        "attacks": 3,
        "color": (200, 100, 50),
    },
    {
        "id": "character2",
        "name": "Зефір",
        "description": "2 атаками",
        "attacks": 2,
        "color": (80, 160, 80),
    },
    {
        "id": "character3",
        "name": "Сайра",
        "description": "3 атаками",
        "attacks": 3,
        "color": (80, 100, 200),
    },
    {
        "id": "character4",
        "name": "Торвал",
        "description": "3 атаками",
        "attacks": 3,
        "color": (160, 140, 60),
    },
]

# Кількість кадрів основного idle для кожного персонажа
IDLE_FRAME_COUNTS = {
    "player":     13,
    "character2": 6,
    "character3": 7,
    "character4": 6,
}


def _build_anim_controller(character_id: str, scale: float = 2.0) -> AnimationController:
    """Створює AnimationController з idle + idle variants для превью."""
    from ui.constants import ANIMATIONS_DIR

    ctrl = AnimationController()
    base_path = ANIMATIONS_DIR / character_id
    frame_count = IDLE_FRAME_COUNTS.get(character_id, 6)

    # Основний idle
    idle_frames = AnimationLoader.load_spritesheet(
        base_path / "idle.png",
        frame_width=128, frame_height=128,
        frame_count=frame_count, scale=scale
    )
    ctrl.add_animation("idle",
        Animation("idle", idle_frames, frame_duration=0.12, loop=True))

    # Idle variants (idle2.png, idle3.png, ...) — автоматично
    variant_index = 2
    while True:
        variant_path = base_path / f"idle{variant_index}.png"
        if not variant_path.exists():
            break
        variant_frames = AnimationLoader.load_spritesheet(
            variant_path,
            frame_width=128, frame_height=128,
            frame_count=AnimationLoader.count_frames(variant_path, 128),
            scale=scale
        )
        anim_name = f"idle{variant_index}"
        ctrl.add_animation(anim_name,
            Animation(anim_name, variant_frames, frame_duration=0.12, loop=False))
        variant_index += 1

    ctrl.play("idle")
    return ctrl


class CharacterSelectScene(Scene):
    """Екран вибору персонажа."""

    def __init__(self, game):
        super().__init__(game)
        self.selected = 0

        # AnimationController для кожного персонажа
        self.anim_controllers = [
            _build_anim_controller(char["id"], scale=2.0)
            for char in CHARACTERS
        ]

        self.cards = []
        self._build_cards()

        self.confirm_btn = Button(
            SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 110, 240, 55,
            "Почати гру ▶", lambda: self._confirm()
        )

        # Підключаємо renderer (малювання)
        from scenes.ui.character_select_renderer import CharacterSelectRenderer
        self._renderer = CharacterSelectRenderer(self)
    def _build_cards(self):
        total = len(CHARACTERS)
        card_w, card_h = 280, 360
        spacing = 60
        total_w = total * card_w + (total - 1) * spacing
        start_x = SCREEN_WIDTH // 2 - total_w // 2

        self.cards = []
        for i, char in enumerate(CHARACTERS):
            x = start_x + i * (card_w + spacing)
            y = SCREEN_HEIGHT // 2 - card_h // 2 - 30
            self.cards.append({"rect": pygame.Rect(x, y, card_w, card_h), "char": char})

    def _confirm(self):
        char = CHARACTERS[self.selected]
        self.game.scene_data["character_id"] = char["id"]
        player_name = self.game.scene_data.get("pending_player_name", "Hero")
        save_name = self.game.scene_data.get("pending_save_name", "Default")
        self.game.start_new_game(player_name, save_name)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            self.confirm_btn.update(mouse_pos, True)
            for i, card in enumerate(self.cards):
                if card["rect"].collidepoint(mouse_pos):
                    self.selected = i

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = max(0, self.selected - 1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = min(len(CHARACTERS) - 1, self.selected + 1)
            elif event.key == pygame.K_RETURN:
                self._confirm()

    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.confirm_btn.update(mouse_pos, False)

        # Оновлюємо всі AnimationController-и
        for ctrl in self.anim_controllers:
            ctrl.update(dt)

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)