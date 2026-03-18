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
        self._draw_background(screen)
        self._draw_fog_particles(screen)
        self._draw_paths(screen)
        self._draw_nodes(screen)
        self._draw_legend(screen)
        self._draw_active_bonuses(screen)
        self._draw_tooltip(screen)
        self._back_btn.draw(screen)

    def _draw_background(self, screen: pygame.Surface):
        # Темно-зелений топографічний фон
        screen.fill((18, 28, 18))

        # Концентричні "горизонталі"
        for i in range(0, max(SCREEN_WIDTH, SCREEN_HEIGHT) * 2, 38):
            alpha = 12 + (i // 38) % 3 * 4
            col = (30 + (i // 38) % 4 * 4, 45, 30)
            pygame.draw.circle(screen, col,
                               (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), i, 1)

        # Сітка
        for x in range(0, SCREEN_WIDTH, 80):
            pygame.draw.line(screen, (25, 40, 25), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 80):
            pygame.draw.line(screen, (25, 40, 25), (0, y), (SCREEN_WIDTH, y))

        # Заголовок
        font = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font.render("🗺 Карта Темного Королівства", True, COLOR_GOLD)
        shadow = font.render("🗺 Карта Темного Королівство", True, (0, 0, 0))
        screen.blit(shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 2, 22))
        screen.blit(title,  (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))

    def _draw_fog_particles(self, screen: pygame.Surface):
        for p in self._fog_particles:
            surf = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 220, 200, p["alpha"]),
                               (p["r"], p["r"]), p["r"])
            screen.blit(surf, (int(p["x"] - p["r"]), int(p["y"] - p["r"])))

    def _draw_paths(self, screen: pygame.Surface):
        loc_map = {l["id"]: l for l in LOCATIONS}

        for a_id, b_id in PATHS:
            a = loc_map[a_id]
            b = loc_map[b_id]
            unlocked = self._path_unlocked(a_id, b_id)

            ax, ay = a["pos"]
            bx, by = b["pos"]

            if unlocked:
                # Пунктирна анімована лінія
                self._draw_dashed_line(screen, (ax, ay), (bx, by),
                                       (120, 180, 120), dash_len=14, gap=8,
                                       offset=int(self._dash_offset), width=3)
            else:
                # Розмита сіра лінія (туман)
                pygame.draw.line(screen, (45, 55, 45), (ax, ay), (bx, by), 2)

    def _draw_dashed_line(self, screen, start, end, color,
                          dash_len=12, gap=8, offset=0, width=2):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return
        ux, uy = dx / length, dy / length
        step = dash_len + gap
        pos = -offset % step

        while pos < length:
            x1 = start[0] + ux * pos
            y1 = start[1] + uy * pos
            x2 = start[0] + ux * min(pos + dash_len, length)
            y2 = start[1] + uy * min(pos + dash_len, length)
            pygame.draw.line(screen, color,
                             (int(x1), int(y1)), (int(x2), int(y2)), width)
            pos += step

    def _draw_nodes(self, screen: pygame.Surface):
        for loc in LOCATIONS:
            self._draw_node(screen, loc)

    def _draw_node(self, screen, loc: dict):
        x, y     = loc["pos"]
        unlocked = self._is_unlocked(loc)
        visited  = self._is_visited(loc["id"])
        hovered  = self.hovered_id == loc["id"]
        selected = self.selected_id == loc["id"]
        color    = loc["color"]

        r = NODE_RADIUS + (4 if hovered or selected else 0)

        if not unlocked:
            # Туман — розмитий сірий круг
            fog = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(fog, (40, 40, 40, FOG_ALPHA),
                               (r + 10, r + 10), r + 10)
            screen.blit(fog, (x - r - 10, y - r - 10))

            # Знак питання
            font_q = assets.get_font(FONT_SIZE_LARGE, bold=True)
            q = font_q.render("?", True, (80, 80, 80))
            screen.blit(q, (x - q.get_width() // 2, y - q.get_height() // 2))
            return

        # Світіння при наведенні / вибраному
        if hovered or selected:
            glow = pygame.Surface((r * 2 + 24, r * 2 + 24), pygame.SRCALPHA)
            glow_col = (*color, 70)
            pygame.draw.circle(glow, glow_col, (r + 12, r + 12), r + 12)
            screen.blit(glow, (x - r - 12, y - r - 12))

        # Зовнішнє кільце
        ring_color = COLOR_GOLD if selected else (
            (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))
            if hovered else color
        )
        pygame.draw.circle(screen, ring_color, (x, y), r + 4)

        # Основний круг
        bg_color = (
            (min(255, color[0] + 20), min(255, color[1] + 20), min(255, color[2] + 20))
            if visited else (40, 40, 50)
        )
        pygame.draw.circle(screen, bg_color, (x, y), r)

        # Іконка
        font_icon = assets.get_font(36)
        icon_surf = font_icon.render(loc["icon"], True, COLOR_TEXT)
        screen.blit(icon_surf, (x - icon_surf.get_width() // 2,
                                y - icon_surf.get_height() // 2 - 6))

        # Назва під вузлом
        font_name = assets.get_font(FONT_SIZE_SMALL, bold=True)
        name_col  = COLOR_GOLD if selected else (COLOR_TEXT if visited else COLOR_TEXT_DIM)
        name_surf = font_name.render(loc["name"], True, name_col)
        screen.blit(name_surf, (x - name_surf.get_width() // 2, y + r + 6))

        # Рекомендований рівень
        font_lvl = assets.get_font(FONT_SIZE_SMALL)
        lvl_col  = COLOR_HP if self.player.level >= loc["rec_level"] else (220, 80, 80)
        lvl_surf = font_lvl.render(f"Рів. {loc['rec_level']}+", True, lvl_col)
        screen.blit(lvl_surf, (x - lvl_surf.get_width() // 2, y + r + 24))

        # Галочка якщо пройдено
        if visited and loc["id"] != "village":
            font_check = assets.get_font(FONT_SIZE_NORMAL)
            check = font_check.render("✓", True, (80, 220, 80))
            screen.blit(check, (x + r - 4, y - r - 4))

    def _draw_tooltip(self, screen: pygame.Surface):
        if not self.selected_id:
            return
        loc = next((l for l in LOCATIONS if l["id"] == self.selected_id), None)
        if not loc or not self._is_unlocked(loc):
            return

        from game.location_bonuses import LOCATION_BONUSES
        bonus = LOCATION_BONUSES.get(loc["id"])
        visited = self._is_visited(loc["id"])

        # Висота панелі — більша якщо є бонус
        panel_w = 360
        panel_h = 155 if bonus else 130
        px = min(loc["pos"][0] + NODE_RADIUS + 12, SCREEN_WIDTH - panel_w - 10)
        py = max(loc["pos"][1] - panel_h // 2, 10)

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 30, 210))
        pygame.draw.rect(panel, loc["color"], (0, 0, panel_w, panel_h), 2, border_radius=10)
        screen.blit(panel, (px, py))

        font_name = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        font_desc = assets.get_font(FONT_SIZE_SMALL)

        name_s = font_name.render(f"{loc['icon']} {loc['name']}", True, COLOR_GOLD)
        screen.blit(name_s, (px + 14, py + 12))

        desc_s = font_desc.render(loc["description"], True, COLOR_TEXT_DIM)
        screen.blit(desc_s, (px + 14, py + 46))

        status = "✓ Відвідано" if visited else f"Рекомендований рівень: {loc['rec_level']}+"
        stat_c = (80, 220, 80) if visited else COLOR_TEXT_DIM
        screen.blit(font_desc.render(status, True, stat_c), (px + 14, py + 70))

        # Пасивний бонус
        if bonus:
            clr = (100, 220, 100) if visited else (120, 100, 80)
            prefix = "✦ Бонус: " if visited else "🔒 Бонус (після відвідання): "
            bonus_s = font_desc.render(prefix + bonus.desc, True, clr)
            screen.blit(bonus_s, (px + 14, py + 94))
            hint_y = py + 120
        else:
            hint_y = py + 96

        hint_s = font_desc.render("Клікни ще раз щоб перейти →", True, COLOR_GOLD)
        screen.blit(hint_s, (px + 14, hint_y))

    def _draw_active_bonuses(self, screen: pygame.Surface):
        """Панель активних бонусів від локацій — знизу ліворуч."""
        from game.location_bonuses import get_active_bonuses
        bonuses = get_active_bonuses(self.player.locations_visited)
        if not bonuses:
            return

        font_h  = assets.get_font(FONT_SIZE_SMALL, bold=True)
        font    = assets.get_font(FONT_SIZE_SMALL)

        row_h   = 20
        pad     = 10
        panel_w = 310
        panel_h = pad * 2 + 22 + len(bonuses) * row_h

        px = 30
        py = SCREEN_HEIGHT - panel_h - 30

        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((15, 15, 25, 200))
        pygame.draw.rect(surf, (80, 160, 80), (0, 0, panel_w, panel_h), 1, border_radius=8)
        screen.blit(surf, (px, py))

        screen.blit(font_h.render("✦ Активні бонуси локацій", True, (100, 220, 100)),
                    (px + pad, py + pad))

        y = py + pad + 22
        for b in bonuses:
            row = font.render(f"{b.icon} {b.desc}", True, b.color)
            screen.blit(row, (px + pad, y))
            y += row_h

    def _draw_legend(self, screen: pygame.Surface):
        lx, ly = 30, 80
        font   = assets.get_font(FONT_SIZE_SMALL)

        items = [
            ((80, 220, 80),   "✓  Відвідано"),
            ((120, 180, 120), "—  Доступно"),
            ((80, 80, 80),    "?  Заховано туманом"),
        ]
        for color, text in items:
            surf = font.render(text, True, color)
            screen.blit(surf, (lx, ly))
            ly += 22

        # HP гравця
        ly += 10
        hp_text = font.render(
            f"❤ {self.player.hp}/{self.player.total_max_hp}  ⭐ Рів. {self.player.level}",
            True, COLOR_HP
        )
        screen.blit(hp_text, (lx, ly))