"""
Сцена шахти — мирна локація з шахтарем-НПС.
"""
from __future__ import annotations
import math
import time
import random
import logging

log = logging.getLogger(__name__)

import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from ui.icons import draw_icon
from game.save_manager import autosave
from game.miner import MinerState, TIERS, RISK_PICKAXE_BREAK
from game.animation import AnimationController, Animation, AnimationLoader
from game.data import MATERIALS


# ── Інструменти шахтаря ───────────────────────────────────────────
PICKAXE_ID        = "pickaxe"
BROKEN_PICKAXE_ID = "broken_pickaxe"
SHOVEL_ID         = "shovel"

# Іконки (emoji fallback)
TOOL_ICONS = {
    PICKAXE_ID:        "⛏",
    BROKEN_PICKAXE_ID: "🔨",
    SHOVEL_ID:         "🪣",
}

# Ремонт зламаного кайла: {материал: кількість} + ціна монетами
REPAIR_RECIPE    = {"iron_bar": 3}
REPAIR_GOLD_COST = 15

# ── Позиції ───────────────────────────────────────────────────────
NPC_X   = 700
NPC_Y   = 340
PANEL_X = 40
PANEL_Y = 100
PANEL_W = 580
PANEL_H = SCREEN_HEIGHT - 160


class MineScene(SceneWithBackground, SceneWithButtons):
    """Шахта — мирна локація з шахтарем."""

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "mine")
        SceneWithButtons.__init__(self, game)

        # Стан шахтаря живе в player
        if not hasattr(self.player, "miner"):
            self.player.miner = MinerState()

        self._miner = self.player.miner

        # Перевіряємо чи повернувся шахтар поки нас не було
        self._miner.check_return()

        # Анімація НПС
        self._npc_ctrl  = self._load_npc()
        self._npc_float = 0.0
        self._npc_shadow = pygame.Surface((80, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(self._npc_shadow, (0, 0, 0, 60), self._npc_shadow.get_rect())

        # UI стан
        self._selected_tier: str | None = None
        self._message = ""
        self._message_t = 0.0

        self._create_buttons()

    # ── Завантаження НПС ─────────────────────────────────────────
    def _load_npc(self) -> AnimationController | None:
        try:
            from pathlib import Path
            base = Path("assets/animations/miner/Trader_2")
            SCALE = 2.5
            FW = FH = 128   # розмір кадру 128×128

            def load(name, count, loop=True):
                frames = AnimationLoader.load_spritesheet(
                    base / f"{name}.png",
                    frame_width=FW, frame_height=FH,
                    frame_count=count, scale=SCALE)
                return Animation(name.lower(), frames,
                                 frame_duration=0.1, loop=loop)

            ctrl = AnimationController()
            ctrl.add_animation("idle",     load("Idle",     14))
            ctrl.add_animation("idle2",    load("Idle_2",   10))
            ctrl.add_animation("idle3",    load("Idle_3",   10))
            ctrl.add_animation("dialogue", load("Dialogue",  4))
            ctrl.add_animation("approval", load("Approval",  8, loop=False))
            ctrl.play("idle")
            return ctrl
        except Exception as e:
            log.warning("Не вдалось завантажити анімацію шахтаря: %s", e)
            return None

    # ── Кнопки ───────────────────────────────────────────────────
    def _create_buttons(self):
        self.exit_btn = Button(30, SCREEN_HEIGHT - 70, 180, 46,
                               "← Назад", lambda: self.game.change_scene("village"))

        self.send_btn = Button(PANEL_X, SCREEN_HEIGHT - 70, 220, 46,
                               "⛏ Відправити", self._on_send)

        self.collect_btn = Button(PANEL_X, SCREEN_HEIGHT - 70, 220, 46,
                                  "📦 Забрати руди", self._on_collect)

        self.hire_btn = Button(PANEL_X, SCREEN_HEIGHT - 70, 220, 46,
                               "👷 Найняти нового", self._on_hire)

        self.rest_btn = Button(PANEL_X + 240, SCREEN_HEIGHT - 70, 180, 46,
                               "😴 Відпочити (10хв)", self._on_rest)

        # Кнопки тарифів
        self.tier_btns: list[Button] = []
        for i, (tid, tier) in enumerate(TIERS.items()):
            btn = Button(PANEL_X + 10, PANEL_Y + 70 + i * 90, PANEL_W - 20, 78,
                         f"{tier.icon} {tier.name}",
                         lambda t=tid: self._select_tier(t))
            self.tier_btns.append(btn)

        self._rebuild_buttons()

    def _select_tier(self, tid: str):
        self._selected_tier = tid
        if self._npc_ctrl:
            self._npc_ctrl.play("dialogue")

    # ── Дії ──────────────────────────────────────────────────────
    def _has_pickaxe(self) -> bool:
        return any(getattr(i, "item_id", "") == PICKAXE_ID
                   for i in self.player.inventory)

    def _has_shovel(self) -> bool:
        return any(getattr(i, "item_id", "") == SHOVEL_ID
                   for i in self.player.inventory)

    def _remove_from_inventory(self, item_id: str) -> bool:
        for i, item in enumerate(self.player.inventory):
            if getattr(item, "item_id", "") == item_id:
                self.player.inventory.pop(i)
                return True
        return False

    def _on_send(self):
        if self._selected_tier is None:
            self._show("Спочатку вибери тариф!")
            return
        if not self._has_pickaxe():
            self._show("⛏ Потрібне кайло! Купи його в крамниці.")
            return
        tier = TIERS[self._selected_tier]
        actual_cost = int(tier.cost * self._miner.cost_multiplier)
        if self.player.gold < actual_cost:
            self._show(f"💸 Потрібно {actual_cost} золота!")
            return

        # Списуємо
        self.player.gold -= actual_cost
        self.player.gold_spent += actual_cost
        has_shovel = self._has_shovel()
        if has_shovel:
            self._remove_from_inventory(SHOVEL_ID)
        self._remove_from_inventory(PICKAXE_ID)

        # Отримуємо поточну погоду з game.scene_data
        weather = self.game.scene_data.get("current_weather", "ясно")
        self._miner.send(self._selected_tier, has_shovel, weather=weather)

        # Статистика + репутація
        self.player.mine_trips = getattr(self.player, "mine_trips", 0) + 1
        from game.reputation import add_reputation, REP_MINE_TRIP
        add_reputation(self.player, REP_MINE_TRIP)
        if self._selected_tier == "deep":
            self.player.mine_deep_trips = getattr(self.player, "mine_deep_trips", 0) + 1

        self._selected_tier = None

        WEATHER_HINTS = {
            "ясно":   " ☀ +5% швидше",
            "дощ":    " 🌧 -10% повільніше, більше ризиків",
            "туман":  " 🌫 -5% повільніше",
            "вітер":  "",
            "хмарно": "",
        }
        w_hint = WEATHER_HINTS.get(weather, "")
        suffix = " (з лопатою)" if has_shovel else ""
        self._show(f"Шахтар пішов!{suffix}{w_hint}")
        if self._npc_ctrl:
            self._npc_ctrl.play("approval")

        self._rebuild_buttons()
        autosave(self.player)

    def _on_collect(self):
        if self._miner.status != MinerState.STATUS_DONE:
            return

        from game.data import MATERIALS as MATS_DATA
        ores = self._miner.ores_ready.copy()
        if not ores:
            self._show("Шахтар нічого не знайшов...")
        else:
            total_qty = 0
            for mat_id, qty in ores.items():
                self.player.materials[mat_id] =                     self.player.materials.get(mat_id, 0) + qty
                total_qty += qty
                mat = MATS_DATA.get(mat_id)
                if mat and mat.rarity == "legendary":
                    self.player.mine_legendary_found = True
            self.player.mine_ores_collected =                 getattr(self.player, "mine_ores_collected", 0) + total_qty
            names = ", ".join(
                f"{MATS_DATA[m].icon if m in MATS_DATA else '?'}{qty}"
                for m, qty in ores.items()
            )
            self._show(f"📦 Отримано: {names}")

        # Бонусні знахідки — монети і предмети
        bonus_gold  = getattr(self._miner, "bonus_gold", 0)
        bonus_items = getattr(self._miner, "bonus_items", [])
        if bonus_gold > 0:
            self.player.gold += bonus_gold
            self.player.total_gold_earned += bonus_gold
            from ui.notifications import notify
            notify(f"💰 Борис знайшов {bonus_gold} монет!", kind="item", duration=2.5)
        if bonus_items:
            for mat_id in bonus_items:
                self.player.materials[mat_id] =                     self.player.materials.get(mat_id, 0) + 1
            from ui.notifications import notify
            bonus_names = ", ".join(
                f"{MATS_DATA[m].icon} {MATS_DATA[m].name}" if m in MATS_DATA else m
                for m in bonus_items
            )
            notify(f"🎁 Знахідка: {bonus_names}!", kind="item", duration=2.5)
        self._miner.bonus_gold  = 0
        self._miner.bonus_items = []

        # Ризик зламаного кайла — перевіряємо після повернення
        if random.random() < RISK_PICKAXE_BREAK:
            # Додаємо зламане кайло в інвентар
            from game.data import Item
            broken = Item(
                item_id="broken_pickaxe", name="Зламане кайло",
                item_type="tool", value=0,
                icon="🔨", description="Потребує ремонту в майстерні",
            )
            self.player.inventory.append(broken)
            self._show(self._message + " | ⚠ Кайло зламалось!")

        self._miner.ores_ready = {}
        self._miner.status = MinerState.STATUS_IDLE
        self._miner.had_cave_in = False

        if self._npc_ctrl:
            self._npc_ctrl.play("idle")

        self._rebuild_buttons()
        autosave(self.player)

    def _on_rest(self):
        """Шахтар відпочиває 10 хв — скидає втому."""
        if self._miner.fatigue_level == 0:
            self._show("Шахтар ще не втомлений!")
            return
        self._miner.start_rest()
        self._show("😴 Шахтар відпочиває 10 хвилин...")
        self._rebuild_buttons()
        autosave(self.player)

    def _on_hire(self):
        """Найняти нового шахтаря (скидає стан)."""
        self._miner.status     = MinerState.STATUS_IDLE
        self._miner.tier_id    = None
        self._miner.ores_ready = {}
        self._show("Найнято нового шахтаря!")
        self._rebuild_buttons()
        autosave(self.player)

    def _rebuild_buttons(self):
        status = self._miner.status
        if self._miner.is_resting:
            self.buttons = [self.exit_btn]
        elif status == MinerState.STATUS_IDLE:
            btns = [self.exit_btn] + self.tier_btns + [self.send_btn]
            if self._miner.fatigue_level > 0:
                btns.append(self.rest_btn)
            self.buttons = btns
        elif status == MinerState.STATUS_WORKING:
            self.buttons = [self.exit_btn]
        elif status == MinerState.STATUS_DONE:
            self.buttons = [self.exit_btn, self.collect_btn]
        elif status == MinerState.STATUS_LOST:
            self.buttons = [self.exit_btn, self.hire_btn]

    def _show(self, msg: str):
        self._message   = msg
        self._message_t = 3.5
        from ui.notifications import notify
        notify(msg, duration=3.0)

    # ── Update ────────────────────────────────────────────────────
    def update(self, dt: float):
        super().update(dt)
        self._npc_float += dt
        if self._npc_ctrl:
            self._npc_ctrl.update(dt)
            # Якщо approval закінчилась — повертаємось до idle
            anim = self._npc_ctrl.current_name
            cur  = self._npc_ctrl.current_animation
            if anim == "approval" and cur and cur.finished:
                idle = random.choice(["idle", "idle2", "idle3"])
                self._npc_ctrl.play(idle)
        if self._message_t > 0:
            self._message_t -= dt

        # Перевірка кінця відпочинку
        if self._miner.is_resting:
            pass  # ще відпочиває
        elif self._miner.resting_until is not None and not self._miner.is_resting:
            if self._miner.trips_since_rest == 0:
                self._miner.resting_until = None
                self._show("😊 Шахтар відпочив та готовий до роботи!")
                self._rebuild_buttons()

        # Перевірка повернення
        changed = self._miner.check_return()
        if changed:
            self._rebuild_buttons()
            if self._miner.status == MinerState.STATUS_DONE:
                cave_msg = " (був обвал!)" if self._miner.had_cave_in else ""
                self._show(f"⛏ Шахтар повернувся{cave_msg}! Забери руди.")
            elif self._miner.status == MinerState.STATUS_LOST:
                self.player.mine_accidents =                     getattr(self.player, "mine_accidents", 0) + 1
                self._show("💀 Шахтар не повернувся... Найми нового.")
            # Перевіряємо досягнення
            from game.achievements import AchievementManager
            AchievementManager.check_all(self.player)
            autosave(self.player)

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)

    # ── Draw ──────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        super().draw(screen)

        self._draw_npc(screen)
        self._draw_left_panel(screen)
        self._draw_header(screen)

        self.draw_buttons(screen)

    def _draw_npc(self, screen: pygame.Surface):
        """Малює анімованого шахтаря."""
        if not self._npc_ctrl:
            return
        frame = self._npc_ctrl.get_current_frame()
        if not frame:
            return
        float_y = math.sin(self._npc_float * 1.4) * 3
        x = NPC_X
        y = int(NPC_Y - frame.get_height() + float_y)
        # Тінь
        sx = x + frame.get_width() // 2 - self._npc_shadow.get_width() // 2
        screen.blit(self._npc_shadow, (sx, NPC_Y + 4))
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
        gold = font_sm.render(f"💰 {self.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold, (SCREEN_WIDTH - gold.get_width() - 40, 55))

        # Інструменти гравця
        has_pick   = self._has_pickaxe()
        has_shovel = self._has_shovel()
        has_broken = any(getattr(i, "item_id", "") == BROKEN_PICKAXE_ID
                         for i in self.player.inventory)
        tools_x = PANEL_X
        tools_y = 60
        draw_icon(screen, PICKAXE_ID,        "⛏", tools_x,      tools_y, size=24,
                  alpha=255 if has_pick else 80)
        draw_icon(screen, SHOVEL_ID,         "🪣", tools_x + 32, tools_y, size=24,
                  alpha=255 if has_shovel else 80)
        if has_broken:
            draw_icon(screen, BROKEN_PICKAXE_ID, "🔨", tools_x + 64, tools_y, size=24)

    def _draw_left_panel(self, screen: pygame.Surface):
        status = self._miner.status
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

        has_pick = self._has_pickaxe()
        if not has_pick:
            warn = font_sm.render("⚠ Потрібне кайло! Купи в крамниці.", True, COLOR_ERROR)
            screen.blit(warn, (px, py)); py += 22

        # Втома
        FATIGUE_ICONS  = ["😊 Свіжий",  "😓 Втомлений", "😵 Виснажений"]
        FATIGUE_COLORS = [(100,220,100), (220,180,60),   (220,80,80)]
        flvl = self._miner.fatigue_level
        fat_lbl = font_sm.render(
            f"Стан: {FATIGUE_ICONS[flvl]}  (похід {self._miner.trips_since_rest})",
            True, FATIGUE_COLORS[flvl])
        screen.blit(fat_lbl, (px, py)); py += 20
        if flvl > 0:
            mult = self._miner.cost_multiplier
            screen.blit(font_sm.render(
                f"⚠ Ціна робіт ×{mult:.2f} — дай відпочити!", True, (220,180,60)),
                (px, py)); py += 18

        # Відпочинок
        if self._miner.is_resting:
            left = self._miner.rest_time_left()
            m, s = divmod(left, 60)
            screen.blit(font_sm.render(f"😴 Відпочиває: {m:02d}:{s:02d}",
                        True, (140,180,255)), (px, py)); py += 20

        screen.blit(font_sm.render("Вибери тариф:", True, COLOR_TEXT_DIM), (px, py))
        py += 30

        for i, (tid, tier) in enumerate(TIERS.items()):
            btn_y = PANEL_Y + 70 + i * 90
            # Підсвітка вибраного
            if self._selected_tier == tid:
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
            actual = int(tier.cost * self._miner.cost_multiplier)
            cost_txt = f"{actual}🪙" if actual == tier.cost else f"{actual}🪙 (втома)"
            screen.blit(font_sm.render(
                f"⏱ {mins} хв  |  💰 {cost_txt}  |  📦 {tier.min_ores}–{tier.max_ores} руд",
                True, COLOR_TEXT), (info_x, info_y + 24))
            screen.blit(font_sm.render(tier.description, True, COLOR_TEXT_DIM),
                        (info_x, info_y + 44))

        # Інфо про інструменти
        iy = PANEL_Y + 70 + len(TIERS) * 90 + 14
        has_pick   = self._has_pickaxe()
        has_shovel = self._has_shovel()

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
        tier = TIERS.get(self._miner.tier_id)
        screen.blit(font.render("⛏ Шахтар працює...", True, COLOR_GOLD), (px, py)); py += 30
        if tier:
            screen.blit(font_n.render(f"Тариф: {tier.icon} {tier.name}", True, COLOR_TEXT),
                        (px, py)); py += 26

        left  = self._miner.time_left()
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
        col = COLOR_ERROR if self._miner.had_cave_in else (100, 220, 100)
        hdr = "⚠ Шахтар повернувся (був обвал!)" if self._miner.had_cave_in \
              else "✅ Шахтар повернувся!"
        screen.blit(font.render(hdr, True, col), (px, py)); py += 30
        screen.blit(font_n.render("Знайдені руди:", True, COLOR_TEXT_DIM), (px, py)); py += 28

        for mat_id, qty in self._miner.ores_ready.items():
            mat = MATERIALS.get(mat_id)
            if not mat:
                continue
            draw_icon(screen, mat_id, mat.icon, px, py, size=22)
            screen.blit(font_n.render(f"  {mat.name}  ×{qty}", True, COLOR_TEXT),
                        (px + 24, py + 2))
            py += 28

        if not self._miner.ores_ready:
            screen.blit(font_sm.render("Нічого не знайдено...", True, COLOR_TEXT_DIM), (px, py))

    def _draw_lost_panel(self, screen, px, py, font, font_n, font_sm):
        screen.blit(font.render("💀 Шахтар не повернувся!", True, COLOR_ERROR), (px, py)); py += 30
        screen.blit(font_n.render("Мабуть стався нещасний випадок.", True, COLOR_TEXT), (px, py)); py += 26
        screen.blit(font_n.render("Кайло також загублено.", True, COLOR_TEXT_DIM), (px, py)); py += 26
        screen.blit(font_sm.render("Натисни 'Найняти нового' щоб продовжити.", True, COLOR_TEXT_DIM),
                    (px, py))