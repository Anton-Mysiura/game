"""
AI супротивника для файтингу — з динамічними фазами і телеграфуванням.

Фази:
  PHASE_NORMAL  (HP > 60%) — стандартна поведінка
  PHASE_WOUNDED (60% > HP > 30%) — більше блокує, обережніший
  PHASE_RAGE    (HP < 30%) — агресивна атака, rush, рідкий блок

Телеграфування:
  Перед важким ударом ворог показує orange flash 0.28–0.45с.
  Це вікно для Counter Stance або dodge гравця.
"""

import random
from .fighter import Fighter


class FighterAI:
    DIFFICULTY_EASY   = "easy"
    DIFFICULTY_MEDIUM = "medium"
    DIFFICULTY_HARD   = "hard"

    PHASE_NORMAL  = "normal"
    PHASE_WOUNDED = "wounded"
    PHASE_RAGE    = "rage"

    def __init__(self, fighter: Fighter, difficulty: str = DIFFICULTY_MEDIUM):
        self.fighter    = fighter
        self.difficulty = difficulty

        self.decision_timer    = 0.0
        self.action_timer      = 0.0
        self.current_action    = "idle"
        self.phase             = self.PHASE_NORMAL

        self.player_last_attack_time = 0.0
        self.consecutive_hits        = 0
        self.aggressive_mode         = False
        self.retreat_cooldown        = 0.0

        self._rush_timer    = 0.0
        self._rush_cooldown = 0.0

        self._hits_received_streak = 0
        self._guard_break_timer    = 0.0

        self._setup_difficulty()

    def _setup_difficulty(self):
        if self.difficulty == self.DIFFICULTY_EASY:
            self.reaction_time      = 0.9
            self.decision_interval  = 0.5
            self.attack_chance      = 0.28
            self.block_chance       = 0.12
            self.jump_chance        = 0.04
            self.use_attack2_chance = 0.08
            self.use_attack3_chance = 0.0
            self.predict_player     = False
            self.rush_threshold     = 0.18
            self.guard_after_hits   = 5

        elif self.difficulty == self.DIFFICULTY_MEDIUM:
            self.reaction_time      = 0.40
            self.decision_interval  = 0.28
            self.attack_chance      = 0.52
            self.block_chance       = 0.38
            self.jump_chance        = 0.09
            self.use_attack2_chance = 0.32
            self.use_attack3_chance = 0.12
            self.predict_player     = False
            self.rush_threshold     = 0.28
            self.guard_after_hits   = 3

        else:  # HARD
            self.reaction_time      = 0.12
            self.decision_interval  = 0.16
            self.attack_chance      = 0.72
            self.block_chance       = 0.62
            self.jump_chance        = 0.16
            self.use_attack2_chance = 0.48
            self.use_attack3_chance = 0.28
            self.predict_player     = True
            self.rush_threshold     = 0.35
            self.guard_after_hits   = 2

        # Telegraph fields
        self._telegraph_timer: float = 0.0
        self._telegraph_armed: bool  = False
        self._telegraph_mult:  float = 1.0
        self._fake_timer:      float = 0.0
        self._fake_cooldown:   float = 0.0

    def _update_phase(self):
        hp_pct = self.fighter.hp / max(1, self.fighter.max_hp)
        old = self.phase
        if hp_pct > 0.60:
            self.phase = self.PHASE_NORMAL
        elif hp_pct > 0.30:
            self.phase = self.PHASE_WOUNDED
        else:
            self.phase = self.PHASE_RAGE
        if old != self.PHASE_RAGE and self.phase == self.PHASE_RAGE:
            self.retreat_cooldown = 0.0
            self._rush_cooldown   = 0.0

    def _phase_block_chance(self) -> float:
        if self.phase == self.PHASE_WOUNDED:
            return min(0.82, self.block_chance * 1.5)
        if self.phase == self.PHASE_RAGE:
            return max(0.05, self.block_chance * 0.22)
        return self.block_chance

    def _phase_attack_chance(self) -> float:
        if self.phase == self.PHASE_RAGE:
            return min(0.95, self.attack_chance * 1.6)
        if self.phase == self.PHASE_WOUNDED:
            return self.attack_chance * 0.82
        return self.attack_chance

    def update(self, dt: float, player: Fighter):
        # Telegraph: заморожуємо рішення поки ворог "готується"
        if self._telegraph_timer > 0:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0 and self._telegraph_armed:
                self._telegraph_armed = False
                if self._telegraph_mult >= 1.5 and getattr(self.fighter, "has_attack3", False):
                    self.fighter.attack3()
                else:
                    self.fighter.attack()
                self.fighter._pending_heavy = True
            return

        if self._fake_cooldown > 0:
            self._fake_cooldown -= dt

        self.decision_timer          += dt
        self.action_timer            -= dt
        self.player_last_attack_time += dt

        if self.retreat_cooldown   > 0: self.retreat_cooldown   -= dt
        if self._rush_cooldown     > 0: self._rush_cooldown     -= dt
        if self._rush_timer        > 0: self._rush_timer        -= dt
        if self._guard_break_timer > 0: self._guard_break_timer -= dt

        self._update_phase()

        hp_ratio_enemy  = self.fighter.hp / max(1, self.fighter.max_hp)
        hp_ratio_player = player.hp       / max(1, player.max_hp)
        self.aggressive_mode = hp_ratio_enemy > hp_ratio_player + 0.2

        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._make_decision(player)

        self._execute_action(player)

    def _make_decision(self, player: Fighter):
        if self.fighter.hit_stun > 0 or not self.fighter.can_move:
            self.current_action = "idle"
            return

        if self._guard_break_timer > 0:
            self.fighter.stop_block()

        distance = abs(self.fighter.body.position.x - player.body.position.x)
        player_attacking = player.state in (
            player.STATE_ATTACKING, player.STATE_ATTACKING2, player.STATE_ATTACKING3
        )
        player_jumping = player.state == player.STATE_JUMPING

        # RAGE: rush attack
        if (self.phase == self.PHASE_RAGE
                and self._rush_cooldown <= 0
                and distance > 100
                and random.random() < self.rush_threshold):
            self.current_action = "rush"
            self._rush_timer    = 1.2
            self._rush_cooldown = 3.5
            return

        if self._rush_timer > 0:
            self.current_action = "rush"
            return

        # Блок при атаці гравця
        if player_attacking and distance < 130 and self._guard_break_timer <= 0:
            if random.random() < self._phase_block_chance():
                self.current_action = "block"
                self.action_timer   = random.uniform(0.35, 0.80)
                return

        if self.fighter.is_blocking and self._guard_break_timer <= 0:
            if random.random() > 0.30:
                return
            self.fighter.stop_block()
            self.current_action = "idle"
            return

        if player_jumping and distance < 150 and self.retreat_cooldown <= 0:
            if random.random() < (0.25 if self.phase == self.PHASE_RAGE else 0.48):
                self.current_action   = "retreat"
                self.action_timer     = random.uniform(0.3, 0.5)
                self.retreat_cooldown = 0.8
                return

        if distance < 90:
            roll  = random.random()
            atk_c = self._phase_attack_chance()
            if roll < atk_c and self.fighter.can_attack:
                self._choose_attack()
                return
            elif roll < atk_c + 0.15 and self.retreat_cooldown <= 0:
                if self.phase != self.PHASE_RAGE:
                    self.current_action   = "retreat"
                    self.action_timer     = random.uniform(0.2, 0.4)
                    self.retreat_cooldown = 0.6
                    return

        elif distance < 260:
            if self.phase == self.PHASE_RAGE or self.aggressive_mode:
                if random.random() < self._phase_attack_chance() and self.fighter.can_attack:
                    self._choose_attack()
                    return
            if random.random() < 0.62:
                self.current_action = "approach"
                self.action_timer   = random.uniform(0.25, 0.55)
            elif self.fighter.can_attack:
                self._choose_attack()
            return

        else:
            self.current_action = "approach"
            self.action_timer   = random.uniform(0.4, 0.8)

        if random.random() < self.jump_chance and self.fighter.is_grounded:
            self.current_action = "jump"
            self.action_timer   = 0.4

    def _choose_attack(self):
        roll  = random.random()
        has3  = getattr(self.fighter, "has_attack3", False)
        bonus = 0.15 if self.phase == self.PHASE_RAGE else 0.0

        # Telegraph перед важким ударом
        use_telegraph = (
            self.difficulty != self.DIFFICULTY_EASY
            and self._telegraph_timer <= 0
            and roll < (0.35 if self.difficulty == self.DIFFICULTY_MEDIUM else 0.20)
        )

        if use_telegraph:
            pose_time = 0.45 if self.difficulty == self.DIFFICULTY_MEDIUM else 0.28
            self._telegraph_timer = pose_time
            self._telegraph_armed = True
            self._telegraph_mult  = 1.6
            # Оранжевий flash — сигнал для гравця
            self.fighter._flash_timer = pose_time
            self.fighter._flash_color = (255, 100, 40)
            self.action_timer = pose_time + 0.1
            return

        if has3 and roll < self.use_attack3_chance + bonus:
            self.current_action = "attack3"
        elif roll < self.use_attack2_chance + bonus:
            self.current_action = "attack2"
        else:
            self.current_action = "attack"
        self.action_timer = 0.6

    def _execute_action(self, player: Fighter):
        dx        = player.body.position.x - self.fighter.body.position.x
        direction = 1 if dx > 0 else -1
        self.fighter.facing_right = dx > 0

        if self.action_timer > 0:
            if self.current_action == "approach":
                if direction > 0: self.fighter.move_right()
                else:             self.fighter.move_left()

            elif self.current_action == "rush":
                self.fighter.body.velocity = (direction * 360, self.fighter.body.velocity.y)
                self.fighter.facing_right  = direction > 0
                dist = abs(self.fighter.body.position.x - player.body.position.x)
                if dist < 95 and self.fighter.can_attack:
                    self._choose_attack()
                    self._rush_timer = 0.0

            elif self.current_action == "retreat":
                if direction > 0: self.fighter.move_left()
                else:             self.fighter.move_right()

            elif self.current_action == "attack":
                self.fighter.attack();  self.action_timer = 0

            elif self.current_action == "attack2":
                self.fighter.attack2(); self.action_timer = 0

            elif self.current_action == "attack3":
                self.fighter.attack3(); self.action_timer = 0

            elif self.current_action == "block":
                if self._guard_break_timer <= 0:
                    self.fighter.block()

            elif self.current_action == "jump":
                self.fighter.jump(); self.action_timer = 0

            elif self.current_action == "idle":
                self.fighter.stop_move()

        else:
            if self.current_action == "block":
                self.fighter.stop_block()
            if self.current_action != "rush":
                self.current_action = "idle"
                self.fighter.stop_move()

    def on_hit(self):
        self.consecutive_hits += 1
        self.current_action    = "idle"
        self.action_timer      = 0
        self.decision_timer    = self.reaction_time * 0.5

        if getattr(self, "_skirmisher", False) and self.retreat_cooldown <= 0:
            self.current_action   = "retreat"
            self.action_timer     = 0.4
            self.retreat_cooldown = 0.7

    def on_received_hit(self):
        """Викликається коли AI отримує удар — накопичує guard break."""
        self._hits_received_streak += 1
        if self._hits_received_streak >= self.guard_after_hits:
            self._hits_received_streak  = 0
            self._guard_break_timer     = 0.8
            self.fighter.stop_block()

        if (getattr(self, "_counter_after_block", False)
                and self.fighter.is_blocking
                and self.fighter.can_attack):
            self.fighter.stop_block()
            self._choose_attack()


