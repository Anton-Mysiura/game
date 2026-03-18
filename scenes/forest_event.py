"""
Сцена рандомної події в лісі.
"""

import pygame
from .base import Scene
from ui.assets import assets
from ui.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, COLOR_HP, COLOR_BG,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, FONT_SIZE_HUGE,
)
from game.forest_events import ForestEvent, EventResult
from game.save_manager import autosave


PANEL_W = 780
PANEL_H = 480
PANEL_X = SCREEN_WIDTH  // 2 - PANEL_W // 2
PANEL_Y = SCREEN_HEIGHT // 2 - PANEL_H // 2


class ForestEventScene(Scene):
    """Показує рандомну подію з вибором дій."""

    def __init__(self, game):
        super().__init__(game)

        self.event: ForestEvent = game.scene_data.get("forest_event")
        self.return_scene: str  = game.scene_data.get("return_scene", "forest")

        # Стан: "choice" → гравець вибирає | "result" → показуємо результат
        self.state   = "choice"
        self.result: EventResult | None = None

        # Кнопки вибору (будуємо в update)
        self._choice_rects: list[pygame.Rect] = []
        self._hovered = -1

        # Кнопка "Продовжити" після результату
        self._continue_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 130, PANEL_Y + PANEL_H - 65, 260, 48
        )

        # Анімація появи
        self.alpha = 0.0

        self._build_choice_rects()

    def _build_choice_rects(self):
        if not self.event:
            return
        n = len(self.event.choices)
        btn_h = 52
        gap   = 10
        total = n * btn_h + (n - 1) * gap
        start_y = PANEL_Y + PANEL_H - total - 75

        self._choice_rects = []
        for i in range(n):
            r = pygame.Rect(PANEL_X + 40, start_y + i * (btn_h + gap),
                            PANEL_W - 80, btn_h)
            self._choice_rects.append(r)

    # ── Events ──────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self.state == "choice":
                self._hovered = next(
                    (i for i, r in enumerate(self._choice_rects)
                     if r.collidepoint(pos)), -1
                )
            else:
                self._hovered = -1

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "choice":
                for i, r in enumerate(self._choice_rects):
                    if r.collidepoint(pos):
                        self._resolve(i)
                        return
            else:
                if self._continue_rect.collidepoint(pos):
                    self._go_next()

        if event.type == pygame.KEYDOWN:
            if self.state == "result" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_next()

    def _resolve(self, choice_idx: int):
        choice = self.event.choices[choice_idx]
        self.result = choice.resolve(self.player)
        self.state = "result"
        autosave(self.player)

    def _go_next(self):
        if self.result and self.result.enemy:
            # Бій — після бою повертаємось у ліс
            self.game.change_scene(
                "battle",
                enemy=self.result.enemy,
                return_scene=self.return_scene,
            )
        else:
            self.game.change_scene(self.return_scene)

    # ── Update ──────────────────────────────────────────────

    def update(self, dt: float):
        self.alpha = min(255, self.alpha + 400 * dt)

    # ── Draw ────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        # Темний оверлей
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(180, int(self.alpha * 0.7))))
        screen.blit(overlay, (0, 0))

        # Панель
        panel = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panel.fill((22, 28, 22, 230))
        pygame.draw.rect(panel, (60, 100, 60), (0, 0, PANEL_W, PANEL_H), 2, border_radius=16)
        screen.blit(panel, (PANEL_X, PANEL_Y))

        if self.state == "choice":
            self._draw_choice(screen)
        else:
            self._draw_result(screen)

    def _draw_choice(self, screen):
        ev = self.event
        cx = SCREEN_WIDTH // 2

        # Іконка
        font_icon = assets.get_font(72)
        icon_s = font_icon.render(ev.icon, True, COLOR_TEXT)
        screen.blit(icon_s, (cx - icon_s.get_width() // 2, PANEL_Y + 18))

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title_s = font_title.render(ev.title, True, COLOR_GOLD)
        screen.blit(title_s, (cx - title_s.get_width() // 2, PANEL_Y + 95))

        # Опис (з переносом)
        font_desc = assets.get_font(FONT_SIZE_NORMAL)
        self._draw_wrapped(screen, font_desc, ev.description,
                           COLOR_TEXT_DIM, PANEL_X + 40, PANEL_Y + 140, PANEL_W - 80)

        # Кнопки вибору
        font_btn = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        for i, (rect, choice) in enumerate(zip(self._choice_rects, ev.choices)):
            hov = i == self._hovered
            bg  = (50, 80, 50) if hov else (30, 48, 30)
            border = COLOR_GOLD if hov else (70, 110, 70)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, border, rect, 2, border_radius=10)

            label_s = font_btn.render(choice.label, True,
                                      COLOR_GOLD if hov else COLOR_TEXT)
            screen.blit(label_s,
                        (rect.centerx - label_s.get_width() // 2,
                         rect.centery - label_s.get_height() // 2))

    def _draw_result(self, screen):
        cx = SCREEN_WIDTH // 2
        res = self.result

        # Іконка результату
        icon = "✅" if res.hp_delta >= 0 and res.gold_delta >= 0 else (
               "⚔" if res.enemy else "❗")
        font_icon = assets.get_font(64)
        icon_s = font_icon.render(icon, True, COLOR_TEXT)
        screen.blit(icon_s, (cx - icon_s.get_width() // 2, PANEL_Y + 24))

        # Текст результату
        font_desc = assets.get_font(FONT_SIZE_NORMAL)
        self._draw_wrapped(screen, font_desc, res.text,
                           COLOR_TEXT, PANEL_X + 40, PANEL_Y + 105, PANEL_W - 80)

        # Здобутки / втрати
        loot_y = PANEL_Y + 220
        font_loot = assets.get_font(FONT_SIZE_NORMAL, bold=True)

        if res.gold_delta != 0:
            col  = COLOR_GOLD if res.gold_delta > 0 else (220, 80, 80)
            sign = "+" if res.gold_delta > 0 else ""
            s = font_loot.render(f"{sign}{res.gold_delta} 🪙", True, col)
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        if res.hp_delta != 0:
            col  = (80, 220, 80) if res.hp_delta > 0 else (220, 80, 80)
            sign = "+" if res.hp_delta > 0 else ""
            s = font_loot.render(f"{sign}{res.hp_delta} ❤", True, col)
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        for item in res.items_gained:
            s = font_loot.render(f"+ {item.name}", True, (100, 220, 255))
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        for mat_id, qty in res.materials_gained.items():
            from game.data import MATERIALS
            mat = MATERIALS.get(mat_id)
            name = mat.name if mat else mat_id
            s = font_loot.render(f"+ {name} ×{qty}", True, (180, 220, 130))
            screen.blit(s, (cx - s.get_width() // 2, loot_y))
            loot_y += 34

        if res.enemy:
            s = font_loot.render(f"⚔ Почнеться бій!", True, (220, 80, 80))
            screen.blit(s, (cx - s.get_width() // 2, loot_y))

        # Кнопка продовжити
        hov = pygame.mouse.get_pos()
        btn_col = (60, 100, 60) if self._continue_rect.collidepoint(hov) else (40, 70, 40)
        pygame.draw.rect(screen, btn_col, self._continue_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, self._continue_rect, 2, border_radius=10)
        label = "⚔ До бою!" if res.enemy else "Продовжити →"
        font_btn = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        s = font_btn.render(label, True, COLOR_GOLD)
        screen.blit(s, (self._continue_rect.centerx - s.get_width() // 2,
                        self._continue_rect.centery - s.get_height() // 2))

        # Підказка
        font_hint = assets.get_font(FONT_SIZE_SMALL)
        hint = font_hint.render("Enter / Пробіл щоб продовжити", True, COLOR_TEXT_DIM)
        screen.blit(hint, (cx - hint.get_width() // 2, PANEL_Y + PANEL_H - 22))

    def _draw_wrapped(self, screen, font, text, color, x, y, max_w):
        """Малює текст з переносом рядків (підтримує \n)."""
        line_h = font.get_height() + 4
        for paragraph in text.split("\n"):
            words = paragraph.split()
            line  = ""
            for word in words:
                test = (line + " " + word).strip()
                if font.size(test)[0] <= max_w:
                    line = test
                else:
                    if line:
                        s = font.render(line, True, color)
                        screen.blit(s, (x, y))
                        y += line_h
                    line = word
            if line:
                s = font.render(line, True, color)
                screen.blit(s, (x, y))
                y += line_h
        return y