"""
Сцена карти світу — топографічна карта з іконками локацій,
туманом війни та анімованими переходами.
"""

import math
import random
import pygame
from .base import Scene
from ui.assets import assets
from ui.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, COLOR_HP,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, FONT_SIZE_HUGE,
)


# ══════════════════════════════════════════
#  ДАНІ ЛОКАЦІЙ
# ══════════════════════════════════════════

LOCATIONS = [
    {
        "id": "village",
        "name": "Пригорщина",
        "icon": "🏘",
        "scene": "village",
        "pos": (160, 420),
        "rec_level": 1,
        "unlocked_by": None,          # відкрита одразу
        "description": "Стартове село. Тут є крамниця та майстерня.",
        "color": (120, 200, 100),
    },
    {
        "id": "forest",
        "name": "Темний Ліс",
        "icon": "🌲",
        "scene": "forest",
        "pos": (420, 320),
        "rec_level": 1,
        "unlocked_by": "village",
        "description": "Небезпечний ліс. Тут живуть гобліни та орки.",
        "color": (60, 160, 60),
    },
    {
        "id": "tower",
        "name": "Вежа Лицаря",
        "icon": "🏰",
        "scene": "tower",
        "pos": (660, 200),
        "rec_level": 3,
        "unlocked_by": "orc",
        "description": "Вежа Темного Лицаря. Важкий бій.",
        "color": (180, 100, 60),
    },
    {
        "id": "ruins",
        "name": "Стародавні Руїни",
        "icon": "🗿",
        "scene": "ruins",
        "pos": (660, 450),
        "rec_level": 2,
        "unlocked_by": "orc",
        "description": "Таємничі руїни. Середній бій.",
        "color": (140, 120, 80),
    },
    {
        "id": "dragon",
        "name": "Лігво Дракона",
        "icon": "🐉",
        "scene": "dragon",
        "pos": (920, 300),
        "rec_level": 5,
        "unlocked_by": ["tower_after_battle", "ruins_after_battle"],
        "description": "Лігво дракона Морвета. Фінальний бос.",
        "color": (220, 60, 60),
    },
]

# Шляхи між локаціями (пари id)
PATHS = [
    ("village", "forest"),
    ("forest",  "tower"),
    ("forest",  "ruins"),
    ("tower",   "dragon"),
    ("ruins",   "dragon"),
]

NODE_RADIUS = 44
FOG_ALPHA   = 180


class WorldMapScene(Scene):
    """Карта світу."""

    def __init__(self, game):
        super().__init__(game)

        self.hovered_id  = None
        self.selected_id = None

        # Пунктирна анімація
        self._dash_offset = 0.0

        # Частинки "туману" для декору
        self._fog_particles = [
            {
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "r": random.randint(60, 180),
                "alpha": random.randint(10, 35),
                "speed": random.uniform(4, 12),
            }
            for _ in range(18)
        ]

        # Кешуємо surf туману (генерується один раз)
        self._fog_surf = None

        # Кнопка "Назад"
        from ui.components import Button
        self._back_btn = Button(30, SCREEN_HEIGHT - 70, 140, 45,
                                "← Назад", lambda: game.change_scene("village"))

    # ── Визначення стану локацій ──────────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.world_map_renderer import WorldMapRenderer
        self._renderer = WorldMapRenderer(self)
    def _is_visited(self, loc_id: str) -> bool:
        return loc_id in self.player.locations_visited

    def _is_unlocked(self, loc: dict) -> bool:
        req = loc["unlocked_by"]
        if req is None:
            return True
        if isinstance(req, list):
            return any(r in self.player.locations_visited for r in req)
        return req in self.player.locations_visited

    def _path_unlocked(self, a_id: str, b_id: str) -> bool:
        a = next(l for l in LOCATIONS if l["id"] == a_id)
        b = next(l for l in LOCATIONS if l["id"] == b_id)
        return self._is_unlocked(a) or self._is_unlocked(b)

    # ── Events ───────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        mouse_pos = pygame.mouse.get_pos()
        self._back_btn.update(mouse_pos, event.type == pygame.MOUSEBUTTONDOWN)

        if event.type == pygame.MOUSEMOTION:
            self.hovered_id = self._loc_at(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self._loc_at(mouse_pos)
            if clicked:
                loc = next(l for l in LOCATIONS if l["id"] == clicked)
                if self._is_unlocked(loc):
                    if self.selected_id == clicked:
                        # Подвійний клік — переходимо
                        self.game.change_scene(loc["scene"])
                    else:
                        self.selected_id = clicked
            else:
                self.selected_id = None

    def _loc_at(self, pos) -> str | None:
        for loc in LOCATIONS:
            dx = pos[0] - loc["pos"][0]
            dy = pos[1] - loc["pos"][1]
            if math.sqrt(dx*dx + dy*dy) < NODE_RADIUS + 6:
                return loc["id"]
        return None

    # ── Update ───────────────────────────────────────────────

    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self._back_btn.update(mouse_pos, False)
        self._dash_offset = (self._dash_offset + dt * 40) % 20

        for p in self._fog_particles:
            p["x"] += p["speed"] * dt
            if p["x"] > SCREEN_WIDTH + p["r"]:
                p["x"] = -p["r"]
                p["y"] = random.randint(0, SCREEN_HEIGHT)

    # ── Draw ─────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)