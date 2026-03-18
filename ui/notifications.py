"""
Централізована система сповіщень-тостів.

Використання:
    from ui.notifications import notify
    notify("💰 +50 золота", kind="gold")
    notify("⭐ Новий рівень!", kind="level")
    notify("✓ Гру збережено", kind="save", duration=1.5)

Типи (kind):
    "info"      — звичайне (сіро-синє)
    "gold"      — золото/нагорода (золотий)
    "level"     — рівень (пурпурний)
    "quest"     — квест (зелено-блакитний)
    "craft"     — крафт/розбирання (помаранчевий)
    "save"      — збереження (темно-сірий, малий)
    "error"     — помилка (червоний)
    "mutation"  — мутація (колір мутації через extra_color)
    "item"      — предмет в інвентарі (синій)
    "market"    — ринок (жовто-зелений)
"""
import math
import pygame
from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TEXT, COLOR_TEXT_DIM


# ── Стилі тостів ─────────────────────────────────────────────────

STYLES = {
    "info":     {"bg": (30, 28, 42, 230),  "border": (120, 120, 180), "icon": "ℹ"},
    "gold":     {"bg": (38, 30, 10, 235),  "border": (220, 180,  40), "icon": "💰"},
    "level":    {"bg": (35, 15, 50, 240),  "border": (180,  80, 255), "icon": "⭐"},
    "quest":    {"bg": (10, 35, 35, 235),  "border": ( 60, 200, 180), "icon": "📜"},
    "craft":    {"bg": (38, 22, 10, 235),  "border": (210, 130,  40), "icon": "⚒"},
    "save":     {"bg": (20, 20, 26, 210),  "border": ( 80,  80, 100), "icon": "💾"},
    "error":    {"bg": (42, 12, 12, 240),  "border": (220,  60,  60), "icon": "⚠"},
    "mutation": {"bg": (25, 12, 38, 240),  "border": (180,  80, 255), "icon": "✦"},
    "item":     {"bg": (12, 28, 42, 235),  "border": ( 80, 160, 220), "icon": "🎒"},
    "market":   {"bg": (15, 35, 15, 235),  "border": (100, 210,  80), "icon": "🏴"},
}

TOAST_W        = 340
TOAST_H_NORMAL = 54
TOAST_H_SMALL  = 36    # для "save"
TOAST_PAD_X    = 14
TOAST_GAP      = 8     # між тостами
TOAST_RIGHT    = 16    # відступ від правого краю
TOAST_BOTTOM   = 80    # відступ від низу

SLIDE_SPEED    = 900   # px/sec для анімації


