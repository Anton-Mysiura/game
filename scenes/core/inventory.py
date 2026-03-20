"""
Сцена інвентаря — фільтр і сортування через Dropdown.
"""
import logging
log = logging.getLogger(__name__)

import pygame
from .base import Scene
from ui.components import Button, Panel, InventoryGrid
from ui.constants import *
from ui.assets import assets
from ui.confirm_dialog import ConfirmDialog
from ui.dropdown import Dropdown
from game.save_manager import autosave
from ui.icons import draw_icon, get_icon_surf

CLR_BETTER = (100, 220, 100)
CLR_WORSE  = (220, 80,  80)
CLR_SAME   = (180, 180, 180)
CLR_NEW    = (120, 180, 255)

EXPENSIVE_THRESHOLD = 60
CMP_W = 580; CMP_H = 320
CMP_X = (SCREEN_WIDTH - CMP_W) // 2
CMP_Y = SCREEN_HEIGHT - CMP_H - 30
_RARITY_RANK = {"legendary":0,"epic":1,"rare":2,"uncommon":3,"common":4,"":5}

FILTER_OPTIONS = [
    ("all",      "📦 Все"),
    ("weapon",   "⚔  Зброя"),
    ("armor",    "🛡 Броня"),
    ("potion",   "🧪 Зілля"),
    ("tool",     "🛠 Інструменти"),
    ("material", "🪨 Матеріали"),
]
SORT_OPTIONS = [
    ("new",     "🕐 Новіші спочатку"),
    ("name",    "🔤 За назвою (А→Я)"),
    ("attack",  "⚔  За атакою ↓"),
    ("defense", "🛡 За захистом ↓"),
    ("rarity",  "✦  За рідкісністю"),
    ("value",   "💰 За ціною ↓"),
]

def _stat_color(d):
    return CLR_BETTER if d>0 else (CLR_WORSE if d<0 else CLR_SAME)
def _arrow(d):
    return "▲" if d>0 else ("▼" if d<0 else "=")



class InventoryScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.close_button  = Button(SCREEN_WIDTH - 230, 20, 200, 50, "Закрити", lambda: game.pop_scene())
        self.equip_button  = Button(SCREEN_WIDTH // 2 + 220, 460, 200, 46, "Екіпірувати", self._equip_selected)
        self.use_button    = Button(SCREEN_WIDTH // 2 + 220, 512, 200, 46, "Використати", self._use_selected)
        self.sell_button   = Button(SCREEN_WIDTH // 2 + 220, 564, 200, 46, "💰 Продати", self._sell_selected)
        self.dismantle_btn = Button(SCREEN_WIDTH // 2 + 220, 616, 200, 46, "🔧 Розібрати", self._dismantle_selected)
        self.heal_all_btn  = Button(100, SCREEN_HEIGHT - 70, 310, 44, "💊 Вжити зілля до макс. HP", self._heal_to_full)
        self.main_panel = Panel(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100, alpha=True)
        self.info_panel = Panel(SCREEN_WIDTH // 2 + 200, 200, 240, 290, alpha=True)
        self.cmp_panel  = Panel(CMP_X, CMP_Y, CMP_W, CMP_H, alpha=True)
        self._filter_dd = Dropdown(x=220, y=150, width=195, height=34,
            label="Фільтр", options=FILTER_OPTIONS,
            on_change=self._on_filter_change, initial="all")
        self._sort_dd = Dropdown(x=570, y=150, width=225, height=34,
            label="Сортування", options=SORT_OPTIONS,
            on_change=self._on_sort_change, initial="new")
        self.inventory_grid = InventoryGrid(100, 202, cols=5, rows=4)
        self._mat_scroll = 0
        self._show_compare = False
        self._confirm = None
        self._anim_t = 0.0
        self._tooltip_item = None   # предмет під курсором для tooltip
        self._tooltip_pos  = (0, 0)

        # Підключаємо renderer (малювання)
        from scenes.ui.inventory_renderer import InventoryRenderer
        self._renderer = InventoryRenderer(self)
    @property
    def _active_filter(self): return self._filter_dd.value
    @property
    def _active_sort(self): return self._sort_dd.value

    def _on_filter_change(self, val):
        self._mat_scroll = 0
        self.inventory_grid.selected_slot = -1

    def _on_sort_change(self, val):
        self.inventory_grid.selected_slot = -1

    def _filtered_items(self):
        inv = self.player.inventory
        f = self._active_filter
        items = list(inv) if f == "all" else [i for i in inv if i.item_type == f]
        return self._sorted_items(items)

    def _sorted_items(self, items):
        from game.mutations import get_mutation
        m = self._active_sort
        if m == "name":    return sorted(items, key=lambda x: x.name)
        if m == "attack":  return sorted(items, key=lambda x: x.attack_bonus, reverse=True)
        if m == "defense": return sorted(items, key=lambda x: x.defense_bonus, reverse=True)
        if m == "value":   return sorted(items, key=lambda x: x.value, reverse=True)
        if m == "rarity":
            def key(it):
                mut = get_mutation(it)
                return (_RARITY_RANK.get(mut.rarity if mut else "", 5), it.name)
            return sorted(items, key=key)
        return list(items)

    def _real_item(self):
        idx = self.inventory_grid.selected_slot
        fl  = self._filtered_items()
        return fl[idx] if 0 <= idx < len(fl) else None

    def _equip_selected(self):
        item = self._real_item()
        if item and item.item_type in ("weapon", "armor"):
            self.player.equip_item(item)
            autosave(self.player)

    def _use_selected(self):
        item = self._real_item()
        if item and item.item_type == "potion":
            if self.player.hp >= self.player.total_max_hp:
                from ui.notifications import notify
                notify("HP вже максимальне!", kind="error", duration=1.5); return
            msg = self.player.use_potion(item)
            from ui.notifications import notify
            notify(f"🧪 {msg}", kind="craft", duration=2.0)
            autosave(self.player)

    def _sell_selected(self):
        item = self._real_item()
        if not item: return
        price = max(1, item.value // 2)
        if item.value >= EXPENSIVE_THRESHOLD:
            from game.mutations import get_mutation
            mut = get_mutation(item)
            self._confirm = ConfirmDialog(
                title="Продати предмет?",
                body=f"{item.icon} {item.name}{chr(10) + chr(10054) + ' Мутація: ' + mut.name if mut else ''}\nЦіна: {price} 🪙",
                yes_lbl=f"💰 Продати за {price}", no_lbl="Назад",
                on_yes=lambda: self._do_sell(item, price), danger=True)
        else:
            self._do_sell(item, price)

    def _do_sell(self, item, price):
        if item not in self.player.inventory: return
        self.player.inventory.remove(item)
        if self.player.equipped_weapon is item: self.player.equipped_weapon = None
        if self.player.equipped_armor  is item: self.player.equipped_armor  = None
        self.player.gold += price
        self.player.total_gold_earned += price
        self.inventory_grid.selected_slot = -1
        autosave(self.player)
        from ui.notifications import notify
        notify(f"💰 Продано: {item.name}  +{price} 🪙", kind="gold", duration=2.5)

    def _dismantle_selected(self):
        item = self._real_item()
        if not item or item.item_type not in ("weapon", "armor"): return
        from game.crafting_queue import dismantle_cost, dismantle_time, fmt_time, DISMANTLE_RETURN, _item_tier
        cost = dismantle_cost(item)
        pct  = int(DISMANTLE_RETURN[_item_tier(item)] * 100)
        t    = fmt_time(dismantle_time(item))
        if item.value >= EXPENSIVE_THRESHOLD:
            from game.mutations import get_mutation
            mut = get_mutation(item)
            mut_line = f"\n\u2736 Мутація: {mut.name}" if mut else ""
            self._confirm = ConfirmDialog(
                title="Розібрати предмет?",
                body=f"{item.icon} {item.name}{mut_line}\nВартість: {cost} 🪙   Час: {t}\nПовернення: ~{pct}%",
                yes_lbl=f"🔧 Розібрати ({cost} 🪙)", no_lbl="Назад",
                on_yes=lambda: self._do_dismantle(item), danger=True)
        else:
            self._do_dismantle(item)

    def _do_dismantle(self, item):
        ok, msg = self.player.start_dismantle(item)
        autosave(self.player)
        from ui.notifications import notify
        notify(msg, kind="craft" if ok else "error", duration=2.5)

    def _heal_to_full(self):
        pots = [i for i in self.player.inventory if i.item_type=="potion" and i.hp_restore>0]
        if not pots:
            from ui.notifications import notify
            notify("Немає зілля здоров'я!", kind="error", duration=2.0); return
        if self.player.hp >= self.player.total_max_hp:
            from ui.notifications import notify
            notify("HP вже максимальне!", kind="error", duration=1.5); return
        used = healed = 0
        for p in pots[:]:
            if self.player.hp >= self.player.total_max_hp: break
            before = self.player.hp
            self.player.use_potion(p)
            healed += self.player.hp - before
            used += 1
        autosave(self.player)
        from ui.notifications import notify
        notify(f"💊 Використано {used} зілля  +{healed} HP", kind="craft", duration=3.0)

    def handle_event(self, event):
        if self._confirm:
            self._confirm.handle_event(event)
            if self._confirm.done: self._confirm = None
            return
        if self._filter_dd.handle_event(event): return
        if self._sort_dd.handle_event(event): return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            self.inventory_grid.update(mp, True)
            self.close_button.update(mp, True)
            self.equip_button.update(mp, True)
            self.use_button.update(mp, True)
            self.sell_button.update(mp, True)
            self.dismantle_btn.update(mp, True)
            self.heal_all_btn.update(mp, True)
            # Клік на "Продати непотрібне"
            junk = [i for i in self.player.inventory
                    if i.item_type not in ("potion",)
                    and i != self.player.equipped_weapon
                    and i != self.player.equipped_armor]
            if junk:
                font = assets.get_font(FONT_SIZE_SMALL)
                lbl  = f"🗑 Продати непотрібне ({len(junk)} шт, {sum(max(1,i.value//2) for i in junk)}🪙)"
                bx, by = 430, SCREEN_HEIGHT - 70
                bw = font.size(lbl)[0] + 20
                if pygame.Rect(bx, by, bw, 30).collidepoint(mp):
                    self._sell_junk()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            if self._active_filter == "material":
                mats = [v for v in self.player.materials.values() if v > 0]
                ms = max(0, len(mats) - 14)
                d  = -1 if event.button == 4 else 1
                self._mat_scroll = max(0, min(ms, self._mat_scroll + d))
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.pop_scene()

    def update(self, dt):
        self._anim_t += dt
        if self._confirm:
            self._confirm.update(dt); return
        mp = pygame.mouse.get_pos()
        self._filter_dd.update(mp)
        self._sort_dd.update(mp)
        self.inventory_grid.update(mp, False)
        self.close_button.update(mp, False)
        self.equip_button.update(mp, False)
        self.use_button.update(mp, False)
        self.sell_button.update(mp, False)
        self.dismantle_btn.update(mp, False)
        self.heal_all_btn.update(mp, False)
        item = self._real_item()
        self._show_compare = bool(item and item.item_type in ("weapon","armor"))

        # Tooltip — предмет під курсором (hovered, не selected)
        hov = self.inventory_grid.hovered_slot
        fl  = self._filtered_items()
        if hov != -1 and hov < len(fl) and hov != self.inventory_grid.selected_slot:
            self._tooltip_item = fl[hov]
            self._tooltip_pos  = mp
        else:
            self._tooltip_item = None

    def draw(self, screen):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)
    def _sell_junk(self):
        """Продає всі непотрібні предмети."""
        junk = [i for i in self.player.inventory
                if i.item_type not in ("potion",)
                and i != self.player.equipped_weapon
                and i != self.player.equipped_armor]
        if not junk:
            return
        total = sum(max(1, i.value // 2) for i in junk)
        for i in junk:
            self.player.inventory.remove(i)
        self.player.gold += total
        from ui.notifications import notify
        notify(f"🗑 Продано {len(junk)} предметів за {total}🪙", kind="gold", duration=2.5)
        from game.save_manager import autosave
        autosave(self.player)