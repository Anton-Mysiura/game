"""
Рендерер для ShopScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/shop.py
"""
from scenes.core.elder import INFO_W, INFO_X, LIST_W, LIST_X, LIST_Y, ROW_H, VISIBLE
from game.data import MATERIALS
import pygame
from scenes.ui.base_renderer import BaseRenderer

import logging
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from ui.icons import draw_icon, get_icon_surf


class ShopRenderer(BaseRenderer):
    """
    Малює ShopScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        self.scene.shop_panel.draw(screen)

        self._draw_header(screen)
        self._draw_tabs(screen)
        self._draw_list(screen)
        self._draw_info(screen)
        self._draw_scrollbar(screen)

        # Оновлюємо текст кнопки купити з ціною і qty
        rows = self.scene._rows()
        abs_idx = self.scene.scroll + self.scene.sel
        if self.scene.sel != -1 and abs_idx < len(rows):
            thing, price = rows[abs_idx]
            qty = self.scene._buy_qty if self.scene.tab == "items" else 1
            total = price * qty
            suffix = f" ×{qty}" if qty > 1 else ""
            owned  = self.scene.tab == "blueprints" and thing in self.scene.player.blueprints
            self.scene.buy_btn.text    = "✓ Вже куплено" if owned else f"💰 Купити{suffix}  {total}🪙"
            self.scene.buy_btn.enabled = not owned and self.scene.player.gold >= total
        else:
            self.scene.buy_btn.text    = "💰 Купити"
            self.scene.buy_btn.enabled = False

        self.scene.buy_btn.draw(screen)
        self.scene.exit_btn.draw(screen)

        # Кнопки qty — тільки для товарів
        if self.scene.tab == "items":
            for i, btn in enumerate(self.scene.qty_btns):
                btn.selected = (self.scene._buy_qty == [1, 5, 10][i])
                btn.draw(screen)

    def _draw_header(self, screen):
        font   = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_n = assets.get_font(FONT_SIZE_NORMAL)
        font_s = assets.get_font(FONT_SIZE_SMALL)
        screen.blit(font.render("🏪 Крамниця Барнуса", True, COLOR_GOLD), (LIST_X, 38))
        gold = font_n.render(f"💰 {self.scene.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold, (SCREEN_WIDTH - gold.get_width() - 50, 42))

        # ── Поле пошуку ───────────────────────────────────────
        search_rect = pygame.Rect(LIST_X + 370, 38, 220, 32)
        border_col  = COLOR_GOLD if self.scene._search_active else (80, 70, 50)
        pygame.draw.rect(screen, (20, 16, 10), search_rect, border_radius=6)
        pygame.draw.rect(screen, border_col,   search_rect, 1, border_radius=6)
        display = self.scene._search_text + ("|" if self.scene._search_active else "")
        hint    = display if display else "🔍 Пошук..."
        col     = COLOR_TEXT if self.scene._search_text else COLOR_TEXT_DIM
        t = font_s.render(hint, True, col)
        screen.blit(t, (search_rect.x + 8, search_rect.y + 8))

    def _draw_tabs(self, screen):
        for i, btn in enumerate(self.scene.tab_btns):
            btn.selected = (i == 0 and self.scene.tab == "items") or \
                           (i == 1 and self.scene.tab == "blueprints")
            btn.draw(screen)

    def _draw_list(self, screen):
        font     = assets.get_font(FONT_SIZE_NORMAL)
        font_sm  = assets.get_font(FONT_SIZE_SMALL)
        mp       = pygame.mouse.get_pos()
        vis_rows = self.scene._visible_rows()

        # Фон списку
        list_bg = pygame.Surface((LIST_W, VISIBLE * ROW_H), pygame.SRCALPHA)
        list_bg.fill((10, 8, 6, 180))
        screen.blit(list_bg, (LIST_X, LIST_Y))

        for i, (thing, price) in enumerate(vis_rows):
            r = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 4)

            # Фон рядка
            if i == self.scene.sel:
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

            if i == self.scene.sel:
                pygame.draw.rect(screen, COLOR_GOLD, r, 1, border_radius=3)

            # Ім'я
            if self.scene.tab == "items":
                icon = thing.icon
                name = thing.name
                sub  = thing.description
            else:
                icon = "📜"
                owned = any(ob.blueprint_id == thing.blueprint_id for ob in self.scene.player.blueprints)
                name  = thing.result_name + (" ✓" if owned else "")
                tp    = "⚔" if thing.result_type == "weapon" else "🛡"
                sub   = f"{tp} {thing.result_desc[:45]}"

            name_clr = (160, 160, 160) if (self.scene.tab == "blueprints" and
                        any(ob.blueprint_id == thing.blueprint_id for ob in self.scene.player.blueprints)) else COLOR_TEXT
            if self.scene.tab == "items":
                draw_icon(screen, thing.item_id, thing.icon, r.x + 8, r.y + 6, size=24)
                screen.blit(font.render(name, True, name_clr), (r.x + 36, r.y + 6))
            else:
                screen.blit(font.render(f"{icon} {name}", True, name_clr), (r.x + 10, r.y + 6))
            screen.blit(font_sm.render(sub, True, COLOR_TEXT_DIM), (r.x + 14, r.y + 30))

            # Ціна
            price_clr = COLOR_GOLD if self.scene.player.gold >= price else COLOR_ERROR
            p_surf = font.render(f"{price}🪙", True, price_clr)
            screen.blit(p_surf, (r.right - p_surf.get_width() - 12, r.y + 14))

        # Лічильник
        total = len(self.scene._rows())
        cnt = font_sm.render(
            f"{self.scene.scroll + 1}–{min(self.scene.scroll + VISIBLE, total)} з {total}",
            True, COLOR_TEXT_DIM)
        screen.blit(cnt, (LIST_X, LIST_Y + VISIBLE * ROW_H + 6))

    def _draw_scrollbar(self, screen):
        rows  = self.scene._rows()
        total = len(rows)
        if total <= VISIBLE:
            return
        bar_h  = VISIBLE * ROW_H
        bar_x  = LIST_X + LIST_W + 6
        thumb_h = max(30, bar_h * VISIBLE // total)
        thumb_y = LIST_Y + (bar_h - thumb_h) * self.scene.scroll // max(1, total - VISIBLE)
        pygame.draw.rect(screen, (40, 38, 30), (bar_x, LIST_Y, 8, bar_h), border_radius=4)
        pygame.draw.rect(screen, COLOR_GOLD,   (bar_x, thumb_y, 8, thumb_h), border_radius=4)

    def _draw_info(self, screen):
        """Панель деталей вибраного товару."""
        rows    = self.scene._rows()
        abs_idx = self.scene.scroll + self.scene.sel
        if self.scene.sel == -1 or abs_idx >= len(rows):
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

        if self.scene.tab == "items":
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
        if self.scene.player.gold < price:
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
            has  = self.scene.player.materials.get(mat_id, 0)
            clr  = (100, 220, 100) if has >= qty else COLOR_ERROR
            draw_icon(screen, mat_id, mat.icon, px + 4, py, size=16)
            screen.blit(fsm.render(f" {mat.name}: {has}/{qty}", True, clr), (px + 22, py)); py += 18

        # Статус куплений
        py += 6
        owned = any(ob.blueprint_id == bp.blueprint_id for ob in self.scene.player.blueprints)
        if owned:
            screen.blit(fsm.render("✓ Вже куплено", True, (100, 220, 100)), (px, py)); py += 20
        else:
            clr = COLOR_GOLD if self.scene.player.gold >= price else COLOR_ERROR
            screen.blit(fsm.render(f"Ціна: {price} 🪙", True, clr), (px, py)); py += 20
            if self.scene.player.gold < price:
                screen.blit(fsm.render("⚠ Недостатньо золота!", True, COLOR_ERROR), (px, py))