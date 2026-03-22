"""
Адмін-панель (F12) — повністю переписана.
Таби, скрол, пошук, статистика гравця, hot-reload.
"""

import pygame
from .base import Scene
from ui.components import Button
from ui.constants import *
from ui.assets import assets
from game.data import OwnedBlueprint, MATERIALS, ITEMS, BLUEPRINTS
from game.save_manager import autosave

_W, _H     = 920, 620
_X         = (SCREEN_WIDTH  - _W) // 2
_Y         = (SCREEN_HEIGHT - _H) // 2
_TAB_H     = 44
_CONTENT_Y = _Y + _TAB_H + 56
_CONTENT_H = _H - _TAB_H - 56 - 60
_ROW_H     = 38
_COL_L     = _X + 16
_COL_R     = _X + _W // 2 + 8

_TABS = [
    ("Гравець",    "player"),
    ("Матеріали",  "materials"),
    ("Предмети",   "items"),
    ("Кресленики", "blueprints"),
    ("Бій",        "battle"),
    ("Скіп",       "skip"),
    ("Текстури",   "textures"),
    ("Система",    "system"),
]

_C_PANEL  = (28, 22, 14)
_C_HEADER = (45, 35, 20)
_C_ROW    = (38, 30, 18)
_C_ROW_H  = (60, 48, 28)
_C_SEL    = (80, 65, 25)
_C_BORDER = (100, 82, 45)
_C_GOLD   = (255, 215, 0)
_C_GREEN  = (70, 200, 90)
_C_RED    = (220, 70, 70)
_C_DIM    = (130, 115, 90)
_C_TEXT   = (220, 200, 170)


class AdminScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self._tab        = "player"
        self._scroll     = 0
        self._search     = ""
        self._input      = ""
        self._input_mode = ""
        self._msg        = ""
        self._msg_color  = _C_GREEN
        self._msg_timer  = 0.0
        self._hovered    = -1
        self._qty        = 10

        self._close_btn = Button(_X + _W - 120, _Y + _H - 52, 110, 40,
                                 "Закрити", lambda: self.game.pop_scene(), style="danger")

        # Кнопки вкладки "Гравець" — створюємо раз, щоб кліки працювали
        self._player_btns = self._build_player_btns()
        # Кнопки вкладок
        self._battle_btns = self._build_battle_btns()
        self._system_btns = self._build_system_btns()
        self._skip_btns   = self._build_skip_btns()

    # ── утиліти ───────────────────────────────────────────────────
        # Підключаємо renderer (малювання)
        from scenes.ui.admin_renderer import AdminRenderer
        self._renderer = AdminRenderer(self)
    def _switch_tab(self, key):
        self._tab = key
        self._scroll = 0
        self._search = ""
        self._input = ""
        self._input_mode = ""

    def _build_player_btns(self):
        bx, by = _COL_R, _CONTENT_Y + 36
        actions = [
            ("Відновити HP",        self._heal,                        "default"),
            ("+1000 золота",        lambda: self._quick(1000, "gold"), "gold"),
            ("+500 XP",             lambda: self._quick(500, "xp"),    "default"),
            ("+1 рівень",          self._level_up,                    "success"),
            ("ДАТИ ВСЕ",           self._give_all,                    "gold"),
            ("Очистити інвентар",  self._clear_inventory,             "danger"),
            ("Очистити матеріали", self._clear_materials,             "danger"),
        ]
        btns = []
        for label, fn_act, style in actions:
            btns.append(Button(bx, by, 300, 36, label, fn_act, style=style))
            by += 44
        return btns

    def _build_battle_btns(self):
        bx, by = _COL_R, _CONTENT_Y + 36
        actions = [
            ("Симулювати перемогу", self._win_battle,  "success"),
            ("Скинути статистику",  self._reset_stats, "danger"),
        ]
        btns = []
        for label, fn_act, style in actions:
            btns.append(Button(bx, by, 300, 36, label, fn_act, style=style))
            by += 44
        return btns

    def _build_system_btns(self):
        sy = _CONTENT_Y + 44
        actions = [
            ("Hot-reload (Ctrl+F5)", self._hot_reload,                                          "success"),
            ("Зберегти гру",         lambda: (autosave(self.player), self._notify("Збережено")), "default"),
        ]
        btns = []
        for label, fn_act, style in actions:
            btns.append(Button(_COL_L, sy, 380, 38, label, fn_act, style=style))
            sy += 48
        return btns

    def _build_skip_btns(self):
        """Кнопки пропуску очікувань — кожна одразу завершує таймер."""
        actions = [
            ("⚒ Завершити крафт",        self._skip_craft,        "success"),
            ("🔨 Завершити розбирання",   self._skip_dismantle,    "success"),
            ("🔄 Оновити ринок",          self._skip_market,       "success"),
            ("⛏ Завершити видобуток",    self._skip_miner,        "success"),
            ("🌙 Скинути відпочинок шахтаря", self._skip_miner_rest, "default"),
            ("📅 Оновити щоденні квести", self._skip_daily_quests, "success"),
            ("✅ ПРОПУСТИТИ ВСЕ",         self._skip_all,          "gold"),
        ]
        btns = []
        sy = _CONTENT_Y + 36
        for label, fn_act, style in actions:
            btns.append(Button(_COL_L, sy, 420, 40, label, fn_act, style=style))
            sy += 50
        return btns

    # ── skip дії ─────────────────────────────────────────────────
    def _skip_craft(self):
        q = getattr(self.player, "crafting_queue", None)
        if not q or not q.orders:
            self._notify("Черга крафту порожня", ok=False); return
        import time
        count = len(q.orders)
        for o in q.orders:
            o.finish_at = time.time() - 1
        autosave(self.player)
        self._notify(f"Крафт завершено ({count} замовлень)")

    def _skip_dismantle(self):
        q = getattr(self.player, "dismantle_queue", None)
        if not q or not q.orders:
            self._notify("Черга розбирання порожня", ok=False); return
        import time
        count = len(q.orders)
        for o in q.orders:
            o.finish_at = time.time() - 1
        autosave(self.player)
        self._notify(f"Розбирання завершено ({count} замовлень)")

    def _skip_market(self):
        m = getattr(self.player, "market", None)
        if not m:
            self._notify("Ринок не знайдено", ok=False); return
        m.next_refresh = 0.0
        autosave(self.player)
        self._notify("Ринок буде оновлено при наступному відкритті")

    def _skip_miner(self):
        mn = getattr(self.player, "miner", None)
        if not mn:
            self._notify("Шахтар не знайдено", ok=False); return
        import time
        if mn.end_time and mn.end_time > time.time():
            mn.end_time = time.time() - 1
            autosave(self.player)
            self._notify("Видобуток завершено!")
        else:
            self._notify("Шахтар зараз не працює", ok=False)

    def _skip_miner_rest(self):
        mn = getattr(self.player, "miner", None)
        if not mn:
            self._notify("Шахтар не знайдено", ok=False); return
        mn.start_time = None
        mn.end_time   = None
        if hasattr(mn, "status"):
            mn.status = getattr(mn, "STATUS_IDLE", "idle")
        autosave(self.player)
        self._notify("Відпочинок шахтаря скинуто")

    def _skip_daily_quests(self):
        dq = getattr(self.player, "daily_quests", None)
        if not dq:
            self._notify("Щоденні квести не знайдені", ok=False); return
        dq.today_str = ""
        dq.refresh_if_needed()
        autosave(self.player)
        self._notify("Щоденні квести оновлено!")

    def _skip_all(self):
        self._skip_craft()
        self._skip_dismantle()
        self._skip_market()
        self._skip_miner()
        self._skip_daily_quests()
        self._notify("Все пропущено!")

    def _notify(self, msg, ok=True):
        self._msg = msg
        self._msg_color = _C_GREEN if ok else _C_RED
        self._msg_timer = 3.0

    def _rows_area(self):
        return pygame.Rect(_COL_L, _CONTENT_Y, _W - 32, _CONTENT_H)

    def _max_scroll(self, total):
        return max(0, total * _ROW_H - _CONTENT_H)

    def _clip_scroll(self, total):
        self._scroll = max(0, min(self._scroll, self._max_scroll(total)))

    def _filtered(self, d):
        q = self._search.lower()
        if not q:
            return list(d.items())
        return [(k, v) for k, v in d.items()
                if q in getattr(v, "name", k).lower() or q in k.lower()]

    # ── дії ───────────────────────────────────────────────────────
    def _confirm_input(self):
        try:
            val = int(self._input) if self._input else 0
        except ValueError:
            self._notify("Невірне число!", ok=False); return
        m = self._input_mode
        if m == "gold":
            self.player.gold += val; self._notify(f"+{val} золота")
        elif m == "xp":
            self.player.xp += val; self._notify(f"+{val} XP")
        elif m == "level":
            if not (1 <= val <= 99):
                self._notify("1-99!", ok=False); return
            diff = val - self.player.level
            self.player.level = val
            if diff > 0:
                self.player.max_hp += 15 * diff
                self.player.hp = self.player.max_hp
                self.player.attack += 2 * diff
                self.player.defense += diff
            self.player.xp = 0
            self.player.xp_next = int(50 * (1.5 ** (val - 1)))
            self._notify(f"Рівень -> {val}")
        elif m == "qty":
            if val > 0:
                self._qty = val; self._notify(f"Кількість -> {val}")
        autosave(self.player)
        self._input = ""; self._input_mode = ""

    def _heal(self):
        self.player.hp = self.player.max_hp
        autosave(self.player); self._notify("HP відновлено")

    def _give_all(self):
        self.player.gold += 9999
        for mid in MATERIALS: self.player.add_material(mid, 99)
        for bp in BLUEPRINTS.values():
            if not any(ob.blueprint_id == bp.blueprint_id for ob in self.player.blueprints):
                self.player.blueprints.append(OwnedBlueprint.new(bp))
        for iid in ["small_potion","big_potion","power_potion","leather_armor","chainmail"]:
            if iid in ITEMS: self.player.inventory.append(ITEMS[iid])
        autosave(self.player); self._notify("Все видано!")

    def _give_mat(self, mid):
        self.player.add_material(mid, self._qty)
        autosave(self.player)
        m = MATERIALS[mid]
        self._notify(f"+{self._qty}x {m.name}")

    def _give_item(self, iid):
        self.player.inventory.append(ITEMS[iid])
        autosave(self.player)
        self._notify(f"Видано: {ITEMS[iid].name}")

    def _give_bp(self, bid):
        bp = BLUEPRINTS[bid]
        if any(ob.blueprint_id == bp.blueprint_id for ob in self.player.blueprints):
            self._notify("Вже є!", ok=False); return
        self.player.blueprints.append(OwnedBlueprint.new(bp))
        autosave(self.player); self._notify(f"Видано: {bp.name}")

    def _give_all_bps(self):
        n = 0
        for bp in BLUEPRINTS.values():
            if not any(ob.blueprint_id == bp.blueprint_id for ob in self.player.blueprints):
                self.player.blueprints.append(OwnedBlueprint.new(bp)); n += 1
        autosave(self.player); self._notify(f"Видано {n} кресленників")

    def _level_up(self):
        self.player.level += 1
        self.player.max_hp += 15; self.player.hp = self.player.max_hp
        self.player.attack += 2; self.player.defense += 1
        self.player.xp = 0
        self.player.xp_next = int(50 * (1.5 ** (self.player.level - 1)))
        autosave(self.player); self._notify(f"Рівень -> {self.player.level}")

    def _clear_inventory(self):
        self.player.inventory.clear(); autosave(self.player)
        self._notify("Інвентар очищено")

    def _clear_materials(self):
        self.player.materials.clear(); autosave(self.player)
        self._notify("Матеріали очищено")

    def _win_battle(self):
        self.player.enemies_killed = getattr(self.player,"enemies_killed",0) + 1
        self.player.battles_won    = getattr(self.player,"battles_won",0) + 1
        self.player.goblins_killed = getattr(self.player,"goblins_killed",0) + 1
        autosave(self.player); self._notify("Симуляція перемоги")

    def _reset_stats(self):
        for attr in ("enemies_killed","goblins_killed","orcs_killed",
                     "dark_knights_killed","battles_won",
                     "total_crits","total_damage_dealt","total_damage_taken"):
            if hasattr(self.player, attr): setattr(self.player, attr, 0)
        autosave(self.player); self._notify("Статистика скинута")

    def _hot_reload(self):
        try:
            from config.hot_reload import reload_all
            r = reload_all(self.game)
            self._notify(f"Hot-reload OK ({r['time_ms']}ms)" if r["ok"]
                         else f"Помилка: {r['errors'][0]}", ok=r["ok"])
        except Exception as e:
            self._notify(str(e), ok=False)

    # ── події ─────────────────────────────────────────────────────
    def handle_event(self, event):
        mouse = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._close_btn.update(mouse, True)
            # Таби
            tab_w = _W // len(_TABS)
            for i, (_, key) in enumerate(_TABS):
                r = pygame.Rect(_X + i*tab_w, _Y+4, tab_w-2, _TAB_H-4)
                if r.collidepoint(mouse):
                    self._switch_tab(key); break
            # Кнопки поточної вкладки
            tab_btns = {"player": self._player_btns,
                        "battle": self._battle_btns,
                        "system": self._system_btns,
                        "skip":   self._skip_btns}.get(self._tab, [])
            for btn in tab_btns:
                btn.update(mouse, True)
            self._handle_row_click(mouse)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._input_mode: self._input_mode = ""; self._input = ""
                else: self.game.pop_scene()
                return
            if event.key == pygame.K_RETURN:
                if self._input_mode: self._confirm_input()
                return
            if event.key == pygame.K_BACKSPACE:
                if self._input_mode: self._input = self._input[:-1]
                else: self._search = self._search[:-1]
                return
            # Ctrl+Q — змінити кількість
            if event.key == pygame.K_q and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self._input_mode = "qty"; self._input = ""; return
            if self._input_mode:
                if event.unicode.isdigit(): self._input += event.unicode
            else:
                if event.unicode and event.unicode.isprintable() and len(event.unicode) == 1:
                    self._search += event.unicode.lower()

        if event.type == pygame.MOUSEWHEEL:
            if self._tab == "textures":
                # Для вкладки текстур — зберігаємо scroll в окремій змінній
                if not hasattr(self, "_tex_scroll"):
                    self._tex_scroll = 0
                self._tex_scroll = max(0, self._tex_scroll - event.y * 30)
            else:
                self._scroll -= event.y * _ROW_H * 2

    def _handle_row_click(self, mouse):
        area = self._rows_area()
        if not area.collidepoint(mouse): return
        local_y = mouse[1] - area.y + self._scroll
        idx = local_y // _ROW_H
        if idx < 0: return
        if self._tab == "materials":
            items = self._filtered(MATERIALS)
            if idx < len(items): self._give_mat(items[idx][0])
        elif self._tab == "items":
            items = self._filtered(ITEMS)
            if idx < len(items): self._give_item(items[idx][0])
        elif self._tab == "blueprints":
            items = self._filtered(BLUEPRINTS)
            if idx < len(items): self._give_bp(items[idx][0])

    # ── update ────────────────────────────────────────────────────
    def update(self, dt):
        if self._msg_timer > 0: self._msg_timer -= dt
        mouse = pygame.mouse.get_pos()
        self._close_btn.update(mouse, False)
        tab_btns = {"player": self._player_btns,
                    "battle": self._battle_btns,
                    "system": self._system_btns,
                    "skip":   self._skip_btns}.get(self._tab, [])
        for btn in tab_btns:
            btn.update(mouse, False)
        area = self._rows_area()
        if area.collidepoint(mouse):
            self._hovered = (mouse[1] - area.y + self._scroll) // _ROW_H
        else:
            self._hovered = -1

    # ── draw ──────────────────────────────────────────────────────
    def draw(self, screen):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)
    def _row_material(self, surf, y, w, key, mat, hover):
        pygame.draw.rect(surf, _C_ROW_H if hover else _C_ROW,
                         (0, y, w, _ROW_H-2), border_radius=3)
        rc = RARITY_COLORS.get(mat.rarity, (120,120,120))
        pygame.draw.rect(surf, rc, (0, y+2, 3, _ROW_H-6))
        fn = assets.get_font(FONT_SIZE_SMALL)
        has = self.player.materials.get(key, 0)
        surf.blit(fn.render(f"{mat.icon}  {mat.name}", True, _C_TEXT), (10, y+10))
        surf.blit(fn.render(f"є: {has}", True, _C_DIM), (w-220, y+10))
        surf.blit(fn.render(f"+{self._qty}", True, _C_GOLD), (w-70, y+10))

    def _row_item(self, surf, y, w, key, item, hover):
        pygame.draw.rect(surf, _C_ROW_H if hover else _C_ROW,
                         (0, y, w, _ROW_H-2), border_radius=3)
        tc = {"weapon":(220,130,60),"armor":(80,160,230),
              "potion":(100,210,100),"tool":(180,180,100)}.get(item.item_type, _C_DIM)
        pygame.draw.rect(surf, tc, (0, y+2, 3, _ROW_H-6))
        fn = assets.get_font(FONT_SIZE_SMALL)
        surf.blit(fn.render(f"{item.icon}  {item.name}", True, _C_TEXT), (10, y+10))
        surf.blit(fn.render(item.item_type, True, _C_DIM), (w-200, y+10))
        surf.blit(fn.render("+1", True, _C_GOLD), (w-50, y+10))

    def _row_blueprint(self, surf, y, w, key, bp, hover):
        has = any(ob.blueprint_id == bp.blueprint_id for ob in self.player.blueprints)
        color = (30,50,30) if has else (_C_ROW_H if hover else _C_ROW)
        pygame.draw.rect(surf, color, (0, y, w, _ROW_H-2), border_radius=3)
        rc = RARITY_COLORS.get(bp.rarity, (120,120,120))
        pygame.draw.rect(surf, rc, (0, y+2, 3, _ROW_H-6))
        fn = assets.get_font(FONT_SIZE_SMALL)
        surf.blit(fn.render(f"  {bp.name}", True, _C_DIM if has else _C_TEXT), (10, y+10))
        surf.blit(fn.render("v maeш" if has else "+1", True,
                             _C_DIM if has else _C_GOLD), (w-70, y+10))

    def _quick(self, val, mode):
        if mode == "gold":
            self.player.gold += val; self._notify(f"+{val} золота")
        elif mode == "xp":
            self.player.xp += val; self._notify(f"+{val} XP")
        autosave(self.player)