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
        screen.fill((20, 15, 25))

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("Вибери персонажа", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        font_name = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_desc = assets.get_font(FONT_SIZE_SMALL)

        for i, card in enumerate(self.cards):
            char = card["char"]
            rect = card["rect"]
            is_selected = i == self.selected

            # Фон картки
            bg_color = (50, 40, 60) if not is_selected else (70, 55, 90)
            pygame.draw.rect(screen, bg_color, rect, border_radius=14)
            border_color = COLOR_GOLD if is_selected else (80, 65, 100)
            pygame.draw.rect(screen, border_color, rect, 3 if is_selected else 1, border_radius=14)

            # Зона анімації
            preview_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, 220)
            pygame.draw.rect(screen, (30, 25, 40), preview_rect, border_radius=10)

            # Поточний кадр з AnimationController
            frame = self.anim_controllers[i].get_current_frame()
            if frame:
                fx = preview_rect.centerx - frame.get_width() // 2
                fy = preview_rect.centery - frame.get_height() // 2
                screen.blit(frame, (fx, fy))

            # Тінь під персонажем
            shadow = pygame.Surface((120, 12), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 60))
            screen.blit(shadow, (preview_rect.centerx - 60, preview_rect.bottom - 18))

            # Ім'я
            name_surf = font_name.render(char["name"], True, COLOR_GOLD if is_selected else COLOR_TEXT)
            screen.blit(name_surf, (rect.centerx - name_surf.get_width() // 2, rect.y + 238))

            # Опис
            desc_surf = font_desc.render(char["description"], True, COLOR_TEXT_DIM)
            screen.blit(desc_surf, (rect.centerx - desc_surf.get_width() // 2, rect.y + 272))

            # Атаки
            atk_surf = font_desc.render(f"Атак: {char['attacks']}", True, COLOR_HP)
            screen.blit(atk_surf, (rect.centerx - atk_surf.get_width() // 2, rect.y + 300))

            # Стрілка вибору
            if is_selected:
                arrow = font_desc.render("▼ Вибрано ▼", True, COLOR_GOLD)
                screen.blit(arrow, (rect.centerx - arrow.get_width() // 2, rect.bottom + 8))

        # Підказка
        hint = font_desc.render("← → для вибору  |  Enter або клік для підтвердження", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 155))

        self.confirm_btn.draw(screen)