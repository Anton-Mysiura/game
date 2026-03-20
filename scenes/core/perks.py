"""
Екран перегляду отриманих перків гравця.
"""

import pygame
from .base import Scene
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.perk_system import PERKS, RARITY_COLORS, RARITY_NAMES


# Порядок відображення рідкостей (від звичайних до GOD)
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "mythic", "legendary", "god"]

# Розміри картки перку
CARD_W = 340
CARD_H = 80
CARD_GAP = 10
CARDS_PER_COL = 7
COL_GAP = 30


class PerksScene(Scene):
    """Екран перегляду всіх отриманих перків."""

    def __init__(self, game):
        super().__init__(game)

        self.close_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70, 200, 46,
            "← Закрити", lambda: game.pop_scene()
        )

        self.main_panel = Panel(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 100, alpha=True)

        # Скролінг
        self.scroll_y = 0
        self.max_scroll = 0

        # Підготовка згрупованих перків
        self._grouped = self._build_grouped()
        self._flat_cards = self._build_flat_cards()

        # Рахуємо загальну висоту і max_scroll
        total_h = len(self._flat_cards) * (CARD_H + CARD_GAP)
        visible_h = SCREEN_HEIGHT - 210
        self.max_scroll = max(0, total_h - visible_h)

        # Tooltip
        self._hovered_perk = None

        # Онбординг-туторіал
        self._ob_tutorial = self.game.scene_data.pop("onboarding_perk_tutorial", False)
        self._ob_step     = 0    # 0=пояснення що таке перки, 1=рідкості, 2=де купити, 3=готово
        self._ob_anim     = 0.0
        self._ob_done     = False

        if self._ob_tutorial:
            # Міняємо кнопку закриття — після туторіалу виходимо у вільну гру
            self.close_button = Button(
                SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70, 200, 46,
                "Далі →", self._ob_next
            )

    # ──────────────────────────────────────────
    #  Підготовка даних
    # ──────────────────────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.perks_renderer import PerksRenderer
        self._renderer = PerksRenderer(self)
    def _build_grouped(self) -> dict:
        """Групує perk_id гравця за рідкістю, рахує дублікати."""
        counts: dict[str, int] = {}
        for pid in self.player.perks:
            counts[pid] = counts.get(pid, 0) + 1

        grouped: dict[str, list[tuple]] = {r: [] for r in RARITY_ORDER}
        for pid, cnt in counts.items():
            perk = PERKS.get(pid)
            if perk:
                grouped[perk.rarity].append((perk, cnt))

        # Сортуємо всередині рідкості за назвою
        for r in grouped:
            grouped[r].sort(key=lambda x: x[0].name)

        return grouped

    def _build_flat_cards(self) -> list:
        """Повертає плоский список (perk, count) у порядку рідкостей."""
        result = []
        for rarity in RARITY_ORDER:
            result.extend(self._grouped[rarity])
        return result

    # ──────────────────────────────────────────
    #  Логіка
    # ──────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if self._ob_tutorial:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._ob_next()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mp = pygame.mouse.get_pos()
                self.close_button.update(mp, True)
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.close_button.update(pygame.mouse.get_pos(), True)
            elif event.button == 4:  # scroll up
                self.scroll_y = max(0, self.scroll_y - 40)
            elif event.button == 5:  # scroll down
                self.scroll_y = min(self.max_scroll, self.scroll_y + 40)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                self.game.pop_scene()
            elif event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 40)
            elif event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 40)

    def _ob_next(self):
        """Наступний крок туторіалу перків."""
        if self._ob_step < 3:
            self._ob_step += 1
            self._ob_anim  = 0.0
            if self._ob_step == 3:
                self.close_button.text = "← Готово"
                self.close_button.callback = self._ob_finish
        else:
            self._ob_finish()

    def _ob_finish(self):
        """Завершення туторіалу — вільна гра."""
        self.player.onboarding_done = True
        from game.save_manager import autosave
        autosave(self.player)
        self.game.pop_scene()
        self.game.change_scene("village")

    def update(self, dt: float):
        if self._ob_tutorial:
            self._ob_anim += dt
        self.close_button.update(pygame.mouse.get_pos(), False)
        self._hovered_perk = self._get_hovered_perk()

    def _get_hovered_perk(self):
        mx, my = pygame.mouse.get_pos()
        list_top = 130
        for i, (perk, cnt) in enumerate(self._flat_cards):
            y = list_top + i * (CARD_H + CARD_GAP) - self.scroll_y
            if y + CARD_H < 120 or y > SCREEN_HEIGHT - 100:
                continue
            rect = pygame.Rect(SCREEN_WIDTH // 2 - CARD_W // 2, y, CARD_W, CARD_H)
            if rect.collidepoint(mx, my):
                return (perk, rect)
        return None

    # ──────────────────────────────────────────
    #  Малювання
    # ──────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)