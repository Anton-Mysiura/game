"""
Рендерер для InventoryScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/inventory.py
"""
from game.data import MATERIALS
from game.data import RARITY_COLOR
from game.mutations import get_mutation
from game.mutations import RARITY_NAME_UA
import pygame
from scenes.ui.base_renderer import BaseRenderer

import logging
from ui.components import Button, Panel, InventoryGrid
from ui.constants import *
from ui.assets import assets
from ui.confirm_dialog import ConfirmDialog
from ui.dropdown import Dropdown
from ui.icons import draw_icon, get_icon_surf


class InventoryRenderer(BaseRenderer):
    """
    Малює InventoryScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,150)); screen.blit(ov, (0,0))
        self.scene.main_panel.draw(screen)
        ft = assets.get_font(FONT_SIZE_HUGE, bold=True)
        screen.blit(ft.render("🎒 Інвентар", True, COLOR_GOLD), (100, 68))
        gs = assets.get_font(FONT_SIZE_MEDIUM).render(f"💰 {self.scene.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gs, (SCREEN_WIDTH - 300, 68))

        if self.scene._active_filter == "material":
            self.scene._filter_dd.draw(screen)
            self._draw_materials_list(screen)
            self.scene.close_button.draw(screen)
            if self.scene._confirm: self.scene._confirm.draw(screen)
            return

        filtered = self.scene._filtered_items()
        self.scene.inventory_grid.draw(screen, filtered)
        self._draw_grid_badges(screen, filtered)
        fsm = assets.get_font(FONT_SIZE_SMALL)
        gbot = self.scene.inventory_grid.y + 4 * (64+5)
        screen.blit(fsm.render(f"{len(filtered)} / {len(self.scene.player.inventory)} предметів",
            True, COLOR_TEXT_DIM), (100, gbot+6))

        fb = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        fn = assets.get_font(FONT_SIZE_NORMAL)
        screen.blit(fb.render("Екіпіровано:", True, COLOR_GOLD), (100, 500))
        ey = 530
        if self.scene.player.equipped_weapon:
            screen.blit(fn.render(f"⚔ {self.scene.player.equipped_weapon.name} (+{self.scene.player.equipped_weapon.attack_bonus} ATK)", True, COLOR_TEXT), (100, ey)); ey += 28
        if self.scene.player.equipped_armor:
            screen.blit(fn.render(f"🛡 {self.scene.player.equipped_armor.name} (+{self.scene.player.equipped_armor.defense_bonus} DEF)", True, COLOR_TEXT), (100, ey))

        self.scene.info_panel.draw(screen)
        item = self.scene._real_item()
        if item: self._draw_item_info(screen, item)
        if self.scene._show_compare and item and item.item_type in ("weapon","armor"):
            self._draw_compare(screen, item)

        self.scene.close_button.draw(screen)
        is_gear = item and item.item_type in ("weapon","armor")
        is_pot  = item and item.item_type == "potion"
        is_tool = item and item.item_type == "tool"
        in_dis  = bool(item and any(o.item_data.get("item_id")==item.item_id
                                    for o in self.scene.player.dismantle_queue.orders))
        self.scene.equip_button.enabled  = bool(is_gear)
        self.scene.use_button.enabled    = bool(is_pot)
        self.scene.sell_button.enabled   = bool(item and not is_tool)
        self.scene.dismantle_btn.enabled = bool(is_gear and not in_dis)
        self.scene.equip_button.draw(screen)
        self.scene.use_button.draw(screen)
        if is_gear:
            self.scene.sell_button.draw(screen)
            self.scene.dismantle_btn.draw(screen)
        elif is_tool:
            # Інструменти не продаються — показуємо підказку
            fi = assets.get_font(FONT_SIZE_SMALL)
            hint = fi.render("🛠 Використовується в шахті", True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH // 2 + 220, 465))
            if item.item_id == "broken_pickaxe":
                hint2 = fi.render("🔨 Полагодь у майстерні (вкл. Ремонт)", True, COLOR_ERROR)
                screen.blit(hint2, (SCREEN_WIDTH // 2 + 220, 487))
        elif item:
            self.scene.sell_button.draw(screen)
        hp_pots = [i for i in self.scene.player.inventory if i.item_type=="potion" and i.hp_restore>0]
        if hp_pots:
            self.scene.heal_all_btn.enabled = self.scene.player.hp < self.scene.player.total_max_hp
            self.scene.heal_all_btn.text = f"💊 Вжити зілля до макс. HP  ({len(hp_pots)}шт)"
            self.scene.heal_all_btn.draw(screen)

        # Dropdown-и — поверх усього (перекривають грид)
        self.scene._filter_dd.draw(screen)
        self.scene._sort_dd.draw(screen)

        # ── Кнопка "Продати непотрібне" ──
        self._draw_sell_junk_btn(screen)

        # ── Tooltip ──
        if self.scene._tooltip_item:
            self._draw_tooltip(screen, self.scene._tooltip_item, self.scene._tooltip_pos)

        if self.scene._confirm: self.scene._confirm.draw(screen)

    def _draw_grid_badges(self, screen, items: list):
        """Малює маленькі кольорові бейджи типу і кількості в куті кожного слоту."""
        TYPE_COLORS = {
            "weapon":   (220, 130,  60),
            "armor":    ( 80, 140, 220),
            "potion":   ( 80, 200, 150),
            "tool":     (180, 180,  60),
            "material": (140, 140, 140),
        }
        TYPE_ICONS = {
            "weapon": "⚔", "armor": "🛡", "potion": "🧪",
            "tool": "🛠", "material": "🪨",
        }
        font = assets.get_font(10)
        active_filter = self.scene._active_filter

        for i, item in enumerate(items):
            if i >= self.scene.inventory_grid.cols * self.scene.inventory_grid.rows:
                break
            if not item:
                continue
            col = i % self.scene.inventory_grid.cols
            row = i // self.scene.inventory_grid.cols
            sx  = self.scene.inventory_grid.x + col * (64 + 5)
            sy  = self.scene.inventory_grid.y + row * (64 + 5)

            itype = getattr(item, "item_type", "")
            color = TYPE_COLORS.get(itype, (160, 160, 160))

            # Бейдж типу — тільки якщо фільтр "all"
            if active_filter == "all":
                ico = TYPE_ICONS.get(itype, "")
                if ico:
                    badge = font.render(ico, True, color)
                    screen.blit(badge, (sx + 2, sy + 2))

            # Кількість для зілля
            if itype == "potion":
                count = sum(1 for x in self.scene.player.inventory
                            if getattr(x, "item_id", "") == item.item_id)
                if count > 1:
                    cnt_s = font.render(str(count), True, (255, 255, 255))
                    screen.blit(cnt_s, (sx + 64 - cnt_s.get_width() - 3, sy + 64 - 14))

            # Зламане кайло — червона рамка
            if getattr(item, "item_id", "") == "broken_pickaxe":
                pygame.draw.rect(screen, (220, 60, 60),
                                 pygame.Rect(sx, sy, 64, 64), 2)

    def _draw_materials_list(self, screen):
        mats = sorted(
            [(mid, qty) for mid,qty in self.scene.player.materials.items() if qty>0],
            key=lambda x: (MATERIALS[x[0]].rarity if x[0] in MATERIALS else "zzz",
                           MATERIALS[x[0]].name   if x[0] in MATERIALS else x[0]))
        if not mats:
            f = assets.get_font(FONT_SIZE_NORMAL)
            m = f.render("Матеріалів немає. Збирай лут з ворогів!", True, COLOR_TEXT_DIM)
            screen.blit(m, (SCREEN_WIDTH//2 - m.get_width()//2, 350)); return
        LX=100; LY=210; CW=280; RH=30; VIS=14
        fh=assets.get_font(FONT_SIZE_NORMAL,bold=True)
        fn=assets.get_font(FONT_SIZE_NORMAL)
        fs=assets.get_font(FONT_SIZE_SMALL)
        RUA={"common":"Звичайні","uncommon":"Незвичайні","rare":"Рідкісні",
             "epic":"Епічні","legendary":"Легендарні","":"Інші"}
        RC ={"common":(160,160,160),"uncommon":(80,200,80),"rare":(80,140,220),
             "epic":(180,80,220),"legendary":(220,160,40),"":(140,140,140)}
        for ci in range(2):
            cx=LX+ci*CW
            screen.blit(fh.render("Матеріал",True,COLOR_GOLD),(cx+30,LY-22))
            screen.blit(fh.render("Кіл.",True,COLOR_GOLD),(cx+210,LY-22))
        pygame.draw.line(screen,COLOR_GOLD,(LX,LY-6),(LX+CW*2,LY-6),1)
        rows=[]; lr=None
        for mid,qty in mats:
            mat=MATERIALS.get(mid); r=mat.rarity if mat else ""
            if r!=lr: rows.append(("h",r)); lr=r
            rows.append(("m",mid,qty))
        ms=max(0,len(rows)-VIS*2); self.scene._mat_scroll=min(self.scene._mat_scroll,ms)
        vis=rows[self.scene._mat_scroll:self.scene._mat_scroll+VIS*2]
        lc=vis[:VIS]; rc2=vis[VIS:]
        for ci,col in enumerate((lc,rc2)):
            cx=LX+ci*CW
            for ri,row in enumerate(col):
                ry=LY+ri*RH
                if row[0]=="h":
                    clr=RC.get(row[1],(140,140,140))
                    screen.blit(fs.render(f"── {RUA.get(row[1],row[1])} ──",True,clr),(cx,ry+6))
                else:
                    _,mid,qty=row; mat=MATERIALS.get(mid)
                    if not mat: continue
                    clr=RC.get(mat.rarity,(160,160,160))
                    draw_icon(screen, mid, mat.icon, cx, ry, size=22)
                    nm=mat.name; ns=fn.render(nm,True,COLOR_TEXT)
                    if ns.get_width()>160:
                        while fn.size(nm)[0]>160 and len(nm)>3: nm=nm[:-1]
                        ns=fn.render(nm+"…",True,COLOR_TEXT)
                    screen.blit(ns,(cx+28,ry))
                    qs=fn.render(f"×{qty}",True,clr)
                    screen.blit(qs,(cx+CW-qs.get_width()-8,ry))
        if len(rows)>VIS*2:
            sbx=LX+CW*2+10; sby=LY; sbh=VIS*RH
            th=max(18,sbh*(VIS*2)//len(rows))
            ty=sby+int((sbh-th)*self.scene._mat_scroll/ms) if ms else sby
            pygame.draw.rect(screen,(40,36,28),(sbx,sby,8,sbh),border_radius=4)
            pygame.draw.rect(screen,COLOR_GOLD,(sbx,ty,8,th),border_radius=4)
            screen.blit(fs.render("↑↓",True,COLOR_TEXT_DIM),(sbx-2,sby+sbh+4))
        ts=fs.render(f"Видів: {len(mats)}   Одиниць: {sum(q for _,q in mats)}",True,COLOR_TEXT_DIM)
        screen.blit(ts,(LX,LY+VIS*RH+8))

    def _draw_item_info(self, screen, item):
        x0=SCREEN_WIDTH//2+220
        mut=get_mutation(item)
        draw_icon(screen, item.item_id, item.icon, SCREEN_WIDTH//2+280, 218, size=48)
        fn=assets.get_font(FONT_SIZE_MEDIUM,bold=True)
        screen.blit(fn.render(item.name,True,mut.color if mut else COLOR_TEXT),(x0,278))
        fi=assets.get_font(FONT_SIZE_SMALL)
        screen.blit(fi.render(f"Тип: {item.item_type}",True,COLOR_TEXT_DIM),(x0,313))
        y=338
        if item.item_type=="weapon":
            screen.blit(fi.render(f"+{item.attack_bonus} ATK",True,CLR_BETTER),(x0,y)); y+=22
            if item.crit_bonus:
                screen.blit(fi.render(f"+{item.crit_bonus*100:.0f}% крит",True,CLR_BETTER),(x0,y)); y+=22
        elif item.item_type=="armor":
            screen.blit(fi.render(f"+{item.defense_bonus} DEF",True,CLR_BETTER),(x0,y)); y+=22
            if item.hp_bonus:
                screen.blit(fi.render(f"+{item.hp_bonus} HP",True,CLR_BETTER),(x0,y)); y+=22
        elif item.item_type == "tool":
            screen.blit(fi.render(item.description, True, CLR_BETTER), (x0, y)); y+=22
            if item.item_id == "pickaxe":
                screen.blit(fi.render("⛏ Обов'язковий для шахтаря", True, (180,200,140)), (x0, y)); y+=22
            elif item.item_id == "shovel":
                screen.blit(fi.render("🪣 Прискорює копання на 10%", True, (180,200,140)), (x0, y)); y+=22
            elif item.item_id == "broken_pickaxe":
                screen.blit(fi.render("🔨 Полагодь у майстерні", True, COLOR_ERROR), (x0, y)); y+=22
        elif item.item_type in ("potion","material"):
            screen.blit(fi.render(item.description,True,CLR_BETTER),(x0,y)); y+=22
        if mut:
            y+=4; rc=RARITY_COLOR.get(mut.rarity,COLOR_TEXT)
            screen.blit(fi.render(f"✦ {mut.icon} {RARITY_NAME_UA.get(mut.rarity,'')}: {mut.name}",True,rc),(x0,y)); y+=20
            screen.blit(fi.render(f"   {mut.desc}",True,rc),(x0,y)); y+=20
        y+=4; price=max(1,item.value//2); warn="  ⚠" if item.value>=EXPENSIVE_THRESHOLD else ""
        screen.blit(fi.render(f"💰 Продаж: {price} 🪙{warn}",True,(255,180,60) if warn else COLOR_GOLD),(x0,y))

    def _draw_compare(self, screen, new_item):
        self.scene.cmp_panel.draw(screen)
        fh=assets.get_font(FONT_SIZE_NORMAL,bold=True)
        fn=assets.get_font(FONT_SIZE_NORMAL)
        fs=assets.get_font(FONT_SIZE_SMALL)
        if new_item.item_type=="weapon":
            cur=self.scene.player.equipped_weapon; nv=new_item.attack_bonus
            cv=cur.attack_bonus if cur else 0; sl="ATK"; si="⚔"
        else:
            cur=self.scene.player.equipped_armor; nv=new_item.defense_bonus
            cv=cur.defense_bonus if cur else 0; sl="DEF"; si="🛡"
        d=nv-cv
        ts=fh.render("⚖ Порівняння",True,COLOR_GOLD)
        screen.blit(ts,(CMP_X+CMP_W//2-ts.get_width()//2,CMP_Y+10))
        pygame.draw.line(screen,COLOR_GOLD,(CMP_X+20,CMP_Y+40),(CMP_X+CMP_W-20,CMP_Y+40),1)
        cc=CMP_X+30; cn=CMP_X+CMP_W//2+20; cw=CMP_W//2-50; ry=CMP_Y+52
        screen.blit(fs.render("Зараз екіпіровано",True,COLOR_TEXT_DIM),(cc,ry))
        screen.blit(fs.render("Вибраний предмет", True,COLOR_GOLD),(cn,ry)); ry+=22
        pygame.draw.line(screen,(80,70,60),(CMP_X+CMP_W//2,CMP_Y+48),(CMP_X+CMP_W//2,CMP_Y+CMP_H-18),1)
        def tr(t,f,mw):
            while f.size(t)[0]>mw and len(t)>3: t=t[:-1]
            return t
        screen.blit(fn.render(tr(cur.name if cur else "— нічого —",fn,cw),True,COLOR_TEXT_DIM if not cur else COLOR_TEXT),(cc,ry))
        screen.blit(fn.render(tr(new_item.name,fn,cw),True,COLOR_TEXT),(cn,ry)); ry+=34
        if cur: draw_icon(screen, cur.item_id, cur.icon, cc+20, ry, size=36)
        draw_icon(screen, new_item.item_id, new_item.icon, cn+20, ry, size=36); ry+=48
        screen.blit(fn.render(f"{si} +{cv} {sl}" if cur else f"{si} — {sl}",True,COLOR_TEXT_DIM if not cur else COLOR_TEXT),(cc,ry))
        screen.blit(fn.render(f"{si} +{nv} {sl}",True,_stat_color(d if cur else 1)),(cn,ry)); ry+=30
        pygame.draw.line(screen,(80,70,60),(CMP_X+20,ry),(CMP_X+CMP_W-20,ry),1); ry+=10
        if not cur:   rtxt=f"★ +{nv} {sl}"; rclr=CLR_NEW;    atxt="Перше екіпірування!"
        elif d>0:     rtxt=f"+{d} {sl} ▲";  rclr=CLR_BETTER; atxt="Покращення!"
        elif d<0:     rtxt=f"{d} {sl} ▼";   rclr=CLR_WORSE;  atxt="Погіршення"
        else:         rtxt=f"= {sl}";         rclr=CLR_SAME;   atxt="Без змін"
        rs=assets.get_font(FONT_SIZE_LARGE,bold=True).render(rtxt,True,rclr)
        as_=fs.render(atxt,True,rclr)
        screen.blit(rs, (CMP_X+CMP_W//2-rs.get_width()//2,  ry))
        screen.blit(as_,(CMP_X+CMP_W//2-as_.get_width()//2, ry+30))

    def _draw_tooltip(self, screen, item, pos):
        """Маленький tooltip при наведенні на предмет."""
        font = assets.get_font(FONT_SIZE_SMALL)
        lines = [item.name]
        if item.item_type == "weapon":
            lines.append(f"⚔ +{item.attack_bonus} ATK")
        elif item.item_type == "armor":
            lines.append(f"🛡 +{item.defense_bonus} DEF")
            if item.hp_bonus: lines.append(f"❤ +{item.hp_bonus} HP")
        elif item.item_type == "potion":
            if item.hp_restore: lines.append(f"🧪 +{item.hp_restore} HP")
        mut = get_mutation(item)
        if mut:
            lines.append(f"✦ {RARITY_NAME_UA.get(mut.rarity,'')}: {mut.name}")
        lines.append(f"💰 {max(1, item.value//2)} 🪙")

        pad = 8
        w = max(font.size(l)[0] for l in lines) + pad * 2
        h = len(lines) * 18 + pad * 2
        mx, my = pos
        tx = min(mx + 14, SCREEN_WIDTH  - w - 4)
        ty = min(my + 14, SCREEN_HEIGHT - h - 4)

        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((18, 14, 10, 220))
        border_col = mut.color if mut else COLOR_GOLD
        pygame.draw.rect(bg, border_col, bg.get_rect(), 1, border_radius=5)
        screen.blit(bg, (tx, ty))

        y = ty + pad
        name_col = mut.color if mut else COLOR_TEXT
        for i, line in enumerate(lines):
            col = name_col if i == 0 else (COLOR_TEXT_DIM if line.startswith("💰") else COLOR_TEXT)
            screen.blit(font.render(line, True, col), (tx + pad, y))
            y += 18

    def _draw_sell_junk_btn(self, screen):
        """Кнопка 'Продати непотрібне' — все окрім зілля і екіпіровки."""
        junk = [i for i in self.scene.player.inventory
                if i.item_type not in ("potion",)
                and i != self.scene.player.equipped_weapon
                and i != self.scene.player.equipped_armor]
        if not junk:
            return
        total = sum(max(1, i.value // 2) for i in junk)
        font  = assets.get_font(FONT_SIZE_SMALL)
        lbl   = f"🗑 Продати непотрібне ({len(junk)} шт, {total}🪙)"
        surf  = font.render(lbl, True, (200, 160, 80))
        mp    = pygame.mouse.get_pos()
        bx, by = 430, SCREEN_HEIGHT - 70
        bw, bh = surf.get_width() + 20, 30
        bg_col = (60, 45, 15) if pygame.Rect(bx, by, bw, bh).collidepoint(mp) else (40, 30, 10)
        pygame.draw.rect(screen, bg_col, (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(screen, (140, 110, 40), (bx, by, bw, bh), 1, border_radius=6)
        screen.blit(surf, (bx + 10, by + 6))