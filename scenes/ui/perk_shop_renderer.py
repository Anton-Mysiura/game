"""
Рендерер для PerkShopScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/perk_shop.py
"""
from game.perk_system import PERKS
from ui.constants import RARITY_COLORS
import pygame
from scenes.ui.base_renderer import BaseRenderer
from ui.constants import *

from ui.assets import assets


class PerkShopRenderer(BaseRenderer):
    """
    Малює PerkShopScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        if self.scene.mode == "menu":
            self._draw_menu(screen)
        elif self.scene.mode in ("extra", "reroll"):
            self._draw_card_pick(screen)
        elif self.scene.mode == "pick":
            self._draw_pick_owned(screen)

        # Повідомлення
        if self.scene._msg and self.scene._msg_timer > 0:
            font = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
            surf = font.render(self.scene._msg, True, self.scene._msg_color)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT - 130))

    # ── Головне меню ──────────────────────

    def _draw_menu(self, screen: pygame.Surface):
        cx = SCREEN_WIDTH // 2

        # Заголовок
        font_huge  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_large = assets.get_font(FONT_SIZE_LARGE)
        font_med   = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)

        title  = font_huge.render("✨ Крамниця перків", True, COLOR_GOLD)
        shadow = font_huge.render("✨ Крамниця перків", True, (0, 0, 0))
        screen.blit(shadow, (cx - title.get_width() // 2 + 2, 52))
        screen.blit(title,  (cx - title.get_width() // 2,     50))

        gold_surf = font_large.render(f"💰 {self.scene.player.gold} золота", True, COLOR_GOLD)
        screen.blit(gold_surf, (cx - gold_surf.get_width() // 2, 120))

        # ── Кнопка «Бонусні картки» ──
        extra_rect = self.scene._extra_btn_rect()
        can_extra  = self.scene.player.gold >= self.scene._extra_cost
        self._draw_shop_btn(
            screen, extra_rect, can_extra,
            "🃏 Бонусні картки",
            f"Вибрати 1 з 3 нових перків",
            f"💰 {self.scene._extra_cost} золота",
            (40, 60, 40), (100, 180, 100),
        )

        # ── Кнопка «Замінити перк» ──
        reroll_rect = self.scene._reroll_btn_rect()
        can_reroll  = self.scene.player.gold >= self.scene._reroll_cost and bool(self.scene.player.perks)
        self._draw_shop_btn(
            screen, reroll_rect, can_reroll,
            "🔄 Замінити перк",
            f"Видалити один з перків та\nвибрати новий замість нього",
            f"💰 {self.scene._reroll_cost} золота",
            (60, 30, 60), (180, 80, 180),
        )

        # Прогрес знижок / підвищень
        next_extra  = extra_cost(self.scene.player.perk_shop_extra_bought + 1)
        next_reroll = reroll_cost(self.scene.player.perk_shop_reroll_bought + 1)
        hint = font_sm.render(
            f"Наст. бонус: {next_extra}💰   Наст. заміна: {next_reroll}💰",
            True, COLOR_TEXT_DIM
        )
        screen.blit(hint, (cx - hint.get_width() // 2, 490))

        # Закрити
        self._draw_close_btn(screen, "← Назад")

    def _draw_shop_btn(self, screen, rect, enabled, title, desc, cost_str,
                        bg_color, border_color):
        font_title = assets.get_font(FONT_SIZE_LARGE, bold=True)
        font_desc  = assets.get_font(FONT_SIZE_SMALL)
        font_cost  = assets.get_font(FONT_SIZE_MEDIUM, bold=True)

        # Hover
        hovered = rect.collidepoint(pygame.mouse.get_pos()) and enabled
        bg = tuple(min(c + 15, 255) for c in bg_color) if hovered else bg_color

        pygame.draw.rect(screen, bg, rect, border_radius=16)
        bc = border_color if enabled else (60, 60, 60)
        pygame.draw.rect(screen, bc, rect, 2 if not hovered else 3, border_radius=16)

        # Текст
        t = font_title.render(title, True, COLOR_TEXT if enabled else COLOR_TEXT_DIM)
        screen.blit(t, (rect.centerx - t.get_width() // 2, rect.y + 20))

        # Опис (з переносом)
        lines = desc.split("\n")
        dy = rect.y + 65
        for line in lines:
            s = font_desc.render(line, True, COLOR_TEXT_DIM)
            screen.blit(s, (rect.centerx - s.get_width() // 2, dy))
            dy += s.get_height() + 4

        # Ціна
        cost_color = COLOR_GOLD if enabled else COLOR_ERROR
        cs = font_cost.render(cost_str, True, cost_color)
        screen.blit(cs, (rect.centerx - cs.get_width() // 2, rect.bottom - 50))

        # "Недостатньо" якщо не може купити
        if not enabled and self.scene.player.perks or not enabled:
            if not self.scene.player.perks and "Замін" in title:
                no_s = font_desc.render("Немає перків для заміни", True, COLOR_ERROR)
                screen.blit(no_s, (rect.centerx - no_s.get_width() // 2, rect.bottom - 28))

    def _draw_close_btn(self, screen, label="← Закрити"):
        rect = self.scene._close_rect()
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        bg = COLOR_BTN_HOVER if hovered else COLOR_BTN_NORMAL
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_GOLD, rect, 2, border_radius=10)
        font = assets.get_font(FONT_SIZE_MEDIUM)
        s = font.render(label, True, COLOR_TEXT)
        screen.blit(s, (rect.centerx - s.get_width() // 2,
                         rect.centery - s.get_height() // 2))

    # ── Вибір картки ──────────────────────

    def _draw_card_pick(self, screen: pygame.Surface):
        cx = SCREEN_WIDTH // 2
        font_title = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_sub   = assets.get_font(FONT_SIZE_MEDIUM)

        if self.scene.mode == "extra":
            title_text = "🃏 Вибери свій перк"
            sub_text   = "Клікни на картку"
        else:
            old_id   = self.scene.player.perks[self.scene.reroll_target_idx] if self.scene.reroll_target_idx >= 0 else ""
            old_name = PERKS[old_id].name if old_id in PERKS else "?"
            title_text = f"🔄 Заміна: {old_name}"
            sub_text   = "Вибери новий перк замість старого"

        title = font_title.render(title_text, True, COLOR_GOLD)
        screen.blit(title, (cx - title.get_width() // 2, 40))
        sub = font_sub.render(sub_text, True, COLOR_TEXT_DIM)
        screen.blit(sub, (cx - sub.get_width() // 2, 110))

        for i, (perk, rect) in enumerate(zip(self.scene.offered_perks, self.scene._card_rects())):
            self._draw_perk_card(screen, perk, rect, hovered=(i == self.scene.hovered_card))

        self._draw_close_btn(screen, "✗ Скасувати")

    def _draw_perk_card(self, screen, perk, rect, hovered: bool):
        rarity_color = RARITY_COLORS[perk.rarity]

        if hovered:
            glow = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
            glow.fill((*rarity_color, 55))
            screen.blit(glow, (rect.x - 6, rect.y - 6))
            draw_rect = rect.inflate(6, 6)
        else:
            draw_rect = rect

        bg = (35, 28, 48) if hovered else (28, 22, 38)
        pygame.draw.rect(screen, bg, draw_rect, border_radius=16)

        stripe = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.w, 7)
        pygame.draw.rect(screen, rarity_color, stripe, border_radius=16)

        pygame.draw.rect(screen, rarity_color, draw_rect,
                         3 if hovered else 2, border_radius=16)

        cx = draw_rect.centerx

        font_icon   = assets.get_font(56)
        font_rarity = assets.get_font(FONT_SIZE_SMALL, bold=True)
        font_name   = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        font_desc   = assets.get_font(FONT_SIZE_SMALL)

        icon_s = font_icon.render(perk.icon, True, COLOR_TEXT)
        screen.blit(icon_s, (cx - icon_s.get_width() // 2, draw_rect.y + 24))

        rar_s = font_rarity.render(RARITY_NAMES[perk.rarity].upper(), True, rarity_color)
        screen.blit(rar_s, (cx - rar_s.get_width() // 2, draw_rect.y + 98))

        name_s = font_name.render(perk.name, True, COLOR_TEXT)
        screen.blit(name_s, (cx - name_s.get_width() // 2, draw_rect.y + 126))

        self._draw_wrapped(screen, font_desc, perk.description, COLOR_TEXT_DIM,
                           draw_rect.x + 14, draw_rect.y + 164, draw_rect.w - 28)

    # ── Вибір перку для заміни ────────────

    def _draw_pick_owned(self, screen: pygame.Surface):
        cx = SCREEN_WIDTH // 2

        font_huge  = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_med   = assets.get_font(FONT_SIZE_MEDIUM)
        font_sm    = assets.get_font(FONT_SIZE_SMALL)
        font_norm  = assets.get_font(FONT_SIZE_NORMAL)

        title = font_huge.render("🔄 Який перк замінити?", True, COLOR_GOLD)
        screen.blit(title, (cx - title.get_width() // 2, 40))

        cost_s = font_med.render(f"Вартість: 💰 {self.scene._reroll_cost} золота", True, COLOR_GOLD)
        screen.blit(cost_s, (cx - cost_s.get_width() // 2, 110))

        warn_s = font_sm.render("Вибраний перк буде видалено назавжди!", True, COLOR_ERROR)
        screen.blit(warn_s, (cx - warn_s.get_width() // 2, 148))

        # Список
        unique  = list(dict.fromkeys(self.scene.player.perks))
        row_h   = 56
        list_x  = cx - 300
        list_top = 200
        visible_h = SCREEN_HEIGHT - list_top - 100
        total_h   = len(unique) * row_h
        self.scene._owned_max_scroll = max(0, total_h - visible_h)
        self.scene.owned_scroll = min(self.scene.owned_scroll, self.scene._owned_max_scroll)

        clip = pygame.Rect(list_x - 4, list_top, 608, visible_h)
        screen.set_clip(clip)

        for i, perk_id in enumerate(unique):
            rect = pygame.Rect(list_x, list_top + i * row_h - self.scene.owned_scroll,
                                600, row_h - 6)
            if rect.bottom < list_top or rect.top > list_top + visible_h:
                continue

            perk = PERKS.get(perk_id)
            if not perk:
                continue

            hovered = (i == self.scene.hovered_owned)
            rarity_color = RARITY_COLORS[perk.rarity]

            bg = (60, 30, 30) if hovered else (35, 25, 35)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            bc = (220, 80, 80) if hovered else rarity_color
            pygame.draw.rect(screen, bc, rect, 2 if not hovered else 3, border_radius=10)

            # Кольорова смужка зліва
            pygame.draw.rect(screen, rarity_color, (rect.x, rect.y, 5, rect.h), border_radius=3)

            icon_s = assets.get_font(FONT_SIZE_LARGE).render(perk.icon, True, rarity_color)
            screen.blit(icon_s, (rect.x + 12, rect.centery - icon_s.get_height() // 2))

            name_s = assets.get_font(FONT_SIZE_NORMAL, bold=True).render(perk.name, True, COLOR_TEXT)
            screen.blit(name_s, (rect.x + 56, rect.y + 8))

            rar_s = font_sm.render(perk.rarity_name, True, rarity_color)
            screen.blit(rar_s, (rect.x + 56, rect.y + 32))

            cnt = self.scene.player.perks.count(perk_id)
            if cnt > 1:
                cnt_s = font_norm.render(f"×{cnt}", True, COLOR_GOLD)
                screen.blit(cnt_s, (rect.right - cnt_s.get_width() - 12,
                                     rect.centery - cnt_s.get_height() // 2))

            if hovered:
                del_s = font_sm.render("🗑 Видалити", True, (220, 80, 80))
                screen.blit(del_s, (rect.right - del_s.get_width() - 40,
                                     rect.centery - del_s.get_height() // 2))

        screen.set_clip(None)

        # Скрол
        if self.scene._owned_max_scroll > 0:
            sb_x = cx + 310
            pygame.draw.rect(screen, (40, 35, 50), (sb_x, list_top, 6, visible_h), border_radius=3)
            ratio   = visible_h / total_h
            thumb_h = max(24, int(visible_h * ratio))
            thumb_y = list_top + int((visible_h - thumb_h) * self.scene.owned_scroll /
                                      self.scene._owned_max_scroll)
            pygame.draw.rect(screen, COLOR_GOLD, (sb_x, thumb_y, 6, thumb_h), border_radius=3)

        self._draw_close_btn(screen, "✗ Скасувати")

    # ──────────────────────────────────────
    #  Утиліти
    # ──────────────────────────────────────

    def _draw_wrapped(screen, font, text: str, color, x, y, max_w):
        words, line, ly = text.split(), "", y
        for w in words:
            test = f"{line} {w}".strip()
            if font.size(test)[0] <= max_w:
                line = test
            else:
                if line:
                    s = font.render(line, True, color)
                    screen.blit(s, (x + max_w // 2 - s.get_width() // 2, ly))
                    ly += font.get_height() + 3
                line = w
        if line:
            s = font.render(line, True, color)
            screen.blit(s, (x + max_w // 2 - s.get_width() // 2, ly))