def create_enemy_ai(fighter: Fighter, enemy_name: str,
                    behavior: str = "balanced",
                    enemy_level: int = 1) -> FighterAI:
    """
    Створює AI для ворога.
    Складність визначається рівнем ворога, а не парсингом імені.
    """
    if enemy_level <= 2:
        difficulty = FighterAI.DIFFICULTY_EASY
    elif enemy_level <= 5:
        difficulty = FighterAI.DIFFICULTY_MEDIUM
    else:
        difficulty = FighterAI.DIFFICULTY_HARD

    ai = FighterAI(fighter, difficulty)

    if behavior == "skirmisher":
        ai.decision_interval  *= 0.7
        ai.attack_chance      *= 1.2
        ai.retreat_cooldown    = 0.0
        ai.rush_threshold      = 0.0
        ai._skirmisher         = True

    elif behavior == "berserker":
        ai.block_chance       *= 0.35
        ai.attack_chance      *= 1.15
        ai.decision_interval  *= 1.3
        ai.use_attack3_chance  = 0.45
        ai.rush_threshold      = 0.40

    elif behavior == "defensive":
        ai.block_chance       *= 1.6
        ai.attack_chance      *= 0.75
        ai.retreat_cooldown    = 0.5
        ai.guard_after_hits    = max(ai.guard_after_hits, 4)
        ai._counter_after_block = True

    elif behavior == "aggressive":
        ai.attack_chance      *= 1.4
        ai.block_chance       *= 0.4
        ai.rush_threshold      = 0.60
        ai.decision_interval  *= 0.8

    ai.behavior = behavior
    return ai