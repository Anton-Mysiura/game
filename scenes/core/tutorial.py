"""
Сцена туторіалу (покрокове навчання).
"""

import pygame
from .base import Scene
from ui.components import Button, Panel, TextBox
from ui.constants import *
from ui.assets import assets


class TutorialScene(Scene):
    """Сцена показу туторіалу."""

    def __init__(self, game, tutorial_data: list, next_scene: str):
        super().__init__(game)

        self.tutorial_data = tutorial_data  # [{id, title, pages}]
        self.next_scene = next_scene

        self.current_tutorial = 0
        self.current_page = 0

        # UI
        self.panel = Panel(SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT // 2 - 250, 800, 500, alpha=True)
        self.text_box = TextBox(SCREEN_WIDTH // 2 - 360, SCREEN_HEIGHT // 2 - 150, 720, FONT_SIZE_NORMAL)

        # Кнопки
        self.next_button = Button(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 200, 200, 50,
                                  "Далі →", lambda: self._next_page())
        self.skip_button = Button(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 + 200, 200, 50,
                                  "Пропустити", lambda: self._skip())

        # Завантажуємо першу сторінку
        self._load_current_page()

        # Підключаємо renderer (малювання)
        from scenes.ui.tutorial_renderer import TutorialRenderer
        self._renderer = TutorialRenderer(self)
    def _load_current_page(self):
        """Завантажує поточну сторінку."""
        if self.current_tutorial >= len(self.tutorial_data):
            # Всі туторіали пройдено
            self._finish()
            return

        tut = self.tutorial_data[self.current_tutorial]
        pages = tut["pages"]

        if self.current_page >= len(pages):
            # Поточний туторіал закінчився
            self.current_tutorial += 1
            self.current_page = 0
            self._load_current_page()
            return

        # Завантажуємо текст сторінки
        page_lines = pages[self.current_page]
        page_text = "\n".join(page_lines)
        self.text_box.set_text(page_text)

        # Змінюємо текст кнопки для останньої сторінки
        is_last = (self.current_tutorial == len(self.tutorial_data) - 1 and
                   self.current_page == len(pages) - 1)

        if is_last:
            self.next_button.text = "Почати гру →"
        else:
            self.next_button.text = "Далі →"

    def _next_page(self):
        """Наступна сторінка."""
        self.current_page += 1
        self._load_current_page()

    def _skip(self):
        """Пропустити туторіал."""
        self._finish()

    def _finish(self):
        """Завершує туторіал."""
        self.game.change_scene(self.next_scene)

    def handle_event(self, event: pygame.event.Event):
        """Обробка подій."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._next_page()
            elif event.key == pygame.K_ESCAPE:
                self._skip()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            self.next_button.update(mouse_pos, True)
            self.skip_button.update(mouse_pos, True)

    def update(self, dt: float):
        """Оновлення."""
        mouse_pos = pygame.mouse.get_pos()
        self.next_button.update(mouse_pos, False)
        self.skip_button.update(mouse_pos, False)

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)