"""
Базовий клас для всіх рендерерів.

Кожен рендерер у scenes/ui/ успадковує цей клас.
Надає доступ до сцени через self.scene і малює фон у draw().
"""
import pygame
from ui.constants import COLOR_BG
from ui.assets import assets


class BaseRenderer:
    """
    Базовий рендерер.

    Використання:
        class MyRenderer(BaseRenderer):
            def draw(self, screen):
                super().draw(screen)   # малює фон
                # ... твоє малювання
    """

    def __init__(self, scene):
        self.scene = scene

    def draw(self, screen: pygame.Surface):
        """Малює фон сцени. Виклич super().draw(screen) на початку draw()."""

        # 1. Якщо сцена вже намалювала фон через SceneWithBackground — нічого не робимо
        if hasattr(self.scene, "background") and self.scene.background is not None:
            screen.blit(self.scene.background, (0, 0))
            return

        # 2. Фон з config/ui.py якщо налаштований
        try:
            scene_key = getattr(self.scene, "_bg_scene_key", None)
            if scene_key is None:
                name = type(self.scene).__name__.lower().replace("scene", "")
                for key in ("main_menu", "village", "forest", "battle",
                            "shop", "workshop", "inventory", "ruins",
                            "tower", "mine", "world_map", "market",
                            "elder", "hero_roulette", "hero_slots"):
                    if key.replace("_", "") in name.replace("_", ""):
                        scene_key = key
                        break

            if scene_key:
                bg = assets.get_background(scene_key,
                                           (screen.get_width(), screen.get_height()))
                if bg:
                    screen.blit(bg, (0, 0))
                    return
        except Exception:
            pass

        # 3. Fallback — суцільний фон
        screen.fill(COLOR_BG)
