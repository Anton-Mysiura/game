"""
Майстерня — крафт зброї/броні з таймером, переплавка руди.
Черга до 3 слотів. Офлайн-прогрес через unix timestamps.
"""
import logging
log = logging.getLogger(__name__)

import math
import pygame
from .base import SceneWithBackground, SceneWithButtons
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.data import MATERIALS, BLUEPRINTS
from game.crafting_queue import get_craft_time, fmt_time
from game.save_manager import autosave
from ui.icons import draw_icon, get_icon_surf
from game.free_craft import (
    FreeCraftRecipe, SlotIngredients,
    calc_multiplier, calc_bonuses, calc_item_stats,
    calc_item_value, calc_craft_time, generate_item_name,
    MIN_TOTAL_MATS,
)

# ══════════════════════════════════════════════════════════════════
#  LAYOUT — всі координати розраховані під 1280×720
#  Зони зверху вниз:
#   [0–36]   Заголовок
#   [38–74]  Вкладки (tabs)
#   [82–506] Контент (425px)
#   [515–669] Черга крафту
#   [676–720] Нижня панель (Exit)
# ══════════════════════════════════════════════════════════════════
_SW, _SH = 1280, 720          # еталонний розмір (virtual surface)

HEADER_Y   = 6
TABS_Y     = 38
TABS_H     = 36
CONTENT_Y  = TABS_Y + TABS_H + 8    # 82
EXIT_Y     = _SH - 40               # 680
EXIT_H     = 36
QUEUE_H    = 157
QUEUE_Y    = EXIT_Y - 6 - QUEUE_H   # 517
CONTENT_H  = QUEUE_Y - CONTENT_Y - 8  # 427
_MARGIN    = 30

# ── Кресленики / Переплавка / Розбирання layout ────────────────────
ROW_H   = 52
LIST_X  = _MARGIN
LIST_W  = 580
LIST_Y  = CONTENT_Y + 4
VISIBLE = CONTENT_H // ROW_H        # ~8 рядків

INFO_X  = LIST_X + LIST_W + 20
INFO_W  = _SW - INFO_X - _MARGIN

QUEUE_X = _MARGIN
QUEUE_W = _SW - _MARGIN * 2

# ── Вільний крафт layout ──────────────────────────────────────────
# Ліва частина: два слоти (половина екрану)
# Права частина: список матеріалів
_FC_LEFT_W   = _SW // 2 - _MARGIN      # ≈ 610px

_FC_SWITCHER_H = 28
FC_SWITCHER_Y  = CONTENT_Y + 4         # 86 — перемикач Зброя/Броня
FC_SLOTS_X     = _MARGIN
FC_SLOTS_Y     = FC_SWITCHER_Y + _FC_SWITCHER_H * 4 + 12

FC_SLOT_GAP  = 12
FC_SLOT_W    = (_FC_LEFT_W - FC_SLOT_GAP) // 2   # ≈ 299px

# Висота слоту
_FC_PREVIEW_H  = 86
_FC_FORGE_H    = 40
_FC_GAPS       = 4 + 6 + 6
FC_SLOT_H = (CONTENT_H
             - _FC_SWITCHER_H
             - _FC_PREVIEW_H
             - _FC_FORGE_H
             - _FC_GAPS)                # ≈ 255px

# Права частина: список матеріалів
FC_MAT_X     = _SW // 2 + 8
FC_MAT_W     = _SW - FC_MAT_X - _MARGIN
FC_MAT_HDR_Y = CONTENT_Y + 2        # заголовок "📦 Матеріали"
FC_MAT_SUB_Y = CONTENT_Y + 22       # підзаголовок "активний слот"
FC_MAT_Y     = CONTENT_Y + 44       # перший рядок списку (після заголовків)
FC_ROW_H     = 34
FC_VISIBLE   = (QUEUE_Y - FC_MAT_Y - 6) // FC_ROW_H   # ≈ 11

