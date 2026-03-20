"""
Онбординг — перший досвід гравця.

Флоу:packets
  1. INTRO     — кінематографічна заставка (текст по рядках + fade)
  2. BATTLE_1  — перший бій з гобліном
  3. REWARD_1  — видача стартових ресурсів + кресленик
  4. WORKSHOP  — покрокове навчання у майстерні
  5. VILLAGE   — село з підсвіченою кнопкою "Ліс"
  6. BATTLE_2  — другий бій з гобліном (дає 2-й рівень)
  7. PERK_PICK — вибір першого перку (слабкі) + навчання
  8. FREE      — вільна гра
"""
from __future__ import annotations
import math
import pygame
from ui.constants import *
from ui.assets import assets
from game.save_manager import autosave


# ── Стартові ресурси ──────────────────────────────────────────────
STARTER_MATERIALS = {
    "iron_ore":  4,   # достатньо для леза
    "wood":      3,   # для рукоятки
    "leather":   2,   # альтернатива рукоятки
    "bone":      2,   # ще варіант
    "hardwood":  1,   # цінніший матеріал — рідше використають
    "coal_ore":  2,   # dummy — щоб список виглядав різноманітним
}
STARTER_GOLD = 30

# Кресленик що дається — звичайний кинджал, 1 використання
STARTER_BLUEPRINT_ID = "bp_dagger"

# XP що дається після бою 2 — достатньо для 2-го рівня з нуля
BATTLE2_XP = 55   # більше ніж xp_next=50

# Найслабші перки для першого вибору
WEAK_PERK_IDS = ["move_speed_5", "range_5", "atk_speed_5"]


class OnboardingScene:
    """Контролер онбордингу — делегує до під-сцен."""

    def __init__(self, game):
        self.game  = game
        self.stage = "intro"
        self._sub  = _IntroScene(self)

        # Підключаємо renderer (малювання)
        from scenes.ui.onboarding_renderer import OnboardingRenderer
        self._renderer = OnboardingRenderer(self)
    @property
    def player(self):
        return self.game.player

    def advance(self, next_stage: str):
        """Переходить до наступного етапу онбордингу."""
        self.stage = next_stage

        if next_stage == "battle_1":
            self._start_battle_1()
        elif next_stage == "reward_1":
            self._give_reward_1()
            self._sub = _RewardScene(self)
        elif next_stage == "workshop":
            self.game.scene_data["onboarding_step"] = "workshop"
            self.game.change_scene("workshop")
        elif next_stage == "village":
            self.game.scene_data["onboarding_step"] = "village"
            self.game.change_scene("village")
        elif next_stage == "battle_2":
            self._start_battle_2()
        elif next_stage == "perk_pick":
            self._force_perk_pick()
        elif next_stage == "free":
            self.player.onboarding_done = True
            autosave(self.player)
            self.game.change_scene("village")

    def _start_battle_1(self):
        from game.enemy import make_goblin
        enemy = make_goblin()
        enemy.level = 1
        enemy.hp    = enemy.max_hp = 30
        self.game.scene_data["onboarding_after_battle"] = "reward_1"
        self.game.change_scene("battle", enemy=enemy,
                               return_scene="onboarding_reward_1",
                               background_name="forest")

    def _give_reward_1(self):
        p = self.player
        p.gold += STARTER_GOLD
        p.total_gold_earned += STARTER_GOLD
        for mat_id, qty in STARTER_MATERIALS.items():
            p.materials[mat_id] = p.materials.get(mat_id, 0) + qty
        # Даємо кресленик з 1 використанням
        from game.data import BLUEPRINTS, OwnedBlueprint
        bp = BLUEPRINTS.get(STARTER_BLUEPRINT_ID)
        if bp:
            ob = OwnedBlueprint(blueprint=bp, uses_left=1)
            p.blueprints.append(ob)
        autosave(p)

    def _start_battle_2(self):
        from game.enemy import make_goblin
        enemy = make_goblin()
        enemy.level = 1
        enemy.hp    = enemy.max_hp = 40
        self.game.scene_data["onboarding_after_battle"] = "perk_pick"
        self.game.scene_data["onboarding_battle2_xp"]   = BATTLE2_XP
        self.game.change_scene("battle", enemy=enemy,
                               return_scene="onboarding_perk",
                               background_name="forest")

    def _force_perk_pick(self):
        """Форсує вибір з трьох найслабших перків."""
        from game.perk_system import PERKS, Perk
        weak = [PERKS[pid] for pid in WEAK_PERK_IDS if pid in PERKS]
        self.player.pending_perk_choices = weak
        self.game.scene_data["onboarding_perk_first"] = True
        self.game.change_scene("level_up")

    def handle_event(self, event):
        if self._sub:
            self._sub.handle_event(event)

    def update(self, dt):
        if self._sub:
            self._sub.update(dt)

    def draw(self, screen):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)
    def on_enter(self): pass
    def on_exit(self):  pass


