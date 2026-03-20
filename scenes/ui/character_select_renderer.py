"""
Рендерер для CharacterSelectScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/character_select.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets


class CharacterSelectRenderer(BaseRenderer):
    """
    Малює CharacterSelectScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        screen.fill((20, 15, 25))

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("Вибери персонажа", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        font_name = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_desc = assets.get_font(FONT_SIZE_SMALL)

        for i, card in enumerate(self.scene.cards):
            char = card["char"]
            rect = card["rect"]
            is_selected = i == self.scene.selected

            # Фон картки
            bg_color = (50, 40, 60) if not is_selected else (70, 55, 90)
            pygame.draw.rect(screen, bg_color, rect, border_radius=14)
            border_color = COLOR_GOLD if is_selected else (80, 65, 100)
            pygame.draw.rect(screen, border_color, rect, 3 if is_selected else 1, border_radius=14)

            # Зона анімації
            preview_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, 220)
            pygame.draw.rect(screen, (30, 25, 40), preview_rect, border_radius=10)

            # Поточний кадр з AnimationController
            frame = self.scene.anim_controllers[i].get_current_frame()
            if frame:
                fx = preview_rect.centerx - frame.get_width() // 2
                fy = preview_rect.centery - frame.get_height() // 2
                screen.blit(frame, (fx, fy))

            # Тінь під персонажем
            shadow = pygame.Surface((120, 12), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 60))
            screen.blit(shadow, (preview_rect.centerx - 60, preview_rect.bottom - 18))

            # Ім'я
            name_surf = font_name.render(char["name"], True, COLOR_GOLD if is_selected else COLOR_TEXT)
            screen.blit(name_surf, (rect.centerx - name_surf.get_width() // 2, rect.y + 238))

            # Опис
            desc_surf = font_desc.render(char["description"], True, COLOR_TEXT_DIM)
            screen.blit(desc_surf, (rect.centerx - desc_surf.get_width() // 2, rect.y + 272))

            # Атаки
            atk_surf = font_desc.render(f"Атак: {char['attacks']}", True, COLOR_HP)
            screen.blit(atk_surf, (rect.centerx - atk_surf.get_width() // 2, rect.y + 300))

            # Стрілка вибору
            if is_selected:
                arrow = font_desc.render("▼ Вибрано ▼", True, COLOR_GOLD)
                screen.blit(arrow, (rect.centerx - arrow.get_width() // 2, rect.bottom + 8))

        # Підказка
        hint = font_desc.render("← → для вибору  |  Enter або клік для підтвердження", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 155))

        self.scene.confirm_btn.draw(screen)