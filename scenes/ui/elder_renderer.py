"""
Рендерер для ElderScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/elder.py
"""
from game.quests import get_completable_quests
from game.reputation import get_next_tier, get_tier
from scenes.core.elder import CLR_ACTIVE, CLR_AVAILABLE, CLR_COMPLETABLE, CLR_DONE, INFO_W, INFO_X, LIST_W, LIST_X, LIST_Y, ROW_H, VISIBLE
from game.data import MATERIALS
import pygame
from scenes.ui.base_renderer import BaseRenderer

import math
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets


class ElderRenderer(BaseRenderer):
    """
    Малює ElderScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        self.scene.main_panel.draw(screen)

        if self.scene.mode == "hub":
            self._draw_hub(screen)
        elif self.scene.mode == "dialog":
            self._draw_dialog(screen)
        elif self.scene.mode == "complete":
            self._draw_complete(screen)

        self.scene.btn_exit.draw(screen)

    # ══════════════════════════════════════════
    # ХАБ КВЕСТІВ
    # ══════════════════════════════════════════

    def _draw_hub(self, screen):
        self._draw_hub_header(screen)
        self._draw_quest_list(screen)
        self._draw_quest_info(screen)
        self._draw_scrollbar(screen)

    def _draw_hub_header(self, screen):
        fh = assets.get_font(FONT_SIZE_LARGE, bold=True)
        screen.blit(fh.render("🧓 Голова села Радомир", True, COLOR_GOLD), (LIST_X, 38))
        fs = assets.get_font(FONT_SIZE_SMALL)
        p  = self.scene.player
        completable_count = len(get_completable_quests(p))
        if completable_count:
            pulse = 0.6 + 0.4 * math.sin(self.scene._anim_t * 3)
            clr = tuple(int(c * pulse) for c in CLR_COMPLETABLE)
            txt = fs.render(f"✦ {completable_count} квест(и) готові до здачі!", True, clr)
        else:
            active = len(self.scene.player.quests_active)
            done   = len(self.scene.player.quests_done)
            txt    = fs.render(f"Активних: {active}   Виконаних: {done}", True, COLOR_TEXT_DIM)
        screen.blit(txt, (LIST_X, 80))

        # ── Панель репутації ──────────────────────────────────────
        self._draw_reputation_bar(screen)

    def _draw_reputation_bar(self, screen):
        """Мала панель репутації у верхньому правому куті."""
        rep   = getattr(self.scene.player, "reputation", 0)
        tier  = get_tier(rep)
        nxt   = get_next_tier(rep)
        fs    = assets.get_font(FONT_SIZE_SMALL)
        fx    = SCREEN_WIDTH - 320
        fy    = 38

        # Фон
        bg = pygame.Surface((290, 60), pygame.SRCALPHA)
        bg.fill((15, 12, 8, 200))
        pygame.draw.rect(bg, tier.color, bg.get_rect(), 1, border_radius=6)
        screen.blit(bg, (fx, fy))

        # Назва рівня
        lbl = fs.render(f"{tier.icon} {tier.name}", True, tier.color)
        screen.blit(lbl, (fx + 8, fy + 6))

        # Знижка
        disc = int((1 - tier.discount) * 100)
        disc_s = fs.render(f"🏷 -{disc}% в крамниці", True, (180, 220, 140))
        screen.blit(disc_s, (fx + 8, fy + 26))

        # Прогрес до наступного рівня
        if nxt:
            prog = (rep - tier.min_rep) / (nxt.min_rep - tier.min_rep)
            bar_w = 270
            pygame.draw.rect(screen, (40, 35, 25),
                             (fx + 8, fy + 46, bar_w, 8), border_radius=4)
            fill = max(4, int(bar_w * prog))
            pygame.draw.rect(screen, tier.color,
                             (fx + 8, fy + 46, fill, 8), border_radius=4)
            left = nxt.min_rep - rep
            hint = fs.render(f"+{left} до {nxt.icon} {nxt.name}", True, COLOR_TEXT_DIM)
            screen.blit(hint, (fx + 155, fy + 26))
        else:
            maxed = fs.render("★ Максимальна репутація!", True, tier.color)
            screen.blit(maxed, (fx + 130, fy + 26))

    def _draw_quest_list(self, screen):
        rows   = self.scene._all_rows()
        font   = assets.get_font(FONT_SIZE_NORMAL)
        font_s = assets.get_font(FONT_SIZE_SMALL)
        mp     = pygame.mouse.get_pos()

        bg = pygame.Surface((LIST_W, VISIBLE * ROW_H), pygame.SRCALPHA)
        bg.fill((10, 8, 6, 185))
        screen.blit(bg, (LIST_X, LIST_Y))

        if not rows:
            screen.blit(font.render("Немає доступних квестів.", True, COLOR_TEXT_DIM),
                        (LIST_X + 16, LIST_Y + 20))
            return

        status_colors = {
            "completable": CLR_COMPLETABLE,
            "active":      CLR_ACTIVE,
            "available":   CLR_AVAILABLE,
            "done":        CLR_DONE,
        }
        status_labels = {
            "completable": "✦ ЗДАТИ",
            "active":      "● Активний",
            "available":   "○ Доступний",
            "done":        "✓ Виконано",
        }

        for i, (status, quest) in enumerate(rows[self.scene.scroll: self.scene.scroll + VISIBLE]):
            r      = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)
            s_clr  = status_colors[status]
            hovered = r.collidepoint(mp) and status != "done"

            # Фон
            if i == self.scene.sel:
                base = (65, 50, 15, 230)
            elif hovered:
                base = (45, 38, 20, 210)
            elif i % 2 == 0:
                base = (20, 16, 12, 165)
            else:
                base = (26, 22, 16, 165)

            surf = pygame.Surface((LIST_W, ROW_H - 4), pygame.SRCALPHA)
            surf.fill(base)
            screen.blit(surf, r.topleft)

            # Ліва кольорова смужка
            pygame.draw.rect(screen, s_clr, (r.x, r.y, 4, r.height), border_radius=2)

            if i == self.scene.sel:
                pygame.draw.rect(screen, s_clr, r, 1, border_radius=3)

            # Пульсація якщо completable
            if status == "completable":
                pulse = 0.6 + 0.4 * math.sin(self.scene._anim_t * 3 + i)
                glow_surf = pygame.Surface((LIST_W, ROW_H - 4), pygame.SRCALPHA)
                glow_surf.fill((80, 255, 140, int(18 * pulse)))
                screen.blit(glow_surf, r.topleft)

            # Іконка + назва
            name_clr = (180, 180, 180) if status == "done" else COLOR_TEXT
            screen.blit(font.render(f"{quest.icon}  {quest.title}", True, name_clr),
                        (r.x + 14, r.y + 8))

            # Ціль і статус
            obj_txt  = quest.objective[:48]
            screen.blit(font_s.render(obj_txt, True, COLOR_TEXT_DIM), (r.x + 14, r.y + 36))

            lbl = font_s.render(status_labels[status], True, s_clr)
            screen.blit(lbl, (r.right - lbl.get_width() - 12, r.y + 10))

        # Лічильник
        total = len(rows)
        if total > VISIBLE:
            screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
                f"{self.scene.scroll+1}–{min(self.scene.scroll+VISIBLE,total)} з {total}", True, COLOR_TEXT_DIM),
                (LIST_X, LIST_Y + VISIBLE * ROW_H + 4))

    def _draw_quest_info(self, screen):
        quest, status = self.scene._selected_quest_and_status()
        panel_h = SCREEN_HEIGHT - LIST_Y - 80

        # Фон панелі
        surf = pygame.Surface((INFO_W, panel_h), pygame.SRCALPHA)
        surf.fill((15, 12, 8, 215))
        border_clr = {
            "completable": CLR_COMPLETABLE,
            "active":      CLR_ACTIVE,
            "available":   CLR_AVAILABLE,
            "done":        (80, 80, 80),
        }.get(status, (60, 55, 40))
        pygame.draw.rect(surf, border_clr, surf.get_rect(), 1, border_radius=8)
        screen.blit(surf, (INFO_X, LIST_Y))

        if not quest:
            hint = assets.get_font(FONT_SIZE_SMALL).render(
                "← Вибери квест", True, COLOR_TEXT_DIM)
            screen.blit(hint, (INFO_X + 14, LIST_Y + 20))
            self.scene.btn_action.enabled = False
            self.scene.btn_action.draw(screen)
            return

        px, py = INFO_X + 14, LIST_Y + 12
        fh  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)

        # Назва
        screen.blit(fh.render(f"{quest.icon}  {quest.title}", True, COLOR_GOLD), (px, py)); py += 28

        # Завдання
        screen.blit(fsm.render("📋 Завдання:", True, (200, 180, 100)), (px, py)); py += 16
        screen.blit(fsm.render(f"  {quest.objective}", True, COLOR_TEXT_DIM), (px, py)); py += 20

        # Прогрес якщо активний
        if status in ("active", "completable"):
            done = quest.complete_cond(self.scene.player)
            prog_clr = CLR_COMPLETABLE if done else CLR_ACTIVE
            prog_txt = "✓ Виконано — здай квест!" if done else "● В процесі..."
            screen.blit(fsm.render(prog_txt, True, prog_clr), (px, py)); py += 22

        py += 4
        # Нагороди
        screen.blit(fsm.render("🎁 Нагороди:", True, (200, 180, 100)), (px, py)); py += 16
        if quest.reward_gold:
            screen.blit(fsm.render(f"  💰 {quest.reward_gold} золота", True, COLOR_GOLD),
                        (px, py)); py += 15
        if quest.reward_xp:
            screen.blit(fsm.render(f"  ⭐ {quest.reward_xp} досвіду", True, (200, 220, 100)),
                        (px, py)); py += 15
        for mat_id, qty in quest.reward_mats.items():
            mat = MATERIALS.get(mat_id)
            if mat:
                screen.blit(fsm.render(f"  {mat.icon} {mat.name} ×{qty}", True, (160, 210, 160)),
                            (px, py)); py += 15
        if getattr(quest, "reward_spins", 0):
            screen.blit(fsm.render(f"  🎰 ×{quest.reward_spins} спін рулетки героїв",
                                   True, (255, 180, 40)), (px, py)); py += 15

        # Ланцюжок
        if quest.unlocks:
            next_q = QUESTS.get(quest.unlocks)
            if next_q:
                py += 6
                screen.blit(fsm.render(f"→ Відкриє: {next_q.icon} {next_q.title}",
                                       True, (140, 160, 200)), (px, py)); py += 16

        # Кнопка дії
        if status == "completable":
            self.scene.btn_action.text    = "✦ Здати квест!"
            self.scene.btn_action.enabled = True
        elif status == "available":
            self.scene.btn_action.text    = "📜 Взяти квест"
            self.scene.btn_action.enabled = True
        else:
            self.scene.btn_action.enabled = False
            if status == "done":
                self.scene.btn_action.text = "✓ Вже виконано"
            else:
                self.scene.btn_action.text = "● В процесі"

        self.scene.btn_action.draw(screen)

    def _draw_scrollbar(self, screen):
        rows = self.scene._all_rows()
        total = len(rows)
        if total <= VISIBLE:
            return
        bar_h   = VISIBLE * ROW_H
        bar_x   = LIST_X + LIST_W + 6
        thumb_h = max(28, bar_h * VISIBLE // total)
        thumb_y = LIST_Y + (bar_h - thumb_h) * self.scene.scroll // max(1, total - VISIBLE)
        pygame.draw.rect(screen, (38, 35, 28), (bar_x, LIST_Y, 7, bar_h), border_radius=3)
        pygame.draw.rect(screen, COLOR_GOLD, (bar_x, thumb_y, 7, thumb_h), border_radius=3)

    # ══════════════════════════════════════════
    # РЕЖИМ ДІАЛОГУ
    # ══════════════════════════════════════════

    def _draw_dialog(self, screen):
        quest = self.scene._dialog_quest
        if not quest:
            return

        # Темний оверлей
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Панель діалогу
        pw, ph = 800, 380
        px     = SCREEN_WIDTH  // 2 - pw // 2
        py     = SCREEN_HEIGHT // 2 - ph // 2

        panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel_surf.fill((18, 14, 10, 240))
        pygame.draw.rect(panel_surf, COLOR_GOLD, panel_surf.get_rect(), 2, border_radius=12)
        screen.blit(panel_surf, (px, py))

        # Заголовок квесту
        fh  = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fsm = assets.get_font(FONT_SIZE_NORMAL)
        fss = assets.get_font(FONT_SIZE_SMALL)

        title = fh.render(f"{quest.icon}  {quest.title}", True, COLOR_GOLD)
        screen.blit(title, (px + pw // 2 - title.get_width() // 2, py + 18))

        # Портрет НПС
        portrait_txt = assets.get_font(48).render("🧓", True, (255, 255, 255))
        screen.blit(portrait_txt, (px + 28, py + 65))

        # Текст сторінки
        pages = quest.story_lines
        page  = self.scene._dialog_page
        text  = pages[page] if page < len(pages) else ""

        # Обгортання тексту
        words_y = py + 70
        words_x = px + 110
        max_w   = pw - 130
        for line in text.split("\n"):
            words = line.split()
            row   = ""
            for w in words:
                test = row + (" " if row else "") + w
                if fsm.size(test)[0] <= max_w:
                    row = test
                else:
                    if row:
                        screen.blit(fsm.render(row, True, COLOR_TEXT), (words_x, words_y))
                        words_y += 28
                    row = w
            if row:
                screen.blit(fsm.render(row, True, COLOR_TEXT), (words_x, words_y))
                words_y += 28

        # Лічильник сторінок
        page_txt = fss.render(f"{page + 1} / {len(pages)}", True, COLOR_TEXT_DIM)
        screen.blit(page_txt, (px + pw // 2 - page_txt.get_width() // 2, py + ph - 55))

        # Підказка на останній сторінці
        if page == len(pages) - 1:
            pulse = 0.7 + 0.3 * math.sin(self.scene._anim_t * 3)
            clr   = tuple(int(c * pulse) for c in CLR_COMPLETABLE)
            hint  = fss.render("Натисни «Далі» щоб прийняти квест", True, clr)
            screen.blit(hint, (px + pw // 2 - hint.get_width() // 2, py + ph - 80))
            self.scene.btn_next.text = "✓ Прийняти"
        else:
            self.scene.btn_next.text = "Далі →"

        # Кнопки навігації
        self.scene.btn_next.x = px + pw - 220
        self.scene.btn_next.y = py + ph + 10
        self.scene.btn_next.draw(screen)

        self.scene.btn_prev.x = px + 20
        self.scene.btn_prev.y = py + ph + 10
        self.scene.btn_prev.enabled = (page > 0)
        self.scene.btn_prev.draw(screen)

    # ══════════════════════════════════════════
    # РЕЖИМ ЗАВЕРШЕННЯ КВЕСТУ
    # ══════════════════════════════════════════

    def _draw_complete(self, screen):
        quest = self.scene._complete_quest
        if not quest:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        pw, ph = 680, 420
        px     = SCREEN_WIDTH  // 2 - pw // 2
        py     = SCREEN_HEIGHT // 2 - ph // 2

        # Фон з золотою рамкою
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((20, 16, 8, 250))
        pygame.draw.rect(panel, COLOR_GOLD, panel.get_rect(), 3, border_radius=14)
        screen.blit(panel, (px, py))

        fh  = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fsm = assets.get_font(FONT_SIZE_NORMAL)
        fss = assets.get_font(FONT_SIZE_SMALL)

        # Заголовок
        pulse = 0.8 + 0.2 * math.sin(self.scene._anim_t * 2)
        clr   = tuple(min(255, int(c * pulse)) for c in COLOR_GOLD)
        title = fh.render("✦ КВЕСТ ВИКОНАНО! ✦", True, clr)
        screen.blit(title, (px + pw // 2 - title.get_width() // 2, py + 20))

        q_name = assets.get_font(FONT_SIZE_MEDIUM, bold=True).render(
            f"{quest.icon}  {quest.title}", True, (220, 210, 180))
        screen.blit(q_name, (px + pw // 2 - q_name.get_width() // 2, py + 60))

        # Нагороди
        ry = py + 108
        screen.blit(fsm.render("Нагороди:", True, (200, 180, 100)),
                    (px + pw // 2 - 60, ry)); ry += 32

        reward_items = []
        if quest.reward_gold:
            reward_items.append((f"💰 +{quest.reward_gold} золота", COLOR_GOLD))
        if quest.reward_xp:
            reward_items.append((f"⭐ +{quest.reward_xp} досвіду", (210, 230, 100)))
        for mat_id, qty in quest.reward_mats.items():
            mat = MATERIALS.get(mat_id)
            if mat:
                reward_items.append((f"{mat.icon} {mat.name} ×{qty}", (150, 215, 155)))

        col_w = pw // 2 - 20
        for i, (txt, clr) in enumerate(reward_items):
            col = i % 2
            row = i // 2
            rx  = px + 30 + col * col_w
            ry2 = ry + row * 28
            surf = fsm.render(txt, True, clr)
            screen.blit(surf, (rx, ry2))

        # Наступний квест
        if quest.unlocks:
            next_q = QUESTS.get(quest.unlocks)
            if next_q:
                ny = py + ph - 110
                line = pygame.Surface((pw - 60, 1), pygame.SRCALPHA)
                line.fill((120, 100, 50, 180))
                screen.blit(line, (px + 30, ny))
                unlock_txt = fss.render(
                    f"→ Відкрито новий квест:  {next_q.icon} {next_q.title}",
                    True, CLR_AVAILABLE)
                screen.blit(unlock_txt,
                            (px + pw // 2 - unlock_txt.get_width() // 2, ny + 8))

        # Кнопка "Закрити"
        self.scene.btn_next.text    = "Закрити"
        self.scene.btn_next.enabled = True
        self.scene.btn_next.x       = px + pw // 2 - 100
        self.scene.btn_next.y       = py + ph - 64
        self.scene.btn_next.draw(screen)