class Toast:
    """Один тост-рядок."""

    def __init__(self, text: str, kind: str = "info",
                 duration: float = 3.0, extra_color=None, subtitle: str = ""):
        style     = STYLES.get(kind, STYLES["info"])
        self.text     = text
        self.subtitle = subtitle
        self.kind     = kind
        self.bg       = style["bg"]
        self.border   = extra_color or style["border"]
        self.icon     = style["icon"]
        self.duration = duration
        self.timer    = duration
        self.small    = (kind == "save")
        self.h        = TOAST_H_SMALL if self.small else TOAST_H_NORMAL

        # Анімація: починаємо за правим краєм
        self.x_offset = TOAST_W + 20   # slide in зправа
        self.alive     = True

    def update(self, dt: float) -> bool:
        self.timer -= dt

        # Slide-in
        target_x = 0
        if self.x_offset > target_x:
            self.x_offset = max(target_x,
                                self.x_offset - SLIDE_SPEED * dt)

        # Slide-out (останні 0.35с)
        if self.timer < 0.35:
            self.x_offset += SLIDE_SPEED * dt * 1.6

        if self.timer <= 0:
            self.alive = False
        return self.alive

    def draw(self, screen: pygame.Surface, x: int, y: int):
        from ui.assets import assets
        from ui.constants import FONT_SIZE_NORMAL, FONT_SIZE_SMALL

        draw_x = x + int(self.x_offset)
        w, h   = TOAST_W, self.h

        # Фон
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill(self.bg)
        # Ліва кольорова смужка
        pygame.draw.rect(surf, self.border, (0, 0, 4, h), border_radius=2)
        # Рамка
        pygame.draw.rect(surf, (*self.border[:3], 160),
                         surf.get_rect(), 1, border_radius=7)
        # Прогрес-бар знизу
        if self.duration > 0 and not self.small:
            pct  = max(0.0, self.timer / self.duration)
            bw   = int((w - 8) * pct)
            if bw > 0:
                pygame.draw.rect(surf, (*self.border[:3], 120),
                                 (4, h - 4, bw, 3), border_radius=1)
        screen.blit(surf, (draw_x, y))

        # Текст
        if self.small:
            font = assets.get_font(FONT_SIZE_SMALL)
            t    = font.render(self.text, True, COLOR_TEXT_DIM)
            screen.blit(t, (draw_x + TOAST_PAD_X + 22, y + h // 2 - t.get_height() // 2))
            icon_s = assets.get_font(16).render(self.icon, True, self.border)
            screen.blit(icon_s, (draw_x + TOAST_PAD_X, y + h // 2 - icon_s.get_height() // 2))
        else:
            font_main = assets.get_font(FONT_SIZE_NORMAL, bold=True)
            font_sub  = assets.get_font(FONT_SIZE_SMALL)
            icon_f    = assets.get_font(22)

            icon_s = icon_f.render(self.icon, True, self.border)
            screen.blit(icon_s, (draw_x + TOAST_PAD_X,
                                  y + h // 2 - icon_s.get_height() // 2))

            tx = draw_x + TOAST_PAD_X + icon_s.get_width() + 8
            if self.subtitle:
                main_s = font_main.render(self.text, True, COLOR_TEXT)
                sub_s  = font_sub.render(self.subtitle, True, COLOR_TEXT_DIM)
                screen.blit(main_s, (tx, y + 6))
                screen.blit(sub_s,  (tx, y + 6 + main_s.get_height()))
            else:
                main_s = font_main.render(self.text, True, COLOR_TEXT)
                screen.blit(main_s, (tx, y + h // 2 - main_s.get_height() // 2))


# ══════════════════════════════════════════
#  МЕНЕДЖЕР
# ══════════════════════════════════════════

class NotificationManager:
    """Зберігає чергу тостів і малює їх поверх усього."""

    MAX_VISIBLE = 5

    def __init__(self):
        self._queue: list[Toast] = []

    def push(self, text: str, kind: str = "info",
             duration: float = 3.0, extra_color=None, subtitle: str = ""):
        """Додає новий тост. Дублікати за текстом ігноруються."""
        # Не дублюємо той самий текст якщо вже є живий
        for t in self._queue:
            if t.text == text and t.alive:
                t.timer = max(t.timer, duration * 0.5)  # продовжуємо
                return
        toast = Toast(text, kind, duration, extra_color, subtitle)
        self._queue.append(toast)

    def update(self, dt: float):
        self._queue = [t for t in self._queue if t.update(dt)]

    def draw(self, screen: pygame.Surface):
        visible = [t for t in self._queue if t.alive][-self.MAX_VISIBLE:]
        # Малюємо знизу вгору
        y = SCREEN_HEIGHT - TOAST_BOTTOM
        for toast in reversed(visible):
            y -= toast.h
            x  = SCREEN_WIDTH - TOAST_W - TOAST_RIGHT
            toast.draw(screen, x, y)
            y -= TOAST_GAP

    def clear(self):
        self._queue.clear()


# ── Глобальний singleton ──────────────────────────────────────────

_manager = NotificationManager()


def notify(text: str, kind: str = "info", duration: float = 3.0,
           extra_color=None, subtitle: str = ""):
    """Головна функція — викликати звідусіль."""
    _manager.push(text, kind, duration, extra_color, subtitle)


def get_manager() -> NotificationManager:
    return _manager