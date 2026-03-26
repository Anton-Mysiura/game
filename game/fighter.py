"""
Клас бійця з фізикою та анімаціями.
"""

import logging
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

import pygame
import pymunk
from typing import Optional
from .animation import AnimationController, Animation, AnimationLoader
from ui.constants import ANIMATIONS_DIR
from game.sound_manager import sounds

log = logging.getLogger(__name__)


@dataclass
class DamageNumber:
    """Число шкоди що спливає над бійцем."""
    value:    int
    x:        float
    y:        float
    vy:       float
    timer:    float
    color:    tuple
    blocked:  bool  = False
    is_crit:  bool  = False
    is_miss:  bool  = False
    is_bleed: bool  = False


class Fighter:
    """Бійець з фізикою та анімаціями."""

    # Стани
    STATE_IDLE      = "idle"
    STATE_WALKING   = "walking"
    STATE_ATTACKING  = "attacking"
    STATE_ATTACKING2 = "attacking2"
    STATE_ATTACKING3 = "attacking3"
    STATE_BLOCKING  = "blocking"
    STATE_HIT       = "hit"
    STATE_KNOCKED   = "knocked"
    STATE_JUMPING   = "jumping"
    STATE_DODGING   = "dodging"

    # Кешовані шрифти — ініціалізуються один раз при першому використанні
    _font_fallback: pygame.font.Font | None = None
    _font_combo:    pygame.font.Font | None = None
    _font_dmg_big:  pygame.font.Font | None = None
    _font_dmg_sm:   pygame.font.Font | None = None
    _font_dmg_crit: pygame.font.Font | None = None
    _font_dmg_miss: pygame.font.Font | None = None
    _font_rage:     pygame.font.Font | None = None

    @classmethod
    def _init_fonts(cls):
        """Ліниво ініціалізує шрифти один раз для всього класу."""
        if cls._font_combo is not None:
            return
        cls._font_fallback = pygame.font.Font(None, 20)
        cls._font_combo    = pygame.font.Font(None, 52)
        cls._font_dmg_big  = pygame.font.Font(None, 42)
        cls._font_dmg_sm   = pygame.font.Font(None, 30)
        cls._font_dmg_crit = pygame.font.Font(None, 52)
        cls._font_dmg_miss = pygame.font.Font(None, 36)
        cls._font_rage     = pygame.font.Font(None, 18)

    def __init__(self, space: pymunk.Space, x: float, y: float,
                 name: str, is_player: bool = True, character_id: str = "player"):
        self.space        = space
        self.name         = name
        self.is_player    = is_player
        self.character_id = character_id
        self.facing_right = is_player  # гравець дивиться вправо, ворог вліво
        self.player_data  = None       # встановлюється зовні для перків

        self._setup_stats()
        self._setup_physics(x, y)
        self._setup_combat()
        self._setup_movement()
        self._setup_visuals()

        self.anim_controller = AnimationController()
        self._load_animations()

    # ── Ініціалізація по групах ────────────────────────────────────────────

    def _setup_stats(self):
        """Бойові характеристики (HP, енергія, захист)."""
        self.hp            = 100
        self.max_hp        = 100
        self.energy        = 100
        self.max_energy    = 100
        self._energy_regen = 18.0   # одиниць/сек
        self.defense       = 5
        self.attack_damage = 15

    def _setup_physics(self, x: float, y: float):
        """Фізичне тіло pymunk."""
        mass   = 70
        size   = (40, 100)
        moment = pymunk.moment_for_box(mass, size)
        self.body          = pymunk.Body(mass, moment)
        self.body.position = x, y

        self.shape                = pymunk.Poly.create_box(self.body, size)
        self.shape.friction       = 0.8
        self.shape.collision_type = 1 if self.is_player else 2
        self.shape.filter         = pymunk.ShapeFilter(
            categories=0b1 if self.is_player else 0b10
        )
        self.space.add(self.body, self.shape)

    def _setup_combat(self):
        """Стан бою: кулдауни, хітбокс, ефекти, комбо, парирування."""
        # Стан машини станів
        self.state       = self.STATE_IDLE
        self.can_move    = True
        self.can_attack  = True
        self.is_blocking = False
        self.is_grounded = True

        # Хітбокс атаки
        self.attack_hitbox: Optional[pymunk.Shape] = None
        self.attack_active = False

        # Кулдауни
        self.attack_cooldown = 0.0
        self.block_cooldown  = 0.0
        self.hit_stun        = 0.0

        # Ефекти від перків
        self.stun_timer  = 0.0
        self.burn_timer  = 0.0
        self.bleed_timer = 0.0
        self._burn_tick  = 0.0   # ініціалізуємо явно, без hasattr
        self._bleed_tick = 0.0

        # Комбо
        self.combo_count         = 0
        self.last_hit_crit       = False
        self.combo_timer         = 0.0
        self.combo_window        = 1.2
        self.max_combo           = 0
        self.combo_display_timer = 0.0

        # Rage mode (ворог <30% HP)
        self.rage_mode   = False
        self._rage_pulse = 0.0

    def _setup_movement(self):
        """Ухилення, заряджений удар, парирування."""
        # Ухилення
        self.dodge_cooldown = 0.0
        self.dodge_timer    = 0.0
        self.dodge_iframes  = 0.0
        self.DODGE_DURATION = 0.35
        self.DODGE_IFRAMES  = 0.28
        self.DODGE_COOLDOWN = 0.9
        self.DODGE_SPEED    = 480

        # Заряджений удар
        self._charge_held     = 0.0
        self.CHARGE_THRESHOLD = 0.6
        self._charge_ready    = False

        # Парирування
        self.parry_window  = 0.0
        self.PARRY_WINDOW  = 0.18
        self._just_parried = False

    def _setup_visuals(self):
        """Візуальні ефекти: flash, damage numbers, HP-бар."""
        self.damage_numbers = []

        self._flash_timer = 0.0
        self._flash_color = (255, 60, 60)

        # Плавний HP бар
        self.displayed_hp    = float(self.max_hp)
        self._hp_drain_speed = 0.0

    def _load_animations(self):
        """
        Завантажує анімації персонажа.

        Якщо character_id відповідає герою в HEROES — використовує AnimConfig.
        Інакше — fallback на стару систему (enemy та legacy character2/3/4).
        """
        from game.heroes import HEROES
        hero = HEROES.get(self.character_id) if self.is_player else None

        if hero is not None:
            self._load_animations_from_config(hero.anim)
        else:
            self._load_animations_legacy()

    def _load_animations_from_config(self, cfg):
        """Завантажує анімації з AnimConfig (нова система героїв)."""
        base = cfg.path()
        fh = cfg.frame_h
        log.info("Завантаження анімацій через AnimConfig: %s", base)

        def _load(slot_name, anim_key, loop=False, duration=0.1, fallback=None):
            """Завантажує один слот. Повертає список кадрів або fallback."""
            fname, count = getattr(cfg, slot_name, (None, 0))
            if not fname or not count:
                return fallback
            # Пробуємо точну назву файлу (регістр!)
            path = base / f"{fname}.png"
            if not path.exists():
                # Fallback: пошук без урахування регістру
                for p in base.iterdir():
                    if p.stem.lower() == fname.lower():
                        path = p
                        break
                else:
                    log.warning("Анімація не знайдена: %s", path)
                    return fallback
            frames = AnimationLoader.load_spritesheet(
                path, frame_width=fh, frame_height=fh, frame_count=count, scale=1.5)
            self.anim_controller.add_animation(
                anim_key, Animation(anim_key, frames, frame_duration=duration, loop=loop))
            return frames

        # IDLE
        idle_frames = _load("idle", "idle", loop=True, duration=0.15)
        if idle_frames is None:
            idle_frames = AnimationLoader._create_placeholder_frames(fh, fh, 4, 1.5)
            self.anim_controller.add_animation("idle",
                Animation("idle", idle_frames, frame_duration=0.15, loop=True))

        # IDLE2
        _load("idle2", "idle2", loop=False, duration=0.12)

        # ATTACKS
        atk1 = _load("attack1", "attacking", loop=False, duration=0.08, fallback=idle_frames)
        atk2 = _load("attack2", "attacking2", loop=False, duration=0.08, fallback=atk1)
        if atk2 is atk1:  # не було файлу → додаємо як копію
            self.anim_controller.add_animation("attacking2",
                Animation("attacking2", atk1, frame_duration=0.08, loop=False))
        atk3 = _load("attack3", "attacking3", loop=False, duration=0.08)
        self.has_attack3 = atk3 is not None
        if not self.has_attack3:
            self.anim_controller.add_animation("attacking3",
                Animation("attacking3", atk1, frame_duration=0.08, loop=False))

        # HURT → "hit" slot
        hurt = _load("hurt", "hit", loop=False, duration=0.10, fallback=idle_frames)

        # DEAD → "knocked" slot (використовуємо як knocked + окремо dead якщо є)
        dead = _load("dead", "knocked", loop=False, duration=0.12, fallback=idle_frames)

        # BLOCK
        block = _load("block", "blocking", loop=True, duration=0.10)
        if block is None:
            self.anim_controller.add_animation("blocking",
                Animation("blocking", idle_frames, frame_duration=0.15, loop=True))

        # JUMP
        jump = _load("jump", "jumping", loop=False, duration=0.10)
        if jump is None:
            self.anim_controller.add_animation("jumping",
                Animation("jumping", idle_frames, frame_duration=0.10, loop=False))

        # WALK
        walk = _load("walk", "walking", loop=True, duration=0.10, fallback=idle_frames)
        if walk is idle_frames:
            self.anim_controller.add_animation("walking",
                Animation("walking", idle_frames, frame_duration=0.10, loop=True))

        # RUN → якщо є, перевантажуємо "walking"
        run = _load("run", "running", loop=True, duration=0.08)

        # SPECIAL animations — зберігаємо в контролері для активних навичок
        _load("special1", "special1", loop=False, duration=0.10)
        _load("special2", "special2", loop=False, duration=0.10)

        log.info("Анімації завантажено для %s", self.character_id)

    def _load_animations_legacy(self):
        """Стара система — для ворогів і legacy character2/3/4."""
        folder = self.character_id if self.is_player else "enemy"
        base_path = ANIMATIONS_DIR / folder
        log.info("Legacy анімації: %s", folder)

        frame_counts = {
            "player":     {"idle": 13, "block": 7, "hit": 4, "knocked": 5, "jump": 10},
            "character2": {"idle": 6,  "block": 6, "hit": 3, "knocked": 4, "jump": 16},
            "character3": {"idle": 7,  "block": 7, "hit": 3, "knocked": 4, "jump": 12},
            "character4": {"idle": 6,  "block": 6, "hit": 2, "knocked": 4, "jump": 8},
            "enemy":      {"idle": 6,  "block": 4, "hit": 3, "knocked": 4, "jump": 8},
        }
        fc = frame_counts.get(folder, frame_counts["enemy"])

        def _ss(filename, count, key, loop=False, dur=0.1):
            path = base_path / filename
            frames = AnimationLoader.load_spritesheet(
                path, frame_width=128, frame_height=128, frame_count=count, scale=1.5)
            self.anim_controller.add_animation(key, Animation(key, frames, frame_duration=dur, loop=loop))
            return frames

        idle_f = _ss("idle.png",    fc["idle"],    "idle",     loop=True,  dur=0.15)
        _ss("attack.png",           6,             "attacking",             dur=0.08)
        _ss("hit.png",              fc["hit"],     "hit",                   dur=0.10)
        _ss("knocked.png",          fc["knocked"], "knocked",               dur=0.12)
        _ss("jump.png",             fc["jump"],    "jumping",               dur=0.10)

        # Block
        block_path = base_path / "block.png"
        if block_path.exists():
            _ss("block.png", fc["block"], "blocking", loop=True, dur=0.10)
        else:
            self.anim_controller.add_animation("blocking",
                Animation("blocking", idle_f, frame_duration=0.15, loop=True))

        # Walk
        walk_path = base_path / "walk.png"
        if walk_path.exists():
            _ss("walk.png", 8, "walking", loop=True, dur=0.10)
        else:
            self.anim_controller.add_animation("walking",
                Animation("walking", idle_f, frame_duration=0.10, loop=True))

        # Attack2/3
        char_config = {
            "player":     {"attack2": 4, "attack3": 6},
            "character2": {"attack2": 3, "attack3": None},
            "character3": {"attack2": 4, "attack3": 4},
            "character4": {"attack2": 5, "attack3": 4},
            "enemy":      {"attack2": None, "attack3": None},
        }
        cfg = char_config.get(folder, {"attack2": None, "attack3": None})
        atk1_frames = self.anim_controller.animations["attacking"].frames

        if cfg["attack2"]:
            p2 = base_path / "attack2.png"
            if p2.exists():
                _ss("attack2.png", cfg["attack2"], "attacking2", dur=0.08)
            else:
                self.anim_controller.add_animation("attacking2",
                    Animation("attacking2", atk1_frames, frame_duration=0.08, loop=False))
        else:
            self.anim_controller.add_animation("attacking2",
                Animation("attacking2", atk1_frames, frame_duration=0.08, loop=False))

        self.has_attack3 = cfg.get("attack3") is not None
        if self.has_attack3:
            p3 = base_path / "attack3.png"
            if p3.exists():
                _ss("attack3.png", cfg["attack3"], "attacking3", dur=0.08)
            else:
                self.anim_controller.add_animation("attacking3",
                    Animation("attacking3", atk1_frames, frame_duration=0.08, loop=False))
        else:
            self.anim_controller.add_animation("attacking3",
                Animation("attacking3", atk1_frames, frame_duration=0.08, loop=False))

        # Idle variants
        for idx in range(2, 6):
            vp = base_path / f"idle{idx}.png"
            if not vp.exists():
                break
            vc = AnimationLoader.count_frames(vp, 128)
            _ss(f"idle{idx}.png", vc, f"idle{idx}", dur=0.12)

    def move_left(self):
        """Рух вліво."""
        if self.can_move and self.is_grounded:
            self.body.velocity = (-200, self.body.velocity.y)
            self.facing_right = False
            if self.state == self.STATE_IDLE:
                self.state = self.STATE_WALKING
                self.anim_controller.play("walking")

    def move_right(self):
        """Рух вправо."""
        if self.can_move and self.is_grounded:
            self.body.velocity = (200, self.body.velocity.y)
            self.facing_right = True
            if self.state == self.STATE_IDLE:
                self.state = self.STATE_WALKING
                self.anim_controller.play("walking")

    def stop_move(self):
        """Зупинка руху."""
        if self.can_move and self.is_grounded:
            self.body.velocity = (0, self.body.velocity.y)
            if self.state == self.STATE_WALKING:
                self.state = self.STATE_IDLE
                if not self.anim_controller.current_name.startswith("idle"):
                    self.anim_controller.play("idle")

    def jump(self):
        """Стрибок."""
        if self.can_move and self.is_grounded:
            self.is_grounded = False
            self.state = self.STATE_JUMPING
            self.can_move = True
            # Зміщуємо тіло від підлоги щоб pymunk не блокував рух
            self.body.position = (self.body.position.x, self.body.position.y - 5)
            self.body.velocity = (self.body.velocity.x, -700)
            sounds.play("jump")
            self.anim_controller.play("jumping", force_restart=True)

    # ── Ухилення ──────────────────────────────────────────────────

    def dodge(self, direction: int):
        """Перекат у напрямку direction (+1 / -1). Витрачає 25 енергії."""
        if (self.dodge_cooldown > 0 or
                self.state in (self.STATE_DODGING, self.STATE_KNOCKED) or
                not self.is_grounded):
            return False
        if self.energy < getattr(self, "DODGE_COST", 25):
            return False   # недостатньо енергії
        self.energy = max(0, self.energy - getattr(self, "DODGE_COST", 25))
        self.state        = self.STATE_DODGING
        self.dodge_timer  = self.DODGE_DURATION
        self.dodge_iframes = self.DODGE_IFRAMES
        self.dodge_cooldown = self.DODGE_COOLDOWN
        self.can_attack   = False
        self.can_move     = False
        self._post_dodge_bonus = True   # для dodge_attack / ghost_dodge перків
        # infinite_combo: ухилення не скидає комбо
        if not (self.player_data and self.player_data.has_perk("infinite_combo")):
            self._reset_combo()
        spd = self.DODGE_SPEED * direction
        self.body.velocity = (spd, self.body.velocity.y)
        # Візуальний flash синім
        self._flash_timer = 0.12
        self._flash_color = (80, 160, 255)
        return True

    # ── Заряджений удар ────────────────────────────────────────

    def start_charge(self):
        """Починає заряджання удару (зупиняє рух)."""
        if not self.can_attack or self.attack_cooldown > 0:
            return
        self._charge_held  = 0.001   # позначаємо початок заряду
        self._charge_ready = False
        self.can_move      = False    # гравець стоїть під час заряду

    def update_charge(self, dt: float):
        """Оновлює таймер заряду. Викликати у _handle_player_input."""
        if self._charge_held <= 0:
            return
        self._charge_held += dt
        if self._charge_held >= self.CHARGE_THRESHOLD and not self._charge_ready:
            self._charge_ready = True
            # Жовтий flash = «заряд готовий»
            self._flash_timer = 0.08
            self._flash_color = (255, 240, 60)

    def release_charge(self):
        """Відпускає заряджений удар. Повертає True якщо був заряджений."""
        held = self._charge_held
        self._charge_held  = 0.0
        self._charge_ready = False
        self.can_move      = True
        if held >= self.CHARGE_THRESHOLD:
            # Заряджений: витрачає 35 енергії
            if self.energy < 35:
                # Немає енергії — звичайна атака
                self.attack()
                return False
            self.energy = max(0, self.energy - 35)
            # Заряджений: ×2.5, завжди knockdown
            self._increment_combo()
            self.state        = self.STATE_ATTACKING
            self.can_attack   = False
            self.attack_cooldown = 1.1
            self.anim_controller.play("attacking", force_restart=True)
            sounds.play("sword_swing", volume=1.0)
            self._create_attack_hitbox(damage_multiplier=2.5)
            self._flash_timer = 0.20
            self._flash_color = (255, 200, 50)
            return True
        elif held > 0.05:
            # Звичайний удар якщо тримали мало
            self.attack()
        return False

    # ── Парирування ────────────────────────────────────────────

    def try_parry(self) -> bool:
        """Спроба парирування (викликати у момент натискання K під ударом).
        Повертає True якщо парирування вдалось."""
        if self.parry_window > 0:
            self._just_parried = True
            self.parry_window  = 0.0
            self._flash_timer  = 0.25
            self._flash_color  = (200, 255, 200)
            return True
        return False

    def attack(self):
        """Атака."""
        if not self.can_attack or self.attack_cooldown > 0:
            return

        self._increment_combo()
        self.state = self.STATE_ATTACKING
        self.can_move = False
        self.can_attack = False
        self.attack_cooldown = 0.6 * (0.85 if self.combo_count >= 3 else 1.0)
        self.anim_controller.play("attacking", force_restart=True)
        sounds.play("sword_swing")

        # Хітбокс з'явиться через 0.15 сек (коли рука вже замахнулась)
        # Поки що створюємо одразу
        self._create_attack_hitbox()

    def attack2(self):
        """Друга атака — швидка, менше шкоди."""
        if not self.can_attack or self.attack_cooldown > 0:
            return
        self._increment_combo()
        self.state = self.STATE_ATTACKING2
        self.can_move = False
        self.can_attack = False
        self.attack_cooldown = 0.4 * (0.85 if self.combo_count >= 3 else 1.0)
        self.anim_controller.play("attacking2", force_restart=True)
        sounds.play("sword_swing", volume=0.5)
        self._create_attack_hitbox(damage_multiplier=0.7)

    def attack3(self):
        """Третя атака — повільна, більше шкоди."""
        if not self.can_attack or self.attack_cooldown > 0 or not self.has_attack3:
            return
        self._increment_combo()
        self.state = self.STATE_ATTACKING3
        self.can_move = False
        self.can_attack = False
        self.attack_cooldown = 1.0
        self.anim_controller.play("attacking3", force_restart=True)
        sounds.play("sword_swing", volume=0.9)
        self._create_attack_hitbox(damage_multiplier=1.8)

    def block(self):
        """Блокування."""
        if self.state != self.STATE_BLOCKING and self.block_cooldown <= 0 and self.is_grounded:
            self.state = self.STATE_BLOCKING
            self.is_blocking = True
            self.can_move = False
            self.anim_controller.play("blocking")

    def stop_block(self):
        """Припиняє блокування."""
        if self.state == self.STATE_BLOCKING:
            self.is_blocking = False
            self.block_cooldown = 0.3
            self._return_to_idle()

    def take_damage(self, damage: int, knockback_x: float = 0, is_crit: bool = False,
                    is_miss: bool = False):
        """Отримує шкоду."""
        # MISS
        if is_miss:
            self._spawn_damage_number(0, blocked=False, is_crit=False, is_miss=True)
            return

        # I-FRAMES під час ухилення — повне уникнення
        if self.dodge_iframes > 0:
            self._spawn_damage_number(0, blocked=False, is_crit=False, is_miss=True)
            return

        # Відкриваємо вікно парирування
        self.parry_window = self.PARRY_WINDOW

        self._reset_combo()
        if self.is_blocking:
            actual_damage = int(damage * 0.3)
            self.hp -= actual_damage
            self.displayed_hp = max(self.hp, self.displayed_hp)  # теж оновлюємо
            self.body.velocity = (knockback_x * 0.3, self.body.velocity.y)
            self._spawn_damage_number(actual_damage, blocked=True)
            self._flash_timer = 0.08
            self._flash_color  = (120, 180, 255)   # синій при блоці
            return

        actual_damage = max(1, damage - self.defense)
        self.hp -= actual_damage
        # Плавний HP бар: миттєво показуємо поточний, потім плавно «доточуємо»
        # (displayed_hp не стрибає, а повільно опускається)
        self._spawn_damage_number(actual_damage, blocked=False, is_crit=is_crit)

        # Flash
        if is_crit:
            self._flash_timer = 0.18
            self._flash_color  = (255, 220, 50)   # жовтий при кріті
        else:
            self._flash_timer = 0.10
            self._flash_color  = (255, 60, 60)    # червоний

        if actual_damage > 25 or abs(knockback_x) > 400:
            sounds.play("grunt")
            self.state = self.STATE_KNOCKED
            self.hit_stun = 1.5
            self.can_move = False
            self.can_attack = False
            self.body.velocity = (knockback_x, -200)
            self.anim_controller.play("knocked", force_restart=True)
        else:
            sounds.play("hurt")
            self.state = self.STATE_HIT
            self.hit_stun = 0.4
            self.can_move = False
            self.can_attack = False
            self.body.velocity = (knockback_x * 0.5, self.body.velocity.y)
            self.anim_controller.play("hit", force_restart=True)

    def _get_combo_multiplier(self) -> float:
        """Повертає множник шкоди залежно від комбо."""
        if self.combo_count <= 1:
            return 1.0
        elif self.combo_count == 2:
            return 1.2
        elif self.combo_count == 3:
            return 1.5
        else:
            return 1.8

    def _get_crit_chance(self) -> float:
        """Шанс крит удару (асимптота до 100%, ніколи не досягає)."""
        t = 0.0526  # базово ~5%
        c = self.combo_count
        if c >= 2:
            t += 0.111
        if c >= 3:
            t += 0.056
        for i in range(4, c + 1):
            t += 0.02 / (1 + (i - 4) * 0.3)
        base_chance = 100 - 100 / (1 + t)

        # Бонус від перків + локацій (через total_crit_chance)
        if self.player_data:
            base_chance += self.player_data.total_crit_chance

        return base_chance

    def _roll_crit(self) -> bool:
        """Кидає кубик на крит."""
        # Перк: кожен 5-й удар = гарантований крит
        if self.player_data and self.player_data.has_perk("every_5th_crit"):
            if (self.combo_count + 1) % 5 == 0:
                return True
        # Перк: кожен 3-й удар = гарантований крит (GOD)
        if self.player_data and self.player_data.has_perk("every_3rd_crit"):
            if (self.combo_count + 1) % 3 == 0:
                return True
        return random.random() * 100 < self._get_crit_chance()

    def _increment_combo(self):
        """Збільшує лічильник комбо."""
        self.combo_count += 1
        self.combo_timer = self.combo_window
        if self.combo_count >= 4:
            self.combo_display_timer = 1.8
        if self.combo_count > self.max_combo:
            self.max_combo = self.combo_count

    def _reset_combo(self):
        """Скидає комбо."""
        self.combo_count = 0
        self.combo_timer = 0.0

    def _spawn_damage_number(self, value: int, blocked: bool = False,
                             is_crit: bool = False, is_miss: bool = False,
                             is_bleed: bool = False):
        """Додає число шкоди що спливає вгору."""
        x = self.body.position.x + random.randint(-20, 20)
        y = self.body.position.y - 60
        if is_miss:
            color = (160, 200, 255)
        elif is_bleed:
            color = (180, 30, 30)
        elif is_crit:
            color = (20, 20, 20)
        elif blocked:
            color = (180, 180, 180)
        elif value >= 25:
            color = (255, 200, 0)
        else:
            color = (255, 80, 80)
        self.damage_numbers.append(DamageNumber(
            value=value,
            x=float(x),
            y=float(y),
            vy=-150.0 if is_crit else -90.0,
            timer=1.5 if is_crit else 1.2,
            color=color,
            blocked=blocked,
            is_crit=is_crit,
            is_miss=is_miss,
            is_bleed=is_bleed,
        ))

    def _update_damage_numbers(self, dt: float):
        """Оновлює позиції чисел шкоди."""
        for num in self.damage_numbers:
            num.y  += num.vy * dt
            num.vy *= 0.92  # уповільнення
            num.timer -= dt
        self.damage_numbers = [n for n in self.damage_numbers if n.timer > 0]

    def get_attack_damage_multiplier(self) -> float:
        """Повертає загальний множник шкоди з урахуванням комбо та перків."""
        multiplier = self._get_combo_multiplier()

        if self.player_data:
            m = self.player_data.perk_multipliers

            # Бонус шкоди від перків
            multiplier *= m["dmg"]

            # Перк: перший удар у комбо +50%
            if self.combo_count == 0 and self.player_data.has_perk("first_hit_combo"):
                multiplier *= 1.5

            # Перк: подвійний удар — множник x2
            if self.player_data.has_perk("double_hit"):
                multiplier *= 2.0

            # Перк: повітряні атаки +200%
            if self.state == self.STATE_JUMPING and self.player_data.has_perk("air_attack_200"):
                multiplier *= 3.0

        return multiplier

    def _create_attack_hitbox(self, damage_multiplier: float = 1.0):
        """Створює хітбокс для атаки."""
        self._attack_damage_multiplier = damage_multiplier
        offset_x = 60 if self.facing_right else -60
        hitbox_pos = (self.body.position.x + offset_x, self.body.position.y)

        # Кінематичне тіло (не впливає на фізику)
        hitbox_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        hitbox_body.position = hitbox_pos

        # Форма
        hitbox_shape = pymunk.Poly.create_box(hitbox_body, (50, 40))
        hitbox_shape.sensor = True  # Не блокує рух
        hitbox_shape.collision_type = 3  # Тип "атака"

        hitbox_shape.damage_multiplier = damage_multiplier
        self.attack_hitbox = hitbox_shape
        self.attack_active = True
        self.space.add(hitbox_body, hitbox_shape)

        # Видалимо через 0.2 секунди
        # (в update перевіримо)

    def _remove_attack_hitbox(self):
        """Видаляє хітбокс атаки."""
        if self.attack_hitbox:
            self.space.remove(self.attack_hitbox.body, self.attack_hitbox)
            self.attack_hitbox = None
            self.attack_active = False

    def _return_to_idle(self):
        """Повертає до idle стану."""
        self.state = self.STATE_IDLE
        self.can_move = True
        self.can_attack = True
        # Не перериваємо idle variant якщо він вже грає
        if not self.anim_controller.current_name.startswith("idle"):
            self.anim_controller.play("idle")

    def update(self, dt: float, ground_y: float = 550):
        """Оновлення бійця: делегує кожній підсистемі."""
        self._update_damage_numbers(dt)
        self._update_resources(dt)
        self._update_timers(dt)
        self._update_status_effects(dt)
        self._update_state_machine(dt, ground_y)

    # ── Підсистеми update ─────────────────────────────────────────────────

    def _update_resources(self, dt: float):
        """Регенерація енергії + плавний HP бар + flash + rage."""
        # Енергія
        if self.energy < self.max_energy:
            regen = self._energy_regen
            if self.state == self.STATE_DODGING or self._charge_held > 0:
                regen *= 0.3
            self.energy = min(self.max_energy, self.energy + regen * dt)

        # Плавний HP бар
        if self.displayed_hp > self.hp:
            drain = max(30, (self.displayed_hp - self.hp) * 4) * dt
            self.displayed_hp = max(float(self.hp), self.displayed_hp - drain)
        else:
            self.displayed_hp = float(self.hp)

        # Flash таймер
        if self._flash_timer > 0:
            self._flash_timer -= dt

        # Rage mode (ворог <30% HP → +30% атаки)
        if not self.is_player:
            if self.hp > 0 and (self.hp / self.max_hp) < 0.30 and not self.rage_mode:
                self.rage_mode     = True
                self.attack_damage = int(self.attack_damage * 1.30)
            self._rage_pulse = (self._rage_pulse + dt * 4) % (2 * 3.14159)

    def _update_timers(self, dt: float):
        """Усі кулдауни та вікна: ухилення, парирування, заряд, комбо."""
        # Ухилення
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= dt
        if self.dodge_iframes > 0:
            self.dodge_iframes -= dt
        if self.dodge_timer > 0:
            self.dodge_timer -= dt
            if self.dodge_timer <= 0:
                self.body.velocity = (0, self.body.velocity.y)
                self._return_to_idle()

        # Парирування
        if self.parry_window > 0:
            self.parry_window -= dt

        # Заряд — помаранчеве миготіння
        if self._charge_held > 0 and not self._charge_ready:
            if (math.sin(self._charge_held * 20) + 1) / 2 > 0.7:
                self._flash_timer = 0.04
                self._flash_color = (255, 160, 40)

        # Комбо
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self._reset_combo()
        if self.combo_display_timer > 0:
            self.combo_display_timer -= dt

    def _update_status_effects(self, dt: float):
        """Тік стану: оглушення, підпалення, кровотеча."""
        # Оглушення
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.can_move   = False
            self.can_attack = False

        # Підпалення — 3% max_hp кожні 0.5 сек
        if self.burn_timer > 0:
            self.burn_timer  -= dt
            self._burn_tick  += dt
            if self._burn_tick >= 0.5:
                self._burn_tick = 0.0
                burn_dmg = max(1, int(self.max_hp * 0.03))
                self.hp  = max(0, self.hp - burn_dmg)
                self._spawn_damage_number(burn_dmg)

        # Кровотеча — 4% max_hp щосекунди
        if self.bleed_timer > 0:
            self.bleed_timer -= dt
            self._bleed_tick += dt
            if self._bleed_tick >= 1.0:
                self._bleed_tick = 0.0
                bleed_dmg = max(1, int(self.max_hp * 0.04))
                self.hp   = max(0, self.hp - bleed_dmg)
                self._spawn_damage_number(bleed_dmg, is_bleed=True)
                self._flash_timer = 0.07
                self._flash_color = (200, 0, 0)

    def _update_state_machine(self, dt: float, ground_y: float):
        """Анімації, кулдауни атаки/блоку, приземлення, обмеження швидкості."""
        self.anim_controller.update(dt)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.block_cooldown > 0:
            self.block_cooldown -= dt
        if self.hit_stun > 0:
            self.hit_stun -= dt
            if self.hit_stun <= 0:
                self._return_to_idle()

        if self.state in (self.STATE_ATTACKING, self.STATE_ATTACKING2, self.STATE_ATTACKING3):
            if self.anim_controller.is_finished():
                self._remove_attack_hitbox()
                self._return_to_idle()
            elif self.anim_controller.current_animation.current_frame >= 3:
                if self.attack_hitbox:
                    self._remove_attack_hitbox()

        if self.state == self.STATE_KNOCKED and self.anim_controller.is_finished():
            self._return_to_idle()

        if self.state == self.STATE_WALKING and abs(self.body.velocity.x) < 10:
            self.state = self.STATE_IDLE
            if not self.anim_controller.current_name.startswith("idle"):
                self.anim_controller.play("idle")

        # Приземлення
        prev_grounded    = self.is_grounded
        self.is_grounded = (self.body.position.y >= ground_y - 20) and abs(self.body.velocity.y) < 80
        if self.is_grounded and not prev_grounded and self.state == self.STATE_JUMPING:
            self._return_to_idle()

        # Обмеження горизонтальної швидкості
        vx = self.body.velocity.x
        if abs(vx) > 300:
            self.body.velocity = (300 if vx > 0 else -300, self.body.velocity.y)




    def draw(self, screen: pygame.Surface, camera_offset: tuple = (0, 0)):
        """Малює бійця."""
        # Отримуємо поточний кадр
        frame = self.anim_controller.get_current_frame()

        if frame is None:
            # Якщо немає кадру — малюємо fallback прямокутник
            rect = pygame.Rect(
                int(self.body.position.x - 20 + camera_offset[0]),
                int(self.body.position.y - 50 + camera_offset[1]),
                40, 100
            )
            pygame.draw.rect(screen, (255, 100, 100), rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 3)

            # Ім'я
            self._init_fonts()
            font = self._font_fallback
            text = font.render(self.name, True, (255, 255, 255))
            screen.blit(text, (rect.x, rect.y - 20))

            self._draw_hp_bar(screen, camera_offset)
            return

        # Є кадр — малюємо його
        # Відзеркалюємо якщо дивимося вліво (використовуємо кеш)
        if not self.facing_right:
            display_frame = self.anim_controller.get_flipped_frame() or frame
        else:
            display_frame = frame

        # Розраховуємо позицію (центруємо по тілу)
        x = int(self.body.position.x - display_frame.get_width() // 2 + camera_offset[0])
        y = int(self.body.position.y - display_frame.get_height() // 2 + camera_offset[1])

        # Малюємо спрайт
        screen.blit(display_frame, (x, y))

        # Flash ефект при отриманні урону
        if self._flash_timer > 0:
            flash_surf = display_frame.copy()
            # Заповнюємо кольором тільки непрозорі пікселі
            flash_surf.fill((*self._flash_color, 0), special_flags=pygame.BLEND_RGBA_MAX)
            alpha = int(180 * min(1.0, self._flash_timer / 0.1))
            flash_surf.set_alpha(alpha)
            screen.blit(flash_surf, (x, y))

        # Числа шкоди
        self._draw_damage_numbers(screen, camera_offset)
        # Комбо напис
        if self.combo_display_timer > 0 and self.combo_count >= 4:
            self._draw_combo_label(screen, camera_offset)

        # HP бар
        self._draw_hp_bar(screen, camera_offset)

    def _draw_combo_label(self, screen: pygame.Surface, camera_offset: tuple):
        """Малює напис COMBO xN над бійцем."""
        alpha = min(255, int(255 * min(1.0, self.combo_display_timer / 0.4)))
        self._init_fonts()
        font = self._font_combo
        label = f"COMBO x{self.combo_count}!"
        surf = font.render(label, True, (255, 220, 0))
        surf.set_alpha(alpha)
        shadow = font.render(label, True, (0, 0, 0))
        shadow.set_alpha(alpha // 2)
        x = int(self.body.position.x - surf.get_width() // 2 + camera_offset[0])
        y = int(self.body.position.y - 110 + camera_offset[1])
        screen.blit(shadow, (x + 2, y + 2))
        screen.blit(surf, (x, y))

    def _draw_damage_numbers(self, screen: pygame.Surface, camera_offset: tuple):
        """Малює числа шкоди що спливають."""
        if not sounds.show_damage_numbers:
            return
        self._init_fonts()
        font_big  = self._font_dmg_big
        font_sm   = self._font_dmg_sm
        font_crit = self._font_dmg_crit
        font_miss = self._font_dmg_miss
        for num in self.damage_numbers:
            max_t = 1.5 if num.is_crit else 1.2
            alpha = min(255, int(255 * (num.timer / max_t)))
            x = int(num.x + camera_offset[0])
            y = int(num.y + camera_offset[1])

            if num.is_miss:
                font  = font_miss
                label = "МИМО"
                shadow_color = (0, 0, 0)
            elif num.is_bleed:
                font  = font_sm
                label = f"🩸{num.value}"
                shadow_color = (0, 0, 0)
            elif num.is_crit:
                font  = font_crit
                label = f"КРИТ! {num.value}"
                shadow_color = (200, 200, 200)
            else:
                font  = font_big if num.value >= 20 else font_sm
                label = "БЛОК" if num.blocked and num.value == 0 else str(num.value)
                shadow_color = (0, 0, 0)

            surf   = font.render(label, True, num.color)
            surf.set_alpha(alpha)
            shadow = font.render(label, True, shadow_color)
            shadow.set_alpha(alpha // 2)
            screen.blit(shadow, (x + 2, y + 2))
            screen.blit(surf, (x, y))

    def _draw_hp_bar(self, screen: pygame.Surface, camera_offset: tuple):
        """Малює HP бар і бар енергії над головою."""
        bar_width  = 80
        bar_height = 8
        x = int(self.body.position.x - bar_width // 2 + camera_offset[0])
        y = int(self.body.position.y - 70 + camera_offset[1])

        bg_rect = pygame.Rect(x, y, bar_width, bar_height)
        pygame.draw.rect(screen, (40, 40, 40), bg_rect)

        # «Жовта» частина — drain
        disp_pct = max(0, self.displayed_hp / self.max_hp)
        disp_w   = int(bar_width * disp_pct)
        if disp_w > 0:
            pygame.draw.rect(screen, (200, 180, 40),
                             pygame.Rect(x, y, disp_w, bar_height))

        # Реальний HP
        hp_pct = max(0, self.hp / self.max_hp)
        fill_w = int(bar_width * hp_pct)
        if fill_w > 0:
            if self.rage_mode:
                pulse = int(30 * math.sin(self._rage_pulse))
                bar_color = (min(255, 200 + pulse), max(0, 40 - pulse), max(0, 40 - pulse))
            else:
                bar_color = (200, 50, 50) if hp_pct > 0.3 else (255, 100, 100)
            pygame.draw.rect(screen, bar_color, pygame.Rect(x, y, fill_w, bar_height))

        pygame.draw.rect(screen, (80, 80, 80), bg_rect, 1)

        # Rage іконка
        if self.rage_mode:
            self._init_fonts()
            font    = self._font_rage
            pulse_a = int(200 + 55 * abs(math.sin(self._rage_pulse)))
            rs = font.render("RAGE!", True, (255, 80, 40))
            rs.set_alpha(pulse_a)
            screen.blit(rs, (x + bar_width // 2 - rs.get_width() // 2, y - 14))

        # ── Бар енергії (тільки для гравця) ────────────────────
        if self.is_player:
            ey       = y + bar_height + 2
            en_pct   = max(0.0, self.energy / self.max_energy)
            en_w     = int(bar_width * en_pct)
            en_bg    = pygame.Rect(x, ey, bar_width, 4)
            pygame.draw.rect(screen, (20, 20, 40), en_bg)
            if en_w > 0:
                # Колір: синій → блакитний залежно від заряду
                low_e = en_pct < 0.3
                en_color = (80, 100, 200) if not low_e else (180, 80, 80)
                pygame.draw.rect(screen, en_color, pygame.Rect(x, ey, en_w, 4))
            pygame.draw.rect(screen, (60, 60, 100), en_bg, 1)