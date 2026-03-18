"""
Головний клас гри (Game loop, зміна сцен, ініціалізація).
"""

import logging

log = logging.getLogger(__name__)

import pygame
import sys
from typing import Optional
from .player import Player
from .save_manager import SaveManager, autosave
from .tutorial_manager import TutorialManager


class Game:
    """Головний клас гри."""

    def __init__(self):
        pygame.init()

        from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

        self._virtual_w = SCREEN_WIDTH
        self._virtual_h = SCREEN_HEIGHT

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE
        )
        # Буфер фіксованого розміру — сюди малює весь ігровий код
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        pygame.display.set_caption("⚔ Темне Королівство")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = FPS

        # Гравець
        self.player: Optional[Player] = None

        # Адмін консоль (одна на всю гру, перехоплює ~ в будь-якій сцені)
        self._console = None  # ініціалізується після створення гравця
        self.is_fullscreen = False

        # Поточна сцена
        self.current_scene = None

        # Стек сцен для повернення назад
        self.scene_stack = []
        # Сповіщення про досягнення
        self.achievement_notifications = []

        # Дані для передачі між сценами
        self.scene_data = {}
        self.last_battle_record = None   # BattleRecord останнього бою
        self._pending_battle    = None   # бій що можна продовжити
        self._exit_confirm      = None   # діалог підтвердження виходу

        # Менеджер переходів між сценами
        from game.transitions import get_transition_manager
        self._transition = get_transition_manager()

    def _scale_rect(self):
        """Повертає (scale, offset_x, offset_y) для letterbox/pillarbox."""
        ww, wh = self.screen.get_size()
        scale = min(ww / self._virtual_w, wh / self._virtual_h)
        ox = (ww - self._virtual_w * scale) / 2
        oy = (wh - self._virtual_h * scale) / 2
        return scale, ox, oy

    def _screen_to_virtual(self, pos):
        """Перетворює координати реального вікна у координати virtual surface."""
        scale, ox, oy = self._scale_rect()
        x = (pos[0] - ox) / scale
        y = (pos[1] - oy) / scale
        return (int(x), int(y))

    def _blit_scaled(self):
        """Масштабує _surface на screen із letterbox."""
        scale, ox, oy = self._scale_rect()
        w = int(self._virtual_w * scale)
        h = int(self._virtual_h * scale)
        scaled = pygame.transform.scale(self._surface, (w, h))
        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled, (int(ox), int(oy)))

    def _transform_mouse_event(self, event: pygame.event.Event) -> pygame.event.Event:
        """Перетворює координати миші з реального вікна у virtual 1280×720."""
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            vx, vy = self._screen_to_virtual(event.pos)
            vx = max(0, min(self._virtual_w - 1, vx))
            vy = max(0, min(self._virtual_h - 1, vy))
            # Створюємо нову подію з трансформованими координатами
            attrs = event.__dict__.copy()
            attrs['pos'] = (vx, vy)
            if event.type == pygame.MOUSEMOTION and 'rel' in attrs:
                scale, _, _ = self._scale_rect()
                rx = int(attrs['rel'][0] / scale)
                ry = int(attrs['rel'][1] / scale)
                attrs['rel'] = (rx, ry)
            return pygame.event.Event(event.type, attrs)
        return event

    def toggle_fullscreen(self):
        """Перемикає повноекранний режим."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE
            )

    def start(self):
        """Запуск гри (головне меню)."""
        self.change_scene("main_menu")

    def change_scene(self, scene_name: str, **kwargs):
        """
        Змінює поточну сцену з анімацією fade-out → swap → fade-in.
        """
        # Якщо перехід вже йде — ігноруємо повторні виклики
        if self._transition.busy:
            return

        # Визначаємо тривалість переходу
        dramatic = scene_name in ("battle", "death", "victory", "dragon")
        from game.transitions import DRAMATIC_OUT, DRAMATIC_IN, DEFAULT_OUT, DEFAULT_IN
        dur = (DRAMATIC_OUT, DRAMATIC_IN) if dramatic else (DEFAULT_OUT, DEFAULT_IN)

        self._transition.request(
            callback=lambda: self._do_change_scene(scene_name, **kwargs),
            duration=dur,
        )

    def _do_change_scene(self, scene_name: str, **kwargs):
        """Внутрішній метод — миттєва зміна сцени (без анімації)."""
        # Зберігаємо дані
        self.scene_data.update(kwargs)

        # Викликаємо on_exit у старої сцени
        if self.current_scene:
            self.current_scene.on_exit()

        # Створюємо нову сцену
        if scene_name == "main_menu":
            from scenes.main_menu import MainMenuScene
            self.current_scene = MainMenuScene(self)

        elif scene_name == "hero_roulette":
            from scenes.hero_roulette import HeroRouletteScene
            self.current_scene = HeroRouletteScene(self)

        elif scene_name == "hero_slots":
            from scenes.hero_slots import HeroSlotsScene
            self.current_scene = HeroSlotsScene(self)

        elif scene_name == "village":
            from scenes.village import VillageScene
            self.current_scene = VillageScene(self)

        elif scene_name == "shop":
            from scenes.shop import ShopScene
            self.current_scene = ShopScene(self)

        elif scene_name == "workshop":
            from scenes.workshop import WorkshopScene
            self.current_scene = WorkshopScene(self)


        elif scene_name == "battle":

            from scenes.battle_fighting import FightingBattleScene

            enemy = kwargs.get("enemy")

            return_scene = kwargs.get("return_scene", "village")
            background_name = kwargs.get("background_name", None)

            self.current_scene = FightingBattleScene(self, enemy, return_scene, background_name)
        elif scene_name == "forest":
            from scenes.forest import ForestScene
            self.current_scene = ForestScene(self)

        elif scene_name == "forest_free":
            # Повернення після вільного бою у лісі
            from scenes.forest import ForestScene
            self.scene_data["from_battle"] = "forest_free"
            self.current_scene = ForestScene(self)

        # У методі change_scene додай цей блок (після "forest"):

        elif scene_name == "forest_battle":
            # Одразу бій з гобліном після туторіалу
            from game.enemy import make_goblin
            enemy = make_goblin()
            self._do_change_scene("battle", enemy=enemy, return_scene="forest")

        elif scene_name == "tower":
            from scenes.tower import TowerScene
            self.current_scene = TowerScene(self)

        elif scene_name == "tower_free":
            from scenes.tower import TowerScene
            self.scene_data["from_battle"] = "tower_free"
            self.current_scene = TowerScene(self)

        elif scene_name == "ruins":
            from scenes.ruins import RuinsScene
            self.current_scene = RuinsScene(self)

        elif scene_name == "ruins_free":
            from scenes.ruins import RuinsScene
            self.scene_data["from_battle"] = "ruins_free"
            self.current_scene = RuinsScene(self)

        elif scene_name == "dragon":
            from scenes.dragon import DragonScene
            self.current_scene = DragonScene(self)

        elif scene_name == "victory":
            from scenes.victory import VictoryScene
            self.current_scene = VictoryScene(self)

        elif scene_name == "death":
            from scenes.death import DeathScene
            self.current_scene = DeathScene(self)

        elif scene_name == "tutorial":
            from scenes.tutorial import TutorialScene
            tutorial_data = kwargs.get("tutorial_data")
            next_scene = kwargs.get("next_scene", "village")
            self.current_scene = TutorialScene(self, tutorial_data, next_scene)

        elif scene_name == "stats":
            from scenes.stats import StatsScene
            self.current_scene = StatsScene(self)

        elif scene_name == "inventory":
            from scenes.inventory import InventoryScene
            self.current_scene = InventoryScene(self)

        elif scene_name == "battle_log":
            from scenes.battle_log_scene import BattleLogScene
            self.current_scene = BattleLogScene(self)

        elif scene_name == "skill_tree":
            from scenes.skill_tree import SkillTreeScene
            self.current_scene = SkillTreeScene(self)

        elif scene_name == "admin":
            from scenes.admin import AdminScene
            self.current_scene = AdminScene(self)
        elif scene_name == "achievements":
            from scenes.achievements import AchievementsScene
            self.current_scene = AchievementsScene(self)

        elif scene_name == "perks":
            from scenes.perks import PerksScene
            self.current_scene = PerksScene(self)

        elif scene_name == "bestiary":
            from scenes.bestiary import BestiaryScene
            self.current_scene = BestiaryScene(self)

        elif scene_name == "daily_quests":
            from scenes.daily_quests_scene import DailyQuestsScene
            self.current_scene = DailyQuestsScene(self)

        elif scene_name == "perk_shop":
            from scenes.perk_shop import PerkShopScene
            self.current_scene = PerkShopScene(self)

        elif scene_name == "level_up":
            from scenes.level_up import LevelUpScene
            self.current_scene = LevelUpScene(self)

        elif scene_name == "world_map":
            from scenes.world_map import WorldMapScene
            self.current_scene = WorldMapScene(self)

        elif scene_name == "market":
            from scenes.market import MarketScene
            self.current_scene = MarketScene(self)

        elif scene_name == "elder":
            from scenes.elder import ElderScene
            self.current_scene = ElderScene(self)

        elif scene_name == "forest_event":
            from scenes.forest_event import ForestEventScene
            self.current_scene = ForestEventScene(self)

        elif scene_name == "onboarding":
            from scenes.onboarding import OnboardingScene
            self.current_scene = OnboardingScene(self)

        elif scene_name == "mine":
            from scenes.mine import MineScene
            self.current_scene = MineScene(self)

        elif scene_name == "wanderer":
            from scenes.wanderer import WandererScene
            self.current_scene = WandererScene(self)

        elif scene_name == "onboarding_reward_1":
            # Після першого бою — нагорода і майстерня
            from scenes.onboarding import OnboardingScene, _RewardScene
            scene = OnboardingScene(self)
            scene.stage = "reward_1"
            scene._give_reward_1()
            scene._sub = _RewardScene(scene)
            self.current_scene = scene

        elif scene_name == "onboarding_perk":
            # Після другого бою — XP + слабкі перки
            from scenes.onboarding import BATTLE2_XP, WEAK_PERK_IDS
            p = self.player
            xp_give = self.scene_data.pop("onboarding_battle2_xp", BATTLE2_XP)
            p.xp += xp_give
            while p.xp >= p.xp_next:
                p.level_up()
            from game.perk_system import PERKS
            p.pending_perk_choices = [PERKS[pid] for pid in WEAK_PERK_IDS if pid in PERKS]
            self.scene_data["onboarding_perk_first"] = True
            autosave(p)
            self._do_change_scene("level_up")

        else:
            log.warning("Невідома сцена: %s", scene_name)
            return

        # Викликаємо on_enter
        if self.current_scene:
            self.current_scene.on_enter()

    def push_scene(self, scene_name: str, **kwargs):
        """Зберігає поточну сцену в стек і переходить до нової (з fade)."""
        if self._transition.busy:
            return
        from game.transitions import DEFAULT_OUT, DEFAULT_IN
        self._transition.request(
            callback=lambda: self._do_push_scene(scene_name, **kwargs),
            duration=(DEFAULT_OUT, DEFAULT_IN),
        )

    def _do_push_scene(self, scene_name: str, **kwargs):
        if self.current_scene:
            self.scene_stack.append(self.current_scene)
        self._do_change_scene(scene_name, **kwargs)

    def pop_scene(self):
        """Повертається до попередньої сцени зі стеку (з fade)."""
        if self._transition.busy:
            return
        if not self.scene_stack:
            return
        from game.transitions import DEFAULT_OUT, DEFAULT_IN
        self._transition.request(
            callback=self._do_pop_scene,
            duration=(DEFAULT_OUT, DEFAULT_IN),
        )

    def _do_pop_scene(self):
        if self.scene_stack:
            if self.current_scene:
                self.current_scene.on_exit()
            self.current_scene = self.scene_stack.pop()
            self.current_scene.on_enter()

    def start_new_game_silent(self, player_name: str, save_name: str):
        """Створює нового гравця без переходу до сцени (для hero_roulette)."""
        self.player = Player(player_name)
        self.player.save_name = save_name
        from ui.admin_console import AdminConsole
        self._console = AdminConsole(self.player)

    def start_new_game(self, player_name: str, save_name: str):
        """Початок нової гри — запускає онбординг."""
        self.player = Player(player_name)
        self.player.save_name      = save_name
        self.player.onboarding_done = False

        from ui.admin_console import AdminConsole
        self._console = AdminConsole(self.player)
        autosave(self.player)
        self.change_scene("onboarding")


    def load_game(self, save_name: str):
        """Завантаження гри."""
        print(f"[CORE] load_game: {save_name}")
        self.player = SaveManager.load_game(save_name)
        if self.player:
            self.player.save_name = save_name
            from ui.admin_console import AdminConsole
            self._console = AdminConsole(self.player)

            # Офлайн-прогрес: збираємо предмети що дійшли поки гра була закрита
            finished = self.player.collect_crafted()
            if finished:
                autosave(self.player)
                # Зберігаємо для показу сповіщення на екрані села
                self.scene_data["offline_crafted"] = finished

            # Офлайн-прогрес: розібрані предмети
            dismantled = self.player.collect_dismantled()
            if dismantled:
                autosave(self.player)
                self.scene_data["offline_dismantled"] = dismantled

            self.change_scene("village")
        else:
            log.error("Не вдалося завантажити збереження: %s", save_name)
            self.change_scene("main_menu")

    def save_game(self):
        """Збереження гри."""
        if self.player:
            autosave(self.player)

    def _show_exit_confirm(self):
        """Показує діалог підтвердження виходу."""
        from ui.confirm_dialog import ConfirmDialog
        from game.save_manager import autosave
        def do_save_quit():
            if self.player:
                autosave(self.player)
            self.running = False
        self._exit_confirm = ConfirmDialog(
            "Вийти з гри?",
            "Зберегти прогрес і вийти?",
            on_yes=do_save_quit,
            yes_lbl="💾 Зберегти і вийти",
            no_lbl="Залишитись",
        )

    def quit_game(self):
        """Вихід з гри."""
        self._show_exit_confirm()

    def show_achievement(self, achievement_id: str):
        """Показує сповіщення про досягнення."""
        from scenes.achievement_notification import AchievementNotification
        self.achievement_notifications.append(AchievementNotification(achievement_id))

    def run(self):
        """Головний ігровий цикл."""
        # Патчимо pygame.mouse.get_pos щоб повертав віртуальні координати
        _real_get_pos = pygame.mouse.get_pos
        game_ref = self
        def _virtual_get_pos():
            return game_ref._screen_to_virtual(_real_get_pos())
        pygame.mouse.get_pos = _virtual_get_pos

        self.start()

        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0

            # Накопичуємо час у грі
            if self.player:
                self.player.total_playtime += dt

            # Обробка подій
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Показуємо підтвердження виходу
                    self._show_exit_confirm()

                elif event.type == pygame.VIDEORESIZE:
                    if not self.is_fullscreen:
                        self.screen = pygame.display.set_mode(
                            event.size, pygame.RESIZABLE
                        )

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.scene_stack:
                            self.pop_scene()
                    elif event.key == pygame.K_F11 or \
                         (event.key == pygame.K_RETURN and (pygame.key.get_mods() & pygame.KMOD_ALT)):
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_F5:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_CTRL:
                            from config.hot_reload import reload_all, show_result
                            result = reload_all(self)
                            show_result(result, self)
                        else:
                            self.save_game()
                    elif event.key == pygame.K_F12:
                        if self.player:
                            from scenes.admin import AdminScene
                            self.push_scene("admin")

                # Трансформуємо координати миші у віртуальний простір
                event = self._transform_mouse_event(event)

                # Діалог підтвердження виходу перехоплює всі події
                if self._exit_confirm:
                    self._exit_confirm.handle_event(event)
                    if self._exit_confirm.done:
                        self._exit_confirm = None
                    continue

                # Передаємо подію в поточну сцену
                if self._console and self._console.handle_event(event):
                    continue
                if self.current_scene and not self._transition.busy:
                    self.current_scene.handle_event(event)

            # Оновлення
            if self._console:
                self._console.update(dt)
            if self.current_scene:
                self.current_scene.update(dt)

            # Оновлення переходів
            self._transition.update(dt)

            # Малювання у virtual surface
            from ui.constants import COLOR_BG
            self._surface.fill(COLOR_BG)

            if self.current_scene:
                self.current_scene.draw(self._surface)
                if self._console:
                    self._console.draw(self._surface)
                for notif in self.achievement_notifications[:]:
                    if not notif.update(dt):
                        self.achievement_notifications.remove(notif)
                    else:
                        notif.draw(self._surface)

                # Централізовані тост-сповіщення (поверх усього)
                from ui.notifications import get_manager
                nm = get_manager()
                nm.update(dt)
                nm.draw(self._surface)

                # Індикатор збереження
                from game.save_indicator import update_save_indicator, draw_save_indicator
                update_save_indicator(dt)
                draw_save_indicator(self._surface)

                # Діалог підтвердження виходу — поверх всього
                if self._exit_confirm and not self._exit_confirm.done:
                    self._exit_confirm.draw(self._surface)

                # Перехід між сценами — самий верхній шар
                self._transition.draw(self._surface)

            # Масштабуємо virtual surface на реальний екран
            self._blit_scaled()
            pygame.display.flip()

        # Завершення
        pygame.quit()
        sys.exit()