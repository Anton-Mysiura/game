"""
Рендерер для StatsScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/stats.py
"""
import pygame
from scenes.ui.base_renderer import BaseRenderer

import math
from ui.components import Button, Panel, ProgressBar
from ui.constants import *
from ui.assets import assets


class StatsRenderer(BaseRenderer):
    """
    Малює StatsScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Заголовок
        fh = assets.get_font(FONT_SIZE_LARGE, bold=True)
        title = fh.render(f"📊 {self.player.name}", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 42))

        # Вкладки
        for i, (btn, (tid, _)) in enumerate(zip(self.scene.tab_btns, TABS)):
            btn.selected = (tid == self.scene._tab)
            btn.draw(screen)

        # Панель
        self.scene.main_panel.draw(screen)

        # Вміст
        t = self.scene._tab
        if t == "general":   self._draw_general(screen)
        elif t == "combat":  self._draw_combat(screen)
        elif t == "mine":    self._draw_mine(screen)
        else:                self._draw_reputation(screen)

        self.scene.close_btn.draw(screen)

    # ── Загальне ──────────────────────────────────────────────────

    def _draw_general(self, screen):
        p   = self.player
        fn  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)
        px, py = PNL_X + 24, PNL_Y + 16

        screen.blit(fn.render(f"Рівень {p.level}", True, COLOR_GOLD), (px, py)); py += 26

        self.scene.hp_bar.draw(screen, p.hp, p.max_hp, "HP")
        self.scene.xp_bar.draw(screen, p.xp, p.xp_next, "XP")
        py += 100

        rows = [
            ("⚔ Атака",   f"{p.total_attack}  (база {p.attack} + бонус {p.bonus_attack})"),
            ("🛡 Захист",  f"{p.total_defense}"),
            ("❤ HP макс", f"{p.max_hp}"),
            ("💰 Золото",  f"{p.gold} 🪙"),
            ("💸 Витрачено", f"{p.gold_spent} 🪙"),
            ("🗡 Зброя",   p.equipped_weapon.name if p.equipped_weapon else "—"),
            ("🛡 Броня",   p.equipped_armor.name  if p.equipped_armor  else "—"),
            ("🕐 Час у грі", _fmt(getattr(p, "total_playtime", 0.0))),
            ("📜 Кресленики", str(len(p.blueprints))),
            ("📦 Матеріалів", f"{sum(p.materials.values())} шт ({len(p.materials)} видів)"),
        ]
        for lbl, val in rows:
            l_s = fsm.render(lbl, True, COLOR_GOLD)
            v_s = fsm.render(val, True, COLOR_TEXT)
            screen.blit(l_s, (px, py))
            screen.blit(v_s, (px + 200, py))
            py += 24

    # ── Бойова ────────────────────────────────────────────────────

    def _draw_combat(self, screen):
        p   = self.player
        fsm = assets.get_font(FONT_SIZE_SMALL)
        fn  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        px, py = PNL_X + 24, PNL_Y + 16

        screen.blit(fn.render("⚔ Бойова статистика", True, COLOR_GOLD), (px, py)); py += 32

        rows = [
            ("👹 Ворогів вбито",   str(p.enemies_killed)),
            ("👺 Гоблінів",         str(p.goblins_killed)),
            ("🗿 Орків",            str(p.orcs_killed)),
            ("⚔ Лицарів",          str(p.knights_killed)),
            ("🐉 Драконів",         str(p.dragons_killed)),
            ("",                    ""),
            ("🔨 Скрафтовано",      str(p.items_crafted)),
            ("💀 Смертей",          str(p.deaths)),
            ("❤ Вижив на 1 HP",   "Так" if p.survived_at_1hp else "Ні"),
            ("🎯 Крит. шанс",      f"{getattr(p, 'perk_multipliers', {}).get('crit_chance', 0.0):.1f}%"),
        ]

        for lbl, val in rows:
            if not lbl:
                py += 8; continue
            l_s = fsm.render(lbl, True, COLOR_GOLD)
            v_s = fsm.render(val, True, COLOR_TEXT)
            screen.blit(l_s, (px, py))
            screen.blit(v_s, (px + 220, py))
            py += 24

        # Рекорд — якщо є last_battle_record
        rec = getattr(self.game, "last_battle_record", None)
        if rec:
            py += 10
            screen.blit(fn.render("Останній бій:", True, COLOR_GOLD), (px, py)); py += 24
            result_col = (100, 220, 100) if rec.player_won else (220, 80, 80)
            screen.blit(fsm.render("✓ Перемога" if rec.player_won else "✗ Поразка",
                                   True, result_col), (px, py)); py += 22
            for lbl, val in [
                (f"⚔ Урон нанесено: {rec.damage_dealt}", (220, 180, 100)),
                (f"🩸 Урон отримано: {rec.damage_taken}", (200, 100, 100)),
                (f"🎯 Критів: {rec.crits}",                (140, 200, 255)),
            ]:
                screen.blit(fsm.render(lbl, True, val), (px, py)); py += 20

    # ── Шахта ─────────────────────────────────────────────────────

    def _draw_mine(self, screen):
        p   = self.player
        fn  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)
        px, py = PNL_X + 24, PNL_Y + 16

        screen.blit(fn.render("⛏ Статистика шахти", True, COLOR_GOLD), (px, py)); py += 32

        trips     = getattr(p, "mine_trips", 0)
        collected = getattr(p, "mine_ores_collected", 0)
        deep      = getattr(p, "mine_deep_trips", 0)
        accidents = getattr(p, "mine_accidents", 0)
        legendary = getattr(p, "mine_legendary_found", False)

        rows = [
            ("⛏ Всього походів",      str(trips)),
            ("💎 Глибоких походів",    str(deep)),
            ("🪨 Руд зібрано",         str(collected)),
            ("💀 Аварій",              str(accidents)),
            ("🌋 Легендарна руда",     "Знайдено ✓" if legendary else "Ще не знайдено"),
        ]
        for lbl, val in rows:
            l_s = fsm.render(lbl, True, COLOR_GOLD)
            v_s = fsm.render(val, True, COLOR_TEXT)
            screen.blit(l_s, (px, py))
            screen.blit(v_s, (px + 240, py))
            py += 26

        # Поточний стан шахтаря
        py += 10
        screen.blit(fn.render("Шахтар Борис:", True, COLOR_GOLD), (px, py)); py += 26

        if hasattr(p, "miner"):
            from game.miner import MinerState, TIERS
            m = p.miner
            STATUS_UA = {
                MinerState.STATUS_IDLE:    ("😊 Вільний", (100, 220, 100)),
                MinerState.STATUS_WORKING: ("⛏ Працює",  (220, 200, 80)),
                MinerState.STATUS_DONE:    ("📦 Повернувся", (80, 200, 255)),
                MinerState.STATUS_LOST:    ("💀 Зник",    (220, 80, 80)),
            }
            st_txt, st_col = STATUS_UA.get(m.status, ("?", COLOR_TEXT))
            screen.blit(fsm.render(f"Стан: {st_txt}", True, st_col), (px, py)); py += 22

            if m.status == MinerState.STATUS_WORKING and m.tier_id:
                tier = TIERS.get(m.tier_id)
                left = m.time_left()
                mm, ss = divmod(left, 60)
                screen.blit(fsm.render(
                    f"Тариф: {tier.name if tier else m.tier_id}  |  Залишилось: {mm:02d}:{ss:02d}",
                    True, COLOR_TEXT), (px, py)); py += 22

            FATIGUE_UA = ["😊 Свіжий", "😓 Втомлений", "😵 Виснажений"]
            flvl = m.fatigue_level
            fat_col = [(100,220,100),(220,180,60),(220,80,80)][flvl]
            screen.blit(fsm.render(
                f"Втома: {FATIGUE_UA[flvl]}  (похід {m.trips_since_rest})",
                True, fat_col), (px, py)); py += 22

        # Топ-5 найпоширеніших руд у гравця
        py += 10
        screen.blit(fn.render("Найбільше руд:", True, COLOR_GOLD), (px, py)); py += 24
        ore_mats = {mid: qty for mid, qty in p.materials.items()
                    if mid.endswith("_ore") and qty > 0}
        top5 = sorted(ore_mats.items(), key=lambda x: x[1], reverse=True)[:5]
        if top5:
            for mid, qty in top5:
                mat = MATERIALS.get(mid)
                name = mat.name if mat else mid
                icon = mat.icon if mat else "🪨"
                screen.blit(fsm.render(f"{icon} {name}: {qty}", True, COLOR_TEXT),
                            (px, py)); py += 20
        else:
            screen.blit(fsm.render("Ще не зібрано жодної руди", True, COLOR_TEXT_DIM),
                        (px, py))

    # ── Репутація ─────────────────────────────────────────────────

    def _draw_reputation(self, screen):
        p   = self.player
        fn  = assets.get_font(FONT_SIZE_NORMAL, bold=True)
        fsm = assets.get_font(FONT_SIZE_SMALL)
        px, py = PNL_X + 24, PNL_Y + 16

        from game.reputation import get_tier, get_next_tier, TIERS as REP_TIERS
        rep  = getattr(p, "reputation", 0)
        tier = get_tier(rep)
        nxt  = get_next_tier(rep)

        screen.blit(fn.render("⭐ Репутація у селі", True, COLOR_GOLD), (px, py)); py += 32

        # Поточний рівень
        pulse = 0.85 + 0.15 * abs(math.sin(self.scene._anim * 1.5))
        col   = tuple(int(c * pulse) for c in tier.color)
        screen.blit(fn.render(f"{tier.icon} {tier.name}", True, col), (px, py)); py += 28
        screen.blit(fsm.render(f"Репутація: {rep} очок", True, COLOR_TEXT), (px, py)); py += 22

        disc = int((1 - tier.discount) * 100)
        screen.blit(fsm.render(f"🏷 Знижка в крамниці: -{disc}%", True, (180, 220, 140)),
                    (px, py)); py += 26

        # Прогрес до наступного
        if nxt:
            prog = (rep - tier.min_rep) / (nxt.min_rep - tier.min_rep)
            bar_w = PNL_W - 48
            pygame.draw.rect(screen, (40, 35, 25), (px, py, bar_w, 16), border_radius=8)
            fill = max(8, int(bar_w * prog))
            pygame.draw.rect(screen, tier.color, (px, py, fill, 16), border_radius=8)
            pygame.draw.rect(screen, tier.color, (px, py, bar_w, 16), 1, border_radius=8)
            py += 24
            screen.blit(fsm.render(
                f"До {nxt.icon} {nxt.name}: +{nxt.min_rep - rep} очок",
                True, COLOR_TEXT_DIM), (px, py)); py += 28
        else:
            screen.blit(fsm.render("★ Максимальна репутація досягнута!", True, tier.color),
                        (px, py)); py += 28

        # Всі рівні
        py += 8
        screen.blit(fn.render("Всі рівні:", True, COLOR_GOLD), (px, py)); py += 26
        for t in REP_TIERS:
            unlocked = rep >= t.min_rep
            clr      = t.color if unlocked else (80, 75, 65)
            mark     = "✓" if unlocked else "○"
            disc_t   = int((1 - t.discount) * 100)
            screen.blit(fsm.render(
                f"{mark} {t.icon} {t.name}  ({t.min_rep} оч.)  -{disc_t}% знижка",
                True, clr), (px + 10, py)); py += 22

        # Як отримати
        py += 10
        screen.blit(fn.render("Як заробити:", True, COLOR_GOLD), (px, py)); py += 24
        for hint in [
            "📜 Квест у голови села: +30",
            "🛒 Кожні 10🪙 в крамниці: +1",
            "⛏ Шахтар повернувся: +8",
            "🔨 Скрафтовано предмет: +5",
            "⚔ За кожного ворога: +1",
        ]:
            screen.blit(fsm.render(hint, True, COLOR_TEXT_DIM), (px + 10, py)); py += 20