# Позиції превью і кнопки "Викувати"
FC_PREVIEW_Y = FC_SLOTS_Y + FC_SLOT_H + 6
FC_PREVIEW_H = _FC_PREVIEW_H
FC_FORGE_X   = FC_SLOTS_X
FC_FORGE_Y   = FC_PREVIEW_Y + FC_PREVIEW_H + 6
FC_FORGE_W   = FC_SLOT_W * 2 + FC_SLOT_GAP
FC_FORGE_H   = _FC_FORGE_H

SMELT_RECIPES = [
    ("iron_ore",   2, "iron_bar",   1, "Залізний зливок"),
    ("silver_ore", 2, "silver_bar", 1, "Срібний зливок"),
    ("mithril_ore",2, "mithril_bar",1, "Мітриловий зливок"),
    ("bone",       3, "bone_dust",  1, "Кісткова пудра"),
]

# Кольори черги за часом що залишився
def queue_color(pct_done: float) -> tuple:
    """pct_done: 0=тільки почали, 1=готово"""
    if pct_done >= 1.0: return (100, 220, 100)
    if pct_done >= 0.7: return (180, 220, 80)
    if pct_done >= 0.4: return (220, 180, 60)
    return (180, 100, 60)


# UI-методи (_draw_*) винесено у workshop_ui.py
# Тут тільки логіка: стан, події, дії
from scenes.workshop_ui import WorkshopUIMixin