# ══════════════════════════════════════════════════════════════════
# 1. INTRO — кінематографічна заставка
# ══════════════════════════════════════════════════════════════════

INTRO_LINES = [
    ("",       0.0,  0.8),   # пауза
    ("Темне королівство...",        2.5,  2.0),
    ("Колись тут були мирні поля.", 2.0,  1.8),
    ("Тепер — тільки руїни і монстри.",  2.0, 1.8),
    ("",       0.0,  0.6),
    ("Ти — мандрівник без імені.",   2.2,  2.0),
    ("Без дому. Без зброї.", 2.0,  1.8),
    ("Але з однією якістю —",        1.8,  1.5),
    ("ти ще живий.",                  2.5,  2.5),
    ("",       0.0,  0.8),
    ("Краєм ока ти помічаєш рух у кущах...", 2.5, 2.2),
    ("",       0.0,  0.5),
]

FLASH_DURATION = 0.3   # спалах перед боєм


class _IntroScene:
    """Кінематографічна заставка."""

    def __init__(self, ctrl: OnboardingScene):
        self.ctrl       = ctrl
        self._line_idx  = 0
        self._line_t    = 0.0      # скільки секунд показується поточний рядок
        self._alpha     = 0        # fade-in поточного рядка
        self._done_t    = 0.0      # таймер після останнього рядка
        self._flash_t   = -1.0     # таймер спалаху (-1 = немає)
        self._skip_hint = 3.0      # таймер підказки "Пробіл — пропустити"
        self._finished  = False

        # Поверхні для рядків що вже показані (залишаються)
        self._shown: list[tuple] = []   # (surface, y, alpha_target)

    def _current_line(self):
        if self._line_idx < len(INTRO_LINES):
            return INTRO_LINES[self._line_idx]
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._skip()
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._skip()

    def _skip(self):
        self._flash_t   = FLASH_DURATION
        self._finished  = True

    def update(self, dt: float):
        self._skip_hint -= dt

        if self._finished:
            if self._flash_t > 0:
                self._flash_t -= dt
            else:
                self.ctrl.advance("battle_1")
            return

        line_data = self._current_line()
        if line_data is None:
            # Всі рядки показані
            self._done_t += dt
            if self._done_t > 1.5:
                self._flash_t  = FLASH_DURATION
                self._finished = True
            return

        text, fade_dur, hold_dur = line_data
        total = fade_dur + hold_dur

        self._line_t += dt

        # Fade in
        if fade_dur > 0 and self._line_t < fade_dur:
            self._alpha = int(255 * (self._line_t / fade_dur))
        else:
            self._alpha = 255

        # Перехід до наступного рядка
        if self._line_t >= total:
            if text:   # порожній рядок — просто пауза
                fn   = assets.get_font(FONT_SIZE_NORMAL)
                surf = fn.render(text, True, (220, 210, 190))
                self._shown.append((surf, None))   # y визначається при малюванні
            self._line_idx += 1
            self._line_t    = 0.0
            self._alpha     = 0

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))

        # Спалах
        if self._flash_t > 0:
            a = int(255 * (self._flash_t / FLASH_DURATION))
            fl = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fl.fill((255, 255, 255))
            fl.set_alpha(a)
            screen.blit(fl, (0, 0))
            return

        fn_large = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fn_norm  = assets.get_font(FONT_SIZE_NORMAL)
        fn_small = assets.get_font(FONT_SIZE_SMALL)

        # Збираємо всі рядки для малювання
        displayed = []
        for i in range(self._line_idx):
            if i < len(INTRO_LINES):
                text, _, _ = INTRO_LINES[i]
                if text:
                    displayed.append((text, 255))

        # Поточний рядок
        line_data = self._current_line()
        if line_data:
            text, _, _ = line_data
            if text:
                displayed.append((text, self._alpha))

        # Малюємо по центру, знизу вгору
        total_h   = len(displayed) * 38
        start_y   = SCREEN_HEIGHT // 2 - total_h // 2

        for i, (text, alpha) in enumerate(displayed):
            # Останній рядок — більший
            is_last = (i == len(displayed) - 1)
            fn = fn_large if is_last and alpha == 255 else fn_norm
            col = (220, 200, 140) if is_last else (160, 150, 130)
            surf = fn.render(text, True, col)
            surf.set_alpha(alpha)
            x = SCREEN_WIDTH // 2 - surf.get_width() // 2
            y = start_y + i * 38
            screen.blit(surf, (x, y))

        # Підказка "пропустити"
        if self._skip_hint > 0:
            hint = fn_small.render("[ Пробіл або кліком — пропустити ]",
                                   True, (80, 75, 65))
            hint.set_alpha(min(255, int(self._skip_hint * 80)))
            screen.blit(hint,
                        (SCREEN_WIDTH//2 - hint.get_width()//2,
                         SCREEN_HEIGHT - 60))

        # Після останнього рядка — кнопка "Почати"
        line_data = self._current_line()
        if line_data is None and not self._finished:
            pulse = 0.7 + 0.3 * abs(math.sin(self._done_t * 2.5))
            col   = tuple(int(c * pulse) for c in (220, 180, 60))
            start_s = fn_large.render("▶ Почати", True, col)
            sx = SCREEN_WIDTH // 2 - start_s.get_width() // 2
            sy = SCREEN_HEIGHT - 100
            screen.blit(start_s, (sx, sy))


