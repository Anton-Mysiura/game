"""
Базовий клас для всіх сцен (екранів гри).
"""

import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.core import Game


class Scene:
    """Базовий клас сцени."""

    def __init__(self, game: 'Game'):
        self.game = game
        self.player = game.player

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, screen: pygame.Surface):
        pass

    def on_enter(self):
        """Викликається при вході в сцену."""
        pass

    def on_exit(self):
        """Викликається при виході зі сцени."""
        pass


class SceneWithBackground(Scene):
    """Сцена з фоновим зображенням."""

    def __init__(self, game: 'Game', background_name: str):
        super().__init__(game)
        self.background_name = background_name
        self.background = None

    def on_enter(self):
        """Завантажує фон при вході."""
        from ui.assets import assets
        from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT
        self.background = assets.load_texture("locations", self.background_name,
                                              (SCREEN_WIDTH, SCREEN_HEIGHT))

    def draw(self, screen: pygame.Surface):
        """Малює фон."""
        if self.background:
            screen.blit(self.background, (0, 0))


class SceneWithButtons(Scene):
    """Сцена з кнопками."""

    def __init__(self, game: 'Game'):
        super().__init__(game)
        self.buttons = []
        self.mouse_clicked_last_frame = False

    def handle_event(self, event: pygame.event.Event):
        """Обробка кліків по кнопках."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, True)

    def update(self, dt: float):
        """Оновлення стану кнопок."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Викликаємо callback тільки при новому кліку
        if mouse_pressed and not self.mouse_clicked_last_frame:
            for button in self.buttons:
                button.update(mouse_pos, True)
        else:
            for button in self.buttons:
                button.update(mouse_pos, False)

        self.mouse_clicked_last_frame = mouse_pressed

    def draw_buttons(self, screen: pygame.Surface):
        """Малює всі кнопки."""
        for button in self.buttons:
            button.draw(screen)


class DungeonScene(SceneWithBackground, SceneWithButtons):
    """
    Базовий клас для локацій-підземель (вежа, руїни тощо).

    Параметри підкласу:
        BACKGROUND   — назва фону (для AssetManager)
        TITLE        — заголовок сцени
        RETURN_SCENE — ідентифікатор для return_scene після бою
        GOLD_REWARD  — нагорода після перемоги
        INTRO_TEXT   — текст при вході
        AFTER_TEXT   — текст після перемоги
        NEXT_SCENE   — сцена після перемоги (наприклад "dragon")
        FIGHT_LABEL  — підпис на кнопці бою
        ENEMY_FACTORY — функція що створює ворога (наприклад make_dark_knight)
    """

    BACKGROUND: str = ""
    TITLE: str = ""
    RETURN_SCENE: str = ""
    GOLD_REWARD: int = 0
    INTRO_TEXT: str = ""
    AFTER_TEXT: str = ""
    NEXT_SCENE: str = "dragon"
    FIGHT_LABEL: str = "⚔ У бій!"
    ENEMY_FACTORY = None

    def __init__(self, game: 'Game'):
        SceneWithBackground.__init__(self, game, self.BACKGROUND)
        SceneWithButtons.__init__(self, game)

        from ui.components import Panel, TextBox
        from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE_NORMAL

        self.stage = "intro"

        self.dialog_panel = Panel(SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT - 300, 800, 250, alpha=True)
        self.text_box = TextBox(SCREEN_WIDTH // 2 - 370, SCREEN_HEIGHT - 270, 740, FONT_SIZE_NORMAL)

        self._show_intro()

    def _show_intro(self):
        """Вступ до локації."""
        from ui.components import Button
        from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT

        self.stage = "intro"
        self.text_box.set_text(self.INTRO_TEXT)

        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 100, 200, 50,
                   self.FIGHT_LABEL, self._start_fight),
            Button(SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT - 100, 200, 50,
                   "🏘 Назад до села", lambda: self.game.change_scene("village")),
        ]

    def _start_fight(self):
        """Починає бій зі створеним ворогом."""
        enemy = self.ENEMY_FACTORY(self.player.level)
        self.game.change_scene("battle", enemy=enemy, return_scene=self.RETURN_SCENE)

    def on_enter(self):
        """Перевіряє результат бою при поверненні."""
        super().on_enter()
        if self.game.scene_data.get("from_battle") == self.RETURN_SCENE:
            self._after_battle()

    def _after_battle(self):
        """Нагорода та текст після перемоги."""
        from ui.components import Button
        from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT
        from game.save_manager import autosave

        self.stage = "after_battle"
        self.player.gold += self.GOLD_REWARD

        # Записуємо локацію як відвідану/пройдену
        if self.RETURN_SCENE:
            self.player.locations_visited.add(self.RETURN_SCENE)

        autosave(self.player)

        self.text_box.set_text(self.AFTER_TEXT)

        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 100, 200, 50,
                   "🐉 Далі!", lambda: self.game.change_scene(self.NEXT_SCENE)),
            Button(SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT - 100, 200, 50,
                   "🏘 До села", lambda: self.game.change_scene("village")),
        ]

    def draw(self, screen: pygame.Surface):
        """Малює фон, заголовок, діалог і кнопки."""
        from ui.assets import assets
        from ui.constants import SCREEN_WIDTH, FONT_SIZE_HUGE, COLOR_GOLD

        super().draw(screen)

        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render(self.TITLE, True, COLOR_GOLD)
        title_shadow = font_title.render(self.TITLE, True, (0, 0, 0))
        screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 2, 52))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        self.dialog_panel.draw(screen)
        self.text_box.draw(screen)
        self.draw_buttons(screen)


class DialogScene(SceneWithBackground):
    """Сцена з діалоговою панеллю."""

    def __init__(self, game: 'Game', background_name: str):
        super().__init__(game, background_name)
        from ui.components import Panel, TextBox
        from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_PADDING

        # Панель для тексту
        panel_width = SCREEN_WIDTH - 200
        panel_height = 250
        panel_x = 100
        panel_y = SCREEN_HEIGHT - panel_height - 50

        self.dialog_panel = Panel(panel_x, panel_y, panel_width, panel_height, alpha=True)
        self.text_box = TextBox(panel_x + PANEL_PADDING,
                                panel_y + PANEL_PADDING,
                                panel_width - PANEL_PADDING * 2)
        self.dialog_text = ""

    def set_dialog(self, text: str):
        """Встановлює текст діалогу."""
        self.dialog_text = text
        self.text_box.set_text(text)

    def draw_dialog(self, screen: pygame.Surface):
        """Малює діалогову панель."""
        if self.dialog_text:
            self.dialog_panel.draw(screen)
            self.text_box.draw(screen)