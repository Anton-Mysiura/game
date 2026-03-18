"""
Адмін-панель (читкоди для тестування).
"""

import pygame
from .base import Scene
from ui.components import Button, Panel, ScrollableList
from ui.constants import *
from ui.assets import assets
from game.data import OwnedBlueprint, MATERIALS, ITEMS, BLUEPRINTS
from game.save_manager import autosave


class AdminScene(Scene):
    """Адмін-панель для розробки та тестування."""

    def __init__(self, game):
        super().__init__(game)

        self.mode = "main"  # main | gold | materials | items | blueprints | level
        self.input_text = ""
        self.selected_material = None
        self.selected_item = None
        self.selected_blueprint = None

        # Панель
        self.main_panel = Panel(SCREEN_WIDTH // 2 - 400, 100, 800, 550, alpha=True)

        # Кнопки головного меню
        self._create_main_buttons()

    def _create_main_buttons(self):
        """Створює кнопки головного меню."""
        center_x = SCREEN_WIDTH // 2
        start_y = 200
        spacing = 70

        self.main_buttons = [
            Button(center_x - 150, start_y, 300, 50, "💰 Додати золото",
                   lambda: self._switch_mode("gold")),
            Button(center_x - 150, start_y + spacing, 300, 50, "📦 Видати матеріали",
                   lambda: self._switch_mode("materials")),
            Button(center_x - 150, start_y + spacing * 2, 300, 50, "🎒 Видати предмети",
                   lambda: self._switch_mode("items")),
            Button(center_x - 150, start_y + spacing * 3, 300, 50, "📜 Видати кресленники",
                   lambda: self._switch_mode("blueprints")),
            Button(center_x - 150, start_y + spacing * 4, 300, 50, "⬆ Встановити рівень",
                   lambda: self._switch_mode("level")),
            Button(center_x - 150, start_y + spacing * 5, 300, 50, "💚 Відновити HP",
                   lambda: self._heal_player()),
            Button(center_x - 150, start_y + spacing * 6, 300, 50, "🎁 ДАТИ ВСЕ",
                   lambda: self._give_all()),
        ]

        self.close_button = Button(SCREEN_WIDTH // 2 - 100, 600, 200, 50,
                                   "Закрити", lambda: self.game.pop_scene())

    def _switch_mode(self, mode: str):
        """Перемикає режим."""
        self.mode = mode
        self.input_text = ""

    def _heal_player(self):
        """Відновлює HP до максимуму."""
        self.player.hp = self.player.max_hp
        autosave(self.player)
        print("HP відновлено!")

    def _give_all(self):
        """Дає все одразу."""
        # Золото
        self.player.gold += 999

        # Матеріали
        for mat_id in MATERIALS.keys():
            self.player.add_material(mat_id, 99)

        # Кресленники
        for bp in BLUEPRINTS.values():
            if not any(ob.blueprint_id == bp.blueprint_id for ob in self.player.blueprints):
                self.player.blueprints.append(OwnedBlueprint.new(bp))

        # Предмети
        for item_id in ["small_potion", "big_potion", "power_potion",
                        "leather_armor", "chainmail"]:
            self.player.inventory.append(ITEMS[item_id])

        autosave(self.player)
        print("Все видано!")

    def _add_gold(self):
        """Додає золото."""
        try:
            amount = int(self.input_text)
            self.player.gold += amount
            autosave(self.player)
            print(f"Додано {amount} золота!")
            self.mode = "main"
            self.input_text = ""
        except ValueError:
            print("Невірне число!")

    def _add_material(self, mat_id: str):
        """Додає матеріал."""
        try:
            amount = int(self.input_text) if self.input_text else 10
            self.player.add_material(mat_id, amount)
            autosave(self.player)
            print(f"Додано {amount}x {MATERIALS[mat_id].name}")
            self.input_text = ""
        except ValueError:
            print("Невірне число!")

    def _add_item(self, item_id: str):
        """Додає предмет."""
        self.player.inventory.append(ITEMS[item_id])
        autosave(self.player)
        print(f"Додано {ITEMS[item_id].name}")

    def _add_blueprint(self, bp_id: str):
        """Додає кресленник."""
        bp = BLUEPRINTS[bp_id]
        if bp not in self.player.blueprints:
            self.player.blueprints.append(bp)
            autosave(self.player)
            print(f"Додано {bp.name}")
        else:
            print("Вже є!")

    def _set_level(self):
        """Встановлює рівень."""
        try:
            level = int(self.input_text)
            if 1 <= level <= 99:
                # Встановлюємо рівень
                old_level = self.player.level
                self.player.level = level

                # Підвищуємо характеристики
                level_diff = level - old_level
                if level_diff > 0:
                    self.player.max_hp += 15 * level_diff
                    self.player.hp = self.player.max_hp
                    self.player.attack += 2 * level_diff
                    self.player.defense += level_diff

                self.player.xp = 0
                self.player.xp_next = int(50 * (1.5 ** (level - 1)))

                autosave(self.player)
                print(f"Рівень встановлено: {level}")
                self.mode = "main"
                self.input_text = ""
            else:
                print("Рівень має бути 1-99!")
        except ValueError:
            print("Невірне число!")

    def handle_event(self, event: pygame.event.Event):
        """Обробка подій."""
        if self.mode == "main":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for btn in self.main_buttons:
                    btn.update(mouse_pos, True)
                self.close_button.update(mouse_pos, True)

        elif self.mode in ["gold", "level"]:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.mode == "gold":
                        self._add_gold()
                    elif self.mode == "level":
                        self._set_level()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode = "main"
                    self.input_text = ""
                elif event.unicode.isdigit():
                    self.input_text += event.unicode

        elif self.mode == "materials":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # Вибір матеріалу
                y = 180
                for mat_id in MATERIALS.keys():
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, y, 300, 40)
                    if btn_rect.collidepoint(mouse_pos):
                        self._add_material(mat_id)
                        break
                    y += 50

                # Кнопка назад
                back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 600, 200, 50)
                if back_btn.collidepoint(mouse_pos):
                    self.mode = "main"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode = "main"
                    self.input_text = ""
                elif event.unicode.isdigit():
                    self.input_text += event.unicode

        elif self.mode == "items":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                y = 180
                for item_id in ITEMS.keys():
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, y, 300, 40)
                    if btn_rect.collidepoint(mouse_pos):
                        self._add_item(item_id)
                        break
                    y += 50

                back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 600, 200, 50)
                if back_btn.collidepoint(mouse_pos):
                    self.mode = "main"

        elif self.mode == "blueprints":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                y = 180
                for bp_id in BLUEPRINTS.keys():
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, y, 300, 40)
                    if btn_rect.collidepoint(mouse_pos):
                        self._add_blueprint(bp_id)
                        break
                    y += 50

                back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 600, 200, 50)
                if back_btn.collidepoint(mouse_pos):
                    self.mode = "main"

    def update(self, dt: float):
        """Оновлення."""
        if self.mode == "main":
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.main_buttons:
                btn.update(mouse_pos, False)
            self.close_button.update(mouse_pos, False)

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # Затемнений фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Панель
        self.main_panel.draw(screen)

        # Заголовок
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        title = font_title.render("🛠 АДМІН-ПАНЕЛЬ", True, COLOR_ERROR)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        if self.mode == "main":
            self._draw_main_menu(screen)
        elif self.mode == "gold":
            self._draw_gold_input(screen)
        elif self.mode == "materials":
            self._draw_materials_list(screen)
        elif self.mode == "items":
            self._draw_items_list(screen)
        elif self.mode == "blueprints":
            self._draw_blueprints_list(screen)
        elif self.mode == "level":
            self._draw_level_input(screen)

    def _draw_main_menu(self, screen):
        """Малює головне меню."""
        for btn in self.main_buttons:
            btn.draw(screen)
        self.close_button.draw(screen)

        # Підказка
        font_hint = assets.get_font(FONT_SIZE_SMALL)
        hint = font_hint.render("F12 — закрити адмін-панель", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 660))

    def _draw_gold_input(self, screen):
        """Малює введення золота."""
        font = assets.get_font(FONT_SIZE_MEDIUM)
        text = font.render("Скільки золота додати?", True, COLOR_TEXT)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 250))

        # Поле вводу
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 320, 300, 50)
        pygame.draw.rect(screen, COLOR_PANEL, input_rect)
        pygame.draw.rect(screen, COLOR_GOLD, input_rect, 3)

        input_display = font.render(self.input_text + "_", True, COLOR_TEXT)
        screen.blit(input_display, (input_rect.x + 10, input_rect.y + 12))

        # Підказка
        font_hint = assets.get_font(FONT_SIZE_SMALL)
        hint = font_hint.render("Enter — підтвердити | ESC — скасувати", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 400))

    def _draw_materials_list(self, screen):
        """Малює список матеріалів."""
        font_title = assets.get_font(FONT_SIZE_MEDIUM)
        title = font_title.render("Вибери матеріал:", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH // 2 - 350, 150))

        # Поле кількості
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 + 50, 150, 200, 40)
        pygame.draw.rect(screen, COLOR_PANEL, input_rect)
        pygame.draw.rect(screen, COLOR_GOLD, input_rect, 2)

        font_input = assets.get_font(FONT_SIZE_NORMAL)
        input_display = font_input.render(f"Кількість: {self.input_text or '10'}", True, COLOR_TEXT)
        screen.blit(input_display, (input_rect.x + 10, input_rect.y + 10))

        # Список
        font_item = assets.get_font(FONT_SIZE_NORMAL)
        y = 180

        for mat_id, mat in MATERIALS.items():
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, y, 300, 40)

            color = COLOR_BTN_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_PANEL
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(screen, COLOR_GOLD, btn_rect, 2)

            has = self.player.materials.get(mat_id, 0)
            text = font_item.render(f"{mat.icon} {mat.name} ({has})", True, COLOR_TEXT)
            screen.blit(text, (btn_rect.x + 10, btn_rect.y + 10))

            y += 50

        # Кнопка назад
        back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 600, 200, 50)
        color = COLOR_BTN_HOVER if back_btn.collidepoint(pygame.mouse.get_pos()) else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, color, back_btn)
        pygame.draw.rect(screen, COLOR_GOLD, back_btn, 2)
        back_text = font_item.render("Назад", True, COLOR_TEXT)
        screen.blit(back_text, (back_btn.centerx - back_text.get_width() // 2, back_btn.y + 15))

    def _draw_items_list(self, screen):
        """Малює список предметів."""
        font_title = assets.get_font(FONT_SIZE_MEDIUM)
        title = font_title.render("Вибери предмет:", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH // 2 - 350, 150))

        font_item = assets.get_font(FONT_SIZE_NORMAL)
        y = 200

        for item_id, item in ITEMS.items():
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, y, 400, 40)

            color = COLOR_BTN_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_PANEL
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(screen, COLOR_GOLD, btn_rect, 2)

            text = font_item.render(f"{item.icon} {item.name}", True, COLOR_TEXT)
            screen.blit(text, (btn_rect.x + 10, btn_rect.y + 10))

            y += 50

        back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 600, 200, 50)
        color = COLOR_BTN_HOVER if back_btn.collidepoint(pygame.mouse.get_pos()) else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, color, back_btn)
        pygame.draw.rect(screen, COLOR_GOLD, back_btn, 2)
        back_text = font_item.render("Назад", True, COLOR_TEXT)
        screen.blit(back_text, (back_btn.centerx - back_text.get_width() // 2, back_btn.y + 15))

    def _draw_blueprints_list(self, screen):
        """Малює список кресленників."""
        font_title = assets.get_font(FONT_SIZE_MEDIUM)
        title = font_title.render("Вибери кресленник:", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH // 2 - 350, 150))

        font_item = assets.get_font(FONT_SIZE_SMALL)
        y = 200

        for bp_id, bp in BLUEPRINTS.items():
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, y, 500, 40)

            has_it = any(ob.blueprint_id == bp.blueprint_id for ob in self.player.blueprints)
            color = COLOR_BTN_DISABLED if has_it else (
                COLOR_BTN_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_PANEL)
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(screen, COLOR_GOLD, btn_rect, 2)

            status = " (маєш)" if has_it else ""
            text = font_item.render(f"📜 {bp.name}{status}", True, COLOR_TEXT)
            screen.blit(text, (btn_rect.x + 10, btn_rect.y + 10))

            y += 50

        back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 600, 200, 50)
        color = COLOR_BTN_HOVER if back_btn.collidepoint(pygame.mouse.get_pos()) else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, color, back_btn)
        pygame.draw.rect(screen, COLOR_GOLD, back_btn, 2)
        back_text = font_item.render("Назад", True, COLOR_TEXT)
        screen.blit(back_text, (back_btn.centerx - back_text.get_width() // 2, back_btn.y + 15))

    def _draw_level_input(self, screen):
        """Малює введення рівня."""
        font = assets.get_font(FONT_SIZE_MEDIUM)
        text = font.render("Встановити рівень (1-99):", True, COLOR_TEXT)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 250))

        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 320, 300, 50)
        pygame.draw.rect(screen, COLOR_PANEL, input_rect)
        pygame.draw.rect(screen, COLOR_GOLD, input_rect, 3)

        input_display = font.render(self.input_text + "_", True, COLOR_TEXT)
        screen.blit(input_display, (input_rect.x + 10, input_rect.y + 12))

        font_hint = assets.get_font(FONT_SIZE_SMALL)
        hint = font_hint.render("Enter — підтвердити | ESC — скасувати", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 400))