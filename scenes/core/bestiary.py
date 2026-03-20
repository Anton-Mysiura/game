"""
Бестіарій — каталог усіх ворогів яких зустрічав гравець.
"""

import pygame
from .base import Scene
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.data import MATERIALS, ITEMS


# ══════════════════════════════════════════
#  РЕЄСТР ВОРОГІВ
#  Статичні дані — не залежать від рандому фабрик
# ══════════════════════════════════════════

ENEMY_REGISTRY = [
    {
        "sprite_name": "goblin",
        "name": "Гоблін",
        "icon": "👺",
        "description": "Дрібний, але підступний. Полює зграями на самотніх мандрівників у лісі.",
        "location": "🌲 Темний Ліс",
        "hp": 30,
        "attack": "7–11",
        "defense": 1,
        "xp_reward": 15,
        "gold_reward": 5,
        "loot_items": ["small_potion"],
        "loot_materials": {"wood": "1–2", "bone": "1"},
        "item_drop_chance": 55,
        "difficulty": 1,
    },
    {
        "sprite_name": "orc",
        "name": "Орк",
        "icon": "👹",
        "description": "Масивний вояк зі шкіряною бронею. Повільний, але кожен удар відчувається.",
        "location": "🌲 Темний Ліс",
        "hp": 55,
        "attack": "12–16",
        "defense": 3,
        "xp_reward": 30,
        "gold_reward": 12,
        "loot_items": ["leather_armor"],
        "loot_materials": {"leather": "1–2", "iron_ore": "1–3"},
        "item_drop_chance": 55,
        "difficulty": 2,
    },
    {
        "sprite_name": "dark_knight",
        "name": "Темний Лицар",
        "icon": "🗡",
        "description": "Колишній паладин, що продав душу. Досвідчений боєць з відмінним блоком.",
        "location": "🏰 Вежа",
        "hp": 80,
        "attack": "18–22",
        "defense": 6,
        "xp_reward": 60,
        "gold_reward": 25,
        "loot_items": ["chainmail"],
        "loot_materials": {"dark_steel": "1–2", "magic_core": "1"},
        "item_drop_chance": 55,
        "difficulty": 3,
    },
    {
        "sprite_name": "dragon",
        "name": "Дракон Морвет",
        "icon": "🐉",
        "description": "Древній дракон що спить у руїнах замку. Кінцевий ворог цих земель.",
        "location": "🏚 Замок Дракона",
        "hp": 150,
        "attack": "25–29",
        "defense": 8,
        "xp_reward": 150,
        "gold_reward": 80,
        "loot_items": [],
        "loot_materials": {"dragon_scale": "2", "magic_core": "2", "dark_steel": "1"},
        "item_drop_chance": 0,
        "difficulty": 5,
    },
]

DIFFICULTY_STARS = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}
DIFFICULTY_COLOR = {
    1: (100, 220, 100),
    2: (180, 220, 80),
    3: (255, 180, 50),
    4: (255, 100, 50),
    5: (220, 60, 60),
}

# Розміри
SIDEBAR_W  = 320
LIST_W     = 260
CONTENT_X  = LIST_W + 20
CONTENT_W  = SCREEN_WIDTH - LIST_W - 60
PANELS_TOP = 110
PANELS_BOT = SCREEN_HEIGHT - 80


class BestiaryScene(Scene):
    """Екран бестіарію."""

    def __init__(self, game):
        super().__init__(game)

        self.close_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 65, 200, 46,
            "← Закрити", lambda: game.pop_scene()
        )

        self.selected_idx = 0
        self._find_first_seen()

        # Скрол лута у деталях
        self.loot_scroll = 0

        # Підключаємо renderer (малювання)
        from scenes.ui.bestiary_renderer import BestiaryRenderer
        self._renderer = BestiaryRenderer(self)
    def _find_first_seen(self):
        """Відкриваємо першого зустрінутого ворога за замовчуванням."""
        for i, e in enumerate(ENEMY_REGISTRY):
            if e["sprite_name"] in self.player.enemies_seen:
                self.selected_idx = i
                return
        self.selected_idx = 0

    def _is_seen(self, entry: dict) -> bool:
        return entry["sprite_name"] in self.player.enemies_seen

    def _kill_count(self, entry: dict) -> int:
        mapping = {
            "goblin":      self.player.goblins_killed,
            "orc":         self.player.orcs_killed,
            "dark_knight": self.player.knights_killed,
            "dragon":      self.player.dragons_killed,
        }
        return mapping.get(entry["sprite_name"], 0)

    # ──────────────────────────────────────────
    #  Логіка
    # ──────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if event.button == 1:
                self.close_button.update((mx, my), True)
                self._handle_list_click(mx, my)
            elif event.button == 4:
                self.loot_scroll = max(0, self.loot_scroll - 24)
            elif event.button == 5:
                self.loot_scroll = min(
                    getattr(self, "_loot_max_scroll", 0),
                    self.loot_scroll + 24
                )

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                self.game.pop_scene()
            elif event.key == pygame.K_UP:
                self.selected_idx = max(0, self.selected_idx - 1)
                self.loot_scroll = 0
            elif event.key == pygame.K_DOWN:
                self.selected_idx = min(len(ENEMY_REGISTRY) - 1, self.selected_idx + 1)
                self.loot_scroll = 0

    def _handle_list_click(self, mx, my):
        item_h = 68
        list_top = PANELS_TOP + 8
        for i in range(len(ENEMY_REGISTRY)):
            y = list_top + i * item_h
            rect = pygame.Rect(10, y, LIST_W - 10, item_h - 6)
            if rect.collidepoint(mx, my):
                self.selected_idx = i
                self.loot_scroll = 0
                return

    def update(self, dt: float):
        self.close_button.update(pygame.mouse.get_pos(), False)

    # ──────────────────────────────────────────
    #  Малювання
    # ──────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)
    def _build_loot_lines(self, entry: dict, font_sm, font_norm) -> list:
        """Будує список рядків луту для відображення."""
        lines = []
        font_icon = assets.get_font(FONT_SIZE_NORMAL)

        # Матеріали
        for mat_id, qty_range in entry["loot_materials"].items():
            mat = MATERIALS.get(mat_id)
            if mat:
                icon_s = font_icon.render(mat.icon, True, (180, 230, 255))
                text   = f"{mat.name}  ×{qty_range}"
                text_s = font_norm.render(text, True, (180, 230, 255))
                lines.append((icon_s, text_s))

        # Предмети
        if entry["loot_items"]:
            for item_id in entry["loot_items"]:
                item = ITEMS.get(item_id)
                if item:
                    icon_s = font_icon.render(item.icon, True, (255, 220, 120))
                    text   = f"{item.name}  ({entry['item_drop_chance']}%)"
                    text_s = font_norm.render(text, True, (255, 220, 120))
                    lines.append((icon_s, text_s))
        else:
            icon_s = font_icon.render("—", True, COLOR_TEXT_DIM)
            text_s = font_norm.render("Предметів немає", True, COLOR_TEXT_DIM)
            lines.append((icon_s, text_s))

        return lines

    @staticmethod
    def _wrap_text(text: str, font, max_width: int) -> list[str]:
        """Переносить текст по словах."""
        words  = text.split()
        lines  = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines