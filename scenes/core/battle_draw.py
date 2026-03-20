"""
Малювання бою — весь draw-код battle_fighting в одному місці.
Логіка бою знаходиться в battle_fighting.py.

Методи:
    draw()                    - головний метод малювання
    _draw_combo_counter()     - лічильник комбо
    _draw_finish_flash()      - спалах завершення бою
    _draw_enemy_speech()      - репліки ворога
    _draw_status_icons_world() - іконки статусів
    _draw_inline_log()        - лог подій бою
    _draw_action_hints()      - підказки клавіш
"""
import math
import pygame
from ui.constants import *
from ui.assets import assets
from game.fighter import Fighter


class BattleDrawMixin:
    """
    Mixin з усіма методами малювання для FightingBattleScene.
    Успадковуй разом з Scene.
    """

    def draw(self, screen: pygame.Surface):
        """Малювання."""
        # ── Shake: малюємо весь контент зі зміщенням ──
        ox, oy = self._shake_offset
        if ox or oy:
            surf = pygame.Surface(screen.get_size())
        else:
            surf = screen

        if self.background_surface:
            surf.blit(self.background_surface, (0, 0))
        else:
            surf.fill((30, 25, 20))

        pygame.draw.rect(surf, (60, 50, 40), (0, 550, SCREEN_WIDTH, SCREEN_HEIGHT - 550))
        pygame.draw.line(surf, (100, 90, 70), (0, 550), (SCREEN_WIDTH, 550), 3)

        camera_offset = (self.camera_x, 0)
        self.enemy_fighter.draw(surf, camera_offset)
        self.player_fighter.draw(surf, camera_offset)

        # ── Індикатори станів над ворогом ──
        self._draw_status_icons_world(surf, self.enemy_fighter, camera_offset)
        self._draw_status_icons_world(surf, self.player_fighter, camera_offset)

        # ── Combo counter ──
        self._draw_combo_counter(surf)

        # ── FINISH / KNOCKOUT flash ──
        self._draw_finish_flash(surf)

        # ── Репліки ворогів ──
        self._draw_enemy_speech(surf, camera_offset)

        # ── Боссові фази ──
        if self._boss_phase_mgr:
            self._boss_phase_mgr.draw(surf)

        # ── Slow-motion vignette ──
        if self._slowmo_timer > 0:
            vign = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int(60 * (self._slowmo_timer / 0.30))
            pygame.draw.rect(vign, (30, 80, 200, alpha), vign.get_rect(), 18)
            surf.blit(vign, (0, 0))

        self._draw_ui(surf)
        self._draw_inline_log(surf)
        self._draw_action_hints(surf)

        if ox or oy:
            screen.fill((0, 0, 0))
            screen.blit(surf, (ox, oy))

        if self.paused:
            if self.show_settings:
                self._draw_settings(screen)
            else:
                self._draw_pause_menu(screen)
            # Діалог підтвердження виходу до села
            if getattr(self, "_confirm_exit", None) and not self._confirm_exit.done:
                self._confirm_exit.draw(screen)

        if self.battle_over:
            if self.result_screen:
                self._draw_result_screen(screen)
            else:
                self._draw_battle_end(screen)

    def _maybe_enemy_speech(self):
        """Тригер випадкової репліки ворога."""
        import random
        if self._enemy_speech_cd > 0 or self._enemy_speech_timer > 0:
            return
        pf_hp_pct = self.player_fighter.hp / max(1, self.player_fighter.max_hp)
        ef_hp_pct = self.enemy_fighter.hp  / max(1, self.enemy_fighter.max_hp)
        name = self.enemy_data.name.lower()

        lines = []
        # Ворог у rage
        if ef_hp_pct < 0.30:
            if "гоблін" in name:
                lines = ["Мене не зупинити!", "ААААА!", "Ти пошкодуєш!"]
            elif "орк" in name:
                lines = ["ОРКИ НЕ ВМИРАЮТЬ!", "КРОВ І СЛАВА!", "Зараз я тебе роздавлю!"]
            elif "лицар" in name:
                lines = ["Ти не переможеш мене...", "МОЯ ЧЕСТЬ НЕ ЗЛАМАНА!", "Відчай тобі..."]
            elif "дракон" in name:
                lines = ["СМЕРТНИЙ! ТИ НЕ ВАРТИЙ МЕНЕ!", "Я СПАЛЮ ВЕСЬ СВІТ!", "АААРГХ!"]
        # Гравець на низькому HP
        elif pf_hp_pct < 0.25:
            if "гоблін" in name:
                lines = ["Ти вже майже мертвий!", "Хі-хі, скоро кінець!"]
            elif "орк" in name:
                lines = ["Ти слабкий!", "Слабак! Падай!"]
            elif "лицар" in name:
                lines = ["Здавайся, поки живий.", "Твоя смерть буде швидкою."]
            elif "дракон" in name:
                lines = ["Слабка людина...", "Твоя кров — моя їжа."]
        # Рандомна нейтральна
        elif random.random() < 0.008:   # ~1% per frame
            if "гоблін" in name:
                lines = ["Га-га-га!", "Дурний герой!", "Тікай поки можеш!"]
            elif "орк" in name:
                lines = ["Груш-груш!", "Ти слабший за гоблін!", "Бий-бий!"]
            elif "лицар" in name:
                lines = ["Честь і сталь.", "Ти гідний суперник.", "Не вистоїш."]
            elif "дракон" in name:
                lines = ["Комаха...", "Тисячу років я чекав...", "Вогонь очищує."]

        if lines:
            self._enemy_speech_text  = random.choice(lines)
            self._enemy_speech_timer = 2.2
            self._enemy_speech_cd    = 5.0

    def _draw_combo_counter(self, screen: pygame.Surface):
        """Малює лічильник комбо гравця."""
        import math
        combo = self.player_fighter.combo_count
        if combo < 2:
            return
        # Пульсуючий розмір
        pulse = 1.0 + 0.08 * abs(math.sin(pygame.time.get_ticks() * 0.01))
        size  = int((36 + min(combo, 10) * 3) * pulse)
        size  = max(24, min(size, 72))
        font  = pygame.font.Font(None, size)

        if combo >= 8:
            color = (255, 80,  40)   # червоний — GOD combo
        elif combo >= 5:
            color = (255, 200, 40)   # золотий
        elif combo >= 3:
            color = (140, 220, 255)  # блакитний
        else:
            color = (220, 220, 180)

        label = font.render(f"×{combo} COMBO", True, color)
        shadow = font.render(f"×{combo} COMBO", True, (0, 0, 0))
        x = 20
        y = SCREEN_HEIGHT - 200
        screen.blit(shadow, (x + 2, y + 2))
        screen.blit(label,  (x, y))

        # Таймер комбо — маленька смужка
        timer_pct = min(1.0, self.player_fighter.combo_timer / 2.0)
        bar_w = label.get_width()
        pygame.draw.rect(screen, (60, 60, 60), pygame.Rect(x, y + label.get_height() + 2, bar_w, 3))
        pygame.draw.rect(screen, color, pygame.Rect(x, y + label.get_height() + 2, int(bar_w * timer_pct), 3))

    def _draw_finish_flash(self, screen: pygame.Surface):
        """Малює НОКАУТ / НИЩІВНИЙ УДАР текст."""
        if self._finish_flash_timer <= 0 or not self._finish_flash_text:
            return
        import math
        t     = self._finish_flash_timer
        alpha = min(255, int(255 * min(1.0, t / 0.3)))
        # Великий текст по центру
        size  = 72 if self._finish_flash_text == "НОКАУТ!" else 58
        font  = pygame.font.Font(None, size)
        color = (255, 230, 50) if "НОКАУТ" in self._finish_flash_text else (255, 140, 40)
        surf  = font.render(self._finish_flash_text, True, color)
        surf.set_alpha(alpha)
        shad  = font.render(self._finish_flash_text, True, (0, 0, 0))
        shad.set_alpha(alpha // 2)
        cx = SCREEN_WIDTH  // 2 - surf.get_width()  // 2
        cy = SCREEN_HEIGHT // 2 - surf.get_height() // 2 - 30
        screen.blit(shad, (cx + 3, cy + 3))
        screen.blit(surf, (cx, cy))

    def _draw_enemy_speech(self, screen: pygame.Surface, camera_offset: tuple):
        """Малює speech bubble над ворогом."""
        if self._enemy_speech_timer <= 0 or not self._enemy_speech_text:
            return
        alpha = min(255, int(255 * min(1.0, self._enemy_speech_timer / 0.4)))
        font  = pygame.font.Font(None, 24)
        text  = font.render(self._enemy_speech_text, True, (255, 255, 220))
        text.set_alpha(alpha)
        pad = 8
        bw, bh = text.get_width() + pad * 2, text.get_height() + pad * 2
        ex = int(self.enemy_fighter.body.position.x + camera_offset[0])
        ey = int(self.enemy_fighter.body.position.y - 115 + camera_offset[1])
        bx = ex - bw // 2
        # Bubble фон
        bubble = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(bubble, (30, 20, 10, int(alpha * 0.7)), bubble.get_rect(), border_radius=8)
        pygame.draw.rect(bubble, (180, 160, 100, alpha), bubble.get_rect(), 1, border_radius=8)
        screen.blit(bubble, (bx, ey))
        screen.blit(text, (bx + pad, ey + pad))

    def _draw_status_icons_world(self, screen: pygame.Surface, fighter: Fighter, camera_offset: tuple):
        """Малює іконки активних статус-ефектів над бійцем."""
        icons = []
        if fighter.bleed_timer   > 0: icons.append(("🩸", (220,  50,  50)))
        if fighter.burn_timer    > 0: icons.append(("🔥", (255, 140,   0)))
        if fighter.stun_timer    > 0: icons.append(("😵", (255, 220,  60)))
        if fighter.rage_mode:          icons.append(("⚡", (255,  80,  40)))
        if fighter.dodge_iframes > 0:  icons.append(("💨", ( 80, 160, 255)))
        if not icons:
            return
        font = pygame.font.Font(None, 22)
        x0 = int(fighter.body.position.x - len(icons) * 12 + camera_offset[0])
        y0 = int(fighter.body.position.y - 90 + camera_offset[1])
        for i, (icon, color) in enumerate(icons):
            s = font.render(icon, True, color)
            screen.blit(s, (x0 + i * 22, y0))

    def _draw_inline_log(self, screen: pygame.Surface):
        """Малює останні події бою в лівому нижньому куті."""
        if not self._inline_log:
            return
        font = pygame.font.Font(None, 26)
        FADE_TIME = 0.8
        x = 18
        base_y = SCREEN_HEIGHT - 110
        for i, entry in enumerate(reversed(self._inline_log)):
            alpha = min(255, int(255 * min(1.0, entry["timer"] / FADE_TIME)))
            text_surf = font.render(entry["text"], True, entry["color"])
            text_surf.set_alpha(alpha)
            shadow = font.render(entry["text"], True, (0, 0, 0))
            shadow.set_alpha(alpha // 2)
            y = base_y - i * 22
            screen.blit(shadow, (x + 1, y + 1))
            screen.blit(text_surf, (x, y))

    def _draw_action_hints(self, screen: pygame.Surface):
        """Малює підказки дій внизу екрану."""
        if self.battle_over or self.paused:
            return
        font = pygame.font.Font(None, 24)
        items = [
            ("[J] Атака",  (220, 200, 140), False),
            ("[U] Важкий", (255, 160,  50), self._heavy_pending),
            ("[K] Захист", (100, 180, 255), self._defend_active),
            ("[I] Зілля",  (100, 220, 120), False),
        ]
        total_w = sum(font.size(t)[0] + 24 for t, _, _ in items)
        x = SCREEN_WIDTH // 2 - total_w // 2
        y = SCREEN_HEIGHT - 28

        for label, color, active in items:
            tw, th = font.size(label)
            bw = tw + 20
            bh = th + 6

            # Фон кнопки
            bg_color = (50, 80, 50, 200) if active else (30, 28, 22, 180)
            border   = (100, 220, 100) if active else (80, 75, 60)
            bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bg.fill((*bg_color[:3], 180))
            screen.blit(bg, (x, y - bh // 2))
            pygame.draw.rect(screen, border,
                             pygame.Rect(x, y - bh // 2, bw, bh), 1, border_radius=3)

            ts = font.render(label, True, color if not active else (150, 255, 150))
            screen.blit(ts, (x + 10, y - ts.get_height() // 2))
            x += bw + 6

        # Підказка зілля — скільки залишилось
        pots = sum(1 for p in self.player.inventory
                   if p.item_type == "potion" and p.hp_restore > 0)
        if pots > 0:
            pfont = pygame.font.Font(None, 20)
            ps = pfont.render(f"×{pots}", True, (160, 240, 160))
            screen.blit(ps, (x - 2, y - ps.get_height() // 2))
        """Малює останні події бою в лівому нижньому куті."""
        if not self._inline_log:
            return
        font = pygame.font.Font(None, 26)
        FADE_TIME = 0.8
        x = 18
        base_y = SCREEN_HEIGHT - 110
        for i, entry in enumerate(reversed(self._inline_log)):
            alpha = min(255, int(255 * min(1.0, entry["timer"] / FADE_TIME)))
            text_surf = font.render(entry["text"], True, entry["color"])
            text_surf.set_alpha(alpha)
            # Тінь
            shadow = font.render(entry["text"], True, (0, 0, 0))
            shadow.set_alpha(alpha // 2)
            y = base_y - i * 22
            screen.blit(shadow, (x + 1, y + 1))
            screen.blit(text_surf, (x, y))