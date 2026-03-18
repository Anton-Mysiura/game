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
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        self._draw_header(screen)
        self._draw_list_panel(screen)
        self._draw_detail_panel(screen)
        self.close_button.draw(screen)

    def _draw_header(self, screen):
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_sub   = assets.get_font(FONT_SIZE_SMALL)

        title  = font_title.render("📖 Бестіарій", True, COLOR_GOLD)
        shadow = font_title.render("📖 Бестіарій", True, (0, 0, 0))
        cx = SCREEN_WIDTH // 2
        screen.blit(shadow, (cx - title.get_width() // 2 + 2, 22))
        screen.blit(title,  (cx - title.get_width() // 2,     20))

        seen_count = sum(1 for e in ENEMY_REGISTRY if self._is_seen(e))
        sub = font_sub.render(
            f"Виявлено: {seen_count} / {len(ENEMY_REGISTRY)}",
            True, COLOR_TEXT_DIM
        )
        screen.blit(sub, (cx - sub.get_width() // 2, 76))

    def _draw_list_panel(self, screen):
        panel_h = PANELS_BOT - PANELS_TOP
        pygame.draw.rect(screen, (22, 18, 30), (8, PANELS_TOP, LIST_W, panel_h), border_radius=14)
        pygame.draw.rect(screen, (80, 70, 100), (8, PANELS_TOP, LIST_W, panel_h), 2, border_radius=14)

        item_h   = 68
        list_top = PANELS_TOP + 8

        for i, entry in enumerate(ENEMY_REGISTRY):
            y    = list_top + i * item_h
            rect = pygame.Rect(10, y, LIST_W - 10, item_h - 6)
            seen = self._is_seen(entry)

            # Фон рядка
            selected = (i == self.selected_idx)
            if selected:
                bg = (50, 40, 70)
            elif rect.collidepoint(pygame.mouse.get_pos()):
                bg = (35, 28, 50)
            else:
                bg = (28, 22, 38)

            pygame.draw.rect(screen, bg, rect, border_radius=8)
            if selected:
                diff_color = DIFFICULTY_COLOR.get(entry["difficulty"], COLOR_GOLD)
                pygame.draw.rect(screen, diff_color, rect, 2, border_radius=8)

            if seen:
                self._draw_list_item_seen(screen, entry, rect, i)
            else:
                self._draw_list_item_unknown(screen, rect)

    def _draw_list_item_seen(self, screen, entry, rect, idx):
        font_name = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_sm   = assets.get_font(FONT_SIZE_SMALL)

        # Іконка
        icon_surf = assets.get_font(FONT_SIZE_LARGE).render(entry["icon"], True, COLOR_TEXT)
        screen.blit(icon_surf, (rect.x + 8, rect.y + rect.h // 2 - icon_surf.get_height() // 2))

        # Назва
        name_surf = font_name.render(entry["name"], True, COLOR_TEXT)
        screen.blit(name_surf, (rect.x + 52, rect.y + 8))

        # Локація
        loc_surf = font_sm.render(entry["location"], True, COLOR_TEXT_DIM)
        screen.blit(loc_surf, (rect.x + 52, rect.y + 34))

        # Ефективний рівень для поточного гравця
        from game.enemy_scaling import enemy_level, level_color
        eff_lvl = enemy_level(entry["sprite_name"], self.player.level)
        lvl_clr = level_color(eff_lvl, self.player.level)
        lvl_surf = font_sm.render(f"Рівень {eff_lvl}", True, lvl_clr)
        screen.blit(lvl_surf, (rect.x + 52, rect.y + 52))

        # Зірки складності (праворуч)
        stars = DIFFICULTY_STARS.get(entry["difficulty"], "")
        diff_color = DIFFICULTY_COLOR.get(entry["difficulty"], COLOR_TEXT_DIM)
        stars_surf = font_sm.render(stars, True, diff_color)
        screen.blit(stars_surf, (rect.right - stars_surf.get_width() - 8, rect.y + 8))

        # К-сть вбитих
        kills = self._kill_count(entry)
        kill_surf = font_sm.render(f"☠ {kills}", True, (180, 180, 180))
        screen.blit(kill_surf, (rect.right - kill_surf.get_width() - 8, rect.y + 34))

    def _draw_list_item_unknown(self, screen, rect):
        font = assets.get_font(FONT_SIZE_NORMAL)
        surf = font.render("??? Невідомий ворог", True, (80, 70, 90))
        screen.blit(surf, (rect.x + 14, rect.y + rect.h // 2 - surf.get_height() // 2))

    def _draw_detail_panel(self, screen):
        cx     = LIST_W + 20
        panel_w = SCREEN_WIDTH - cx - 12
        panel_h = PANELS_BOT - PANELS_TOP

        pygame.draw.rect(screen, (18, 22, 18), (cx, PANELS_TOP, panel_w, panel_h), border_radius=14)
        pygame.draw.rect(screen, (70, 90, 70), (cx, PANELS_TOP, panel_w, panel_h), 2, border_radius=14)

        entry = ENEMY_REGISTRY[self.selected_idx]
        if not self._is_seen(entry):
            self._draw_unknown_detail(screen, cx, panel_w, panel_h)
        else:
            self._draw_known_detail(screen, entry, cx, panel_w, panel_h)

    def _draw_unknown_detail(self, screen, cx, panel_w, panel_h):
        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_sub = assets.get_font(FONT_SIZE_NORMAL)
        cy = PANELS_TOP + panel_h // 2

        q = font.render("???", True, (80, 70, 90))
        screen.blit(q, (cx + panel_w // 2 - q.get_width() // 2, cy - 40))

        sub = font_sub.render("Зустрінь цього ворога, щоб дізнатись більше", True, (70, 60, 80))
        screen.blit(sub, (cx + panel_w // 2 - sub.get_width() // 2, cy + 10))

    def _draw_known_detail(self, screen, entry, cx, panel_w, panel_h):
        font_huge  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_large = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_med   = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)
        font_norm  = assets.get_font(FONT_SIZE_NORMAL)

        pad = 20
        x   = cx + pad
        y   = PANELS_TOP + pad

        # ── Заголовок ──
        icon_surf = font_huge.render(entry["icon"], True, COLOR_TEXT)
        screen.blit(icon_surf, (x, y))

        name_surf = font_large.render(entry["name"], True, COLOR_GOLD)
        screen.blit(name_surf, (x + icon_surf.get_width() + 12, y + 4))

        diff_color = DIFFICULTY_COLOR.get(entry["difficulty"], COLOR_TEXT_DIM)
        stars_surf = font_sm.render(
            DIFFICULTY_STARS.get(entry["difficulty"], ""), True, diff_color
        )
        screen.blit(stars_surf, (x + icon_surf.get_width() + 12,
                                  y + 4 + name_surf.get_height() + 2))

        loc_surf = font_sm.render(entry["location"], True, COLOR_TEXT_DIM)
        screen.blit(loc_surf, (cx + panel_w - loc_surf.get_width() - pad, y + 8))

        y += max(icon_surf.get_height(), name_surf.get_height()) + 16

        # ── Опис ──
        desc_lines = self._wrap_text(entry["description"], font_norm,
                                      panel_w - pad * 2 - 10)
        for line in desc_lines:
            surf = font_norm.render(line, True, COLOR_TEXT_DIM)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 2
        y += 12

        # ── Розділювач ──
        pygame.draw.line(screen, (60, 80, 60), (x, y), (cx + panel_w - pad, y), 1)
        y += 12

        # ── Стати (ліва колонка) + Нагороди (права колонка) ──
        col_w    = (panel_w - pad * 2) // 2 - 10
        stats_x  = x
        rewards_x = x + col_w + 20

        # Статистика
        stat_title = font_med.render("📊 Характеристики", True, COLOR_GOLD)
        screen.blit(stat_title, (stats_x, y))
        sy = y + stat_title.get_height() + 8

        stats = [
            ("❤ HP",      str(entry["hp"])),
            ("⚔ Атака",   entry["attack"]),
            ("🛡 Захист",  str(entry["defense"])),
            ("✨ XP",      str(entry["xp_reward"])),
            ("💰 Золото",  str(entry["gold_reward"])),
            ("☠ Вбито",   str(self._kill_count(entry))),
        ]
        for lbl, val in stats:
            lbl_s = font_sm.render(lbl,  True, COLOR_TEXT_DIM)
            val_s = font_norm.render(val, True, COLOR_TEXT)
            screen.blit(lbl_s, (stats_x, sy))
            screen.blit(val_s, (stats_x + 130, sy))
            sy += lbl_s.get_height() + 8

        # Нагороди — скрол-зона
        rew_title = font_med.render("🎁 Лут", True, COLOR_GOLD)
        screen.blit(rew_title, (rewards_x, y))

        loot_area_top = y + rew_title.get_height() + 8
        loot_area_bot = PANELS_BOT - 10
        loot_area_h   = loot_area_bot - loot_area_top

        loot_lines = self._build_loot_lines(entry, font_sm, font_norm)
        row_h = font_norm.get_height() + 6
        total_loot_h = len(loot_lines) * row_h
        max_scroll = max(0, total_loot_h - loot_area_h)
        self._loot_max_scroll = max_scroll
        scroll = min(self.loot_scroll, max_scroll)

        clip = pygame.Rect(rewards_x, loot_area_top, col_w, loot_area_h)
        screen.set_clip(clip)

        ry = loot_area_top - scroll
        for icon_s, text_s in loot_lines:
            if ry + row_h >= loot_area_top and ry <= loot_area_bot:
                screen.blit(icon_s, (rewards_x, ry))
                screen.blit(text_s, (rewards_x + icon_s.get_width() + 6, ry))
            ry += row_h

        screen.set_clip(None)

        # Смуга скролу
        if max_scroll > 0:
            sb_x = cx + panel_w - 14
            pygame.draw.rect(screen, (40, 55, 40),
                              (sb_x, loot_area_top, 5, loot_area_h), border_radius=3)
            ratio   = loot_area_h / total_loot_h
            thumb_h = max(20, int(loot_area_h * ratio))
            thumb_y = loot_area_top + int((loot_area_h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(screen, COLOR_GOLD,
                              (sb_x, thumb_y, 5, thumb_h), border_radius=3)

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