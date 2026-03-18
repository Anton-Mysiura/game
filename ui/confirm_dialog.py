"""
Модальне вікно підтвердження.

Використання:
    self._confirm = ConfirmDialog(
        title   = "Продати предмет?",
        body    = "Залізний меч  (+12 ATK)\nЦіна: 40 🪙",
        yes_lbl = "💰 Продати",
        no_lbl  = "Назад",
        on_yes  = lambda: self._do_sell(),
        danger  = True,   # червона рамка
    )

В handle_event:
    if self._confirm:
        self._confirm.handle_event(event)
        return

В draw:
    if self._confirm:
        self._confirm.draw(screen)
        if self._confirm.done:
            self._confirm = None
"""
import math
import pygame
from ui.constants import (SCREEN_WIDTH, SCREEN_HEIGHT,
                           COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD,
                           COLOR_ERROR, COLOR_BTN_NORMAL, COLOR_BTN_HOVER,
                           FONT_SIZE_LARGE, FONT_SIZE_NORMAL, FONT_SIZE_SMALL)


class ConfirmDialog:

    W = 520
    H = 240

    def __init__(self, title: str, body: str,
                 on_yes,
                 yes_lbl: str = "Підтвердити",
                 no_lbl:  str = "Скасувати",
                 danger:  bool = False):
        self.title   = title
        self.body    = body
        self.on_yes  = on_yes
        self.yes_lbl = yes_lbl
        self.no_lbl  = no_lbl
        self.danger  = danger
        self.done    = False
        self._anim   = 0.0        # для пульсації

        self.x = SCREEN_WIDTH  // 2 - self.W // 2
        self.y = SCREEN_HEIGHT // 2 - self.H // 2

        bw, bh = 170, 46
        by     = self.y + self.H - bh - 18
        self._yes_rect = pygame.Rect(self.x + self.W // 2 - bw - 12, by, bw, bh)
        self._no_rect  = pygame.Rect(self.x + self.W // 2 + 12,      by, bw, bh)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self._yes_rect.collidepoint(mp):
                self.on_yes()
                self.done = True
            elif self._no_rect.collidepoint(mp):
                self.done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_yes()
                self.done = True
            elif event.key == pygame.K_ESCAPE:
                self.done = True

    def update(self, dt: float):
        self._anim += dt

    def draw(self, screen: pygame.Surface):
        from ui.assets import assets

        # Затемнення
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # Панель
        panel = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        panel.fill((22, 18, 12, 252))
        border_clr = COLOR_ERROR if self.danger else COLOR_GOLD
        if self.danger:
            pulse = 0.7 + 0.3 * math.sin(self._anim * 3)
            border_clr = tuple(min(255, int(c * pulse)) for c in COLOR_ERROR)
        pygame.draw.rect(panel, border_clr, panel.get_rect(), 2, border_radius=12)
        screen.blit(panel, (self.x, self.y))

        fh  = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fm  = assets.get_font(FONT_SIZE_NORMAL)
        fs  = assets.get_font(FONT_SIZE_SMALL)
        mp  = pygame.mouse.get_pos()

        # Заголовок
        title_s = fh.render(self.title, True, COLOR_ERROR if self.danger else COLOR_GOLD)
        screen.blit(title_s, (self.x + self.W // 2 - title_s.get_width() // 2,
                               self.y + 18))

        # Тіло — кілька рядків
        ty = self.y + 62
        for line in self.body.split("\n"):
            if line.strip():
                ls = fm.render(line, True, COLOR_TEXT)
                screen.blit(ls, (self.x + self.W // 2 - ls.get_width() // 2, ty))
            ty += 26

        # Кнопка "Так"
        yes_hover = self._yes_rect.collidepoint(mp)
        yes_bg    = (160, 40, 40) if (self.danger and yes_hover) else \
                    (80, 130, 80) if (not self.danger and yes_hover) else \
                    (110, 30, 30) if self.danger else (55, 95, 55)
        pygame.draw.rect(screen, yes_bg,    self._yes_rect, border_radius=8)
        pygame.draw.rect(screen, border_clr, self._yes_rect, 2, border_radius=8)
        yes_s = fm.render(self.yes_lbl, True, COLOR_TEXT)
        screen.blit(yes_s, (self._yes_rect.centerx - yes_s.get_width() // 2,
                             self._yes_rect.centery - yes_s.get_height() // 2))

        # Кнопка "Ні"
        no_hover = self._no_rect.collidepoint(mp)
        no_bg    = COLOR_BTN_HOVER if no_hover else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, no_bg,    self._no_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_GOLD, self._no_rect, 2, border_radius=8)
        no_s = fm.render(self.no_lbl, True, COLOR_TEXT)
        screen.blit(no_s, (self._no_rect.centerx - no_s.get_width() // 2,
                            self._no_rect.centery - no_s.get_height() // 2))

        # Підказка клавіш
        hint = fs.render("Enter — підтвердити   Esc — скасувати", True, COLOR_TEXT_DIM)
        screen.blit(hint, (self.x + self.W // 2 - hint.get_width() // 2,
                            self.y + self.H - 16))