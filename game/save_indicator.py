"""
Індикатор збереження — «💾 Збережено» що плавно з'являється і зникає.

Використання:
    # При збереженні:
    from game.save_indicator import signal_saved

    signal_saved()   # викликається з autosave()

    # В game loop (draw, поверх усього):
    from game.save_indicator import draw_save_indicator
    draw_save_indicator(screen)

    # В game loop (update):
    from game.save_indicator import update_save_indicator
    update_save_indicator(dt)
"""

import pygame

# ── Параметри анімації ──────────────────────────────────────────
_FADE_IN  = 0.25   # секунд на появу
_HOLD     = 1.6    # секунд на показ
_FADE_OUT = 0.6    # секунд на зникнення
_TOTAL    = _FADE_IN + _HOLD + _FADE_OUT

# ── Стан ────────────────────────────────────────────────────────
_timer: float = -1.0   # <0 → неактивний

def signal_saved():
    """Запускає анімацію індикатора."""
    global _timer
    _timer = _TOTAL          # скидаємо таймер навіть якщо вже показується

def update_save_indicator(dt: float):
    global _timer
    if _timer > 0:
        _timer -= dt

def draw_save_indicator(screen: pygame.Surface):
    """Малює індикатор у правому нижньому куті."""
    if _timer <= 0:
        return

    elapsed = _TOTAL - _timer

    # Розрахунок прозорості
    if elapsed < _FADE_IN:
        alpha = int(255 * elapsed / _FADE_IN)
    elif elapsed < _FADE_IN + _HOLD:
        alpha = 255
    else:
        fade_progress = (elapsed - _FADE_IN - _HOLD) / _FADE_OUT
        alpha = int(255 * (1.0 - fade_progress))

    alpha = max(0, min(255, alpha))
    if alpha == 0:
        return

    # Геометрія
    from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE_NORMAL
    from ui.assets import assets
    from ui.constants import COLOR_GOLD

    font  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
    label = "💾  Збережено"
    text_surf = font.render(label, True, (200, 220, 140))

    PAD_X, PAD_Y = 14, 8
    W = text_surf.get_width()  + PAD_X * 2
    H = text_surf.get_height() + PAD_Y * 2
    MARGIN = 14

    x = SCREEN_WIDTH  - W - MARGIN
    y = SCREEN_HEIGHT - H - MARGIN

    # Фонова плашка
    bg = pygame.Surface((W, H), pygame.SRCALPHA)
    bg_alpha = int(alpha * 0.80)
    bg.fill((20, 28, 14, bg_alpha))
    screen.blit(bg, (x, y))

    # Рамка
    border_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    border_color = (*COLOR_GOLD, alpha)
    pygame.draw.rect(border_surf, border_color, (0, 0, W, H), 2, border_radius=6)
    screen.blit(border_surf, (x, y))

    # Текст з прозорістю
    text_alpha = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
    text_alpha.blit(text_surf, (0, 0))
    text_alpha.set_alpha(alpha)
    screen.blit(text_alpha, (x + PAD_X, y + PAD_Y))