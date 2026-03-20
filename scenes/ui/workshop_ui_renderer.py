"""
Рендерер майстерні — весь draw-код WorkshopUIMixin.
ТІЛЬКИ малювання — жодної логіки гри.
Дизайнер змінює цей файл.
Логіка: scenes/core/workshop.py + scenes/core/workshop_ui.py
"""
from game.data import BLUEPRINTS
from scenes.workshop import SMELT_RECIPES
from scenes.workshop import queue_color
import math
import pygame
from scenes.ui.base_renderer import BaseRenderer
from ui.constants import *
from ui.assets import assets
from ui.components import Button, Panel, ProgressBar, TextBox
from ui.icons import draw_icon


class WorkshopRenderer(BaseRenderer):
    """
    Mixin з усіма методами малювання для WorkshopScene.
    
    WorkshopScene успадковує цей клас разом з іншими,
    тому всі _draw_* методи автоматично доступні.
    
    Структура:
        draw()                    - головний метод
        _draw_header()            - заголовок
        _draw_mode_tabs()         - вкладки режимів
        _draw_free_craft()        - вільний крафт
        _draw_craft_list()        - список кресленників
        _draw_craft_info()        - деталі кресленника
        _draw_smelt_list()        - список переплавки  
        _draw_smelt_info()        - деталі переплавки
        _draw_dismantle_list()    - список розбирання
        _draw_dismantle_info()    - деталі розбирання
        _draw_queue_panel()       - черга замовлень
        _draw_msg()               - повідомлення
        _draw_scrollbar()         - смуга прокрутки
        _draw_wow_overlay()       - WOW ефект при першому крафті
        _draw_ob_overlay()        - туторіал
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        self.scene.main_panel.draw(screen)

        self._draw_header(screen)
        self._draw_mode_tabs(screen)

        if self.scene.mode == "free_craft":
            self._draw_free_craft(screen)
        elif self.scene.mode == "craft":
            self._draw_craft_list(screen)
            self._draw_craft_info(screen)
        elif self.scene.mode == "smelt":
            self._draw_smelt_list(screen)
            self._draw_smelt_info(screen)
        else:
            self._draw_dismantle_list(screen)
            self._draw_dismantle_info(screen)

        self._draw_queue_panel(screen)
        if self.scene.mode != "free_craft":
            self._draw_scrollbar(screen)
        self._draw_msg(screen)

        if self.scene.mode != "free_craft":
            self.scene.action_btn.draw(screen)
        self.scene.exit_btn.draw(screen)

        if self.scene._confirm:
            self.scene._confirm.draw(screen)

        # WOW ефект першого крафту
        if self.scene._wow_timer > 0:
            self._draw_wow_overlay(screen)

        # Онбординг
        if self.scene._ob_active:
            self._draw_ob_overlay(screen)

    def _draw_wow_overlay(self, screen: pygame.Surface):
        """Спецефект при отриманні першої скрафтованої зброї."""
        import math
        item = self.scene._wow_item
        if not item:
            return
        t    = self.scene._wow_timer
        anim = self.scene._wow_anim

        # Alpha fade
        alpha = 255
        if t < 0.6:
            alpha = int(255 * (t / 0.6))
        elif t > 3.0:
            alpha = int(255 * ((t - 3.0) / 0.5))

        # Фон затемнення
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, int(180 * alpha / 255)))
        screen.blit(ov, (0, 0))

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # Промені світла
        import random as _rng
        _rng.seed(42)
        for _ in range(16):
            angle  = _rng.uniform(0, math.pi * 2)
            length = 300 + 80 * math.sin(anim * 2 + angle)
            ex     = cx + int(math.cos(angle) * length)
            ey     = cy + int(math.sin(angle) * length)
            ray    = pygame.Surface((4, int(length)), pygame.SRCALPHA)
            ray.fill((255, 215, 60, int(40 * alpha / 255)))
            # Малюємо промінь як лінію
            pygame.draw.line(screen, (255, 215, 60, int(30 * alpha / 255)),
                             (cx, cy), (ex, ey), 2)

        # Іконка предмета - велика
        fn_huge = assets.get_font(80, bold=True)
        fn_lrg  = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fn_med  = assets.get_font(FONT_SIZE_MEDIUM)
        fn_sm   = assets.get_font(FONT_SIZE_SMALL)

        scale   = 1.0 + 0.08 * abs(math.sin(anim * 3))
        icon_s  = fn_huge.render(item.icon, True, (255, 215, 60))
        icon_s.set_alpha(alpha)

        # Пульс рамки
        pulse_r = int(80 + 30 * abs(math.sin(anim * 2)))
        pygame.draw.circle(screen, (255, 215, 60, int(60 * alpha / 255)),
                           (cx, cy - 30), pulse_r + 10)
        pygame.draw.circle(screen, (255, 180, 20, int(100 * alpha / 255)),
                           (cx, cy - 30), pulse_r)

        screen.blit(icon_s, (cx - icon_s.get_width() // 2, cy - 110))

        # Назва
        if item.item_type == "weapon" and item.attack_bonus:
            stat_txt = f"+{item.attack_bonus} ATK"
        elif item.item_type == "armor":
            stat_txt = f"+{item.defense_bonus} DEF"
        else:
            stat_txt = ""

        from game.mutations import get_mutation
        mut = get_mutation(item)
        name_col = mut.color if mut else (255, 215, 60)

        name_s = fn_lrg.render(item.name, True, name_col)
        name_s.set_alpha(alpha)
        screen.blit(name_s, (cx - name_s.get_width() // 2, cy + 10))

        if stat_txt:
            stat_s = fn_med.render(stat_txt, True, (180, 255, 180))
            stat_s.set_alpha(alpha)
            screen.blit(stat_s, (cx - stat_s.get_width() // 2, cy + 50))

        if mut:
            mut_s = fn_sm.render(f"✦ {mut.name}", True, mut.color)
            mut_s.set_alpha(alpha)
            screen.blit(mut_s, (cx - mut_s.get_width() // 2, cy + 80))

        # "Перша зброя!" текст
        if anim < 1.5:
            slide = max(0.0, 1.0 - anim / 0.5)
            tag_y = cy - 150 - int(slide * 40)
            tag_s = fn_med.render("⚒ Перша зброя!", True, (255, 255, 200))
            tag_s.set_alpha(int(alpha * min(1.0, anim / 0.3)))
            screen.blit(tag_s, (cx - tag_s.get_width() // 2, tag_y))

        # "Клікни щоб закрити"
        if t < 1.5:
            hint = fn_sm.render("[ клік щоб закрити ]", True, (140, 130, 110))
            hint.set_alpha(int(alpha * (1.0 - t / 1.5)))
            screen.blit(hint, (cx - hint.get_width() // 2, cy + 120))

    def _draw_ob_overlay(self, screen: pygame.Surface):
        """Покроковий туторіал майстерні."""
        import math
        STEPS = [
            {"title": "📜 Крок 1: Вибери кресленик",
             "text": ["Вгорі - список кресленників.",
                      "Кресленик визначає що ти скуєш.",
                      "","У тебе є кресленик Кинджала.",
                      "Натисни на нього щоб вибрати."],
             "hl": "bp"},
            {"title": "⚔ Крок 2: Слот 'Лезо'",
             "text": ["Лезо - основа зброї.",
                      "Тільки металеві матеріали: руда, зливки.",
                      "","Натисни 'Лезо', потім вибери матеріал."],
             "hl": "blade"},
            {"title": "🪵 Крок 3: Рукоятка",
             "text": ["Рукоятка - будь-які матеріали.",
                      "Дерево, шкіра, кістка - твій вибір.",
                      "","Різні матеріали дають різні бонуси!"],
             "hl": "handle"},
            {"title": "⚒ Крок 4: Кувати!",
             "text": ["Натисни '⚒ Викувати'.",
                      "Зброя кується певний час.",
                      "Забери в блоці 'Черга' праворуч."],
             "hl": "forge"},
            {"title": "📦 Крок 5: Черга",
             "text": ["Праворуч - черга майстерні.",
                      "Коли '✓ ГОТОВО!' - натисни",
                      "'📦 Забрати готове'."],
             "hl": "queue"},
            {"title": "✅ Готово! Поки що...",
             "text": ["Ти навчився основам.",
                      "","Наставник повернеться пізніше",
                      "щоб розповісти про переплавку.",
                      "","Іди на перший бій!"],
             "hl": None},
        ]
        step_d    = STEPS[min(self.scene._ob_step, len(STEPS)-1)]
        highlight = step_d["hl"]

        HL_RECTS = {
            "bp":     pygame.Rect(FC_SLOTS_X-4, FC_SWITCHER_Y-4,
                                  FC_SLOT_W*2+FC_SLOT_GAP+8, _FC_SWITCHER_H*4+16),
            "blade":  pygame.Rect(FC_SLOTS_X-4, FC_SLOTS_Y-4, FC_SLOT_W+8, FC_SLOT_H+8),
            "handle": pygame.Rect(FC_SLOTS_X+FC_SLOT_W+FC_SLOT_GAP-4, FC_SLOTS_Y-4,
                                  FC_SLOT_W+8, FC_SLOT_H+8),
            "forge":  pygame.Rect(FC_FORGE_X-4, FC_FORGE_Y-4, FC_FORGE_W+8, FC_FORGE_H+8),
            "queue":  pygame.Rect(QUEUE_X-4, QUEUE_Y-4, QUEUE_W+8, QUEUE_H+8),
        }
        hl_rect = HL_RECTS.get(highlight)

        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155))
        if hl_rect:
            pygame.draw.rect(ov, (0,0,0,0), hl_rect, border_radius=8)
        screen.blit(ov, (0,0))

        if hl_rect:
            pulse = 0.6 + 0.4*abs(math.sin(self.scene._ob_anim*3.0))
            col   = tuple(int(c*pulse) for c in (255,200,60))
            pygame.draw.rect(screen, col, hl_rect, 3, border_radius=8)
            cx2   = hl_rect.centerx
            ay    = hl_rect.top - 14
            sz    = int(12 + 4*pulse)
            pygame.draw.polygon(screen, col,
                                [(cx2, ay+sz),(cx2-sz, ay-sz//2),(cx2+sz, ay-sz//2)])

        pw, ph = 520, 300
        px2 = SCREEN_WIDTH - pw - 20
        py2 = SCREEN_HEIGHT // 2 - ph // 2
        bg2 = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg2.fill((12,10,6,245))
        bc  = tuple(int(c*(0.85+0.15*abs(math.sin(self.scene._ob_anim*1.5))))
                    for c in (220,180,60))
        pygame.draw.rect(bg2, bc, bg2.get_rect(), 2, border_radius=12)
        screen.blit(bg2, (px2, py2))

        fn   = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        fsm2 = assets.get_font(FONT_SIZE_NORMAL)
        fxs2 = assets.get_font(FONT_SIZE_SMALL)

        t_s = fn.render(step_d["title"], True, COLOR_GOLD)
        screen.blit(t_s, (px2+14, py2+12))
        cy2 = py2 + 52
        for line in step_d["text"]:
            if not line: cy2 += 8; continue
            screen.blit(fsm2.render(line, True, COLOR_TEXT), (px2+14, cy2))
            cy2 += 26

        step_num = min(self.scene._ob_step, len(STEPS)-1)
        is_last  = (step_num == len(STEPS)-1)
        btn_lbl  = "← Закрити" if is_last else "Далі →"
        btn_r2   = pygame.Rect(px2+pw-160, py2+ph-46, 146, 36)
        mp2      = pygame.mouse.get_pos()
        pygame.draw.rect(screen, (80,65,20) if btn_r2.collidepoint(mp2) else (50,40,12),
                         btn_r2, border_radius=8)
        pygame.draw.rect(screen, COLOR_GOLD, btn_r2, 1, border_radius=8)
        bs = fsm2.render(btn_lbl, True, COLOR_GOLD)
        screen.blit(bs, (btn_r2.centerx - bs.get_width()//2,
                         btn_r2.centery - bs.get_height()//2))

        total_s = len(STEPS)
        for i in range(total_s):
            pygame.draw.circle(screen, COLOR_GOLD if i==step_num else (50,45,35),
                               (px2+pw//2-(total_s-1)*12+i*24, py2+ph-18), 5)

    def _draw_header(self, screen):
        font = assets.get_font(FONT_SIZE_LARGE, bold=True)
        screen.blit(font.render("🔨 Майстерня Коваля", True, COLOR_GOLD), (LIST_X, HEADER_Y))

    def _draw_mode_tabs(self, screen):
        modes = ["free_craft", "craft", "smelt", "dismantle"]
        for i, btn in enumerate(self.scene.mode_btns):
            btn.selected = (self.scene.mode == modes[i])
            btn.draw(screen)


    # ── Вільний крафт: малювання ──────────────────────────────────

    def _draw_free_craft(self, screen):
        """Малює весь інтерфейс вільного крафту."""
        r = self.scene._fc_recipe
        mp = pygame.mouse.get_pos()

        # Перемикач тип предмета
        self._draw_fc_type_switcher(screen, mp)
        # Два слоти
        self._draw_fc_slot(screen, "blade",  FC_SLOTS_X,                          mp)
        self._draw_fc_slot(screen, "handle", FC_SLOTS_X + FC_SLOT_W + FC_SLOT_GAP, mp)
        # Список матеріалів праворуч
        self._draw_fc_mat_list(screen, mp)
        # Превью результату
        self._draw_fc_preview(screen)
        # Кнопка "Викувати"
        self._draw_fc_forge_btn(screen, mp)
        # Підказка про контролі - всередині кнопки Викувати, дрібний текст
        font_hint = assets.get_font(10)
        hint = font_hint.render("ЛКМ +1  |  ПКМ +5  |  ПКМ на слоті −1  |  Shift+ЛКМ видалити все", True, (80, 80, 100))
        screen.blit(hint, (FC_FORGE_X, FC_FORGE_Y + FC_FORGE_H + 2))

    def _draw_fc_type_switcher(self, screen, mp):
        """Список кресленників для вільного крафту."""
        from game.data import BP_RARITY_COLORS
        fn  = assets.get_font(FONT_SIZE_SMALL, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)
        px  = FC_SLOTS_X
        pw  = FC_SLOT_W * 2 + FC_SLOT_GAP
        ph  = _FC_SWITCHER_H * 4 + 8

        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((15, 12, 8, 200))
        pygame.draw.rect(bg, COLOR_GOLD, bg.get_rect(), 1, border_radius=6)
        screen.blit(bg, (px, FC_SWITCHER_Y))

        ob = self.scene._fc_blueprint
        if ob:
            bp  = ob.blueprint
            rc  = BP_RARITY_COLORS.get(bp.rarity, (180,180,180))
            hdr = fn.render(f"📜 {bp.result_icon} {bp.result_name}  |  {ob.uses_left} вик.",
                            True, rc)
        else:
            hdr = fn.render("📜 Вибери кресленик →", True, COLOR_TEXT_DIM)
        screen.blit(hdr, (px + 8, FC_SWITCHER_Y + 6))

        bps    = [o for o in self.player.blueprints
                  if o.blueprint.result_type in ("weapon","armor","tool")
                  and not o.is_broken]
        scroll = self.scene._fc_bp_scroll
        vis    = bps[scroll:scroll+8]
        row_y  = FC_SWITCHER_Y + 28
        for i, ob_i in enumerate(vis):
            bp_i  = ob_i.blueprint
            rc_i  = BP_RARITY_COLORS.get(bp_i.rarity, (180,180,180))
            btn_w = max(80, fsm.render(bp_i.result_name[:12], True, (0,0,0)).get_width() + 20)
            btn_r = pygame.Rect(px + 8 + i*(btn_w+4), row_y, btn_w, _FC_SWITCHER_H*3-6)
            sel   = (self.scene._fc_blueprint is ob_i)
            hov   = btn_r.collidepoint(mp)
            pygame.draw.rect(screen, (70,55,20) if sel else (45,35,12) if hov else (25,20,10),
                             btn_r, border_radius=5)
            pygame.draw.rect(screen, rc_i if sel else (80,65,35), btn_r, 1, border_radius=5)
            screen.blit(fsm.render(bp_i.result_icon, True, rc_i), (btn_r.x+4, btn_r.y+2))
            screen.blit(fsm.render(bp_i.result_name[:12], True, rc_i if sel else COLOR_TEXT_DIM),
                        (btn_r.x+4, btn_r.y+18))
            screen.blit(assets.get_font(10).render(f"×{ob_i.uses_left}", True, (160,140,100)),
                        (btn_r.right-22, btn_r.y+2))

        if not bps:
            screen.blit(fsm.render("Немає кресленників", True, COLOR_ERROR),
                        (px+8, row_y+6))

    def _draw_fc_slot(self, screen, slot_name, sx, mp):
        """Малює один слот (лезо або рукоятка)."""
        r         = self.scene._fc_recipe
        slot_obj  = r.blade if slot_name == "blade" else r.handle
        is_active = (self.scene._fc_active == slot_name)
        sy        = FC_SLOTS_Y

        # Фон
        slot_surf = pygame.Surface((FC_SLOT_W, FC_SLOT_H), pygame.SRCALPHA)
        bg_col    = (30, 24, 14, 220) if is_active else (20, 16, 10, 180)
        slot_surf.fill(bg_col)
        screen.blit(slot_surf, (sx, sy))
        border_col = COLOR_GOLD if is_active else (70, 60, 40)
        pygame.draw.rect(screen, border_col, (sx, sy, FC_SLOT_W, FC_SLOT_H), 2, border_radius=8)

        # Заголовок
        font_h  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_sm = assets.get_font(FONT_SIZE_SMALL)
        if slot_name == "blade":
            label_text = "⚔ Лезо / Основа"
            sub_text   = "(тільки метали)"
            sub_col    = (150, 120, 80)
        else:
            label_text = "🪵 Рукоятка / Підкладка"
            sub_text   = "(будь-які матеріали)"
            sub_col    = (100, 160, 100)

        screen.blit(font_h.render(label_text, True, COLOR_GOLD if is_active else COLOR_TEXT_DIM),
                    (sx + 8, sy + 6))
        screen.blit(font_sm.render(sub_text, True, sub_col), (sx + 8, sy + 28))

        # Кнопка "Очистити"
        if not slot_obj.is_empty():
            clear_r = pygame.Rect(sx + FC_SLOT_W - 85, sy + 4, 80, 26)
            clr_hov = clear_r.collidepoint(mp)
            pygame.draw.rect(screen, (70, 30, 30) if clr_hov else (45, 20, 20), clear_r, border_radius=5)
            pygame.draw.rect(screen, (180, 60, 60), clear_r, 1, border_radius=5)
            lbl_s = font_sm.render("✕ Очистити", True, (220, 100, 100))
            screen.blit(lbl_s, (clear_r.x + 4, clear_r.y + 5))

        # Список матеріалів у слоті
        iy = sy + 50
        items_in_slot = list(slot_obj.mats.items())
        for mid, qty in items_in_slot:
            mat = MATERIALS.get(mid)
            if not mat:
                continue
            item_r = pygame.Rect(sx + 6, iy, FC_SLOT_W - 12, 26)
            hov = item_r.collidepoint(mp)
            bg2 = (50, 40, 20, 180) if hov else (35, 28, 16, 160)
            s2  = pygame.Surface((FC_SLOT_W - 12, 26), pygame.SRCALPHA)
            s2.fill(bg2)
            screen.blit(s2, (sx + 6, iy))
            pygame.draw.rect(screen, (80, 65, 35), (sx + 6, iy, FC_SLOT_W - 12, 26), 1, border_radius=4)

            from game.data import RARITY_COLOR
            rc = RARITY_COLOR.get(mat.rarity, COLOR_TEXT)
            draw_icon(screen, mid, mat.icon, sx + 12, iy + 3, size=20)
            screen.blit(font_sm.render(mat.name, True, rc), (sx + 36, iy + 5))
            qty_s = font_sm.render(f"×{qty}", True, COLOR_GOLD)
            screen.blit(qty_s, (sx + FC_SLOT_W - qty_s.get_width() - 14, iy + 5))

            if hov:
                hint_s = font_sm.render("ПКМ −1  Shift+ЛКМ видалити", True, (120, 120, 140))
                screen.blit(hint_s, (sx + 12, iy + 5))   # overlay підказки

            iy += 28
            if iy > sy + FC_SLOT_H - 20:
                more = len(items_in_slot) - items_in_slot.index((mid, qty)) - 1
                if more > 0:
                    screen.blit(font_sm.render(f"…ще {more} матеріали", True, COLOR_TEXT_DIM),
                                (sx + 12, iy - 2))
                break

        # Підсумок слоту
        total_q = slot_obj.total_qty()
        if total_q > 0:
            mult_slot = sum(MATERIALS[m].multiplier * q for m, q in slot_obj.mats.items()
                            if m in MATERIALS) / total_q if total_q else 0
            smry = font_sm.render(f"Матеріалів: {total_q}  |  множник слоту: ×{mult_slot:.2f}",
                                   True, (160, 180, 120))
            screen.blit(smry, (sx + 8, sy + FC_SLOT_H - 22))

        # Клік на заголовок = активувати
        header_r = pygame.Rect(sx, sy, FC_SLOT_W, 40)
        if not is_active and header_r.collidepoint(mp):
            pygame.draw.rect(screen, (255, 255, 100, 20),
                             (sx, sy, FC_SLOT_W, FC_SLOT_H), 2, border_radius=8)

    def _draw_fc_mat_list(self, screen, mp):
        """Список матеріалів у гравця (праворуч)."""
        font_h  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_sm = assets.get_font(FONT_SIZE_SMALL)
        font_xs = assets.get_font(12)

        # Заголовок
        slot_label = "Металеві матеріали" if self.scene._fc_active == "blade" else "Усі матеріали"
        screen.blit(font_h.render(f"📦 {slot_label}", True, COLOR_GOLD),
                    (FC_MAT_X, FC_MAT_HDR_Y))
        screen.blit(font_sm.render("активний слот: " + ("⚔ Лезо" if self.scene._fc_active == "blade" else "🪵 Рукоятка"),
                                    True, (120, 160, 120)),
                    (FC_MAT_X, FC_MAT_SUB_Y))

        mat_list = self.scene._fc_visible_mats()
        # Повний список для скролу
        slot = self.scene._fc_active
        all_mats_full = [(mid, qty) for mid, qty in self.player.materials.items()
                         if qty > 0 and (slot != "blade" or MATERIALS.get(mid) and MATERIALS[mid].is_metal)]

        if not all_mats_full:
            screen.blit(font_sm.render("Немає підхожих матеріалів", True, COLOR_ERROR),
                        (FC_MAT_X, FC_MAT_Y + 12))
            return

        for i, (mid, qty) in enumerate(mat_list):
            mat    = MATERIALS.get(mid)
            if not mat:
                continue
            in_recipe = self.scene._fc_recipe.all_mats().get(mid, 0)
            available = qty - in_recipe

            ry = FC_MAT_Y + i * FC_ROW_H
            r  = pygame.Rect(FC_MAT_X, ry, FC_MAT_W, FC_ROW_H - 3)
            hov = r.collidepoint(mp) or (i == self.scene._fc_hovered)

            from game.data import RARITY_COLOR
            rc = RARITY_COLOR.get(mat.rarity, COLOR_TEXT)

            bg_col = (50, 42, 22, 210) if hov else (25, 20, 12, 170)
            s = pygame.Surface((FC_MAT_W, FC_ROW_H - 3), pygame.SRCALPHA)
            s.fill(bg_col)
            screen.blit(s, (FC_MAT_X, ry))
            pygame.draw.rect(screen, rc if hov else (60, 50, 30), r, 1, border_radius=4)

            # Іконка + назва
            draw_icon(screen, mid, mat.icon, FC_MAT_X + 6, ry + 6, size=22)
            screen.blit(font_sm.render(mat.name, True, rc), (FC_MAT_X + 32, ry + 8))

            # Кількість у гравця і вже в рецепті
            if in_recipe > 0:
                qty_text = f"є {available}  (в рецепті: {in_recipe})"
                qty_col  = COLOR_GOLD
            else:
                qty_text = f"є {qty}"
                qty_col  = (180, 180, 180)
            qty_s = font_sm.render(qty_text, True, qty_col)
            screen.blit(qty_s, (FC_MAT_X + FC_MAT_W - qty_s.get_width() - 6, ry + 2))

            # Множник
            mult_s = font_xs.render(f"×{mat.multiplier:.1f}", True, (140, 200, 140))
            screen.blit(mult_s, (FC_MAT_X + FC_MAT_W - mult_s.get_width() - 6, ry + 18))

            # Баф матеріалу
            buffs = []
            if mat.bonus_attack:  buffs.append(f"+{mat.bonus_attack}ATK")
            if mat.bonus_defense: buffs.append(f"+{mat.bonus_defense}DEF")
            if mat.bonus_hp:      buffs.append(f"+{mat.bonus_hp}HP")
            if mat.bonus_crit:    buffs.append(f"+{int(mat.bonus_crit*100)}%крит")
            if buffs:
                b_s = font_xs.render("  ".join(buffs), True, (180, 140, 200))
                screen.blit(b_s, (FC_MAT_X + 6, ry + 20))

        # Скрол-смуга
        total_count = len(all_mats_full)
        if total_count > FC_VISIBLE:
            sb_h     = FC_VISIBLE * FC_ROW_H
            thumb_h  = max(20, int(sb_h * FC_VISIBLE / total_count))
            thumb_y  = FC_MAT_Y + int((sb_h - thumb_h) * self.scene._fc_mat_scroll / max(1, total_count - FC_VISIBLE))
            pygame.draw.rect(screen, (40, 35, 25), (FC_MAT_X + FC_MAT_W + 2, FC_MAT_Y, 5, sb_h), border_radius=3)
            pygame.draw.rect(screen, COLOR_GOLD,   (FC_MAT_X + FC_MAT_W + 2, thumb_y,  5, thumb_h), border_radius=3)

    def _draw_fc_preview(self, screen):
        """Превью результату крафту."""
        r = self.scene._fc_recipe
        font_h  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_sm = assets.get_font(FONT_SIZE_SMALL)
        font_xs = assets.get_font(12)

        px = FC_SLOTS_X
        py = FC_PREVIEW_Y
        pw = FC_SLOT_W * 2 + FC_SLOT_GAP

        bg = pygame.Surface((pw, FC_PREVIEW_H), pygame.SRCALPHA)
        bg.fill((18, 14, 8, 200))
        screen.blit(bg, (px, py))
        pygame.draw.rect(screen, (80, 65, 30), (px, py, pw, FC_PREVIEW_H), 1, border_radius=6)

        if r.total_qty() == 0:
            msg = font_sm.render("Додайте матеріали для крафту", True, COLOR_TEXT_DIM)
            screen.blit(msg, (px + pw // 2 - msg.get_width() // 2, py + FC_PREVIEW_H // 2 - 8))
            return

        stats = calc_item_stats(r)
        mult  = stats["multiplier"]
        name, icon = generate_item_name(r)
        bonuses = calc_bonuses(r)
        total_q = r.total_qty()

        # Назва + іконка
        name_s = font_h.render(f"{icon}  {name}", True, COLOR_GOLD)
        screen.blit(name_s, (px + 12, py + 8))

        # Час крафту
        from game.free_craft import calc_craft_time as fc_time
        time_s = font_sm.render(f"⏱ {fmt_time(fc_time(r))}", True, (160, 160, 200))
        screen.blit(time_s, (px + pw - time_s.get_width() - 12, py + 8))

        # Статистика
        col_y = py + 36
        col1x = px + 12
        col2x = px + pw // 3
        col3x = px + pw * 2 // 3

        mult_col = (100, 220, 100) if mult >= 3.0 else (220, 220, 100) if mult >= 1.5 else COLOR_TEXT

        screen.blit(font_sm.render(f"Множник: ×{mult:.2f}", True, mult_col),    (col1x, col_y))
        screen.blit(font_sm.render(f"Матеріалів: {total_q}", True, COLOR_TEXT), (col2x, col_y))

        col_y += 20
        if r.result_type == "weapon":
            screen.blit(font_sm.render(f"⚔ Атака: {stats['attack']}", True, (220, 160, 80)), (col1x, col_y))
        else:
            screen.blit(font_sm.render(f"🛡 Захист: {stats['defense']}", True, (80, 160, 220)), (col1x, col_y))
            screen.blit(font_sm.render(f"❤ HP: +{stats['hp']}", True, (220, 80, 80)),           (col2x, col_y))

        if stats["crit"] > 0:
            screen.blit(font_sm.render(f"🎯 Крит: +{stats['crit']*100:.0f}%", True, (200, 180, 80)), (col3x, col_y))

        # Бафи від матеріалів
        col_y += 20
        buff_parts = []
        if bonuses["attack"]:  buff_parts.append(f"+{bonuses['attack']} ATK")
        if bonuses["defense"]: buff_parts.append(f"+{bonuses['defense']} DEF")
        if bonuses["hp"]:      buff_parts.append(f"+{bonuses['hp']} HP")
        if bonuses["crit"]:    buff_parts.append(f"+{int(bonuses['crit']*100)}% крит")
        if buff_parts:
            buffs_s = font_xs.render("Бафи матеріалів: " + "  ".join(buff_parts), True, (180, 140, 220))
            screen.blit(buffs_s, (col1x, col_y))

        # Ціна
        val_s = font_xs.render(f"💰 Ціна: ~{calc_item_value(r)} 🪙", True, COLOR_GOLD)
        screen.blit(val_s, (px + pw - val_s.get_width() - 12, py + FC_PREVIEW_H - 18))

        # Попередження якщо мало матеріалів
        if not r.is_valid():
            warn = font_xs.render(f"⚠ Потрібно мінімум {MIN_TOTAL_MATS} матеріали", True, COLOR_ERROR)
            screen.blit(warn, (px + pw // 2 - warn.get_width() // 2, py + FC_PREVIEW_H - 18))

    def _draw_fc_forge_btn(self, screen, mp):
        """Кнопка Викувати."""
        r       = self.scene._fc_recipe
        can     = r.is_valid() and not r.blade.is_empty()
        ok, _   = r.can_afford(self.player.materials) if can else (False, "")
        can_all = can and ok and len(self.player.crafting_queue.orders) < self.player.crafting_queue.MAX_SLOTS

        btn_r   = pygame.Rect(FC_FORGE_X, FC_FORGE_Y, FC_FORGE_W, FC_FORGE_H)
        hov     = btn_r.collidepoint(mp)
        font    = assets.get_font(FONT_SIZE_NORMAL, bold=True)

        if can_all:
            bg_col  = (80, 60, 15) if hov else (55, 42, 10)
            brd_col = COLOR_GOLD
            txt_col = COLOR_GOLD
        else:
            bg_col  = (30, 28, 24)
            brd_col = (70, 65, 55)
            txt_col = COLOR_TEXT_DIM

        pygame.draw.rect(screen, bg_col,  btn_r, border_radius=10)
        pygame.draw.rect(screen, brd_col, btn_r, 2, border_radius=10)
        lbl = font.render("⚒ Викувати", True, txt_col)
        screen.blit(lbl, (btn_r.centerx - lbl.get_width() // 2,
                           btn_r.centery - lbl.get_height() // 2))

    # ── Список крафтів ────────────────────────────────────────────

    def _draw_craft_list(self, screen):
        from game.data import BP_RARITY_COLORS, BP_RARITY_NAMES_UA
        font    = assets.get_font(FONT_SIZE_NORMAL)
        font_sm = assets.get_font(FONT_SIZE_SMALL)
        mp      = pygame.mouse.get_pos()
        # Сортуємо: що можна зробити - вгору, потім за рідкістю
        RARITY_ORDER = ["legendary", "epic", "rare", "uncommon", "common"]
        raw_bps = self.player.blueprints
        bps = sorted(raw_bps, key=lambda ob: (
            0 if ob.can_craft(self.player.materials) else 1,
            RARITY_ORDER.index(ob.rarity) if ob.rarity in RARITY_ORDER else 5,
            ob.blueprint.result_name,
        ))

        bg = pygame.Surface((LIST_W, VISIBLE * ROW_H), pygame.SRCALPHA)
        bg.fill((10, 8, 6, 180)); screen.blit(bg, (LIST_X, LIST_Y))

        if not bps:
            screen.blit(font.render("Немає кресленників! Купи в крамниці.", True, COLOR_ERROR),
                        (LIST_X + 20, LIST_Y + 20))
            return

        for i, ob in enumerate(bps[self.scene.scroll: self.scene.scroll + VISIBLE]):
            bp  = ob.blueprint
            r   = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)
            can = ob.can_craft(self.player.materials)
            rar_clr = BP_RARITY_COLORS.get(ob.rarity, (180, 180, 180))

            bg_clr = (80, 65, 20, 210) if i == self.scene.sel else \
                     (50, 45, 30, 190) if r.collidepoint(mp) else \
                     (22, 18, 14, 160) if i % 2 == 0 else (30, 24, 18, 160)
            s = pygame.Surface((LIST_W, ROW_H - 4), pygame.SRCALPHA); s.fill(bg_clr)
            screen.blit(s, r.topleft)
            if i == self.scene.sel:
                pygame.draw.rect(screen, COLOR_GOLD, r, 1, border_radius=3)

            # Кольорова смужка рідкості зліва
            pygame.draw.rect(screen, rar_clr, (r.x, r.y, 4, r.height), border_radius=2)

            tp   = "⚔" if bp.result_type == "weapon" else "🛡"
            stat = f"+{bp.result_attack} ATK" if bp.result_type == "weapon" \
                   else f"+{bp.result_defense} DEF" + (f", +{bp.result_hp} HP" if bp.result_hp else "")
            name_clr = COLOR_TEXT if can else (120, 110, 100)

            screen.blit(font.render(f"{bp.result_icon} {tp} {bp.result_name}  {stat}",
                        True, name_clr), (r.x + 14, r.y + 6))

            # Рядок знизу: статус + uses
            uses_clr = (100, 220, 100) if ob.uses_left > ob.uses_max * 0.4 else \
                       (220, 180, 60) if ob.uses_left > 1 else (220, 80, 80)
            status = "✓ Готово до крафту" if can else "✗ Не вистачає матеріалів"
            screen.blit(font_sm.render(status, True, (100, 220, 100) if can else (200, 80, 80)),
                        (r.x + 14, r.y + 34))

            # Uses + рідкість праворуч
            uses_txt = f"📜 {BP_RARITY_NAMES_UA.get(ob.rarity, ob.rarity)}  🔄 {ob.uses_left}/{ob.uses_max}"
            uses_s = font_sm.render(uses_txt, True, uses_clr)
            screen.blit(uses_s, (r.right - uses_s.get_width() - 10, r.y + 34))

            # Час крафту
            t_str = fmt_time(get_craft_time(bp.blueprint_id))
            t_surf = font_sm.render(f"⏱ {t_str}", True, (160, 160, 180))
            screen.blit(t_surf, (r.right - t_surf.get_width() - 10, r.y + 8))

        total = len(bps)
        screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
            f"{self.scene.scroll+1}–{min(self.scene.scroll+VISIBLE, total)} з {total}", True, COLOR_TEXT_DIM),
            (LIST_X, LIST_Y + VISIBLE * ROW_H + 4))

    # ── Список переплавки ─────────────────────────────────────────

    def _draw_smelt_list(self, screen):
        font    = assets.get_font(FONT_SIZE_NORMAL)
        font_sm = assets.get_font(FONT_SIZE_SMALL)
        mp      = pygame.mouse.get_pos()

        bg = pygame.Surface((LIST_W, len(SMELT_RECIPES) * ROW_H), pygame.SRCALPHA)
        bg.fill((10, 8, 6, 180)); screen.blit(bg, (LIST_X, LIST_Y))

        for i, (from_mat, from_qty, to_mat, to_qty, label) in enumerate(SMELT_RECIPES):
            r    = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)
            fm   = MATERIALS.get(from_mat)
            tm   = MATERIALS.get(to_mat)
            have = self.player.materials.get(from_mat, 0)
            can  = have >= from_qty

            bg_clr = (80, 65, 20, 210) if i == self.scene.sel else \
                     (50, 45, 30, 190) if r.collidepoint(mp) else \
                     (22, 18, 14, 160) if i % 2 == 0 else (30, 24, 18, 160)
            s = pygame.Surface((LIST_W, ROW_H - 4), pygame.SRCALPHA); s.fill(bg_clr)
            screen.blit(s, r.topleft)
            if i == self.scene.sel:
                pygame.draw.rect(screen, COLOR_GOLD, r, 1, border_radius=3)

            if fm and tm:
                screen.blit(font.render(
                    f"{fm.icon} {fm.name} ×{from_qty}  →  {tm.icon} {tm.name} ×{to_qty}",
                    True, COLOR_TEXT if can else (120, 110, 100)), (r.x + 10, r.y + 8))
                status = f"Маєш: {have}  →  можна: {have // from_qty} зливків" if can \
                         else f"Маєш: {have} / потрібно мінімум {from_qty}"
                screen.blit(font_sm.render(status, True,
                    (100, 220, 100) if can else (200, 80, 80)), (r.x + 14, r.y + 36))

    # ── Черга замовлень ───────────────────────────────────────────

    def _draw_queue_panel(self, screen):
        import time as time_module
        q = self.player.crafting_queue

        # Фон панелі
        qsurf = pygame.Surface((QUEUE_W, QUEUE_H), pygame.SRCALPHA)
        qsurf.fill((12, 10, 8, 200))
        pygame.draw.rect(qsurf, COLOR_GOLD, qsurf.get_rect(), 1, border_radius=8)
        screen.blit(qsurf, (QUEUE_X, QUEUE_Y))

        font_h  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font    = assets.get_font(FONT_SIZE_SMALL)

        screen.blit(font_h.render("⚒ Черга майстерні", True, COLOR_GOLD),
                    (QUEUE_X + 14, QUEUE_Y + 10))

        slot_w = (QUEUE_W - 28) // q.MAX_SLOTS
        has_done = any(o.is_done() for o in q.orders)

        for slot_i in range(q.MAX_SLOTS):
            sx = QUEUE_X + 14 + slot_i * (slot_w + 6)
            sy = QUEUE_Y + 38
            sh = QUEUE_H - 55
            sw = slot_w

            slot_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

            if slot_i < len(q.orders):
                order = q.orders[slot_i]
                bp    = BLUEPRINTS.get(order.blueprint_id)
                total = get_craft_time(order.blueprint_id)
                left  = order.seconds_left()
                done  = order.is_done()
                pct   = 1.0 - (left / total) if total > 0 else 1.0

                clr = queue_color(pct)
                slot_surf.fill((30, 25, 18, 220))
                screen.blit(slot_surf, (sx, sy))
                pygame.draw.rect(screen, clr, (sx, sy, sw, sh), 2, border_radius=6)

                # Назва предмета
                name = order.item_data.get("name", bp.result_name if bp else "???")
                icon = order.item_data.get("icon", "⚔")
                name_s = font.render(f"{icon} {name[:22]}", True, COLOR_TEXT)
                screen.blit(name_s, (sx + 8, sy + 6))

                # Прогрес-бар
                bar_y  = sy + 28
                bar_h  = 10
                bar_w  = sw - 16
                pygame.draw.rect(screen, (40, 35, 28), (sx + 8, bar_y, bar_w, bar_h), border_radius=4)
                fill_w = int(bar_w * min(1.0, pct))
                if fill_w > 0:
                    pygame.draw.rect(screen, clr, (sx + 8, bar_y, fill_w, bar_h), border_radius=4)

                # Час
                if done:
                    # Пульсуюча анімація
                    alpha = int(180 + 75 * math.sin(self.scene._anim_t * 4))
                    done_s = font.render("✓ ГОТОВО!", True, (100, 255, 100))
                    done_s.set_alpha(alpha)
                    screen.blit(done_s, (sx + sw // 2 - done_s.get_width() // 2, sy + 44))
                else:
                    time_s = font.render(f"⏱ {fmt_time(left)}", True, (180, 180, 200))
                    screen.blit(time_s, (sx + 8, sy + 44))

                # Мутація якщо є
                mut_id = order.item_data.get("mutation", "")
                if mut_id:
                    from game.mutations import MUTATIONS, RARITY_COLOR
                    mut = MUTATIONS.get(mut_id)
                    if mut:
                        m_s = font.render(f"✦ {mut.icon} {mut.name}", True,
                                          RARITY_COLOR.get(mut.rarity, COLOR_TEXT))
                        screen.blit(m_s, (sx + 8, sy + 62))
            else:
                # Порожній слот
                slot_surf.fill((18, 16, 12, 180))
                screen.blit(slot_surf, (sx, sy))
                pygame.draw.rect(screen, (60, 55, 45), (sx, sy, sw, sh), 1, border_radius=6)
                empty_s = font.render("- вільний слот -", True, (70, 65, 55))
                screen.blit(empty_s, (sx + sw // 2 - empty_s.get_width() // 2,
                                      sy + sh // 2 - 8))

        # Кнопка "Забрати" - тільки якщо є готові
        dq = self.player.dismantle_queue
        has_any_done = has_done or any(o.is_done() for o in dq.orders)
        if has_any_done:
            self.scene.collect_btn.enabled = True
            self.scene.collect_btn.draw(screen)

        # Лічильник слотів крафту
        cnt = font.render(
            f"Крафт: {len(q.orders)}/{q.MAX_SLOTS}   Розбирання: {len(dq.orders)}/{dq.MAX_SLOTS}",
            True, COLOR_TEXT_DIM)
        screen.blit(cnt, (QUEUE_X + 14, QUEUE_Y + QUEUE_H - 18))

        # Слоти розбирання - компактно під слотами крафту
        if dq.orders:
            self._draw_dismantle_queue_slots(screen, dq)

    # ── Інфо-панелі ───────────────────────────────────────────────

    def _draw_craft_info(self, screen):
        bps     = self.player.blueprints
        abs_idx = self.scene.scroll + self.scene.sel
        if self.scene.sel == -1 or abs_idx >= len(bps):
            hint = assets.get_font(FONT_SIZE_SMALL).render(
                "← Вибери кресленник", True, COLOR_TEXT_DIM)
            screen.blit(hint, (INFO_X, LIST_Y + 20))
            return
        # Сортуємо так само як у списку щоб індекс відповідав
        RARITY_ORDER = ["legendary", "epic", "rare", "uncommon", "common"]
        sorted_bps = sorted(bps, key=lambda ob: (
            0 if ob.can_craft(self.player.materials) else 1,
            RARITY_ORDER.index(ob.rarity) if ob.rarity in RARITY_ORDER else 5,
            ob.blueprint.result_name,
        ))
        if abs_idx >= len(sorted_bps):
            return
        self._draw_bp_detail(screen, sorted_bps[abs_idx])

    def _draw_bp_detail(self, screen, ob):
        from game.data import BP_RARITY_COLORS, BP_RARITY_NAMES_UA
        bp = ob.blueprint
        panel_h = QUEUE_Y - LIST_Y - 12
        surf = pygame.Surface((INFO_W, panel_h), pygame.SRCALPHA)
        surf.fill((15, 12, 8, 210))
        rar_clr = BP_RARITY_COLORS.get(ob.rarity, (180, 180, 180))
        pygame.draw.rect(surf, rar_clr, surf.get_rect(), 1, border_radius=8)
        screen.blit(surf, (INFO_X, LIST_Y))

        px, py = INFO_X + 14, LIST_Y + 12
        fh  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)

        screen.blit(fh.render(f"{bp.result_icon} {bp.result_name}", True, COLOR_GOLD), (px, py)); py += 28

        # Рідкість + uses
        rar_name = BP_RARITY_NAMES_UA.get(ob.rarity, ob.rarity)
        uses_clr = (100, 220, 100) if ob.uses_left > ob.uses_max * 0.4 else \
                   (220, 180, 60) if ob.uses_left > 1 else (220, 80, 80)
        screen.blit(fsm.render(f"📜 {rar_name}  🔄 Використань: {ob.uses_left}/{ob.uses_max}",
                               True, rar_clr), (px, py)); py += 18
        screen.blit(fsm.render(bp.result_desc, True, COLOR_TEXT_DIM), (px, py)); py += 20

        # Uses progress bar
        bar_w = INFO_W - 28
        bar_h = 6
        pygame.draw.rect(screen, (40, 35, 25), (px, py, bar_w, bar_h), border_radius=3)
        fill_w = max(0, int(bar_w * ob.uses_left / ob.uses_max))
        if fill_w > 0:
            pygame.draw.rect(screen, uses_clr, (px, py, fill_w, bar_h), border_radius=3)
        py += 12

        py += 4
        if bp.result_type == "weapon":
            screen.blit(fsm.render(f"⚔ Атака: +{bp.result_attack}", True, COLOR_TEXT), (px, py)); py += 18
        else:
            screen.blit(fsm.render(f"🛡 Захист: +{bp.result_defense}", True, COLOR_TEXT), (px, py)); py += 18
            if bp.result_hp:
                screen.blit(fsm.render(f"❤ HP: +{bp.result_hp}", True, COLOR_TEXT), (px, py)); py += 18

        # Час крафту
        py += 4
        t_clr = (160, 180, 220)
        screen.blit(fsm.render(f"⏱ Час крафту: {fmt_time(get_craft_time(bp.blueprint_id))}",
                               True, t_clr), (px, py)); py += 18

        # Рецепт
        py += 6
        screen.blit(fsm.render("📋 Рецепт:", True, COLOR_GOLD), (px, py)); py += 16
        for mat_id, qty in bp.recipe.items():
            mat  = MATERIALS.get(mat_id)
            if not mat: continue
            have = self.player.materials.get(mat_id, 0)
            clr  = (100, 220, 100) if have >= qty else COLOR_ERROR
            draw_icon(screen, mat_id, mat.icon, px + 4, py, size=16)
            screen.blit(fsm.render(f" {mat.name}: {have}/{qty}", True, clr), (px + 22, py)); py += 16

        # Статус
        can = ob.can_craft(self.player.materials)
        q   = self.player.crafting_queue
        py += 4
        if ob.is_broken:
            screen.blit(fsm.render("💥 Кресленик зламаний!", True, COLOR_ERROR), (px, py))
        elif len(q.orders) >= q.MAX_SLOTS:
            screen.blit(fsm.render("⚠ Черга повна!", True, COLOR_ERROR), (px, py))
        elif can:
            screen.blit(fsm.render("✓ Можна скувати!", True, (100, 220, 100)), (px, py))
        else:
            screen.blit(fsm.render("✗ Не вистачає матеріалів", True, COLOR_ERROR), (px, py))

        # Кнопка дії
        self.scene.action_btn.enabled = can and len(q.orders) < q.MAX_SLOTS and not ob.is_broken
        self.scene.action_btn.draw(screen)

    def _draw_smelt_info(self, screen):
        if self.scene.sel == -1 or self.scene.sel >= len(SMELT_RECIPES):
            screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
                "← Вибери рецепт", True, COLOR_TEXT_DIM), (INFO_X, LIST_Y + 20))
            self.scene.action_btn.enabled = False
            self.scene.action_btn.draw(screen)
            return

        from_mat, from_qty, to_mat, to_qty, label = SMELT_RECIPES[self.scene.sel]
        fm   = MATERIALS.get(from_mat)
        tm   = MATERIALS.get(to_mat)
        have = self.player.materials.get(from_mat, 0)

        panel_h = QUEUE_Y - LIST_Y - 12
        surf = pygame.Surface((INFO_W, panel_h), pygame.SRCALPHA)
        surf.fill((15, 12, 8, 210))
        pygame.draw.rect(surf, COLOR_GOLD, surf.get_rect(), 1, border_radius=8)
        screen.blit(surf, (INFO_X, LIST_Y))

        px, py = INFO_X + 14, LIST_Y + 12
        fh  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)

        screen.blit(fh.render(f"🔥 {label}", True, COLOR_GOLD), (px, py)); py += 28
        screen.blit(fsm.render(f"{fm.icon} {fm.name} ×{from_qty} → {tm.icon} {tm.name}",
                               True, COLOR_TEXT), (px, py)); py += 22
        screen.blit(fsm.render(f"Маєш: {have}", True, COLOR_TEXT), (px, py)); py += 18
        batches = have // from_qty
        screen.blit(fsm.render(f"Вихід: {batches} зливків", True,
            (100, 220, 100) if batches > 0 else COLOR_ERROR), (px, py)); py += 18

        if tm and (tm.bonus_attack or tm.bonus_defense or tm.bonus_hp or tm.bonus_crit):
            py += 6
            screen.blit(fsm.render("✦ Бонус у крафті:", True, (200, 180, 100)), (px, py)); py += 16
            if tm.bonus_attack:  screen.blit(fsm.render(f"  ⚔ +{tm.bonus_attack} ATK", True, (160, 220, 160)), (px, py)); py += 16
            if tm.bonus_defense: screen.blit(fsm.render(f"  🛡 +{tm.bonus_defense} DEF", True, (160, 220, 160)), (px, py)); py += 16
            if tm.bonus_hp:      screen.blit(fsm.render(f"  ❤ +{tm.bonus_hp} HP", True, (160, 220, 160)), (px, py)); py += 16
            if tm.bonus_crit:    screen.blit(fsm.render(f"  🎯 +{tm.bonus_crit*100:.0f}% крит", True, (160, 220, 160)), (px, py)); py += 16

        self.scene.action_btn.enabled = batches > 0
        self.scene.action_btn.draw(screen)

    # ── Scrollbar ─────────────────────────────────────────────────

    def _draw_scrollbar(self, screen):
        if self.scene.mode != "craft": return
        total = len(self.player.blueprints)
        if total <= VISIBLE: return
        bar_h   = VISIBLE * ROW_H
        bar_x   = LIST_X + LIST_W + 6
        thumb_h = max(30, bar_h * VISIBLE // total)
        thumb_y = LIST_Y + (bar_h - thumb_h) * self.scene.scroll // max(1, total - VISIBLE)
        pygame.draw.rect(screen, (40, 38, 30), (bar_x, LIST_Y, 8, bar_h), border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD, (bar_x, thumb_y, 8, thumb_h), border_radius=4)

    # ── Повідомлення ──────────────────────────────────────────────

    def _draw_msg(self, screen):
        if self.scene.craft_msg_t <= 0: return
        alpha = min(255, int(self.scene.craft_msg_t * 100))
        mut   = self.scene._msg_mutation
        clr   = mut.color if mut else ((200, 80, 80) if self.scene._msg_error else (100, 220, 100))
        font  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        surf  = font.render(self.scene.craft_msg, True, clr)
        surf.set_alpha(alpha)
        # Показуємо над чергою, завжди у видимій зоні
        msg_y = QUEUE_Y - 32
        screen.blit(surf, (_SW // 2 - surf.get_width() // 2, msg_y))

    def _collect_all_done(self):
        """Забирає і скрафчені і розібрані предмети."""
        self.scene._collect_done()
        self.scene._collect_dismantled()

    # ── Список розбирання ─────────────────────────────────────────

    def _draw_dismantle_list(self, screen):
        from game.crafting_queue import dismantle_cost, dismantle_time, fmt_time, _item_tier
        from game.mutations import get_mutation, RARITY_COLOR
        font    = assets.get_font(FONT_SIZE_NORMAL)
        font_sm = assets.get_font(FONT_SIZE_SMALL)
        mp      = pygame.mouse.get_pos()
        items   = self.scene._dismantle_items()

        bg = pygame.Surface((LIST_W, VISIBLE * ROW_H), pygame.SRCALPHA)
        bg.fill((10, 8, 6, 180)); screen.blit(bg, (LIST_X, LIST_Y))

        if not items:
            screen.blit(font.render("Немає зброї чи броні для розбирання.", True, COLOR_TEXT_DIM),
                        (LIST_X + 20, LIST_Y + 20))
            return

        for i, item in enumerate(items[self.scene.scroll: self.scene.scroll + VISIBLE]):
            r   = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)
            mut = get_mutation(item)
            bg_clr = (80, 30, 30, 210) if i == self.scene.sel else \
                     (55, 35, 30, 190) if r.collidepoint(mp) else \
                     (22, 18, 14, 160) if i % 2 == 0 else (28, 22, 18, 160)
            s = pygame.Surface((LIST_W, ROW_H - 4), pygame.SRCALPHA); s.fill(bg_clr)
            screen.blit(s, r.topleft)

            border_clr = mut.color if mut else ((180, 100, 60) if i == self.scene.sel else (60, 50, 40))
            if i == self.scene.sel:
                pygame.draw.rect(screen, border_clr, r, 2, border_radius=3)

            # Назва
            name_clr = mut.color if mut else COLOR_TEXT
            tp = "⚔" if item.item_type == "weapon" else "🛡"
            stat = f"+{item.attack_bonus} ATK" if item.item_type == "weapon" \
                   else f"+{item.defense_bonus} DEF"
            draw_icon(screen, item.item_id, item.icon, _icon_x := LIST_X + 10, _icon_y := LIST_Y + i * ROW_H + (ROW_H - 28) // 2, size=28)
            screen.blit(font.render(f" {tp} {item.name}  {stat}", True, name_clr),
                        (r.x + 10, r.y + 6))

            # Ціна і час
            cost = dismantle_cost(item)
            t    = fmt_time(dismantle_time(item))
            cost_clr = COLOR_GOLD if self.player.gold >= cost else COLOR_ERROR
            right_txt = f"💰{cost}  ⏱{t}"
            rs = font_sm.render(right_txt, True, cost_clr)
            screen.blit(rs, (r.right - rs.get_width() - 10, r.y + 8))

            # Шанс повернення
            tier = _item_tier(item)
            from game.crafting_queue import DISMANTLE_RETURN
            pct  = int(DISMANTLE_RETURN[tier] * 100)
            screen.blit(font_sm.render(f"~{pct}% матеріалів назад", True, (160, 160, 160)),
                        (r.x + 14, r.y + 36))

        total = len(items)
        screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
            f"{self.scene.scroll+1}–{min(self.scene.scroll+VISIBLE,total)} з {total}", True, COLOR_TEXT_DIM),
            (LIST_X, LIST_Y + VISIBLE * ROW_H + 4))

    # ── Інфо-панель розбирання ────────────────────────────────────

    def _draw_dismantle_info(self, screen):
        from game.crafting_queue import (dismantle_cost, dismantle_time, fmt_time,
                                         dismantle_preview, _item_tier, DISMANTLE_RETURN)
        from game.mutations import get_mutation, RARITY_COLOR, RARITY_NAME_UA
        from game.data import MATERIALS

        items   = self.scene._dismantle_items()
        abs_idx = self.scene.scroll + self.scene.sel
        if self.scene.sel < 0 or abs_idx >= len(items):
            screen.blit(assets.get_font(FONT_SIZE_SMALL).render(
                "← Вибери предмет для розбирання", True, COLOR_TEXT_DIM),
                (INFO_X, LIST_Y + 20))
            self.scene.action_btn.enabled = False
            self.scene.action_btn.draw(screen)
            return

        item = items[abs_idx]
        mut  = get_mutation(item)
        cost = dismantle_cost(item)
        dur  = dismantle_time(item)
        tier = _item_tier(item)
        pct  = int(DISMANTLE_RETURN[tier] * 100)
        preview = dismantle_preview(item)

        panel_h = QUEUE_Y - LIST_Y - 12
        surf = pygame.Surface((INFO_W, panel_h), pygame.SRCALPHA)
        surf.fill((25, 12, 10, 210))
        border_clr = mut.color if mut else (160, 80, 60)
        pygame.draw.rect(surf, border_clr, surf.get_rect(), 1, border_radius=8)
        screen.blit(surf, (INFO_X, LIST_Y))

        px, py = INFO_X + 14, LIST_Y + 12
        fh  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)

        name_clr = mut.color if mut else COLOR_GOLD
        draw_icon(screen, item.item_id, item.icon, px, py, size=28)
        screen.blit(fh.render(item.name, True, name_clr), (px + 34, py + 2)); py += 34

        # Мутація
        if mut:
            rar_clr = RARITY_COLOR.get(mut.rarity, COLOR_TEXT)
            screen.blit(fsm.render(f"✦ {mut.icon} {RARITY_NAME_UA.get(mut.rarity,'')}: {mut.name}",
                                   True, rar_clr), (px, py)); py += 20

        # Стати
        if item.item_type == "weapon":
            screen.blit(fsm.render(f"⚔ Атака: +{item.attack_bonus}", True, COLOR_TEXT), (px, py)); py += 18
        else:
            screen.blit(fsm.render(f"🛡 Захист: +{item.defense_bonus}", True, COLOR_TEXT), (px, py)); py += 18
            if item.hp_bonus:
                screen.blit(fsm.render(f"❤ HP: +{item.hp_bonus}", True, COLOR_TEXT), (px, py)); py += 18

        # Умови розбирання
        py += 6
        screen.blit(fsm.render(f"⏱ Час: {fmt_time(dur)}", True, (160, 180, 220)), (px, py)); py += 18
        cost_clr = COLOR_GOLD if self.player.gold >= cost else COLOR_ERROR
        screen.blit(fsm.render(f"💰 Вартість: {cost} золота", True, cost_clr), (px, py)); py += 18
        screen.blit(fsm.render(f"📊 Шанс повернення: ~{pct}% кожного", True, (180, 160, 120)),
                    (px, py)); py += 20

        # Очікуваний вихід
        if preview:
            screen.blit(fsm.render("📦 Орієнтовний вихід:", True, COLOR_GOLD), (px, py)); py += 16
            for mat_id, exp_qty in preview.items():
                mat = MATERIALS.get(mat_id)
                if not mat: continue
                # Показуємо у форматі "іконка назва: ~X"
                screen.blit(fsm.render(
                    f"  {mat.icon} {mat.name}: ~{exp_qty:.1f}", True, (160, 200, 160)),
                    (px, py)); py += 15
        else:
            screen.blit(fsm.render("⚠ Рецепт невідомий - матеріали орієнтовні",
                                   True, COLOR_TEXT_DIM), (px, py)); py += 18

        # Кнопка
        dq  = self.player.dismantle_queue
        can = (self.player.gold >= cost and len(dq.orders) < dq.MAX_SLOTS)
        if len(dq.orders) >= dq.MAX_SLOTS:
            screen.blit(fsm.render("⚠ Черга розбирання повна!", True, COLOR_ERROR), (px, py))
        elif self.player.gold < cost:
            screen.blit(fsm.render(f"⚠ Не вистачає {cost - self.player.gold} 🪙", True, COLOR_ERROR),
                        (px, py))
        self.scene.action_btn.enabled = can
        self.scene.action_btn.draw(screen)

    def _draw_dismantle_queue_slots(self, screen, dq):
        """Компактні слоти черги розбирання - правий бік панелі черги."""
        import math as _math
        from game.crafting_queue import fmt_time
        font = assets.get_font(FONT_SIZE_SMALL)

        base_x = QUEUE_X + QUEUE_W // 2 + 30
        base_y = QUEUE_Y + 38
        slot_w = (QUEUE_W // 2 - 50) // dq.MAX_SLOTS

        for i, order in enumerate(dq.orders):
            sx = base_x + i * (slot_w + 6)
            sy = base_y
            sh = QUEUE_H - 55
            done = order.is_done()
            clr  = (100, 220, 100) if done else (180, 130, 60)

            sl = pygame.Surface((slot_w, sh), pygame.SRCALPHA)
            sl.fill((25, 18, 12, 220))
            screen.blit(sl, (sx, sy))
            pygame.draw.rect(screen, clr, (sx, sy, slot_w, sh), 2, border_radius=6)

            name = order.item_data.get("name", "???")[:18]
            icon = order.item_data.get("icon", "⚔")
            screen.blit(font.render(f"{icon} {name}", True, COLOR_TEXT_DIM), (sx + 6, sy + 6))

            # Прогрес-бар
            from game.crafting_queue import dismantle_time
            from game.save_manager import _deserialize_item
            item = _deserialize_item(order.item_data)
            total = dismantle_time(item) if item else 60
            left  = order.seconds_left()
            pct   = 1.0 - (left / total) if total > 0 else 1.0
            bw = slot_w - 12
            pygame.draw.rect(screen, (40, 35, 28), (sx + 6, sy + 28, bw, 8), border_radius=3)
            if int(bw * pct) > 0:
                pygame.draw.rect(screen, clr, (sx + 6, sy + 28, int(bw * pct), 8), border_radius=3)

            if done:
                alpha = int(180 + 75 * _math.sin(self.scene._anim_t * 4))
                ds = font.render("✓ ГОТОВО!", True, (100, 255, 100))
                ds.set_alpha(alpha)
                screen.blit(ds, (sx + slot_w // 2 - ds.get_width() // 2, sy + 42))
            else:
                screen.blit(font.render(f"⏱ {fmt_time(left)}", True, (180, 160, 120)),
                            (sx + 6, sy + 42))