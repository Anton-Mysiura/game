"""
Рендерер для HeroIndexWidget.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/hero_index.py
"""
from scenes.core.hero_index import _INFO_W, _INFO_X, _INFO_Y, _LIST_W, _LIST_X, _LIST_Y, _ROW_H, _VISIBLE
from game.heroes import HERO_RARITY_COLORS
from game.heroes import HERO_RARITY_NAMES_UA
import pygame
from scenes.ui.base_renderer import BaseRenderer
from ui.constants import *

from ui.components import Button
from ui.constants import *
from ui.assets import assets

_SW = SCREEN_WIDTH
_SH = SCREEN_HEIGHT


class HeroIndexRenderer(BaseRenderer):
    """
    Малює HeroIndexWidget.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        self._draw_list(screen)
        self._draw_info(screen)

    def _draw_list(self, screen: pygame.Surface):
        fn = assets.get_font(FONT_SIZE_NORMAL)
        fs = assets.get_font(FONT_SIZE_SMALL)
        fh = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        mp = pygame.mouse.get_pos()

        # Фон списку
        bg = pygame.Surface((_LIST_W, _VISIBLE * _ROW_H), pygame.SRCALPHA)
        bg.fill((10, 8, 6, 180))
        screen.blit(bg, (_LIST_X, _LIST_Y))

        for i in range(_VISIBLE):
            idx = self.scene._scroll + i
            if idx >= len(self.scene._rows):
                break
            row  = self.scene._rows[idx]
            ry   = _LIST_Y + i * _ROW_H
            rect = pygame.Rect(_LIST_X, ry, _LIST_W, _ROW_H - 3)

            if row[0] == "header":
                gdata = row[2]
                # Заголовок групи
                hs = pygame.Surface((_LIST_W, _ROW_H - 3), pygame.SRCALPHA)
                hs.fill((40, 35, 15, 220))
                screen.blit(hs, (_LIST_X, ry))
                pygame.draw.rect(screen, COLOR_GOLD,
                                 pygame.Rect(_LIST_X, ry, _LIST_W, _ROW_H - 3), 1, border_radius=4)
                label = fh.render(f"{gdata['icon']} {gdata['name']}", True, COLOR_GOLD)
                screen.blit(label, (_LIST_X + 12, ry + 8))
            else:
                hid  = row[1]
                hero = row[2]
                rar_col = HERO_RARITY_COLORS.get(hero.rarity, (180, 180, 180))
                owned   = self.scene.roster.has_hero(hid)
                is_sel  = (idx == self.scene._sel)
                is_hov  = rect.collidepoint(mp)

                bg_col = (60, 50, 15, 200) if is_sel else \
                         (35, 30, 20, 180) if is_hov else \
                         (18, 15, 10, 160)
                rs = pygame.Surface((_LIST_W, _ROW_H - 3), pygame.SRCALPHA)
                rs.fill(bg_col)
                pygame.draw.rect(rs, rar_col if is_sel else (50, 45, 30),
                                 rs.get_rect(), 1, border_radius=4)
                screen.blit(rs, (_LIST_X, ry))

                # Смужка рідкості
                pygame.draw.rect(screen, rar_col, (_LIST_X, ry, 3, _ROW_H - 3), border_radius=2)

                # Іконка
                fi = assets.get_font(22)
                icon = fi.render(hero.icon, True, rar_col)
                screen.blit(icon, (_LIST_X + 10, ry + (_ROW_H - 3 - icon.get_height()) // 2))

                # Назва
                name_col = rar_col if owned or is_sel else (120, 110, 90)
                name = fn.render(hero.name, True, name_col)
                screen.blit(name, (_LIST_X + 36, ry + 4))

                # Рідкість (маленько)
                rar_name = HERO_RARITY_NAMES_UA.get(hero.rarity, "")
                rar_s = fs.render(rar_name, True, rar_col)
                screen.blit(rar_s, (_LIST_X + 36, ry + 24))

                # Мітка "є в колекції"
                if owned:
                    owned_s = fs.render("✓", True, (100, 220, 100))
                    screen.blit(owned_s, (_LIST_X + _LIST_W - 22, ry + 14))

    def _draw_info(self, screen: pygame.Surface):
        hero = self.scene._selected_hero
        if not hero:
            fn = assets.get_font(FONT_SIZE_SMALL)
            hint = fn.render("← Вибери героя зі списку", True, COLOR_TEXT_DIM)
            screen.blit(hint, (_INFO_X, _INFO_Y + 20))
            return

        rar_col = HERO_RARITY_COLORS.get(hero.rarity, (180, 180, 180))
        owned   = self.scene.roster.has_hero(hero.hero_id)

        # Панель
        panel_h = _SH - _INFO_Y - 60
        psurf = pygame.Surface((_INFO_W, panel_h), pygame.SRCALPHA)
        psurf.fill((14, 12, 8, 210))
        pygame.draw.rect(psurf, rar_col, psurf.get_rect(), 1, border_radius=10)
        screen.blit(psurf, (_INFO_X, _INFO_Y))

        px, py = _INFO_X + 14, _INFO_Y + 14
        fh = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        fm = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        fn = assets.get_font(FONT_SIZE_NORMAL)
        fs = assets.get_font(FONT_SIZE_SMALL)

        # Іконка + назва
        fi = assets.get_font(44)
        icon = fi.render(hero.icon, True, rar_col)
        screen.blit(icon, (px, py))
        name = fh.render(hero.name, True, rar_col)
        screen.blit(name, (px + 56, py + 4))

        rar_name = HERO_RARITY_NAMES_UA.get(hero.rarity, "")
        rar_surf = fs.render(f"✦ {rar_name}", True, rar_col)
        screen.blit(rar_surf, (px + 56, py + 34))

        if owned:
            own_surf = fs.render("✓ В колекції", True, (100, 220, 100))
            screen.blit(own_surf, (px + 56 + rar_surf.get_width() + 12, py + 34))

        py += 62

        # Лор
        lore = fs.render(hero.lore[:70], True, COLOR_TEXT_DIM)
        screen.blit(lore, (px, py)); py += 22

        pygame.draw.line(screen, (60, 55, 35), (px, py), (px + _INFO_W - 28, py)); py += 10

        # Базові стати
        b = hero.passive_bonuses()
        screen.blit(fm.render("Бонуси:", True, COLOR_GOLD), (px, py)); py += 22

        stat_rows = [
            (f"❤ HP:          +{b['hp']}",       (220, 80, 80)  if b['hp']      else None),
            (f"⚔ Атака:       +{b['attack']}",   (220, 160, 80) if b['attack']  else None),
            (f"🛡 Захист:      +{b['defense']}",  (80, 160, 220) if b['defense'] else None),
            (f"🎯 Крит:        +{int(b['crit']*100)}%",
             (220, 200, 80) if b['crit'] else None),
            (f"💨 Ухилення:   +{int(b['dodge']*100)}%",
             (80, 220, 160) if b['dodge'] else None),
            (f"🛡 Парирування: +{int(b['parry']*100)}%",
             (160, 120, 220) if b['parry'] else None),
        ]
        for txt, col in stat_rows:
            if col:
                screen.blit(fn.render(txt, True, col), (px, py)); py += 20

        py += 8
        pygame.draw.line(screen, (60, 55, 35), (px, py), (px + _INFO_W - 28, py)); py += 10

        # Навички
        screen.blit(fm.render("Навички:", True, COLOR_GOLD), (px, py)); py += 22
        for sk in hero.skills:
            prefix = "⚡ " if not sk.is_passive else "🔹 "
            col    = (255, 200, 80) if not sk.is_passive else COLOR_TEXT
            name_s = fn.render(f"{prefix}{sk.name}", True, col)
            screen.blit(name_s, (px, py)); py += 18
            desc_s = fs.render(f"   {sk.desc[:60]}", True, COLOR_TEXT_DIM)
            screen.blit(desc_s, (px, py)); py += 18
            if py > _INFO_Y + panel_h - 40:
                break