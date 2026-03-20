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
        # Підключаємо renderer (малювання)
        from scenes.ui.mine_renderer import MineRenderer
        self._renderer = MineRenderer(self)
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
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)