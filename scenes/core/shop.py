"""
Сцена крамниці (купівля предметів, кресленників).
Підтримує скролінг, показує бонуси матеріалів для кресленників.
"""
import logging
log = logging.getLogger(__name__)

import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.data import ITEMS, BLUEPRINTS, MATERIALS, OwnedBlueprint, BP_RARITY_COLORS, BP_RARITY_NAMES_UA
from game.save_manager import autosave
from game.reputation import apply_discount, add_reputation, REP_SHOP_SPEND_10
from ui.icons import draw_icon, get_icon_surf

# ── Що продається в крамниці — читається з config/shop.py ──────────
def _load_shop_data():
    try:
        from config.shop import SHOP_ITEMS as _SI, SHOP_BLUEPRINTS as _SB
        items = [(ITEMS[iid], price) for iid, price in _SI if iid in ITEMS]
        bps   = [(BLUEPRINTS[bid], price) for bid, price in _SB if bid in BLUEPRINTS]
        return items, bps
    except Exception:
        pass
    # fallback — старий хардкод
    return (
        [(ITEMS["small_potion"],10),(ITEMS["big_potion"],25),(ITEMS["power_potion"],30),
         (ITEMS["leather_armor"],40),(ITEMS["chainmail"],80)],
        []
    )

SHOP_ITEMS, SHOP_BLUEPRINTS = _load_shop_data()

# (старий хардкод залишено нижче для резерву — не використовується)
_SHOP_BLUEPRINTS_LEGACY = [
    # ── Інструменти шахтаря ──
    (BLUEPRINTS["bp_pickaxe"],        15),
    (BLUEPRINTS["bp_shovel"],         12),
    # ── Tier 1: Залізна/базова зброя ──
    (BLUEPRINTS["bp_dagger"],         12),
    (BLUEPRINTS["bp_iron_sword"],     20),
    (BLUEPRINTS["bp_battle_axe"],     30),
    (BLUEPRINTS["bp_war_hammer"],     32),
    (BLUEPRINTS["bp_bone_club"],      18),
    (BLUEPRINTS["bp_bone_spear"],     22),
    # ── Tier 2: Срібна/кварцова зброя ──
    (BLUEPRINTS["bp_silver_dagger"],  25),
    (BLUEPRINTS["bp_silver_sword"],   35),
    (BLUEPRINTS["bp_quartz_blade"],   28),
    (BLUEPRINTS["bp_frost_blade"],    38),
    # ── Tier 3: Темна/магічна зброя ──
    (BLUEPRINTS["bp_dark_blade"],     50),
    (BLUEPRINTS["bp_shadow_blade"],   60),
    (BLUEPRINTS["bp_fire_sword"],     65),
    (BLUEPRINTS["bp_storm_blade"],    62),
    (BLUEPRINTS["bp_blood_sword"],    70),
    (BLUEPRINTS["bp_runic_sword"],    72),
    # ── Tier 4: Мітрилова/void зброя ──
    (BLUEPRINTS["bp_mithril_sword"],  80),
    (BLUEPRINTS["bp_void_blade"],     75),
    (BLUEPRINTS["bp_shadow_reaper"],  85),
    (BLUEPRINTS["bp_phoenix_sword"],  88),
    # ── Tier 5: Легендарна зброя ──
    (BLUEPRINTS["bp_dragon_sword"],   90),
    (BLUEPRINTS["bp_star_blade"],    100),
    (BLUEPRINTS["bp_void_dragon"],   120),
    (BLUEPRINTS["bp_ancient_sword"], 150),
    # ── Броня Tier 1 ──
    (BLUEPRINTS["bp_leather_armor"],  15),
    (BLUEPRINTS["bp_bone_armor"],     22),
    (BLUEPRINTS["bp_hardwood_shield"],20),
    # ── Броня Tier 2 ──
    (BLUEPRINTS["bp_chainmail_plus"], 35),
    (BLUEPRINTS["bp_silver_mail"],    50),
    (BLUEPRINTS["bp_frost_armor"],    55),
    # ── Броня Tier 3 ──
    (BLUEPRINTS["bp_shadow_vest"],    45),
    (BLUEPRINTS["bp_runic_armor"],    65),
    (BLUEPRINTS["bp_shadow_armor"],   70),
    # ── Броня Tier 4-5 ──
    (BLUEPRINTS["bp_mithril_plate"],  75),
    (BLUEPRINTS["bp_phoenix_armor"],  90),
    (BLUEPRINTS["bp_dragon_armor"],  100),
    (BLUEPRINTS["bp_ancient_armor"], 140),
]

ROW_H    = 54
LIST_X   = 60
LIST_W   = 620
LIST_Y   = 130
VISIBLE  = 9     # скільки рядків видно одночасно

INFO_X   = LIST_X + LIST_W + 20
INFO_W   = SCREEN_WIDTH - INFO_X - 30


