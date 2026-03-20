"""
Рендерер для OnboardingScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/onboarding.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

import math
from ui.constants import *
from ui.assets import assets


class OnboardingRenderer(BaseRenderer):
    """
    Малює OnboardingScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen):
        if self.scene._sub:
            self.scene._sub.draw(screen)