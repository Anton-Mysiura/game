"""
Адмін консоль — викликається через F1 або ~
"""

import pygame
from ui.assets import assets
from ui.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOLD, COLOR_ERROR, COLOR_SUCCESS,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
)
from game.data import ITEMS, MATERIALS
from game.perk_system import PERKS
from game.save_manager import autosave


CONSOLE_H      = 300
CONSOLE_BG     = (10, 12, 10)
CONSOLE_BORDER = (0, 200, 80)
MAX_LOG        = 30
CURSOR_BLINK   = 0.5

SUGGEST_MAX    = 8
SUGGEST_W      = 400
SUGGEST_ROW_H  = 28

CLR_SUGGEST_BG      = (15, 25, 15)
CLR_SUGGEST_BG_SEL  = (30, 70, 30)
CLR_SUGGEST_BORDER  = (0, 140, 50)
CLR_SUGGEST_CMD     = (120, 220, 120)
CLR_SUGGEST_ITEM    = (255, 220, 100)
CLR_SUGGEST_MAT     = (100, 200, 255)
CLR_SUGGEST_PERK    = (200, 130, 255)
CLR_SUGGEST_DIM     = (100, 130, 100)


class AdminConsole:
    def __init__(self, player):
        self.player      = player
        self.active      = False
        self.input       = ""
        self.log         = []
        self.history     = []
        self.hist_idx    = -1
        self.cursor_t    = 0.0
        self.show_cursor = True
        self.suggestions: list = []
        self.sug_idx     = -1
        self.sug_hovered = -1
        self._cmds       = self._build_registry()
        self._log("Адмін консоль. 'help' — список команд.", COLOR_TEXT_DIM)

    def _build_registry(self) -> dict:
        return {
            "help":       (self._cmd_help,       "Список усіх команд"),
            "hp":         (self._cmd_hp,          "hp [число|max]"),
            "xp":         (self._cmd_xp,          "xp <число>"),
            "level":      (self._cmd_level,       "level <рівень>"),
            "gold":       (self._cmd_gold,        "gold <число>"),
            "setgold":    (self._cmd_setgold,     "setgold <число>"),
            "heal":       (self._cmd_heal,        "Повне відновлення HP"),
            "stat":       (self._cmd_stat,        "Характеристики гравця"),
            "give":       (self._cmd_give,        "give <item_id> [кількість]"),
            "items":      (self._cmd_items,       "Список ID предметів"),
            "mat":        (self._cmd_mat,         "mat <mat_id> <кількість>"),
            "mats":       (self._cmd_mats,        "Список ID матеріалів"),
            "clearinv":   (self._cmd_clearinv,    "Очистити інвентар"),
            "perk":       (self._cmd_perk,        "perk <perk_id>"),
            "perklist":   (self._cmd_perklist,    "Список ID перків"),
            "clearperks": (self._cmd_clearperks,  "Видалити всі перки"),
            "seenall":    (self._cmd_seenall,     "Відкрити весь бестіарій"),
            "save":       (self._cmd_save,        "Зберегти гру"),
            "clear":      (self._cmd_clear,       "Очистити лог"),
        }

    # ── Підказки ──────────────────────────

    def _update_suggestions(self):
        self.suggestions = []
        self.sug_idx = -1
        inp = self.input
        if not inp:
            return
        parts = inp.split()

        # Підказки команд — перше слово ще не завершене
        if len(parts) == 1 and not inp.endswith(" "):
            word = parts[0].lower()
            for name, (_, desc) in sorted(self._cmds.items()):
                if name.startswith(word):
                    self.suggestions.append((name, desc, name + " ", CLR_SUGGEST_CMD))

        # Підказки аргументів
        elif len(parts) >= 1:
            cmd = parts[0].lower()
            arg = "" if inp.endswith(" ") else (parts[1].lower() if len(parts) >= 2 else "")
            if cmd == "give":
                self.suggestions = self._suggest_from(ITEMS, arg, cmd + " ",
                    lambda k, v: (f"{v.icon} {k}", v.name, CLR_SUGGEST_ITEM))
            elif cmd == "mat":
                self.suggestions = self._suggest_from(MATERIALS, arg, cmd + " ",
                    lambda k, v: (f"{v.icon} {k}", v.name, CLR_SUGGEST_MAT))
            elif cmd == "perk":
                self.suggestions = self._suggest_from(PERKS, arg, cmd + " ",
                    lambda k, v: (f"{v.icon} {k}", v.name, CLR_SUGGEST_PERK))

        self.suggestions = self.suggestions[:SUGGEST_MAX]

    def _suggest_from(self, data: dict, prefix: str, cmd_prefix: str, fmt) -> list:
        result = []
        for k, v in sorted(data.items()):
            name_lower = v.name.lower() if hasattr(v, 'name') else ""
            if k.startswith(prefix) or name_lower.startswith(prefix):
                label, desc, color = fmt(k, v)
                result.append((label, desc, cmd_prefix + k + " ", color))
        return result

    def _apply_suggestion(self, idx: int):
        if 0 <= idx < len(self.suggestions):
            self.input = self.suggestions[idx][2]
            self.suggestions = []
            self.sug_idx = -1
            self._update_suggestions()

    def _sug_panel_rect(self) -> pygame.Rect:
        n = len(self.suggestions)
        if n == 0:
            return pygame.Rect(0, 0, 0, 0)
        h = n * SUGGEST_ROW_H + 4
        y = SCREEN_HEIGHT - CONSOLE_H - h - 2
        return pygame.Rect(8, y, SUGGEST_W, h)

    def _sug_row_rect(self, i: int) -> pygame.Rect:
        p = self._sug_panel_rect()
        return pygame.Rect(p.x + 2, p.y + 2 + i * SUGGEST_ROW_H, p.w - 4, SUGGEST_ROW_H)

    # ── Публічний API ──────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION and self.active:
            mx, my = event.pos
            self.sug_hovered = next(
                (i for i in range(len(self.suggestions)) if self._sug_row_rect(i).collidepoint(mx, my)), -1
            )

        if event.type == pygame.MOUSEBUTTONDOWN and self.active and event.button == 1:
            mx, my = event.pos
            for i in range(len(self.suggestions)):
                if self._sug_row_rect(i).collidepoint(mx, my):
                    self._apply_suggestion(i)
                    return True

        if event.type == pygame.KEYDOWN:
            is_toggle = (
                event.key == pygame.K_BACKQUOTE or
                event.key == pygame.K_F1 or
                (hasattr(event, 'unicode') and event.unicode in ("~", "`", "ё", "Ё", "є", "Є"))
            )
            if is_toggle:
                self.active = not self.active
                self.input = ""
                self.suggestions = []
                return True

            if not self.active:
                return False

            if event.key == pygame.K_ESCAPE:
                if self.suggestions:
                    self.suggestions = []
                    self.sug_idx = -1
                else:
                    self.active = False
                    self.input = ""
                return True

            if event.key == pygame.K_RETURN:
                if self.sug_idx >= 0:
                    self._apply_suggestion(self.sug_idx)
                    return True
                cmd = self.input.strip()
                if cmd:
                    self.history.append(cmd)
                    self.hist_idx = -1
                    self._log(f"> {cmd}", COLOR_GOLD)
                    self._execute(cmd)
                self.input = ""
                self.suggestions = []
                return True

            if event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
                self._update_suggestions()
                return True

            if event.key == pygame.K_UP:
                if self.suggestions:
                    self.sug_idx = len(self.suggestions) - 1 if self.sug_idx < 0 \
                        else max(0, self.sug_idx - 1)
                elif self.history:
                    self.hist_idx = min(self.hist_idx + 1, len(self.history) - 1)
                    self.input = self.history[-(self.hist_idx + 1)]
                    self._update_suggestions()
                return True

            if event.key == pygame.K_DOWN:
                if self.suggestions:
                    self.sug_idx = self.sug_idx + 1 if self.sug_idx < len(self.suggestions) - 1 else -1
                elif self.hist_idx > 0:
                    self.hist_idx -= 1
                    self.input = self.history[-(self.hist_idx + 1)]
                    self._update_suggestions()
                else:
                    self.hist_idx = -1
                    self.input = ""
                    self._update_suggestions()
                return True

            if event.key == pygame.K_TAB:
                idx = self.sug_idx if self.sug_idx >= 0 else (0 if self.suggestions else -1)
                if idx >= 0:
                    self._apply_suggestion(idx)
                return True

            if event.unicode and event.unicode.isprintable():
                self.input += event.unicode
                self._update_suggestions()
                self.sug_idx = -1
                return True

        return self.active

    def update(self, dt: float):
        if not self.active:
            return
        self.cursor_t += dt
        if self.cursor_t >= CURSOR_BLINK:
            self.cursor_t = 0.0
            self.show_cursor = not self.show_cursor

    # ── Малювання ─────────────────────────

    def draw(self, screen: pygame.Surface):
        if not self.active:
            return

        y0 = SCREEN_HEIGHT - CONSOLE_H
        bg = pygame.Surface((SCREEN_WIDTH, CONSOLE_H), pygame.SRCALPHA)
        bg.fill((*CONSOLE_BG, 230))
        screen.blit(bg, (0, y0))
        pygame.draw.line(screen, CONSOLE_BORDER, (0, y0), (SCREEN_WIDTH, y0), 2)

        font   = assets.get_font(FONT_SIZE_SMALL)
        font_b = assets.get_font(FONT_SIZE_SMALL, bold=True)
        line_h = font.get_height() + 3

        input_y  = SCREEN_HEIGHT - line_h - 10
        prefix_s = font_b.render("> ", True, CONSOLE_BORDER)
        screen.blit(prefix_s, (8, input_y))
        inp_s = font.render(self.input, True, (180, 255, 180))
        screen.blit(inp_s, (8 + prefix_s.get_width(), input_y))

        if self.show_cursor:
            cx = 8 + prefix_s.get_width() + inp_s.get_width() + 2
            pygame.draw.rect(screen, CONSOLE_BORDER, (cx, input_y + 2, 2, line_h - 4))

        pygame.draw.line(screen, (0, 100, 40), (0, input_y - 4), (SCREEN_WIDTH, input_y - 4), 1)

        log_y = input_y - 4 - line_h
        for text, color in reversed(self.log[-MAX_LOG:]):
            if log_y < y0 + 4:
                break
            screen.blit(font.render(text, True, color), (10, log_y))
            log_y -= line_h

        hint = font.render("F1/~ — закрити  |  ↑↓ — вибір підказки  |  Tab/Enter — вставити", True, (0, 120, 60))
        screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 8, y0 + 4))

        self._draw_suggestions(screen, font)

    def _draw_suggestions(self, screen, font):
        if not self.suggestions:
            return

        panel = self._sug_panel_rect()
        bg = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
        bg.fill((*CLR_SUGGEST_BG, 245))
        screen.blit(bg, panel.topleft)
        pygame.draw.rect(screen, CLR_SUGGEST_BORDER, panel, 1, border_radius=4)

        for i, (label, desc, _, color) in enumerate(self.suggestions):
            row = self._sug_row_rect(i)
            selected = (i == self.sug_idx) or (i == self.sug_hovered)
            if selected:
                pygame.draw.rect(screen, CLR_SUGGEST_BG_SEL, row, border_radius=3)
                pygame.draw.rect(screen, color, row, 1, border_radius=3)

            lbl_s = font.render(label, True, color)
            screen.blit(lbl_s, (row.x + 6, row.y + (row.h - lbl_s.get_height()) // 2))

            desc_color = (160, 200, 160) if selected else CLR_SUGGEST_DIM
            desc_s = font.render(desc, True, desc_color)
            desc_x = row.right - desc_s.get_width() - 8
            if desc_x > row.x + lbl_s.get_width() + 14:
                screen.blit(desc_s, (desc_x, row.y + (row.h - desc_s.get_height()) // 2))

    # ── Команди ───────────────────────────

    def _execute(self, raw: str):
        parts = raw.strip().split()
        if not parts:
            return
        name, args = parts[0].lower(), parts[1:]
        if name in self._cmds:
            try:
                self._cmds[name][0](args)
            except Exception as e:
                self._log(f"Помилка: {e}", COLOR_ERROR)
        else:
            self._log(f"Невідома команда '{name}'. Введи 'help'.", COLOR_ERROR)

    def _cmd_help(self, args):
        self._log("══ Команди ══", COLOR_GOLD)
        for name, (_, desc) in sorted(self._cmds.items()):
            self._log(f"  {name:<14} {desc}", COLOR_TEXT_DIM)

    def _cmd_hp(self, args):
        p = self.player
        if not args or args[0] == "max":
            p.hp = p.max_hp
        else:
            p.hp = max(1, min(p.max_hp, int(args[0])))
        self._log(f"HP: {p.hp}/{p.max_hp}", COLOR_SUCCESS)

    def _cmd_heal(self, args):
        self.player.hp = self.player.max_hp
        self._log(f"Зцілено: {self.player.max_hp} HP", COLOR_SUCCESS)

    def _cmd_xp(self, args):
        if not args:
            return self._log("xp <кількість>", COLOR_ERROR)
        val, old = int(args[0]), self.player.level
        self.player.gain_xp(val)
        msg = f"+{val} XP"
        if self.player.level > old:
            msg += f" → Рівень {self.player.level}!"
        self._log(msg, COLOR_SUCCESS)

    def _cmd_level(self, args):
        if not args:
            return self._log("level <рівень>", COLOR_ERROR)
        target, p = max(1, int(args[0])), self.player
        while p.level < target:
            p.level_up()
        p.level = target
        self._log(f"Рівень: {target}", COLOR_SUCCESS)

    def _cmd_gold(self, args):
        if not args:
            return self._log("gold <число>", COLOR_ERROR)
        self.player.gold += int(args[0])
        self._log(f"+{args[0]} золота. Всього: {self.player.gold}", COLOR_SUCCESS)

    def _cmd_setgold(self, args):
        if not args:
            return self._log("setgold <число>", COLOR_ERROR)
        self.player.gold = max(0, int(args[0]))
        self._log(f"Золото: {self.player.gold}", COLOR_SUCCESS)

    def _cmd_stat(self, args):
        p = self.player
        self._log(f"{p.name}  Рівень {p.level}  HP {p.hp}/{p.max_hp}", COLOR_GOLD)
        self._log(f"  XP {p.xp}/{p.xp_next}  Золото {p.gold}", COLOR_TEXT)
        self._log(f"  Атака {p.total_attack}  Захист {p.total_defense}", COLOR_TEXT)

    def _cmd_give(self, args):
        if not args:
            return self._log("give <item_id> [кількість]", COLOR_ERROR)
        item_id, qty = args[0], int(args[1]) if len(args) > 1 else 1
        if item_id not in ITEMS:
            return self._log(f"'{item_id}' не знайдено", COLOR_ERROR)
        for _ in range(qty):
            self.player.inventory.append(ITEMS[item_id])
        self._log(f"{ITEMS[item_id].icon} {ITEMS[item_id].name} ×{qty}", COLOR_SUCCESS)

    def _cmd_items(self, args):
        self._log("══ Предмети ══", COLOR_GOLD)
        for k, v in ITEMS.items():
            self._log(f"  {k:<20} {v.icon} {v.name}", COLOR_TEXT_DIM)

    def _cmd_mat(self, args):
        if len(args) < 2:
            return self._log("mat <mat_id> <кількість>", COLOR_ERROR)
        mat_id, qty = args[0], int(args[1])
        if mat_id not in MATERIALS:
            return self._log(f"'{mat_id}' не знайдено", COLOR_ERROR)
        self.player.add_material(mat_id, qty)
        self._log(f"{MATERIALS[mat_id].icon} {MATERIALS[mat_id].name} ×{qty}", COLOR_SUCCESS)

    def _cmd_mats(self, args):
        self._log("══ Матеріали ══", COLOR_GOLD)
        for k, v in MATERIALS.items():
            self._log(f"  {k:<20} {v.icon} {v.name}", COLOR_TEXT_DIM)

    def _cmd_clearinv(self, args):
        cnt = len(self.player.inventory)
        self.player.inventory.clear()
        self._log(f"Інвентар очищено ({cnt} шт.)", COLOR_SUCCESS)

    def _cmd_perk(self, args):
        if not args:
            return self._log("perk <perk_id>", COLOR_ERROR)
        perk_id = args[0]
        if perk_id not in PERKS:
            return self._log(f"'{perk_id}' не знайдено", COLOR_ERROR)
        self.player.apply_perk(PERKS[perk_id])
        self._log(f"{PERKS[perk_id].icon} {PERKS[perk_id].name}", COLOR_SUCCESS)

    def _cmd_perklist(self, args):
        self._log("══ Перки ══", COLOR_GOLD)
        for k, v in PERKS.items():
            self._log(f"  {k:<25} {v.icon} {v.name} [{v.rarity}]", COLOR_TEXT_DIM)

    def _cmd_clearperks(self, args):
        cnt = len(self.player.perks)
        self.player.perks.clear()
        self._log(f"Перки видалено ({cnt} шт.)", COLOR_SUCCESS)

    def _cmd_seenall(self, args):
        from scenes.bestiary import ENEMY_REGISTRY
        for e in ENEMY_REGISTRY:
            self.player.enemies_seen.add(e["sprite_name"])
        self._log(f"Бестіарій відкрито ({len(ENEMY_REGISTRY)} ворогів)", COLOR_SUCCESS)

    def _cmd_save(self, args):
        autosave(self.player)
        self._log("Збережено.", COLOR_SUCCESS)

    def _cmd_clear(self, args):
        self.log.clear()

    def _log(self, text: str, color=None):
        self.log.append((text, color or COLOR_TEXT))
        if len(self.log) > MAX_LOG * 2:
            self.log = self.log[-MAX_LOG:]