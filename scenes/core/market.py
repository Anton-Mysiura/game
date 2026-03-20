"""
Сцена Чорного ринку.
Лоти оновлюються кожні 5 хвилин (реальний час, офлайн-прогрес включно).
"""
import math
import logging
log = logging.getLogger(__name__)

import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.market import RARITY_COLOR, RARITY_UA, REFRESH_SEC, fmt_time_market
from game.save_manager import autosave
from ui.icons import draw_icon, get_icon_surf

# Скільки лотів відображаємо в рядок та кількість рядків
COLS = 3
ROWS = 2
CARD_W = 360
CARD_H = 185
GAP_X  = 24
GAP_Y  = 18
GRID_X = (1280 - (COLS * CARD_W + (COLS - 1) * GAP_X)) // 2
GRID_Y = 115


class MarketScene(SceneWithBackground, SceneWithButtons):

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "market")
        SceneWithButtons.__init__(self, game)

        self._anim_t  = 0.0
        self._msg     = ""
        self._msg_t   = 0.0
        self._msg_ok  = True
        self._sel     = -1        # індекс вибраного лота

        # Ринок завжди свіжий (ensure_fresh вже викликано при завантаженні)
        self.player.market.ensure_fresh()

        self._create_buttons()
        self.main_panel = Panel(20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40, alpha=True)

    # ── Кнопки ────────────────────────────────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.market_renderer import MarketRenderer
        self._renderer = MarketRenderer(self)
    def _create_buttons(self):
        self.buy_btn = Button(
            SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT - 72, 260, 48,
            "💰 Купити", self._buy_selected)
        self.refresh_btn = Button(
            SCREEN_WIDTH - 220, SCREEN_HEIGHT - 72, 190, 48,
            "🔄 Оновити (безкошт.)", self._force_refresh)
        self.exit_btn = Button(
            30, SCREEN_HEIGHT - 72, 160, 48,
            "← Вийти", lambda: self.game.change_scene("village"))
        self.buttons = [self.buy_btn, self.refresh_btn, self.exit_btn]

    # ── Дії ───────────────────────────────────────────────────────

    def _buy_selected(self):
        if self._sel < 0:
            return
        lot = self.player.market.lots[self._sel] if self._sel < len(self.player.market.lots) else None
        ok, msg = self.player.market.buy(self._sel, self.player)
        self._msg    = msg
        self._msg_t  = 2.5
        self._msg_ok = ok
        from ui.notifications import notify
        if ok:
            autosave(self.player)
            self._sel = -1
            # Визначаємо що саме купили
            if lot:
                if lot.lot_type in ("weapon", "armor"):
                    name = lot.item_data.get("name", "")
                    notify(f"🛒 Куплено: {name}", kind="market", duration=3.0)
                elif lot.lot_type == "blueprint":
                    from game.data import BLUEPRINTS
                    bp = BLUEPRINTS.get(lot.bp_id)
                    notify(f"📜 Кресленик: {bp.result_name if bp else ''}", kind="market", duration=3.0)
                elif lot.lot_type == "tool":
                    notify(f"🛠 Куплено: {lot.item_data.get('icon','')} {lot.item_data.get('name','')}", kind="market", duration=2.0)
                else:
                    notify(f"🛒 {msg}", kind="market", duration=2.0)
        else:
            notify(msg, kind="error", duration=2.0)

    def _force_refresh(self):
        self.player.market.refresh()
        autosave(self.player)
        self._sel   = -1
        self._msg   = "🔄 Ринок оновлено!"
        self._msg_t = 2.0
        self._msg_ok = True
        from ui.notifications import notify
        notify("🔄 Ринок оновлено!", kind="market", duration=2.0)

    # ── Події ─────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            for i, lot in enumerate(self.player.market.lots):
                r = self._card_rect(i)
                if r.collidepoint(mp):
                    self._sel = i if self._sel != i else -1
                    break

    def update(self, dt: float):
        super().update(dt)
        self._anim_t += dt
        if self._msg_t > 0:
            self._msg_t -= dt
        # Авто-оновлення якщо час вийшов
        if self.player.market.needs_refresh():
            self.player.market.refresh()
            autosave(self.player)

    # ── Позиція картки ────────────────────────────────────────────

    def _card_rect(self, idx: int) -> pygame.Rect:
        col = idx % COLS
        row = idx // COLS
        x   = GRID_X + col * (CARD_W + GAP_X)
        y   = GRID_Y + row * (CARD_H + GAP_Y)
        return pygame.Rect(x, y, CARD_W, CARD_H)

    # ── Малювання ─────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)
    def _lot_display(self, lot) -> tuple:
        """Повертає (icon, name, [(line, color)], (mut_id, rar) | None)."""
        from game.data import ITEMS, MATERIALS, BLUEPRINTS

        stat_lines = []
        mut_info   = None

        if lot.lot_type == "potion":
            item = ITEMS.get(lot.item_id)
            if not item:
                return "❓", "???", [], None
            icon = item.icon
            name = f"{item.name} ×{lot.qty}" if lot.qty > 1 else item.name
            if item.hp_restore:
                stat_lines.append((f"🧪 Відновлює {item.hp_restore} HP", (100, 220, 180)))
            if item.attack_bonus:
                stat_lines.append((f"⚔ +{item.attack_bonus} ATK", (220, 180, 100)))

        elif lot.lot_type == "material":
            mat = MATERIALS.get(lot.item_id)
            if not mat:
                return "❓", "???", [], None
            icon = mat.icon
            name = f"{mat.name} ×{lot.qty}" if lot.qty > 1 else mat.name
            stat_lines.append((mat.description, COLOR_TEXT_DIM))
            parts = []
            if mat.bonus_attack:  parts.append(f"+{mat.bonus_attack}ATK/шт")
            if mat.bonus_defense: parts.append(f"+{mat.bonus_defense}DEF/шт")
            if mat.bonus_hp:      parts.append(f"+{mat.bonus_hp}HP/шт")
            if mat.bonus_crit:    parts.append(f"+{mat.bonus_crit*100:.0f}%крит/шт")
            if parts:
                stat_lines.append((f"✦ {' '.join(parts)}", (160, 220, 140)))

        elif lot.lot_type == "blueprint":
            from game.data import BP_RARITY_COLORS, BP_RARITY_NAMES_UA, BP_RARITY_USES
            bp = BLUEPRINTS.get(lot.bp_id)
            if not bp:
                return "❓", "???", [], None
            icon = "📜"
            rar_name = BP_RARITY_NAMES_UA.get(bp.rarity, bp.rarity)
            uses = BP_RARITY_USES.get(bp.rarity, 2)
            name = f"{bp.result_name}"
            tp_icon = "⚔" if bp.result_type == "weapon" else "🛡"
            stat = f"+{bp.result_attack} ATK" if bp.result_type == "weapon" \
                   else f"+{bp.result_defense} DEF"
            rar_clr = BP_RARITY_COLORS.get(bp.rarity, (180, 180, 180))
            stat_lines.append((f"{tp_icon} Кресленик: {stat}", COLOR_TEXT))
            stat_lines.append((f"📜 {rar_name}  🔄 {uses} використань", rar_clr))

        elif lot.lot_type == "tool":
            icon = lot.item_data.get("icon", "⛏")
            name = lot.item_data.get("name", "Інструмент")
            if lot.item_id == "pickaxe":
                stat_lines.append(("⛏ Обов'язковий для шахтаря", COLOR_TEXT))
                stat_lines.append(("⚠ Може зламатись після походу", COLOR_TEXT_DIM))
            elif lot.item_id == "shovel":
                stat_lines.append(("🪣 Прискорює копання на 10%", COLOR_TEXT))
                stat_lines.append(("Необов'язковий інструмент", COLOR_TEXT_DIM))
            stat_lines.append(("🏷 Дешевше ніж у крамниці!", (100, 220, 100)))

        else:  # weapon / armor
            d = lot.item_data
            if not d:
                return "❓", "???", [], None
            icon = d.get("icon", "⚔")
            name = d.get("name", "???")
            if lot.lot_type == "weapon":
                stat_lines.append((f"⚔ Атака: +{d.get('attack_bonus', 0)}", (220, 180, 100)))
                if d.get("crit_bonus"):
                    stat_lines.append((f"🎯 Крит: +{d['crit_bonus']*100:.0f}%", (200, 160, 100)))
            else:
                stat_lines.append((f"🛡 Захист: +{d.get('defense_bonus', 0)}", (100, 180, 220)))
                if d.get("hp_bonus"):
                    stat_lines.append((f"❤ HP: +{d['hp_bonus']}", (220, 100, 100)))
            if d.get("mutation"):
                mut_info = (d["mutation"], lot.rarity)

        return icon, name, stat_lines, mut_info

    # ── Нижня панель ──────────────────────────────────────────────
