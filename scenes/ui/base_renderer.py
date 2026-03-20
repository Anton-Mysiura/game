"""
Базовий клас Renderer.

Кожен Renderer відповідає ТІЛЬКИ за малювання однієї сцени.
Він нічого не змінює в стані гри — тільки читає і малює.

Як використовувати:
    У draw() сцени:
        self._renderer.draw(screen)

    Renderer отримує сцену через self.scene і читає з неї
    будь-які атрибути: self.scene.player, self.scene.stage тощо.
"""
import pygame


class BaseRenderer:
    """
    Базовий клас рендерера сцени.

    Параметри:
        scene — посилання на об'єкт сцени (core).
                Renderer читає стан сцени, але НІКОЛИ не змінює його.
    """

    def __init__(self, scene):
        self.scene  = scene
        self.player = scene.player
        self.game   = scene.game

    def draw(self, screen: pygame.Surface):
        """Головний метод малювання. Перевизначається в підкласах."""
        # Малюємо фон сцени якщо він є (SceneWithBackground)
        if hasattr(self.scene, 'background') and self.scene.background:
            screen.blit(self.scene.background, (0, 0))
        elif hasattr(self.scene, '_bg') and self.scene._bg:
            screen.blit(self.scene._bg, (0, 0))
        else:
            from ui.constants import COLOR_BG
            screen.fill(COLOR_BG)

    # ── Утиліти, спільні для всіх рендерерів ─────────────────────

    def _overlay(self, screen: pygame.Surface,
                 color: tuple = (0, 0, 0), alpha: int = 150):
        """Напівпрозоре затемнення поверх всього."""
        surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        surf.fill((*color[:3], alpha))
        screen.blit(surf, (0, 0))

    def _draw_wrapped_text(self, screen: pygame.Surface, font,
                           text: str, color,
                           x: int, y: int, max_width: int,
                           line_spacing: int = 4) -> int:
        """
        Малює текст з автоматичним переносом рядків.
        Повертає Y-координату після останнього рядка.
        Підтримує \\n для явного переносу.
        """
        line_h = font.get_height() + line_spacing
        for paragraph in text.split("\n"):
            words = paragraph.split()
            line  = ""
            for word in words:
                test = (line + " " + word).strip()
                if font.size(test)[0] <= max_width:
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

    def _centered(self, screen: pygame.Surface, surf: pygame.Surface,
                  y: int, x_offset: int = 0):
        """Малює surf по центру екрану на висоті y."""
        x = screen.get_width() // 2 - surf.get_width() // 2 + x_offset
        screen.blit(surf, (x, y))