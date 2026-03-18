"""
Менеджер фаз боса.

Три фази:
  Фаза 1 (HP > 66%) — нормальна
  Фаза 2 (33–66%)   — щит на 40 HP треба пробити, +rage
  Фаза 3 (< 33%)    — щит на 60 HP, +rush, подвійна атака
"""
import pygame
import math


class BossShield:
    """Щит між фазами — тимчасовий HP що треба знищити."""

    def __init__(self, hp: int):
        self.max_hp = hp
        self.hp     = hp
        self.active = True
        self._flash = 0.0

    def absorb(self, damage: int) -> int:
        """Поглинає частину урону. Повертає урон що пройшов крізь."""
        if not self.active:
            return damage
        self._flash = 0.15
        self.hp -= damage
        if self.hp <= 0:
            self.active = False
            return abs(self.hp)   # залишок прориву
        return 0

    def update(self, dt: float):
        if self._flash > 0:
            self._flash -= dt

    def draw(self, screen: pygame.Surface, x: int, y: int, width: int = 120):
        if not self.active:
            return
        bar_h = 10
        bg = pygame.Rect(x - width // 2, y, width, bar_h)
        pygame.draw.rect(screen, (20, 20, 60), bg)

        pct  = max(0, self.hp / self.max_hp)
        fill = int(width * pct)
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
        if self._flash > 0:
            color = (255, 255, 255)
        else:
            r = int(80  + 100 * pulse)
            g = int(120 + 80  * pulse)
            color = (r, g, 255)
        if fill > 0:
            pygame.draw.rect(screen, color, pygame.Rect(x - width // 2, y, fill, bar_h))
        pygame.draw.rect(screen, (120, 160, 255), bg, 1)

        font = pygame.font.Font(None, 18)
        lbl  = font.render(f"🛡 ЩИТ  {self.hp}/{self.max_hp}", True, (160, 200, 255))
        screen.blit(lbl, (x - lbl.get_width() // 2, y - 16))


class BossPhaseManager:
    """Керує фазами боса і перехідними щитами."""

    PHASE_1 = 1
    PHASE_2 = 2
    PHASE_3 = 3

    def __init__(self, fighter, enemy_data, battle_scene):
        self.fighter      = fighter
        self.enemy_data   = enemy_data
        self.battle       = battle_scene
        self.phase        = self.PHASE_1
        self.shield: BossShield | None = None

        # Анімація переходу
        self._phase_text       = ""
        self._phase_text_timer = 0.0

    # ─────────────────────────────────────────
    def update(self, dt: float):
        if self.shield:
            self.shield.update(dt)

        if self._phase_text_timer > 0:
            self._phase_text_timer -= dt

        hp_pct = self.fighter.hp / max(1, self.fighter.max_hp)

        # Перехід фаза 1 → 2
        if self.phase == self.PHASE_1 and hp_pct <= 0.66:
            self._enter_phase(self.PHASE_2, shield_hp=40)

        # Перехід фаза 2 → 3
        elif self.phase == self.PHASE_2 and hp_pct <= 0.33:
            self._enter_phase(self.PHASE_3, shield_hp=65)

    def _enter_phase(self, new_phase: int, shield_hp: int):
        # Не переходимо якщо щит ще активний
        if self.shield and self.shield.active:
            return

        self.phase  = new_phase
        self.shield = BossShield(shield_hp)

        # Заморожуємо ворога на 0.5с при появі щита
        self.fighter.stun_timer = max(self.fighter.stun_timer, 0.5)

        labels = {
            self.PHASE_2: "⚡ ФАЗА 2 — ЛЮТЬ!",
            self.PHASE_3: "💀 ФАЗА 3 — АГОНІЯ!",
        }
        self._phase_text       = labels.get(new_phase, "")
        self._phase_text_timer = 2.5

        # Посилення ворога
        if new_phase == self.PHASE_2:
            self.fighter.attack_damage = int(self.fighter.attack_damage * 1.20)
            if hasattr(self.battle, "enemy_ai"):
                ai = self.battle.enemy_ai
                ai.attack_chance  = min(0.95, ai.attack_chance  * 1.3)
                ai.block_chance   = max(0.05, ai.block_chance   * 0.7)
                ai.rush_threshold = min(0.55, ai.rush_threshold + 0.15)

        elif new_phase == self.PHASE_3:
            self.fighter.attack_damage = int(self.fighter.attack_damage * 1.15)
            self.fighter.rage_mode     = True
            if hasattr(self.battle, "enemy_ai"):
                ai = self.battle.enemy_ai
                ai.attack_chance   = 0.98
                ai.block_chance    = 0.04
                ai.rush_threshold  = 0.70
                ai.decision_interval = max(0.10, ai.decision_interval * 0.7)

        # Тряска
        if hasattr(self.battle, "_shake"):
            self.battle._shake(18, 0.4)

        if hasattr(self.battle, "_log_event"):
            self.battle._log_event(self._phase_text, (255, 80, 40))

    def absorb_damage(self, damage: int) -> int:
        """Перехоплює урон якщо щит активний. Повертає скільки пройшло."""
        if self.shield and self.shield.active:
            remaining = self.shield.absorb(damage)
            if not self.shield.active:
                self.shield = None
                if hasattr(self.battle, "_shake"):
                    self.battle._shake(15, 0.35)
                if hasattr(self.battle, "_log_event"):
                    self.battle._log_event("🛡 Щит зламано!", (255, 220, 60))
            return remaining
        return damage

    # ─────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        if self.shield and self.shield.active:
            ex = int(self.fighter.body.position.x)
            ey = int(self.fighter.body.position.y - 105)
            self.shield.draw(screen, ex, ey)

        if self._phase_text_timer > 0:
            font  = pygame.font.Font(None, 52)
            alpha = min(255, int(255 * min(1.0, self._phase_text_timer / 0.4)))
            surf  = font.render(self._phase_text, True, (255, 80, 40))
            surf.set_alpha(alpha)
            cx = screen.get_width()  // 2 - surf.get_width()  // 2
            cy = screen.get_height() // 2 - surf.get_height() // 2 - 60
            screen.blit(surf, (cx, cy))