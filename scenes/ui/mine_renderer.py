"""
Рендерер для MineScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/mine.py
"""
from game.miner import MinerState
from scenes.core.forest_event import PANEL_H, PANEL_W, PANEL_X, PANEL_Y
from scenes.core.mine import BROKEN_PICKAXE_ID, NPC_X, NPC_Y, PICKAXE_ID, SHOVEL_ID
from game.data import MATERIALS
import pygame
from scenes.ui.base_renderer import BaseRenderer

import math
import time
import random
import logging
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from ui.icons import draw_icon


class MineRenderer(BaseRenderer):
    """
    Малює MineScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)

        self._draw_npc(screen)
        self._draw_left_panel(screen)
        self._draw_header(screen)

        self.scene.draw_buttons(screen)

    def _draw_npc(self, screen: pygame.Surface):
        """Малює анімованого шахтаря."""
        if not self.scene._npc_ctrl:
            return
        frame = self.scene._npc_ctrl.get_current_frame()
        if not frame:
            return
        float_y = math.sin(self.scene._npc_float * 1.4) * 3
        x = NPC_X
        y = int(NPC_Y - frame.get_height() + float_y)
        # Тінь
        sx = x + frame.get_width() // 2 - self.scene._npc_shadow.get_width() // 2
        screen.blit(self.scene._npc_shadow, (sx, NPC_Y + 4))
        screen.blit(frame, (x, y))

        # Ім'я НПС
        font = assets.get_font(FONT_SIZE_SMALL, bold=True)
        lbl  = font.render("⛏ Шахтар Борис", True, COLOR_GOLD)
        screen.blit(lbl, (x + frame.get_width() // 2 - lbl.get_width() // 2, y - 22))

    def _draw_header(self, screen: pygame.Surface):
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)
        title = font_title.render("⛏ Шахта", True, COLOR_GOLD)
        screen.blit(title, (PANEL_X, 50))
        gold = font_sm.render(f"💰 {self.scene.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold, (SCREEN_WIDTH - gold.get_width() - 40, 55))

        # Інструменти гравця
        has_pick   = self.scene._has_pickaxe()
        has_shovel = self.scene._has_shovel()
        has_broken = any(getattr(i, "item_id", "") == BROKEN_PICKAXE_ID
                         for i in self.scene.player.inventory)
        tools_x = PANEL_X
        tools_y = 60
        draw_icon(screen, PICKAXE_ID,        "⛏", tools_x,      tools_y, size=24,
                  alpha=255 if has_pick else 80)
        draw_icon(screen, SHOVEL_ID,         "🪣", tools_x + 32, tools_y, size=24,
                  alpha=255 if has_shovel else 80)
        if has_broken:
            draw_icon(screen, BROKEN_PICKAXE_ID, "🔨", tools_x + 64, tools_y, size=24)

    def _draw_left_panel(self, screen: pygame.Surface):
        status = self.scene._miner.status
        panel  = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panel.fill((12, 10, 8, 210))
        pygame.draw.rect(panel, COLOR_GOLD, panel.get_rect(), 1, border_radius=10)
        screen.blit(panel, (PANEL_X, PANEL_Y))

        font    = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_n  = assets.get_font(FONT_SIZE_NORMAL)
        font_sm = assets.get_font(FONT_SIZE_SMALL)

        px, py = PANEL_X + 14, PANEL_Y + 14

        if status == MinerState.STATUS_IDLE:
            self._draw_idle_panel(screen, px, py, font, font_n, font_sm)

        elif status == MinerState.STATUS_WORKING:
            self._draw_working_panel(screen, px, py, font, font_n, font_sm)

        elif status == MinerState.STATUS_DONE:
            self._draw_done_panel(screen, px, py, font, font_n, font_sm)

        elif status == MinerState.STATUS_LOST:
            self._draw_lost_panel(screen, px, py, font, font_n, font_sm)

    def _draw_idle_panel(self, screen, px, py, font, font_n, font_sm):
        screen.blit(font.render("Шахтар чекає на замовлення", True, COLOR_GOLD), (px, py))
        py += 30

        has_pick = self.scene._has_pickaxe()
        if not has_pick:
            warn = font_sm.render("⚠ Потрібне кайло! Купи в крамниці.", True, COLOR_ERROR)
            screen.blit(warn, (px, py)); py += 22

        # Втома
        FATIGUE_ICONS  = ["😊 Свіжий",  "😓 Втомлений", "😵 Виснажений"]
        FATIGUE_COLORS = [(100,220,100), (220,180,60),   (220,80,80)]
        flvl = self.scene._miner.fatigue_level
        fat_lbl = font_sm.render(
            f"Стан: {FATIGUE_ICONS[flvl]}  (похід {self.scene._miner.trips_since_rest})",
            True, FATIGUE_COLORS[flvl])
        screen.blit(fat_lbl, (px, py)); py += 20
        if flvl > 0:
            mult = self.scene._miner.cost_multiplier
            screen.blit(font_sm.render(
                f"⚠ Ціна робіт ×{mult:.2f} — дай відпочити!", True, (220,180,60)),
                (px, py)); py += 18

        # Відпочинок
        if self.scene._miner.is_resting:
            left = self.scene._miner.rest_time_left()
            m, s = divmod(left, 60)
            screen.blit(font_sm.render(f"😴 Відпочиває: {m:02d}:{s:02d}",
                        True, (140,180,255)), (px, py)); py += 20

        screen.blit(font_sm.render("Вибери тариф:", True, COLOR_TEXT_DIM), (px, py))
        py += 30

        for i, (tid, tier) in enumerate(TIERS.items()):
            btn_y = PANEL_Y + 70 + i * 90
            # Підсвітка вибраного
            if self.scene._selected_tier == tid:
                hl = pygame.Surface((PANEL_W - 20, 78), pygame.SRCALPHA)
                hl.fill((80, 65, 20, 120))
                pygame.draw.rect(hl, COLOR_GOLD, hl.get_rect(), 1, border_radius=6)
                screen.blit(hl, (PANEL_X + 10, btn_y))

            # Деталі тарифу
            info_x = PANEL_X + 24
            info_y = btn_y + 6
            mins   = tier.duration // 60
            screen.blit(font_n.render(f"{tier.icon} {tier.name}", True, COLOR_GOLD),
                        (info_x, info_y))
            actual = int(tier.cost * self.scene._miner.cost_multiplier)
            cost_txt = f"{actual}🪙" if actual == tier.cost else f"{actual}🪙 (втома)"
            screen.blit(font_sm.render(
                f"⏱ {mins} хв  |  💰 {cost_txt}  |  📦 {tier.min_ores}–{tier.max_ores} руд",
                True, COLOR_TEXT), (info_x, info_y + 24))
            screen.blit(font_sm.render(tier.description, True, COLOR_TEXT_DIM),
                        (info_x, info_y + 44))

        # Інфо про інструменти
        iy = PANEL_Y + 70 + len(TIERS) * 90 + 14
        has_pick   = self.scene._has_pickaxe()
        has_shovel = self.scene._has_shovel()

        # Рамка інструментів
        tool_surf = pygame.Surface((PANEL_W - 20, 54), pygame.SRCALPHA)
        tool_surf.fill((30, 24, 14, 160))
        border_col = (100, 220, 100) if has_pick else COLOR_ERROR
        pygame.draw.rect(tool_surf, border_col, tool_surf.get_rect(), 1, border_radius=6)
        screen.blit(tool_surf, (PANEL_X + 10, iy))

        # Кайло
        draw_icon(screen, PICKAXE_ID, "⛏", PANEL_X + 18, iy + 6, size=22,
                  alpha=255 if has_pick else 80)
        pick_lbl = "⛏ Кайло: є ✓" if has_pick else "⛏ Кайло: немає ✗"
        pick_col = (100, 220, 100) if has_pick else COLOR_ERROR
        screen.blit(font_sm.render(pick_lbl, True, pick_col), (PANEL_X + 44, iy + 7))

        # Лопата
        draw_icon(screen, SHOVEL_ID, "🪣", PANEL_X + 18, iy + 30, size=22,
                  alpha=255 if has_shovel else 80)
        shov_lbl = "🪣 Лопата: є (-10% часу)" if has_shovel else "🪣 Лопата: немає"
        shov_col = (100, 220, 100) if has_shovel else COLOR_TEXT_DIM
        screen.blit(font_sm.render(shov_lbl, True, shov_col), (PANEL_X + 44, iy + 31))

        screen.blit(font_sm.render(
            "Інструменти беруться з інвентаря автоматично при відправці.",
            True, COLOR_TEXT_DIM), (PANEL_X + 14, iy + 58))

    def _draw_working_panel(self, screen, px, py, font, font_n, font_sm):
        tier = TIERS.get(self.scene._miner.tier_id)
        screen.blit(font.render("⛏ Шахтар працює...", True, COLOR_GOLD), (px, py)); py += 30
        if tier:
            screen.blit(font_n.render(f"Тариф: {tier.icon} {tier.name}", True, COLOR_TEXT),
                        (px, py)); py += 26

        left  = self.scene._miner.time_left()
        total = tier.duration if tier else 1
        elapsed = total - left
        progress = max(0.0, min(1.0, elapsed / total))

        # Таймер
        m, s = divmod(left, 60)
        timer_col = COLOR_ERROR if left < 60 else COLOR_GOLD
        t_surf = assets.get_font(FONT_SIZE_LARGE, bold=True).render(
            f"⏱ {m:02d}:{s:02d}", True, timer_col)
        screen.blit(t_surf, (px, py)); py += 48

        # Прогрес-бар
        bar_w = PANEL_W - 28
        pygame.draw.rect(screen, (40, 35, 25), (px, py, bar_w, 18), border_radius=9)
        fill = int(bar_w * progress)
        if fill > 0:
            pygame.draw.rect(screen, COLOR_GOLD, (px, py, fill, 18), border_radius=9)
        pygame.draw.rect(screen, COLOR_GOLD, (px, py, bar_w, 18), 1, border_radius=9)
        py += 28

        screen.blit(font_sm.render(
            "Шахтар в шахті. Повернись пізніше!", True, COLOR_TEXT_DIM), (px, py))

    def _draw_done_panel(self, screen, px, py, font, font_n, font_sm):
        col = COLOR_ERROR if self.scene._miner.had_cave_in else (100, 220, 100)
        hdr = "⚠ Шахтар повернувся (був обвал!)" if self.scene._miner.had_cave_in \
              else "✅ Шахтар повернувся!"
        screen.blit(font.render(hdr, True, col), (px, py)); py += 30
        screen.blit(font_n.render("Знайдені руди:", True, COLOR_TEXT_DIM), (px, py)); py += 28

        for mat_id, qty in self.scene._miner.ores_ready.items():
            mat = MATERIALS.get(mat_id)
            if not mat:
                continue
            draw_icon(screen, mat_id, mat.icon, px, py, size=22)
            screen.blit(font_n.render(f"  {mat.name}  ×{qty}", True, COLOR_TEXT),
                        (px + 24, py + 2))
            py += 28

        if not self.scene._miner.ores_ready:
            screen.blit(font_sm.render("Нічого не знайдено...", True, COLOR_TEXT_DIM), (px, py))

    def _draw_lost_panel(self, screen, px, py, font, font_n, font_sm):
        screen.blit(font.render("💀 Шахтар не повернувся!", True, COLOR_ERROR), (px, py)); py += 30
        screen.blit(font_n.render("Мабуть стався нещасний випадок.", True, COLOR_TEXT), (px, py)); py += 26
        screen.blit(font_n.render("Кайло також загублено.", True, COLOR_TEXT_DIM), (px, py)); py += 26
        screen.blit(font_sm.render("Натисни 'Найняти нового' щоб продовжити.", True, COLOR_TEXT_DIM),
                    (px, py))