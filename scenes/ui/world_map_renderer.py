"""
Рендерер для WorldMapScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/world_map.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer
from ui.constants import *

import math
import random
from ui.assets import assets


class WorldMapRenderer(BaseRenderer):
    """
    Малює WorldMapScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        self._draw_background(screen)
        self._draw_fog_particles(screen)
        self._draw_paths(screen)
        self._draw_nodes(screen)
        self._draw_legend(screen)
        self._draw_active_bonuses(screen)
        self._draw_tooltip(screen)
        self.scene._back_btn.draw(screen)

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
        for p in self.scene._fog_particles:
            surf = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 220, 200, p["alpha"]),
                               (p["r"], p["r"]), p["r"])
            screen.blit(surf, (int(p["x"] - p["r"]), int(p["y"] - p["r"])))

    def _draw_paths(self, screen: pygame.Surface):
        loc_map = {l["id"]: l for l in LOCATIONS}

        for a_id, b_id in PATHS:
            a = loc_map[a_id]
            b = loc_map[b_id]
            unlocked = self.scene._path_unlocked(a_id, b_id)

            ax, ay = a["pos"]
            bx, by = b["pos"]

            if unlocked:
                # Пунктирна анімована лінія
                self._draw_dashed_line(screen, (ax, ay), (bx, by),
                                       (120, 180, 120), dash_len=14, gap=8,
                                       offset=int(self.scene._dash_offset), width=3)
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
        unlocked = self.scene._is_unlocked(loc)
        visited  = self.scene._is_visited(loc["id"])
        hovered  = self.scene.hovered_id == loc["id"]
        selected = self.scene.selected_id == loc["id"]
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
        if not self.scene.selected_id:
            return
        loc = next((l for l in LOCATIONS if l["id"] == self.scene.selected_id), None)
        if not loc or not self.scene._is_unlocked(loc):
            return

        from game.location_bonuses import LOCATION_BONUSES
        bonus = LOCATION_BONUSES.get(loc["id"])
        visited = self.scene._is_visited(loc["id"])

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