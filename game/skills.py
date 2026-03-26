"""
Активні скіли для Action RPG бою.

Кожен скіл — окремий клас з методами:
    can_use(fighter)  → bool
    execute(fighter, enemy_fighter, scene) → None
    update(dt) → None  (кулдаун)

Глобальний реєстр SKILLS: skill_id → Skill
Призначення на кнопки — через SkillBar.

Підключення у battle_fighting.py:
    from game.skills import SkillBar
    self.skill_bar = SkillBar(default_loadout())

    # handle_event:
    if event.key == pygame.K_1: self.skill_bar.try_use(0, pf, ef, self)
    ...

    # _draw_ui:
    self.skill_bar.draw(screen, focus)
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.fighter import Fighter

# ══════════════════════════════════════════
#  FOCUS (ресурс)
# ══════════════════════════════════════════

class FocusBar:
    """
    Focus — ресурс що заповнюється від ударів і витрачається на скіли.
    Не є енергією (energy = витривалість для dodge/block).
    """

    MAX = 100
    GAIN_LIGHT = 8     # з легкого удару
    GAIN_HEAVY = 20    # з важкого / charge
    GAIN_CRIT  = 15    # бонус при крит
    GAIN_PARRY = 30    # за успішне парирування
    REGEN_IDLE = 3.0   # пасивна регенерація / сек

    def __init__(self):
        self.value: float = 0.0

    def gain(self, amount: float):
        self.value = min(self.MAX, self.value + amount)

    def spend(self, amount: float) -> bool:
        if self.value >= amount:
            self.value -= amount
            return True
        return False

    def update(self, dt: float):
        # Повільна пасивна регенерація
        if self.value < self.MAX:
            self.value = min(self.MAX, self.value + self.REGEN_IDLE * dt)

    @property
    def pct(self) -> float:
        return self.value / self.MAX


# ══════════════════════════════════════════
#  БАЗОВИЙ СКІЛ
# ══════════════════════════════════════════

@dataclass
class Skill:
    skill_id:    str
    name:        str
    description: str
    icon:        str
    focus_cost:  float
    cooldown:    float            # секунд
    color:       tuple = (180, 140, 255)

    # runtime
    _cd_remaining: float = field(default=0.0, repr=False, init=False)

    @property
    def ready(self) -> bool:
        return self._cd_remaining <= 0.0

    @property
    def cd_pct(self) -> float:
        """0.0 = готовий, 1.0 = щойно використали."""
        if self.cooldown <= 0:
            return 0.0
        return self._cd_remaining / self.cooldown

    def update(self, dt: float):
        if self._cd_remaining > 0:
            self._cd_remaining = max(0.0, self._cd_remaining - dt)

    def can_use(self, fighter: Fighter, focus: FocusBar) -> bool:
        return self.ready and focus.value >= self.focus_cost

    def _start_cooldown(self):
        self._cd_remaining = self.cooldown

    def execute(self, fighter: Fighter, enemy: Fighter,
                focus: FocusBar, scene) -> bool:
        """
        Виконує скіл. Повертає True якщо успішно.
        Дочірні класи перекривають цей метод.
        """
        raise NotImplementedError


# ══════════════════════════════════════════
#  КОНКРЕТНІ СКІЛИ
# ══════════════════════════════════════════

class DashStrike(Skill):
    """
    [1] Dash Strike — стрімкий рив уперед + удар.
    Переміщує бійця до ворога і завдає 1.4× damage.
    Короткий i-frame під час ривка (0.12с).
    """

    def __init__(self):
        super().__init__(
            skill_id    = "dash_strike",
            name        = "Dash Strike",
            description = "Рив до ворога + удар 140%",
            icon        = "⚡",
            focus_cost  = 25,
            cooldown    = 4.0,
            color       = (100, 180, 255),
        )

    def execute(self, fighter: Fighter, enemy: Fighter,
                focus: FocusBar, scene) -> bool:
        if not self.can_use(fighter, focus):
            return False
        focus.spend(self.focus_cost)
        self._start_cooldown()

        # Рив — різкий імпульс до ворога
        dx = enemy.body.position.x - fighter.body.position.x
        direction = 1 if dx > 0 else -1
        fighter.facing_right = direction > 0
        fighter.body.velocity = (direction * 600, fighter.body.velocity.y)

        # Короткий i-frame
        fighter.dodge_iframes = 0.12

        # Атака з затримкою 0.1с (коли досягнемо ворога)
        fighter._skill_attack_timer = 0.10
        fighter._skill_attack_mult  = 1.4
        fighter._skill_attack_name  = "dash_strike"

        # Flash синій
        fighter._flash_timer = 0.15
        fighter._flash_color = (80, 160, 255)

        # Частинки
        try:
            from game.particles import HitEffects
            HitEffects.spawn_dodge(fighter.particles,
                                   fighter.body.position.x,
                                   fighter.body.position.y,
                                   direction=direction)
        except Exception:
            pass

        if hasattr(scene, '_log_event'):
            scene._log_event("⚡ Dash Strike!", (100, 200, 255))
        return True


class PowerSlam(Skill):
    """
    [2] Power Slam — важкий удар що б'є донизу.
    Knockdown завжди. Damage 2.5×. Сповільнена атака (0.5с замах).
    """

    def __init__(self):
        super().__init__(
            skill_id    = "power_slam",
            name        = "Power Slam",
            description = "Нищівний удар. Knockdown, 250%",
            icon        = "💥",
            focus_cost  = 40,
            cooldown    = 7.0,
            color       = (255, 120, 40),
        )
        self._windup_timer: float = 0.0   # час замаху

    def execute(self, fighter: Fighter, enemy: Fighter,
                focus: FocusBar, scene) -> bool:
        if not self.can_use(fighter, focus):
            return False
        focus.spend(self.focus_cost)
        self._start_cooldown()

        # Замах — гравець «заряджається» 0.45с
        fighter.can_move   = False
        fighter.can_attack = False
        fighter._skill_windup_timer = 0.45
        fighter._skill_windup_name  = "power_slam"
        fighter._skill_attack_mult  = 2.5
        fighter._skill_attack_name  = "power_slam"
        fighter._skill_force_knockdown = True

        # Жовтий спалах — «готується удар»
        fighter._flash_timer = 0.40
        fighter._flash_color = (255, 200, 40)

        if hasattr(scene, '_log_event'):
            scene._log_event("💥 Power Slam…", (255, 160, 40))
        return True


class CounterStance(Skill):
    """
    [3] Counter Stance — 0.4с вікно.
    Якщо ворог б'є у цьому вікні — автоматичний парирований
    контрудар 2× damage + стан.
    """

    def __init__(self):
        super().__init__(
            skill_id    = "counter_stance",
            name        = "Counter",
            description = "0.4с вікно парирування → контрудар 200%",
            icon        = "🛡",
            focus_cost  = 30,
            cooldown    = 6.0,
            color       = (80, 220, 140),
        )
        self.active_window: float = 0.0   # runtime: залишок вікна

    def update(self, dt: float):
        super().update(dt)
        if self.active_window > 0:
            self.active_window = max(0.0, self.active_window - dt)

    @property
    def is_active(self) -> bool:
        return self.active_window > 0

    def execute(self, fighter: Fighter, enemy: Fighter,
                focus: FocusBar, scene) -> bool:
        if not self.can_use(fighter, focus):
            return False
        focus.spend(self.focus_cost)
        self._start_cooldown()

        self.active_window = 0.40
        fighter._counter_stance_active = True
        fighter._counter_stance_mult   = 2.0

        # Зелений спалах
        fighter._flash_timer = 0.30
        fighter._flash_color = (80, 255, 140)

        try:
            from game.particles import HitEffects
            HitEffects.spawn_parry(fighter.particles,
                                   fighter.body.position.x,
                                   fighter.body.position.y - 30)
        except Exception:
            pass

        if hasattr(scene, '_log_event'):
            scene._log_event("🛡 Counter Stance!", (80, 255, 140))
        return True

    def on_hit_received(self, fighter: Fighter, damage: int,
                         enemy: Fighter, scene) -> int:
        """
        Викликається із take_damage якщо вікно активне.
        Повертає реальний damage (зменшений) і запускає контратаку.
        """
        if not self.is_active:
            return damage
        self.active_window = 0.0
        fighter._counter_stance_active = False

        # Поглинаємо удар
        absorbed_damage = max(1, damage // 5)

        # Затримана контратака через 0.05с
        fighter._skill_attack_timer = 0.05
        fighter._skill_attack_mult  = fighter._counter_stance_mult
        fighter._skill_attack_name  = "counter_stance"

        fighter._flash_timer = 0.25
        fighter._flash_color = (200, 255, 200)

        try:
            from game.particles import HitEffects
            HitEffects.spawn_parry(fighter.particles,
                                   fighter.body.position.x,
                                   fighter.body.position.y - 30)
        except Exception:
            pass

        if hasattr(scene, '_log_event'):
            scene._log_event("⚔ КОНТРАТАКА!", (100, 255, 140))

        return absorbed_damage


class BerserkerRush(Skill):
    """
    [4] Berserker Rush — 3 стрімкі удари підряд.
    Кожен удар 0.8× damage, але разом 2.4× + швидкий.
    Після активації гравець не може рухатись — сам б'є 3 рази з інтервалом 0.18с.
    """

    def __init__(self):
        super().__init__(
            skill_id    = "berserker_rush",
            name        = "Berserker Rush",
            description = "3 удари поспіль, кожен 80% damage",
            icon        = "⚔",
            focus_cost  = 50,
            cooldown    = 10.0,
            color       = (255, 60, 60),
        )

    def execute(self, fighter: Fighter, enemy: Fighter,
                focus: FocusBar, scene) -> bool:
        if not self.can_use(fighter, focus):
            return False
        focus.spend(self.focus_cost)
        self._start_cooldown()

        fighter.can_move   = False
        fighter.can_attack = False

        # Черга ударів: [(затримка, mult), ...]
        fighter._rush_queue = [
            (0.05, 0.8),
            (0.23, 0.8),
            (0.41, 0.8),
        ]
        fighter._rush_elapsed = 0.0
        fighter._skill_attack_name = "berserker_rush"

        # Червоний спалах
        fighter._flash_timer = 0.20
        fighter._flash_color = (255, 60, 60)

        if hasattr(scene, '_log_event'):
            scene._log_event("⚔⚔⚔ Berserker Rush!", (255, 80, 80))
        return True


# ══════════════════════════════════════════
#  РЕЄСТР
# ══════════════════════════════════════════

SKILLS: dict[str, Skill] = {
    "dash_strike":    DashStrike(),
    "power_slam":     PowerSlam(),
    "counter_stance": CounterStance(),
    "berserker_rush": BerserkerRush(),
}


def default_loadout() -> list[str]:
    """Дефолтний набір 4 скілів."""
    return ["dash_strike", "power_slam", "counter_stance", "berserker_rush"]


# ══════════════════════════════════════════
#  SKILL BAR (UI + логіка)
# ══════════════════════════════════════════

class SkillBar:
    """
    Панель з 4 скілами. Керується клавішами 1-4.
    Відображається внизу екрану між action bar і країю.
    """

    SLOT_W  = 64
    SLOT_H  = 64
    PADDING = 8

    def __init__(self, loadout: list[str] = None):
        ids = loadout or default_loadout()
        # Беремо копії щоб різні бої мали незалежні cd
        import copy
        self.slots: list[Optional[Skill]] = [
            copy.deepcopy(SKILLS.get(sid)) for sid in ids
        ]
        # Доповнюємо до 4
        while len(self.slots) < 4:
            self.slots.append(None)

    def update(self, dt: float):
        for skill in self.slots:
            if skill:
                skill.update(dt)

    def get(self, index: int) -> Optional[Skill]:
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None

    def try_use(self, index: int, fighter: Fighter, enemy: Fighter,
                focus: FocusBar, scene) -> bool:
        skill = self.get(index)
        if skill and skill.can_use(fighter, focus):
            return skill.execute(fighter, enemy, focus, scene)
        elif skill and not skill.ready:
            if hasattr(scene, '_log_event'):
                rem = skill._cd_remaining
                scene._log_event(
                    f"{skill.icon} {skill.name}: {rem:.1f}s",
                    (160, 160, 160)
                )
        elif skill and focus.value < skill.focus_cost:
            if hasattr(scene, '_log_event'):
                scene._log_event(
                    f"{skill.icon} Мало Focus! ({int(focus.value)}/{int(skill.focus_cost)})",
                    (255, 160, 60)
                )
        return False

    def draw(self, screen, focus: FocusBar,
             screen_w: int = 1280, screen_h: int = 720):
        """Малює skill bar внизу екрану."""
        import pygame

        total_w = 4 * self.SLOT_W + 3 * self.PADDING
        x0      = screen_w // 2 - total_w // 2
        y0      = screen_h - self.SLOT_H - 80   # вище за action bar

        for i, skill in enumerate(self.slots):
            x = x0 + i * (self.SLOT_W + self.PADDING)
            y = y0

            # Фон слоту
            bg_col = (25, 20, 30) if skill else (20, 20, 20)
            bg_rect = pygame.Rect(x, y, self.SLOT_W, self.SLOT_H)
            pygame.draw.rect(screen, bg_col, bg_rect, border_radius=8)

            if not skill:
                pygame.draw.rect(screen, (60, 60, 60), bg_rect, 2, border_radius=8)
                continue

            # Кулдаун — затемнена «шторка» зверху
            if not skill.ready:
                cd_h = int(self.SLOT_H * skill.cd_pct)
                shade = pygame.Surface((self.SLOT_W, cd_h), pygame.SRCALPHA)
                shade.fill((0, 0, 0, 160))
                screen.blit(shade, (x, y))

                # Час кулдауну
                font_cd = pygame.font.Font(None, 22)
                cd_surf = font_cd.render(f"{skill._cd_remaining:.1f}", True, (220, 220, 220))
                screen.blit(cd_surf, (
                    x + self.SLOT_W // 2 - cd_surf.get_width() // 2,
                    y + self.SLOT_H // 2 - cd_surf.get_height() // 2,
                ))

            # Focus cost індикатор — чи можемо використати
            can_afford = focus.value >= skill.focus_cost
            border_col = skill.color if can_afford else (80, 60, 60)
            pygame.draw.rect(screen, border_col, bg_rect, 2, border_radius=8)

            # Іконка (emoji → текст)
            font_icon = pygame.font.Font(None, 30)
            icon_surf = font_icon.render(skill.icon, True, (240, 230, 200))
            screen.blit(icon_surf, (
                x + self.SLOT_W // 2 - icon_surf.get_width() // 2,
                y + 8,
            ))

            # Назва
            font_nm = pygame.font.Font(None, 16)
            name_surf = font_nm.render(skill.name[:10], True, (180, 170, 160))
            screen.blit(name_surf, (x + 4, y + self.SLOT_H - 18))

            # Клавіша
            font_key = pygame.font.Font(None, 18)
            key_surf = font_key.render(str(i + 1), True, (140, 130, 120))
            screen.blit(key_surf, (x + 4, y + 4))

            # Counter stance — активний пульс
            if (isinstance(skill, CounterStance) and skill.is_active):
                pulse_alpha = int(120 + 80 * math.sin(skill.active_window * 20))
                pulse = pygame.Surface((self.SLOT_W, self.SLOT_H), pygame.SRCALPHA)
                pygame.draw.rect(pulse, (80, 255, 140, pulse_alpha), pulse.get_rect(), border_radius=8)
                screen.blit(pulse, (x, y))

        # Focus bar під скілами
        self._draw_focus_bar(screen, focus, x0, y0 + self.SLOT_H + 4, total_w)

    def _draw_focus_bar(self, screen, focus: FocusBar,
                         x: int, y: int, width: int):
        import pygame
        bg = pygame.Rect(x, y, width, 6)
        pygame.draw.rect(screen, (30, 20, 40), bg, border_radius=3)
        if focus.value > 0:
            fw = int(width * focus.pct)
            # Колір: синій → пурпурний при повному
            t   = focus.pct
            r   = int(80  + t * 120)
            g   = int(60  + t * 20)
            b   = int(220 - t * 40)
            pygame.draw.rect(screen, (r, g, b),
                              pygame.Rect(x, y, fw, 6), border_radius=3)
        pygame.draw.rect(screen, (80, 60, 100), bg, 1, border_radius=3)

        # «Focus» label
        font = pygame.font.Font(None, 16)
        lbl  = font.render(f"Focus {int(focus.value)}", True, (140, 120, 180))
        screen.blit(lbl, (x, y + 8))