# ══════════════════════════════════════════════════════════════════
# 3. REWARD — показ нагороди після першого бою
# ══════════════════════════════════════════════════════════════════

class _RewardScene:
    """Показує стартові ресурси і кресленик."""

    def __init__(self, ctrl: OnboardingScene):
        self.ctrl   = ctrl
        self._anim  = 0.0
        self._done  = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN or (
                event.type == pygame.KEYDOWN and
                event.key in (pygame.K_SPACE, pygame.K_RETURN)):
            self._done = True

    def update(self, dt):
        self._anim += dt
        if self._done:
            self.ctrl.advance("workshop")

    def draw(self, screen: pygame.Surface):
        screen.fill((8, 6, 4))

        fn   = assets.get_font(FONT_SIZE_LARGE, bold=True)
        fn_n = assets.get_font(FONT_SIZE_NORMAL)
        fn_s = assets.get_font(FONT_SIZE_SMALL)
        from ui.icons import draw_icon
        from game.data import MATERIALS, BLUEPRINTS, BP_RARITY_COLORS

        cx = SCREEN_WIDTH // 2

        # Заголовок
        pulse = 0.85 + 0.15 * abs(math.sin(self._anim * 1.5))
        col   = tuple(int(c * pulse) for c in (220, 180, 60))
        title = fn.render("⚔ Гоблін переможений!", True, col)
        screen.blit(title, (cx - title.get_width() // 2, 80))

        sub = fn_n.render("Ти знайшов перші ресурси та отримав кресленик:", True, (160, 150, 130))
        screen.blit(sub, (cx - sub.get_width() // 2, 130))

        # Золото
        gold_s = fn_n.render(f"💰 +{STARTER_GOLD} золота", True, COLOR_GOLD)
        screen.blit(gold_s, (cx - gold_s.get_width() // 2, 175))

        # Матеріали
        y = 220
        mat_items = [(mid, qty) for mid, qty in STARTER_MATERIALS.items()]
        cols_count = 3
        item_w = 220
        start_x = cx - (cols_count * item_w) // 2

        for i, (mid, qty) in enumerate(mat_items):
            mat = MATERIALS.get(mid)
            if not mat:
                continue
            col_i = i % cols_count
            row_i = i // cols_count
            ix = start_x + col_i * item_w
            iy = y + row_i * 36
            draw_icon(screen, mid, mat.icon, ix, iy, size=26)
            txt = fn_n.render(f"  {mat.name} ×{qty}", True, (180, 170, 150))
            screen.blit(txt, (ix + 28, iy + 2))

        # Кресленик
        bp = BLUEPRINTS.get(STARTER_BLUEPRINT_ID)
        if bp:
            y2 = y + ((len(mat_items) - 1) // cols_count + 1) * 36 + 20
            rc = BP_RARITY_COLORS.get(bp.rarity, (180, 180, 180))
            bp_lbl = fn_n.render("📜 Кресленик (1 використання):", True, COLOR_GOLD)
            screen.blit(bp_lbl, (cx - bp_lbl.get_width() // 2, y2))
            y2 += 30
            bp_name = fn.render(f"{bp.result_icon} {bp.result_name}", True, rc)
            screen.blit(bp_name, (cx - bp_name.get_width() // 2, y2))
            y2 += 36
            bp_note = fn_s.render("* Кресленик дає форму — матеріали визначають силу", True, (120,110,90))
            screen.blit(bp_note, (cx - bp_note.get_width() // 2, y2))

        # Продовжити
        cont_pulse = 0.7 + 0.3 * abs(math.sin(self._anim * 2.2))
        cont_col   = tuple(int(c * cont_pulse) for c in (180, 220, 140))
        cont = fn_n.render("[ Клікни або Пробіл — іти до майстерні ]", True, cont_col)
        screen.blit(cont, (cx - cont.get_width() // 2, SCREEN_HEIGHT - 70))