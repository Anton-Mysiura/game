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
        super().draw(screen)
        self.shop_panel.draw(screen)

        self._draw_header(screen)
        self._draw_tabs(screen)
        self._draw_list(screen)
        self._draw_info(screen)
        self._draw_scrollbar(screen)

        # Оновлюємо текст кнопки купити з ціною і qty
        rows = self._rows()
        abs_idx = self.scroll + self.sel
        if self.sel != -1 and abs_idx < len(rows):
            thing, price = rows[abs_idx]
            qty = self._buy_qty if self.tab == "items" else 1
            total = price * qty
            suffix = f" ×{qty}" if qty > 1 else ""
            owned  = self.tab == "blueprints" and thing in self.player.blueprints
            self.buy_btn.text    = "✓ Вже куплено" if owned else f"💰 Купити{suffix}  {total}🪙"
            self.buy_btn.enabled = not owned and self.player.gold >= total
        else:
            self.buy_btn.text    = "💰 Купити"
            self.buy_btn.enabled = False

        self.buy_btn.draw(screen)
        self.exit_btn.draw(screen)

        # Кнопки qty — тільки для товарів
        if self.tab == "items":
            for i, btn in enumerate(self.qty_btns):
                btn.selected = (self._buy_qty == [1, 5, 10][i])
                btn.draw(screen)

    def _draw_header(self, screen):
        font   = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_n = assets.get_font(FONT_SIZE_NORMAL)
        font_s = assets.get_font(FONT_SIZE_SMALL)
        screen.blit(font.render("🏪 Крамниця Барнуса", True, COLOR_GOLD), (LIST_X, 38))
        gold = font_n.render(f"💰 {self.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold, (SCREEN_WIDTH - gold.get_width() - 50, 42))

        # ── Поле пошуку ───────────────────────────────────────
        search_rect = pygame.Rect(LIST_X + 370, 38, 220, 32)
        border_col  = COLOR_GOLD if self._search_active else (80, 70, 50)
        pygame.draw.rect(screen, (20, 16, 10), search_rect, border_radius=6)
        pygame.draw.rect(screen, border_col,   search_rect, 1, border_radius=6)
        display = self._search_text + ("|" if self._search_active else "")
        hint    = display if display else "🔍 Пошук..."
        col     = COLOR_TEXT if self._search_text else COLOR_TEXT_DIM
        t = font_s.render(hint, True, col)
        screen.blit(t, (search_rect.x + 8, search_rect.y + 8))

    def _draw_tabs(self, screen):
        for i, btn in enumerate(self.tab_btns):
            btn.selected = (i == 0 and self.tab == "items") or \
                           (i == 1 and self.tab == "blueprints")
            btn.draw(screen)

    def _draw_list(self, screen):
        font     = assets.get_font(FONT_SIZE_NORMAL)
        font_sm  = assets.get_font(FONT_SIZE_SMALL)
        mp       = pygame.mouse.get_pos()
        vis_rows = self._visible_rows()

        # Фон списку
        list_bg = pygame.Surface((LIST_W, VISIBLE * ROW_H), pygame.SRCALPHA)
        list_bg.fill((10, 8, 6, 180))
        screen.blit(list_bg, (LIST_X, LIST_Y))

        for i, (thing, price) in enumerate(vis_rows):
            r = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)

            # Фон рядка
            if i == self.sel:
                bg = (80, 65, 20, 200)
            elif r.collidepoint(mp):
                bg = (50, 45, 30, 200)
            elif i % 2 == 0:
                bg = (20, 18, 14, 160)
            else:
                bg = (28, 24, 18, 160)

            surf = pygame.Surface((LIST_W, ROW_H - 4), pygame.SRCALPHA)
            surf.fill(bg)
            screen.blit(surf, (r.x, r.y))

            if i == self.sel:
                pygame.draw.rect(screen, COLOR_GOLD, r, 1, border_radius=3)

            # Ім'я
            if self.tab == "items":
                icon = thing.icon
                name = thing.name
                sub  = thing.description
            else:
                icon = "📜"
                owned = any(ob.blueprint_id == thing.blueprint_id for ob in self.player.blueprints)
                name  = thing.result_name + (" ✓" if owned else "")
                tp    = "⚔" if thing.result_type == "weapon" else "🛡"
                sub   = f"{tp} {thing.result_desc[:45]}"

            name_clr = (160, 160, 160) if (self.tab == "blueprints" and
                        any(ob.blueprint_id == thing.blueprint_id for ob in self.player.blueprints)) else COLOR_TEXT
            if self.tab == "items":
                draw_icon(screen, thing.item_id, thing.icon, r.x + 8, r.y + 6, size=24)
                screen.blit(font.render(name, True, name_clr), (r.x + 36, r.y + 6))
            else:
                screen.blit(font.render(f"{icon} {name}", True, name_clr), (r.x + 10, r.y + 6))
            screen.blit(font_sm.render(sub, True, COLOR_TEXT_DIM), (r.x + 14, r.y + 30))

            # Ціна
            price_clr = COLOR_GOLD if self.player.gold >= price else COLOR_ERROR
            p_surf = font.render(f"{price}🪙", True, price_clr)
            screen.blit(p_surf, (r.right - p_surf.get_width() - 12, r.y + 14))

        # Лічильник
        total = len(self._rows())
        cnt = font_sm.render(
            f"{self.scroll + 1}–{min(self.scroll + VISIBLE, total)} з {total}",
            True, COLOR_TEXT_DIM)
        screen.blit(cnt, (LIST_X, LIST_Y + VISIBLE * ROW_H + 6))

    def _draw_scrollbar(self, screen):
        rows  = self._rows()
        total = len(rows)
        if total <= VISIBLE:
            return
        bar_h  = VISIBLE * ROW_H
        bar_x  = LIST_X + LIST_W + 6
        thumb_h = max(30, bar_h * VISIBLE // total)
        thumb_y = LIST_Y + (bar_h - thumb_h) * self.scroll // max(1, total - VISIBLE)
        pygame.draw.rect(screen, (40, 38, 30), (bar_x, LIST_Y, 8, bar_h), border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD,   (bar_x, thumb_y, 8, thumb_h), border_radius=4)

    def _draw_info(self, screen):
        """Панель деталей вибраного товару."""
        rows    = self._rows()
        abs_idx = self.scroll + self.sel
        if self.sel == -1 or abs_idx >= len(rows):
            # Підказка
            font = assets.get_font(FONT_SIZE_SMALL)
            hint = font.render("← Вибери товар щоб побачити деталі", True, COLOR_TEXT_DIM)
            screen.blit(hint, (INFO_X, LIST_Y + 20))
            return

        thing, price = rows[abs_idx]

        # Панель
        panel_h = SCREEN_HEIGHT - LIST_Y - 70
        info_surf = pygame.Surface((INFO_W, panel_h), pygame.SRCALPHA)
        info_surf.fill((15, 12, 8, 210))
        pygame.draw.rect(info_surf, COLOR_GOLD, info_surf.get_rect(), 1, border_radius=8)
        screen.blit(info_surf, (INFO_X, LIST_Y))

        px, py = INFO_X + 14, LIST_Y + 14
        font_h  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        font    = assets.get_font(FONT_SIZE_NORMAL)
        font_sm = assets.get_font(FONT_SIZE_SMALL)

        if self.tab == "items":
            self._draw_item_info(screen, thing, price, px, py, font_h, font, font_sm)
        else:
            self._draw_bp_info(screen, thing, price, px, py, font_h, font, font_sm)

    def _draw_item_info(self, screen, item, price, px, py, fh, f, fsm):
        draw_icon(screen, item.item_id, item.icon, px, py, size=32)
        screen.blit(fh.render(item.name, True, COLOR_GOLD), (px + 38, py + 4));  py += 38

        lines = [item.description, ""]
        if item.item_type == "weapon":
            lines.append(f"⚔ Атака: +{item.attack_bonus}")
        elif item.item_type == "armor":
            lines.append(f"🛡 Захист: +{item.defense_bonus}")
            if item.hp_bonus:
                lines.append(f"❤ HP: +{item.hp_bonus}")
        elif item.item_type == "potion":
            if item.hp_restore:
                lines.append(f"🧪 Відновлює: {item.hp_restore} HP")
            if item.attack_bonus:
                lines.append(f"⚔ Атака: +{item.attack_bonus}")
        lines += ["", f"Ціна: {price} 🪙"]
        if self.player.gold < price:
            lines.append("⚠ Недостатньо золота!")

        for line in lines:
            clr = COLOR_ERROR if line.startswith("⚠") else COLOR_TEXT
            screen.blit(fsm.render(line, True, clr), (px, py));  py += 22

    def _draw_bp_info(self, screen, bp, price, px, py, fh, f, fsm):
        tp_icon = "⚔" if bp.result_type == "weapon" else "🛡"
        screen.blit(fh.render(f"{bp.result_icon} {bp.result_name}", True, COLOR_GOLD), (px, py)); py += 30
        screen.blit(fsm.render(bp.result_desc, True, COLOR_TEXT_DIM), (px, py));                  py += 22

        # Тип і базові стати
        py += 6
        if bp.result_type == "weapon":
            screen.blit(fsm.render(f"⚔ Атака: +{bp.result_attack}", True, COLOR_TEXT), (px, py)); py += 20
        else:
            screen.blit(fsm.render(f"🛡 Захист: +{bp.result_defense}", True, COLOR_TEXT), (px, py)); py += 20
            if bp.result_hp:
                screen.blit(fsm.render(f"❤ HP: +{bp.result_hp}", True, COLOR_TEXT), (px, py));    py += 20

        # Бонус від матеріалу
        if bp.bonus_material:
            mat = MATERIALS.get(bp.bonus_material)
            if mat:
                py += 4
                screen.blit(fsm.render("✦ Бонус матеріалу:", True, (200, 180, 100)), (px, py)); py += 18
                qty = bp.recipe.get(bp.bonus_material, 1)
                parts = []
                if mat.bonus_attack:  parts.append(f"+{mat.bonus_attack * qty} ATK")
                if mat.bonus_defense: parts.append(f"+{mat.bonus_defense * qty} DEF")
                if mat.bonus_hp:      parts.append(f"+{mat.bonus_hp * qty} HP")
                if mat.bonus_crit:    parts.append(f"+{mat.bonus_crit * qty * 100:.0f}% крит")
                bonus_txt = f"  {mat.icon} {mat.name} ×{qty}: {', '.join(parts)}"
                screen.blit(fsm.render(bonus_txt, True, (160, 220, 160)), (px, py)); py += 20

        # Рецепт
        py += 8
        screen.blit(fsm.render("📋 Рецепт:", True, COLOR_GOLD), (px, py)); py += 18
        for mat_id, qty in bp.recipe.items():
            mat = MATERIALS.get(mat_id)
            if not mat:
                continue
            has  = self.player.materials.get(mat_id, 0)
            clr  = (100, 220, 100) if has >= qty else COLOR_ERROR
            draw_icon(screen, mat_id, mat.icon, px + 4, py, size=16)
            screen.blit(fsm.render(f" {mat.name}: {has}/{qty}", True, clr), (px + 22, py)); py += 18

        # Статус куплений
        py += 6
        owned = any(ob.blueprint_id == bp.blueprint_id for ob in self.player.blueprints)
        if owned:
            screen.blit(fsm.render("✓ Вже куплено", True, (100, 220, 100)), (px, py)); py += 20
        else:
            clr = COLOR_GOLD if self.player.gold >= price else COLOR_ERROR
            screen.blit(fsm.render(f"Ціна: {price} 🪙", True, clr), (px, py)); py += 20
            if self.player.gold < price:
                screen.blit(fsm.render("⚠ Недостатньо золота!", True, COLOR_ERROR), (px, py))