class ShopScene(SceneWithBackground, SceneWithButtons):
    """Крамниця."""

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "shop")
        SceneWithButtons.__init__(self, game)

        self.tab    = "items"
        self.sel    = -1
        self.scroll = 0

        # ── Пошук ─────────────────────────────────────────────
        self._search_text   = ""
        self._search_active = False   # чи активне поле вводу

        # ── Кількість покупки ──────────────────────────────────
        self._buy_qty = 1   # 1 / 5 / 10

        self._create_buttons()
        self.shop_panel = Panel(30, 30, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60, alpha=True)

    # ── Кнопки ────────────────────────────────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.shop_renderer import ShopRenderer
        self._renderer = ShopRenderer(self)
    def _create_buttons(self):
        self.tab_btns = [
            Button(LIST_X,       80, 160, 38, "🧪 Товари",      lambda: self._switch("items")),
            Button(LIST_X + 175, 80, 180, 38, "📜 Кресленники", lambda: self._switch("blueprints")),
        ]
        self.buy_btn  = Button(INFO_X, SCREEN_HEIGHT - 90, INFO_W, 50, "💰 Купити",
                               self._buy_selected)
        self.exit_btn = Button(30, SCREEN_HEIGHT - 90, 160, 50, "← Вийти",
                               lambda: self.game.change_scene("village"))
        # Кнопки кількості — тільки для товарів
        self.qty_btns = [
            Button(LIST_X,       SCREEN_HEIGHT - 90, 70, 50, "×1",  lambda: self._set_qty(1)),
            Button(LIST_X + 78,  SCREEN_HEIGHT - 90, 70, 50, "×5",  lambda: self._set_qty(5)),
            Button(LIST_X + 156, SCREEN_HEIGHT - 90, 70, 50, "×10", lambda: self._set_qty(10)),
        ]
        self.buttons = self.tab_btns + [self.buy_btn, self.exit_btn] + self.qty_btns

    def _set_qty(self, qty: int):
        self._buy_qty = qty

    def _switch(self, tab):
        self.tab    = tab
        self.sel    = -1
        self.scroll = 0
        self._buy_qty = 1

    # ── Дані поточної вкладки ─────────────────────────────────────

    def _rows(self):
        rows = SHOP_ITEMS if self.tab == "items" else SHOP_BLUEPRINTS
        if not self._search_text:
            return rows
        q = self._search_text.lower()
        return [(t, p) for t, p in rows if q in t.name.lower()]

    def _visible_rows(self):
        rows = self._rows()
        return rows[self.scroll: self.scroll + VISIBLE]

    # ── Купівля ───────────────────────────────────────────────────

    def _buy_selected(self):
        if self.sel == -1:
            return
        rows = self._rows()
        abs_idx = self.scroll + self.sel
        if abs_idx >= len(rows):
            return

        thing, price = rows[abs_idx]
        qty = self._buy_qty if self.tab == "items" else 1
        total_price = price * qty

        if self.player.gold < total_price:
            from ui.notifications import notify
            notify("💸 Недостатньо золота!", kind="error", duration=1.5)
            return

        if self.tab == "items":
            self.player.gold       -= total_price
            self.player.gold_spent += total_price
            for _ in range(qty):
                import copy
                self.player.inventory.append(copy.copy(thing))
            add_reputation(self.player, total_price // 10 * REP_SHOP_SPEND_10)
            from ui.notifications import notify
            suffix = f" ×{qty}" if qty > 1 else ""
            notify(f"🛒 Куплено: {thing.icon} {thing.name}{suffix}", kind="item", duration=2.0)
            autosave(self.player)

        else:  # blueprints
            # Дозволяємо купити ще раз якщо вже є — отримає новий OwnedBlueprint
            ob = OwnedBlueprint.new(thing)
            self.player.gold       -= price
            self.player.gold_spent += price
            self.player.blueprints.append(ob)
            rar = BP_RARITY_NAMES_UA.get(thing.rarity, "")
            from ui.notifications import notify
            notify(f"📜 Куплено: {thing.result_name} ({rar})", kind="item", duration=2.0)
            autosave(self.player)

    # ── події ─────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mp = pygame.mouse.get_pos()
            # Клік на поле пошуку
            search_rect = pygame.Rect(LIST_X, 38, 320, 32)
            self._search_active = search_rect.collidepoint(mp)

            if event.button == 1:
                for i, _ in enumerate(self._visible_rows()):
                    r = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)
                    if r.collidepoint(mp):
                        self.sel = i
                        break
            elif event.button == 4:
                self.scroll = max(0, self.scroll - 1)
                self.sel    = -1
            elif event.button == 5:
                max_sc = max(0, len(self._rows()) - VISIBLE)
                self.scroll = min(max_sc, self.scroll + 1)
                self.sel    = -1

        elif event.type == pygame.KEYDOWN:
            if self._search_active:
                if event.key == pygame.K_BACKSPACE:
                    self._search_text = self._search_text[:-1]
                    self.sel = -1; self.scroll = 0
                elif event.key == pygame.K_ESCAPE:
                    self._search_active = False
                    self._search_text   = ""
                    self.sel = -1; self.scroll = 0
                elif event.unicode and len(self._search_text) < 24:
                    self._search_text += event.unicode
                    self.sel = -1; self.scroll = 0
            else:
                if event.key == pygame.K_UP:
                    if self.sel > 0:
                        self.sel -= 1
                    elif self.scroll > 0:
                        self.scroll -= 1
                elif event.key == pygame.K_DOWN:
                    vis = len(self._visible_rows())
                    if self.sel < vis - 1:
                        self.sel += 1
                    elif self.scroll + VISIBLE < len(self._rows()):
                        self.scroll += 1

    def update(self, dt: float):
        super().update(dt)

    # ── Малювання ─────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)