class WorkshopScene(WorkshopUIMixin, SceneWithBackground, SceneWithButtons):

    def __init__(self, game):
        SceneWithBackground.__init__(self, game, "workshop")
        SceneWithButtons.__init__(self, game)

        self.mode   = "craft"
        self.sel    = -1
        self.scroll = 0
        self.craft_msg    = ""
        self.craft_msg_t  = 0.0
        self._msg_error   = False
        self._msg_mutation = None
        self._anim_t      = 0.0   # для анімації
        self._confirm     = None  # модальне підтвердження

        # ── Вільний крафт ──────────────────────────────────────────
        self._fc_recipe     = FreeCraftRecipe("weapon")
        self._fc_active     = "blade"
        self._fc_mat_scroll = 0
        self._fc_hovered    = -1
        self._fc_blueprint  = None   # вибраний OwnedBlueprint
        self._fc_bp_scroll  = 0

        # ── WOW-ефект при першому крафті ──────────────────────
        self._wow_item      = None
        self._wow_timer     = 0.0
        self._wow_anim      = 0.0

        # ── Онбординг ──────────────────────────────────────────
        self._ob_active = (self.game.scene_data.get("onboarding_step") == "workshop")
        self._ob_step   = 0
        self._ob_anim   = 0.0
        if self._ob_active:
            self.mode = "free_craft"

        self._create_buttons()
        self.main_panel = Panel(_MARGIN - 2, 2, _SW - (_MARGIN - 2) * 2, _SH - 4, alpha=True)

    def _create_buttons(self):
        tab_w, tab_gap = 156, 6
        self.mode_btns = [
            Button(LIST_X + i * (tab_w + tab_gap), TABS_Y, tab_w, TABS_H, lbl,
                   lambda m=mode: self._switch(m))
            for i, (lbl, mode) in enumerate([
                ("⚒ Вільний крафт", "free_craft"),
                ("📜 Кресленики",    "craft"),
                ("🪨 Переплавка",    "smelt"),
                ("🔧 Розбирання",    "dismantle"),
            ])
        ]
        self.action_btn = Button(INFO_X, QUEUE_Y - 58, INFO_W, 46,
                                 "⚒ Почати крафт", self._perform_action)
        self.collect_btn = Button(QUEUE_X + QUEUE_W - 202, QUEUE_Y + QUEUE_H - 40, 196, 32,
                                  "📦 Забрати готове", self._collect_all_done)
        self.exit_btn = Button(LIST_X, EXIT_Y, 150, EXIT_H, "← Вийти",
                               lambda: self.game.change_scene("village"))
        self.buttons = self.mode_btns + [self.action_btn, self.collect_btn, self.exit_btn]

    def _switch(self, mode):
        self.mode   = mode
        self.sel    = -1
        self.scroll = 0
        self._fc_mat_scroll = 0
        labels = {
            "free_craft": "⚒ Викувати",
            "craft":      "⚒ Почати крафт",
            "smelt":      "🔥 Переплавити",
            "dismantle":  "🔧 Розібрати",
        }
        self.action_btn.text = labels.get(mode, "OK")
        # Ховаємо action_btn для free_craft (у нього окрема кнопка)
        self.action_btn.visible = (mode != "free_craft")

    # ── Дії ───────────────────────────────────────────────────────

    def _perform_action(self):
        if self.mode == "free_craft":
            self._do_free_craft()
        elif self.mode == "craft":
            self._start_craft()
        elif self.mode == "smelt":
            self._smelt()
        else:
            self._start_dismantle()


    # ── Вільний крафт: дії ────────────────────────────────────────

    def _do_free_craft(self):
        """Запускає вільний крафт (потребує кресленика)."""
        ob = self._fc_blueprint
        if ob is None:
            self._msg("⚠ Спочатку вибери кресленик!", error=True)
            return
        if ob.is_broken:
            self._msg("⚠ Цей кресленик зламаний!", error=True)
            self._fc_blueprint = None
            return

        r = self._fc_recipe
        if not r.is_valid():
            self._msg(f"⚠ Додайте мінімум {MIN_TOTAL_MATS} матеріали!", error=True)
            return
        if r.blade.is_empty():
            self._msg("⚠ Слот 'Лезо/Основа' порожній!", error=True)
            return
        ok, err = r.can_afford(self.player.materials)
        if not ok:
            self._msg(f"⚠ {err}", error=True)
            return
        q = self.player.crafting_queue
        if len(q.orders) >= q.MAX_SLOTS:
            self._msg("⚠ Черга майстерні повна!", error=True)
            return

        bp    = ob.blueprint
        from game.free_craft import calc_item_stats, calc_craft_time, calc_item_value
        from game.data import Item
        stats = calc_item_stats(r)
        value = calc_item_value(r)
        import time as _t
        item_id = f"free_{bp.result_id}_{int(_t.time())}"

        if bp.result_type == "armor":
            item = Item(item_id, bp.result_name, "armor", value,
                        bp.result_icon,
                        f"Виковано власноруч (×{stats['multiplier']:.2f})",
                        defense_bonus=stats["defense"],
                        hp_bonus=stats["hp"], crit_bonus=stats["crit"])
        elif bp.result_type == "tool":
            item = Item(item_id, bp.result_name, "tool", value,
                        bp.result_icon, bp.result_desc)
        else:
            item = Item(item_id, bp.result_name, "weapon", value,
                        bp.result_icon,
                        f"Виковано власноруч (×{stats['multiplier']:.2f})",
                        attack_bonus=stats["attack"], crit_bonus=stats["crit"])

        from game.mutations import roll_mutation, apply_mutation
        mut_id = roll_mutation(bp.result_type)
        if mut_id:
            apply_mutation(item, mut_id)

        self.player.consume_materials(r.all_mats())
        ob.use_one()
        if ob.is_broken:
            try: self.player.blueprints.remove(ob)
            except ValueError: pass
            self._fc_blueprint = None
            uses_msg = " | 💥 Кресленик зламався!"
        else:
            uses_msg = f" | лишилось: {ob.uses_left}"

        from game.save_manager import _serialize_item
        from game.crafting_queue import CraftOrder
        import time as _time
        duration  = calc_craft_time(r)
        finish_at = _time.time() + duration
        order = CraftOrder(bp.blueprint_id, finish_at, _serialize_item(item))
        self.player.crafting_queue.orders.append(order)

        autosave(self.player)
        t = fmt_time(duration)
        self._msg(f"⚒ {bp.result_name} — у кузні! ({t}){uses_msg}")
        self._fc_recipe = FreeCraftRecipe(r.result_type)

    def _fc_add_mat(self, mat_id: str, qty: int = 1):
        """Додає матеріал до активного слоту вільного крафту."""
        mat = MATERIALS.get(mat_id)
        if not mat:
            return
        slot_name = self._fc_active
        slot = self._fc_recipe.blade if slot_name == "blade" else self._fc_recipe.handle
        if slot_name == "blade" and not mat.is_metal:
            self._msg("⚠ У слот 'Лезо' можна тільки метали!", error=True)
            return
        current_in_recipe = self._fc_recipe.all_mats().get(mat_id, 0)
        have = self.player.materials.get(mat_id, 0)
        if current_in_recipe + qty > have:
            available = have - current_in_recipe
            if available <= 0:
                self._msg(f"⚠ {mat.name} закінчилось!", error=True)
                return
            qty = available
        slot.add(mat_id, qty)

    def _fc_remove_mat(self, mat_id: str, slot_name: str, qty: int = 1):
        """Прибирає матеріал зі слоту."""
        slot = self._fc_recipe.blade if slot_name == "blade" else self._fc_recipe.handle
        slot.remove(mat_id, qty)

    def _fc_clear_slot(self, slot_name: str):
        """Очищає слот повністю."""
        if slot_name == "blade":
            self._fc_recipe.blade.clear()
        else:
            self._fc_recipe.handle.clear()

    def _fc_set_type(self, result_type: str):
        """Змінює тип предмета, скидає рецепт."""
        self._fc_recipe = FreeCraftRecipe(result_type)

    def _start_craft(self):
        if self.sel == -1:
            return
        bps = self.player.blueprints
        abs_idx = self.scroll + self.sel
        if abs_idx >= len(bps):
            return
        ob = bps[abs_idx]   # OwnedBlueprint
        bp = ob.blueprint

        q = self.player.crafting_queue
        if len(q.orders) >= q.MAX_SLOTS:
            self._msg("⚠ Черга майстерні повна! (макс. 3 слоти)", error=True)
            return
        if ob.is_broken:
            self._msg("⚠ Кресленик зламаний!", error=True)
            return
        if not bp.can_craft(self.player.materials):
            self._msg("⚠ Недостатньо матеріалів!", error=True)
            return

        order = self.player.craft_weapon(ob)
        if order:
            autosave(self.player)
            t = fmt_time(get_craft_time(bp.blueprint_id))
            uses_left = ob.uses_left  # вже зменшено після use_one()
            uses_msg = f" | лишилось використань: {uses_left}" if not ob.is_broken else " | 💥 Кресленик зламався!"
            self._msg(f"⚒ {bp.result_name} — у кузні! ({t}){uses_msg}")
        else:
            self._msg("⚠ Помилка крафту", error=True)

    def _collect_done(self):
        items = self.player.collect_crafted()
        if not items:
            return
        autosave(self.player)
        is_first = (self.player.items_crafted == 0)
        self.player.items_crafted += len(items)
        from game.achievements import AchievementManager
        AchievementManager.check_all(self.player)
        from game.mutations import get_mutation
        for item in items:
            mut = get_mutation(item)
            if mut:
                self._msg(f"✦ {item.name}  [{mut.rarity.upper()}]!", mutation=mut)
            else:
                self._msg(f"✓ {item.name} готово!")
            # WOW при першому крафті
            if is_first:
                self._wow_item  = item
                self._wow_timer = 3.5
                self._wow_anim  = 0.0
                is_first = False

    def _collect_dismantled(self):
        results = self.player.collect_dismantled()
        if not results:
            return
        autosave(self.player)
        from game.data import MATERIALS
        for item_name, mats in results:
            if mats:
                parts = []
                for mat_id, qty in mats.items():
                    mat = MATERIALS.get(mat_id)
                    parts.append(f"{mat.icon if mat else '?'}{qty}")
                self._msg(f"🔧 {item_name}: {' '.join(parts)}")
            else:
                self._msg(f"🔧 {item_name}: нічого не вийшло...", error=True)

    def _start_dismantle(self):
        items = self._dismantle_items()
        if self.sel < 0 or self.sel >= len(items):
            return
        item = items[self.sel]

        from game.crafting_queue import dismantle_cost, dismantle_time, fmt_time, DISMANTLE_RETURN, _item_tier
        from ui.confirm_dialog import ConfirmDialog

        if item.value >= 60:
            cost = dismantle_cost(item)
            tier = _item_tier(item)
            pct  = int(DISMANTLE_RETURN[tier] * 100)
            t    = fmt_time(dismantle_time(item))
            from game.mutations import get_mutation
            mut  = get_mutation(item)
            mut_line = f"\n✦ Мутація: {mut.name}" if mut else ""

            def _do():
                ok, msg = self.player.start_dismantle(item)
                self._msg(msg, error=not ok)
                if ok:
                    autosave(self.player)
                    self.sel = -1

            self._confirm = ConfirmDialog(
                title   = "Розібрати предмет?",
                body    = (f"{item.icon} {item.name}{mut_line}\n"
                           f"Вартість: {cost} 🪙   Час: {t}\n"
                           f"Повернення матеріалів: ~{pct}%"),
                yes_lbl = f"🔧 Розібрати ({cost} 🪙)",
                no_lbl  = "Назад",
                on_yes  = _do,
                danger  = True,
            )
        else:
            ok, msg = self.player.start_dismantle(item)
            self._msg(msg, error=not ok)
            if ok:
                autosave(self.player)
                self.sel = -1

    def _smelt(self):
        if self.sel == -1 or self.sel >= len(SMELT_RECIPES):
            return
        from_mat, from_qty, to_mat, to_qty, label = SMELT_RECIPES[self.sel]
        have    = self.player.materials.get(from_mat, 0)
        batches = have // from_qty
        if batches == 0:
            self._msg(f"⚠ Потрібно мінімум {from_qty} одиниць!", error=True)
            return
        self.player.materials[from_mat] = have - batches * from_qty
        self.player.add_material(to_mat, batches * to_qty)
        autosave(self.player)
        self._msg(f"✓ Переплавлено → {batches} × {label}")

    def _msg(self, text, error=False, mutation=None):
        self.craft_msg     = text
        self.craft_msg_t   = 3.0
        self._msg_error    = error
        self._msg_mutation = mutation
        # Також тост
        from ui.notifications import notify
        if mutation:
            notify(text, kind="mutation", duration=3.5,
                   extra_color=mutation.color)
        elif error:
            notify(text, kind="error", duration=2.5)
        else:
            notify(text, kind="craft", duration=2.5)

    # ── Події ─────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        # WOW overlay перехоплює кліки
        if self._wow_timer > 0:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self._wow_timer = 0.0; return
        # Онбординг перехоплює
        if self._ob_active:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._ob_next(); return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mp = pygame.mouse.get_pos()
                pw, ph = 520, 310
                px = SCREEN_WIDTH - pw - 20
                py = SCREEN_HEIGHT // 2 - ph // 2
                btn_r = pygame.Rect(px + pw - 160, py + ph - 46, 146, 36)
                if btn_r.collidepoint(mp):
                    self._ob_next(); return
        if self._confirm:
            self._confirm.handle_event(event)
            if self._confirm.done:
                self._confirm = None
            return

        # Вільний крафт — окрема обробка
        if self.mode == "free_craft":
            self._fc_handle_event(event)
            # Дозволяємо exit_btn теж спрацювати
            super().handle_event(event)
            return

        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mp = pygame.mouse.get_pos()
            if event.button == 1:
                rows = self._row_count()
                for i in range(min(VISIBLE, rows - self.scroll)):
                    r = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)
                    if r.collidepoint(mp):
                        self.sel = i; break
            elif event.button == 4:
                self.scroll = max(0, self.scroll - 1); self.sel = -1
            elif event.button == 5:
                mx = max(0, self._row_count() - VISIBLE)
                self.scroll = min(mx, self.scroll + 1); self.sel = -1

    def _fc_handle_event(self, event: pygame.event.Event):
        """Обробка подій для вільного крафту."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mp = pygame.mouse.get_pos()
            b  = event.button
            self._fc_handle_click(mp, b)
        elif event.type == pygame.MOUSEMOTION:
            self._fc_hovered = self._fc_mat_at(pygame.mouse.get_pos())

    def _fc_mat_at(self, mp) -> int:
        """Повертає індекс матеріалу у списку під мишею, або -1."""
        mat_list = self._fc_visible_mats()
        for i, _ in enumerate(mat_list):
            r = pygame.Rect(FC_MAT_X, FC_MAT_Y + i * FC_ROW_H, FC_MAT_W, FC_ROW_H - 3)
            if r.collidepoint(mp):
                return i
        return -1

    def _fc_visible_mats(self) -> list:
        """Матеріали у гравця, що підходять для активного слоту, зі скролом."""
        slot = self._fc_active
        all_mats = sorted(
            [(mid, qty) for mid, qty in self.player.materials.items()
             if qty > 0 and (slot != "blade" or MATERIALS.get(mid, None) and MATERIALS[mid].is_metal)],
            key=lambda x: (
                ["legendary","epic","rare","uncommon","common"].index(
                    MATERIALS[x[0]].rarity if x[0] in MATERIALS else "common"),
                MATERIALS[x[0]].name if x[0] in MATERIALS else x[0]
            )
        )
        return all_mats[self._fc_mat_scroll: self._fc_mat_scroll + FC_VISIBLE]

    def _fc_handle_click(self, mp, button):
        """Обробка кліків у вільному крафті."""
        from game.data import BP_RARITY_COLORS
        fsm    = assets.get_font(FONT_SIZE_SMALL)
        px     = FC_SLOTS_X
        row_y  = FC_SWITCHER_Y + 28
        bps    = [o for o in self.player.blueprints
                  if o.blueprint.result_type in ("weapon","armor","tool")
                  and not o.is_broken]
        scroll = self._fc_bp_scroll
        vis    = bps[scroll:scroll+8]
        if button == 1:
            for i, ob_i in enumerate(vis):
                bp_i  = ob_i.blueprint
                btn_w = max(80, fsm.render(bp_i.result_name[:12], True, (0,0,0)).get_width()+20)
                btn_r = pygame.Rect(px+8+i*(btn_w+4), row_y, btn_w, _FC_SWITCHER_H*3-6)
                if btn_r.collidepoint(mp):
                    self._fc_select_blueprint(ob_i); return

        # Вибір активного слоту
        blade_header  = pygame.Rect(FC_SLOTS_X, FC_SLOTS_Y, FC_SLOT_W, 36)
        handle_header = pygame.Rect(FC_SLOTS_X + FC_SLOT_W + FC_SLOT_GAP, FC_SLOTS_Y, FC_SLOT_W, 36)
        if button == 1:
            if blade_header.collidepoint(mp):
                self._fc_active = "blade"; return
            if handle_header.collidepoint(mp):
                self._fc_active = "handle"; return

        # Клік на матеріал у списку
        mat_list = self._fc_visible_mats()
        for i, (mid, _) in enumerate(mat_list):
            r = pygame.Rect(FC_MAT_X, FC_MAT_Y + i * FC_ROW_H, FC_MAT_W, FC_ROW_H - 3)
            if r.collidepoint(mp):
                if button == 1:
                    self._fc_add_mat(mid, 1)
                elif button == 3:   # ПКМ — додає ×5
                    self._fc_add_mat(mid, 5)
                return

        # Скрол списку матеріалів
        mat_area = pygame.Rect(FC_MAT_X, FC_MAT_Y, FC_MAT_W, FC_VISIBLE * FC_ROW_H)
        if mat_area.collidepoint(mp):
            if button == 4:
                self._fc_mat_scroll = max(0, self._fc_mat_scroll - 1)
            elif button == 5:
                all_count = sum(1 for mid, qty in self.player.materials.items()
                                if qty > 0 and (self._fc_active != "blade"
                                                or MATERIALS.get(mid) and MATERIALS[mid].is_metal))
                self._fc_mat_scroll = min(max(0, all_count - FC_VISIBLE),
                                          self._fc_mat_scroll + 1)
            return

        # Кнопка "Викувати"
        forge_btn = pygame.Rect(FC_FORGE_X, FC_FORGE_Y, FC_FORGE_W, FC_FORGE_H)
        if button == 1 and forge_btn.collidepoint(mp):
            self._do_free_craft(); return

        # ПКМ / скрол у слотах — видалення
        for slot_name, slot_x in (("blade", FC_SLOTS_X),
                                   ("handle", FC_SLOTS_X + FC_SLOT_W + FC_SLOT_GAP)):
            slot_obj = (self._fc_recipe.blade if slot_name == "blade"
                        else self._fc_recipe.handle)
            items = list(slot_obj.mats.items())
            for j, (mid, qty) in enumerate(items):
                item_r = pygame.Rect(slot_x + 6, FC_SLOTS_Y + 44 + j * 28, FC_SLOT_W - 12, 26)
                if item_r.collidepoint(mp):
                    if button == 3:   # ПКМ — прибрати ×1
                        self._fc_remove_mat(mid, slot_name, 1)
                    elif button == 1 and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self._fc_remove_mat(mid, slot_name, qty)  # Shift+ЛКМ — всі
                    return
            # Кнопка "Очистити слот"
            clear_r = pygame.Rect(slot_x + FC_SLOT_W - 85, FC_SLOTS_Y + 4, 80, 26)
            if button == 1 and clear_r.collidepoint(mp):
                self._fc_clear_slot(slot_name); return

    def _ob_next(self):
        if self._ob_step < 5:
            self._ob_step += 1
            self._ob_anim  = 0.0
        if self._ob_step >= 5:
            self._ob_active = False
            self.game.scene_data.pop("onboarding_step", None)
            self.game.scene_data["onboarding_step"] = "village"
            from game.save_manager import autosave
            autosave(self.player)
            self.game.change_scene("village")

    def _fc_select_blueprint(self, ob):
        self._fc_blueprint = ob
        if ob is not None:
            bp    = ob.blueprint
            rtype = bp.result_type if bp.result_type in ("weapon","armor") else "weapon"
            self._fc_recipe = FreeCraftRecipe(rtype)
            self._fc_active = "blade"

    def _fc_set_type(self, result_type: str):
        self._fc_recipe = FreeCraftRecipe(result_type)

    def update(self, dt: float):
        if self._confirm:
            self._confirm.update(dt)
        super().update(dt)
        self._anim_t += dt
        if self._ob_active:
            self._ob_anim += dt
        if self._wow_timer > 0:
            self._wow_timer -= dt
            self._wow_anim  += dt
        if self.craft_msg_t > 0:
            self.craft_msg_t -= dt
        # auto-collect handled by queue

    def _row_count(self):
        if self.mode == "craft":    return len(self.player.blueprints)
        if self.mode == "smelt":    return len(SMELT_RECIPES)
        return len(self._dismantle_items())

    def _dismantle_items(self):
        """Предмети інвентарю що можна розібрати (зброя і броня)."""
        return [i for i in self.player.inventory
                if getattr(i, "item_type", "") in ("weapon", "armor")]

    # ── Малювання ─────────────────────────────────────────────────

    def update(self, dt: float):
        """Оновлення стану майстерні."""
        super().update(dt)
        if self._wow_timer > 0:
            self._wow_timer -= dt
            self._wow_anim  += dt
        if self.craft_msg_t > 0:
            self.craft_msg_t -= dt
        # auto-collect handled by queue

    def _row_count(self):
        if self.mode == "craft":    return len(self.player.blueprints)
        if self.mode == "smelt":    return len(SMELT_RECIPES)
        return len(self._dismantle_items())

    def _dismantle_items(self):
        """Предмети доступні для розбирання."""
        return [item for item in self.player.inventory
                if getattr(item, "item_type", "") in ("weapon", "armor")]

    def _collect_all_done(self):
        """Забирає всі готові замовлення з черги."""
        self._collect_done()
        self._collect_dismantled()
