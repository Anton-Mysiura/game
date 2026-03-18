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
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170)); screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, _C_PANEL,  (_X, _Y, _W, _H), border_radius=10)
        pygame.draw.rect(screen, _C_BORDER, (_X, _Y, _W, _H), 2, border_radius=10)

        # Заголовок
        fn_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = fn_title.render("ADMIN", True, _C_RED)
        screen.blit(title, (_X + 16, _Y + 10))

        self._draw_tabs(screen)
        self._draw_search_bar(screen)

        if   self._tab == "player":     self._draw_player(screen)
        elif self._tab == "materials":  self._draw_list(screen, MATERIALS,  self._row_material)
        elif self._tab == "items":      self._draw_list(screen, ITEMS,      self._row_item)
        elif self._tab == "blueprints": self._draw_list(screen, BLUEPRINTS, self._row_blueprint)
        elif self._tab == "battle":     self._draw_battle(screen)
        elif self._tab == "skip":       self._draw_skip(screen)
        elif self._tab == "system":     self._draw_system(screen)

        self._draw_statusbar(screen)
        self._close_btn.draw(screen)
        if self._input_mode: self._draw_input_overlay(screen)

    def _draw_tabs(self, screen):
        tab_w = _W // len(_TABS)
        for i, (label, key) in enumerate(_TABS):
            active = key == self._tab
            x = _X + i * tab_w
            color = _C_SEL if active else _C_HEADER
            pygame.draw.rect(screen, color, (x+1, _Y+4, tab_w-2, _TAB_H-4), border_radius=6)
            if active:
                pygame.draw.rect(screen, _C_GOLD, (x+1, _Y+4, tab_w-2, _TAB_H-4), 1, border_radius=6)
            fn = assets.get_font(14)
            lbl = fn.render(label, True, _C_TEXT if active else _C_DIM)
            screen.blit(lbl, (x + (tab_w - lbl.get_width())//2,
                               _Y+4 + (_TAB_H-4-lbl.get_height())//2))

    def _draw_search_bar(self, screen):
        if self._tab not in ("materials","items","blueprints"): return
        sy = _Y + _TAB_H + 8
        pygame.draw.rect(screen, _C_ROW, (_COL_L, sy, _W-32, 32), border_radius=4)
        pygame.draw.rect(screen, _C_BORDER, (_COL_L, sy, _W-32, 32), 1, border_radius=4)
        fn = assets.get_font(FONT_SIZE_SMALL)
        prompt = self._search + "I" if self._search else "Пошук..."
        lbl = fn.render(prompt, True, _C_TEXT if self._search else _C_DIM)
        screen.blit(lbl, (_COL_L + 8, sy + 8))
        if self._tab == "materials":
            qty_lbl = fn.render(f"x{self._qty}  [Ctrl+Q]", True, _C_DIM)
            screen.blit(qty_lbl, (_COL_L + _W - 32 - qty_lbl.get_width() - 8, sy + 8))

    def _draw_list(self, screen, data_dict, row_fn):
        area = self._rows_area()
        filtered = self._filtered(data_dict)
        total = len(filtered)
        self._clip_scroll(total)

        clip = pygame.Surface((area.width, area.height), pygame.SRCALPHA)
        first = self._scroll // _ROW_H
        last  = min(total, first + area.height // _ROW_H + 2)
        off_y = -(self._scroll % _ROW_H)

        for i in range(first, last):
            k, v = filtered[i]
            ry = (i - first) * _ROW_H + off_y
            row_fn(clip, ry, area.width, k, v, i == self._hovered)

        screen.blit(clip, area.topleft)

        # Смуга прокрутки
        if total * _ROW_H > area.height:
            th = max(24, area.height * area.height // (total * _ROW_H))
            ty = int(self._scroll / max(1, total*_ROW_H - area.height) * (area.height - th))
            sx = area.right + 4
            pygame.draw.rect(screen, _C_ROW,   (sx, area.y, 6, area.height), border_radius=3)
            pygame.draw.rect(screen, _C_GOLD,  (sx, area.y+ty, 6, th),       border_radius=3)

        # Кількість результатів
        fn = assets.get_font(FONT_SIZE_SMALL)
        cnt_lbl = fn.render(f"{total} записів", True, _C_DIM)
        screen.blit(cnt_lbl, (_COL_L, _Y + _H - 56))

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

    def _draw_player(self, screen):
        p = self.player
        fn  = assets.get_font(FONT_SIZE_NORMAL)
        fns = assets.get_font(FONT_SIZE_SMALL)
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        sy  = _CONTENT_Y

        screen.blit(fnb.render("Статистика", True, _C_GOLD), (_COL_L, sy)); sy += 36
        stats = [
            ("Рівень",   str(p.level)),
            ("HP",       f"{p.hp} / {p.max_hp}"),
            ("Атака",    str(p.attack)),
            ("Захист",   str(p.defense)),
            ("Золото",   str(p.gold)),
            ("XP",       f"{p.xp} / {p.xp_next}"),
            ("Вбито",    str(getattr(p,"enemies_killed",0))),
            ("Перемог",  str(getattr(p,"battles_won",0))),
            ("Предметів",str(len(p.inventory))),
        ]
        for name, val in stats:
            pygame.draw.rect(screen, _C_ROW, (_COL_L, sy, _W//2-20, 30), border_radius=3)
            screen.blit(fns.render(name, True, _C_DIM),  (_COL_L+8, sy+7))
            screen.blit(fns.render(val,  True, _C_TEXT), (_COL_L+180, sy+7))
            sy += 34

        # Дії
        bx = _COL_R
        screen.blit(fnb.render("Швидкі дії", True, _C_GOLD), (bx, _CONTENT_Y))
        for btn in self._player_btns:
            btn.draw(screen)

    def _quick(self, val, mode):
        if mode == "gold":
            self.player.gold += val; self._notify(f"+{val} золота")
        elif mode == "xp":
            self.player.xp += val; self._notify(f"+{val} XP")
        autosave(self.player)

    def _draw_battle(self, screen):
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        fns = assets.get_font(FONT_SIZE_SMALL)
        sy  = _CONTENT_Y
        p   = self.player

        screen.blit(fnb.render("Бойова статистика", True, _C_GOLD), (_COL_L, sy)); sy += 44
        rows = [
            ("Ворогів вбито",   getattr(p,"enemies_killed",0)),
            ("Перемог",         getattr(p,"battles_won",0)),
            ("Гоблінів",        getattr(p,"goblins_killed",0)),
            ("Орків",           getattr(p,"orcs_killed",0)),
            ("Темних лицарів",  getattr(p,"dark_knights_killed",0)),
            ("Критичних ударів",getattr(p,"total_crits",0)),
        ]
        for name, val in rows:
            pygame.draw.rect(screen, _C_ROW, (_COL_L, sy, 360, 30), border_radius=3)
            screen.blit(fns.render(name, True, _C_DIM),  (_COL_L+8, sy+7))
            screen.blit(fns.render(str(val), True, _C_TEXT), (_COL_L+260, sy+7))
            sy += 34

        screen.blit(fnb.render("Тестування", True, _C_GOLD), (_COL_R, _CONTENT_Y))
        for btn in self._battle_btns:
            btn.draw(screen)

    def _draw_skip(self, screen):
        import time
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        fns = assets.get_font(FONT_SIZE_SMALL)
        sy  = _CONTENT_Y

        screen.blit(fnb.render("Пропуск очікувань", True, _C_GOLD), (_COL_L, sy))
        sy += 44

        # Малюємо кнопки
        for btn in self._skip_btns:
            btn.draw(screen)

        # Права колонка — поточний статус таймерів
        bx = _COL_R
        screen.blit(fnb.render("Поточний стан", True, _C_GOLD), (bx, _CONTENT_Y))
        sy2 = _CONTENT_Y + 44

        def status_row(label, value, color=None):
            nonlocal sy2
            pygame.draw.rect(screen, _C_ROW, (bx, sy2, 300, 28), border_radius=3)
            screen.blit(fns.render(label, True, _C_DIM),  (bx+8,   sy2+6))
            clr = color or _C_TEXT
            screen.blit(fns.render(str(value), True, clr), (bx+180, sy2+6))
            sy2 += 32

        # Крафт
        q = getattr(self.player, "crafting_queue", None)
        if q:
            active = [o for o in q.orders if not o.is_done()]
            done   = [o for o in q.orders if  o.is_done()]
            if active:
                secs = max(0, int(active[0].finish_at - time.time()))
                status_row("Крафт", f"{len(active)} в черзі, {secs}с",
                           _C_RED if secs > 0 else _C_GREEN)
            else:
                status_row("Крафт", "порожньо", _C_DIM)

        # Розбирання
        dq = getattr(self.player, "dismantle_queue", None)
        if dq:
            active_d = [o for o in dq.orders if not o.is_done()]
            if active_d:
                secs = max(0, int(active_d[0].finish_at - time.time()))
                status_row("Розбирання", f"{len(active_d)} в черзі, {secs}с",
                           _C_RED if secs > 0 else _C_GREEN)
            else:
                status_row("Розбирання", "порожньо", _C_DIM)

        # Ринок
        m = getattr(self.player, "market", None)
        if m:
            t = m.time_to_refresh()
            if t > 0:
                mins = int(t // 60); secs = int(t % 60)
                status_row("Ринок", f"оновлення через {mins}хв {secs}с", _C_RED)
            else:
                status_row("Ринок", "готовий до оновлення", _C_GREEN)

        # Шахтар
        mn = getattr(self.player, "miner", None)
        if mn:
            tl = mn.time_left() if hasattr(mn, "time_left") else 0
            if tl > 0:
                mins = tl // 60; secs = tl % 60
                status_row("Шахтар", f"копає, {mins}хв {secs}с", _C_RED)
            else:
                status_row("Шахтар", "вільний", _C_GREEN)

        # Щоденні квести
        daily = getattr(self.player, "daily_quests", None)
        if daily:
            done_count = sum(1 for dq2 in daily.quests if dq2.done)
            total      = len(daily.quests)
            status_row("Щоденні квести", f"{done_count}/{total} виконано",
                       _C_GREEN if done_count == total else _C_TEXT)

    def _draw_system(self, screen):
        fnb = assets.get_font(FONT_SIZE_MEDIUM)
        fns = assets.get_font(FONT_SIZE_SMALL)
        sy  = _CONTENT_Y

        screen.blit(fnb.render("Система", True, _C_GOLD), (_COL_L, sy)); sy += 44

        for btn in self._system_btns:
            btn.draw(screen)
        sy += 48 * len(self._system_btns)

        sy += 16
        info = [
            ("FPS", str(round(self.game.clock.get_fps())) if hasattr(self.game,"clock") else "?"),
            ("Сцена", type(self.game.current_scene).__name__ if hasattr(self.game,"current_scene") else "?"),
        ]
        for k, v in info:
            screen.blit(fns.render(f"{k}:  {v}", True, _C_DIM), (_COL_L, sy))
            sy += 24

        sy += 20
        screen.blit(fnb.render("Гарячі клавіші", True, _C_GOLD), (_COL_L, sy)); sy += 36
        for k, v in [("F12","Адмін-панель"),("Ctrl+F5","Hot-reload"),
                     ("F5","Зберегти"),("Ctrl+Q","Змінити кількість"),
                     ("Scroll","Прокрутка"),("Друкування","Пошук")]:
            screen.blit(fns.render(k, True, _C_GOLD), (_COL_L, sy))
            screen.blit(fns.render(v, True, _C_DIM),  (_COL_L+130, sy))
            sy += 24

    def _draw_input_overlay(self, screen):
        ov = pygame.Surface((_W, _H), pygame.SRCALPHA)
        ov.fill((0,0,0,160)); screen.blit(ov, (_X, _Y))
        prompts = {"gold":"Скільки золота?","xp":"Скільки XP?",
                   "level":"Рівень (1-99):","qty":"Кількість за клік:"}
        fn = assets.get_font(FONT_SIZE_MEDIUM)
        ix, iy = SCREEN_WIDTH//2-180, SCREEN_HEIGHT//2-60
        pygame.draw.rect(screen, _C_PANEL, (ix-20,iy-20,400,120), border_radius=8)
        pygame.draw.rect(screen, _C_GOLD,  (ix-20,iy-20,400,120), 2, border_radius=8)
        screen.blit(fn.render(prompts.get(self._input_mode,"Введіть:"), True, _C_TEXT), (ix, iy))
        ir = pygame.Rect(ix, iy+40, 360, 44)
        pygame.draw.rect(screen, _C_ROW, ir, border_radius=4)
        pygame.draw.rect(screen, _C_GOLD, ir, 2, border_radius=4)
        screen.blit(fn.render((self._input or "0")+"I", True, _C_TEXT), (ir.x+10, ir.y+8))
        screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
            "Enter - ОК  |  ESC - скасувати", True, _C_DIM), (ix, iy+92))

    def _draw_statusbar(self, screen):
        sy = _Y + _H - 52
        if self._msg and self._msg_timer > 0:
            screen.blit(assets.get_font(FONT_SIZE_NORMAL).render(
                self._msg, True, self._msg_color), (_X+16, sy+12))
        elif self._tab in ("materials","items","blueprints"):
            screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
                "Друкуй для пошуку  *  колесо миші - прокрутка  *  Ctrl+Q - змінити кількість",
                True, _C_DIM), (_X+16, sy+14))