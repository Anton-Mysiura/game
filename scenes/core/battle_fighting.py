"""
Сцена файтингу (real-time бій).
"""

import random
import time
import logging
import pygame
import pymunk

from .base import Scene
from .battle_ui import BattleUIMixin
from .battle_pause import BattlePauseMixin
# Draw-методи винесено у battle_draw.py — тут тільки логіка: стан, AI, фізика бою
from scenes.core.battle_draw import BattleDrawMixin

from ui.assets import assets
from ui.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from ui.notifications import notify

from game.achievements import AchievementManager
from game.battle_log import BattleLogger
from game.boss_phases import BossPhaseManager
from game.data import MATERIALS
from game.enemy import Enemy
from game.fighter import Fighter
from game.fighter_ai import create_enemy_ai
from game.save_manager import autosave
from game.skills import SkillBar, FocusBar, CounterStance, default_loadout
from game.sound_manager import sounds

log = logging.getLogger(__name__)

# ── Константи меню вибору дій ─────────────────────────────────
ACTION_ATTACK = "attack"   # J — звичайна атака
ACTION_HEAVY  = "heavy"    # U — сильний удар ×1.8, −20% влучності
ACTION_DEFEND = "defend"   # K — захист, −60% наступного удару
ACTION_ITEM   = "item"     # I — використати зілля

# Підказки дій для HUD
ACTION_HINTS = {
    ACTION_ATTACK: ("[J] Атака",   (220, 200, 140)),
    ACTION_HEAVY:  ("[U] Важкий",  (255, 160,  50)),
    ACTION_DEFEND: ("[K] Захист",  (100, 180, 255)),
    ACTION_ITEM:   ("[I] Зілля",   (100, 220, 120)),
}

# ── Бойові константи ──────────────────────────────────────────
HEAVY_DAMAGE_MULT = 1.8    # множник урону важкого удару
HEAVY_MISS_BONUS  = 0.20   # додатковий шанс промаху для важкого удару
BLOCK_REDUCTION   = 0.40   # частка урону що проходить крізь блок
LIFESTEAL_RATE    = 0.20   # частка урону що повертається як HP
HIT_RANGE         = 60     # радіус (px) для реєстрації влучання
ARENA_MARGIN      = 60     # відступ від краю екрану для обмеження арени
FINISH_FLASH_TIME = 1.8    # тривалість фінішного флешу (секунди)


class FightingBattleScene(BattleDrawMixin, BattleUIMixin, BattlePauseMixin, Scene):
    """Сцена файтингу з фізикою."""

    def __init__(self, game, enemy: Enemy, return_scene: str = "village", background_name: str = None):
        super().__init__(game)

        self.enemy_data = enemy
        self.return_scene = return_scene

        # Фонове зображення
        self.background_name = background_name
        self.background_surface = None
        if background_name:
            self.background_surface = assets.load_texture(
                "locations", background_name, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )

        # Фізичний світ
        self.space = pymunk.Space()
        self.space.gravity = (0, 981)
        self._create_ground()

        # Бійці
        self.player_fighter = self._create_player_fighter()
        self.enemy_fighter = self._create_enemy_fighter()

        # AI супротивника
        self.enemy_ai = create_enemy_ai(
            self.enemy_fighter, enemy.name,
            behavior=getattr(enemy, "behavior", "balanced"),
            enemy_level=getattr(enemy, "level", 1),
        )

        # Стан бою
        self.battle_over = False
        self.player_won = False
        self.end_timer = 0.0

        # Таймер бою
        self.battle_time_limit = 99.0
        self.battle_elapsed = 0.0

        # Статистика бою
        self.stat_damage_dealt = 0
        self.stat_damage_taken = 0
        self.stat_hits_landed  = 0
        self.stat_hits_taken   = 0
        self.stat_blocks_done  = 0
        self.stat_crits        = 0
        # Статистика для щоденних завдань
        self.stat_dodges       = 0
        self.stat_parries      = 0
        self.stat_potions_used = 0
        self.stat_bleed_applied = 0
        self.stat_heavy_kill   = False
        self.result_screen     = False
        self.result_buttons    = []
        self.loot_gained       = []

        # Журнал бою
        self._battle_logger = BattleLogger(
            player_name = self.player.name,
            enemy_name  = self.enemy_data.name,
            enemy_icon  = getattr(self.enemy_data, "icon", "👾"),
        )

        # ── Shake екрану ──
        self._shake_timer  = 0.0
        self._shake_mag    = 0
        self._shake_offset = (0, 0)

        # ── Slow-motion ─────────────────────────────────────────
        self._slowmo_timer  = 0.0   # скільки лишилось slow-mo
        self._slowmo_factor = 1.0   # поточний множник dt (1.0 = норма)

        # ── Finish blow flash ───────────────────────────────────
        self._finish_flash_timer = 0.0
        self._finish_flash_text  = ""

        # ── Enemy speech bubbles ────────────────────────────────
        self._enemy_speech_timer = 0.0
        self._enemy_speech_text  = ""
        self._enemy_speech_cd    = 0.0   # кулдаун між репліками

        # ── Боссові фази ────────────────────────────────────────
        self._boss_phase_mgr = None
        _beh = getattr(self.enemy_data, "behavior", "")
        if getattr(self.enemy_data, "is_boss", False) or "дракон" in self.enemy_data.name.lower():
            self._boss_phase_mgr = BossPhaseManager(
                self.enemy_fighter, self.enemy_data, self)

        self._confirm_exit = None   # діалог підтвердження виходу до села

        # ── Inline лог останніх подій ──
        self._inline_log: list[dict] = []  # {text, color, timer}
        self._INLINE_MAX = 5

        # ── Вибір дій ──────────────────────────────────────────
        # Захист: якщо активний, наступний удар по гравцю −60%
        self._defend_active  = False
        # Сильний удар: якщо вибрано, наступна атака J застосує множник
        self._heavy_pending  = False

        # ── Double-tap для ухилення ─────────────────────────────
        self._tap_tracker: dict = {}      # key → (last_tap_time, count)
        self.DOUBLE_TAP_WINDOW = 0.28     # сек між двома натисканнями

        # ── Заряджений удар ─────────────────────────────────────
        self._j_held   = False
        self._j_hold_t = 0.0

        self.camera_x = 0

        # ── Skill bar і Focus ────────────────────────────────────
        self.skill_bar = SkillBar(default_loadout())
        self.focus     = FocusBar()

        # UI (з BattleUIMixin)
        self._create_ui()

        # Керування
        self.keys_pressed = set()
        self.jump_pressed = False

        # Музика бою
        sounds.play_music("battle music loop.flac")

    # ══════════════════════════════════════════
    #  ІНІЦІАЛІЗАЦІЯ
    # ══════════════════════════════════════════

    def _create_ground(self):
        """Створює статичну підлогу."""
        ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        ground_body.position = (640, 600)
        ground_shape = pymunk.Segment(ground_body, (-700, 0), (700, 0), 5)
        ground_shape.friction = 1.0
        self.space.add(ground_body, ground_shape)

    def _create_player_fighter(self) -> Fighter:
        """Створює бійця гравця з характеристиками RPG."""
        # Беремо активного героя з roster замість character_id з scene_data
        hero = self.player.hero_roster.active_hero
        char_id = hero.hero_id if hero else self.game.scene_data.get("character_id", "player")

        fighter = Fighter(self.space, x=300, y=450,
                          name=self.player.name, is_player=True, character_id=char_id)
        fighter.max_hp = self.player.total_max_hp
        fighter.hp = min(self.player.hp, self.player.total_max_hp)
        fighter.attack_damage = self.player.total_attack
        fighter.defense = self.player.total_defense

        # Пасивні бонуси активного героя
        if hero:
            b = hero.passive_bonuses()
            fighter.max_hp       += b["hp"]
            fighter.hp            = min(fighter.hp + b["hp"], fighter.max_hp)
            fighter.attack_damage += b["attack"]
            fighter.defense       += b["defense"]
            fighter.hero_crit_bonus  = b["crit"]
            fighter.hero_dodge_bonus = b["dodge"]
            fighter.hero_parry_bonus = b["parry"]
            fighter.hero_id          = hero.hero_id
        else:
            fighter.hero_crit_bonus  = 0.0
            fighter.hero_dodge_bonus = 0.0
            fighter.hero_parry_bonus = 0.0
            fighter.hero_id          = None

        # Підключаємо перки
        fighter.player_data = self.player

        # Перки енергії
        m = self.player.perk_multipliers
        fighter.max_energy += m.get("max_energy", 0)
        fighter.energy      = fighter.max_energy
        fighter._energy_regen *= m.get("energy_regen", 1.0)
        if self.player.has_perk("shadow_step"):
            fighter.DODGE_COST = 0

        # Множник швидкості атаки
        spd = self.player.perk_multipliers["atk_speed"]
        if spd != 1.0:
            fighter.attack_cooldown = max(0.05, fighter.attack_cooldown / spd)

        return fighter

    def _create_enemy_fighter(self) -> Fighter:
        """Створює бійця ворога."""
        fighter = Fighter(self.space, x=980, y=450,
                          name=self.enemy_data.name, is_player=False)
        fighter.max_hp = self.enemy_data.max_hp
        fighter.hp = self.enemy_data.hp
        fighter.attack_damage = self.enemy_data.attack
        fighter.defense = self.enemy_data.defense
        return fighter

    # ══════════════════════════════════════════
    #  ЕФЕКТИ БОЮ
    # ══════════════════════════════════════════

    def _handle_double_tap(self, key: int):
        """Детектує подвійне натискання A/D і запускає ухилення."""
        now = time.monotonic()
        if key not in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
            return
        last_t, count = self._tap_tracker.get(key, (0.0, 0))
        if now - last_t < self.DOUBLE_TAP_WINDOW:
            count += 1
        else:
            count = 1
        self._tap_tracker[key] = (now, count)
        if count >= 2:
            self._tap_tracker[key] = (0.0, 0)
            direction = -1 if key in (pygame.K_a, pygame.K_LEFT) else 1
            did_dodge = self.player_fighter.dodge(direction)
            if did_dodge:
                self.stat_dodges += 1
                self._log_event("💨 Ухилення!", (80, 160, 255))

    def _shake(self, magnitude: int = 8, duration: float = 0.18):
        """Запускає тряску екрану."""
        if magnitude > self._shake_mag:
            self._shake_mag   = magnitude
            self._shake_timer = duration

    def _log_event(self, text: str, color=(220, 220, 180)):
        """Додає рядок у inline лог бою (макс _INLINE_MAX рядків)."""
        self._inline_log.append({"text": text, "color": color, "timer": 3.5})
        if len(self._inline_log) > self._INLINE_MAX:
            self._inline_log.pop(0)

    @staticmethod
    def _calc_miss_chance(attacker_level: int, defender_level: int) -> float:
        """Шанс промаху: базові 8%, +4% за кожний рівень різниці (коли атакер слабший)."""
        diff = defender_level - attacker_level
        base = 0.08
        if diff > 0:
            return min(0.45, base + diff * 0.04)
        return max(0.02, base + diff * 0.02)   # -2% якщо атакер сильніший

    # ══════════════════════════════════════════
    #  КОЛІЗІЇ
    # ══════════════════════════════════════════

    def _check_collisions(self):
        """Перевірка зіткнень вручну (для Pymunk 7.x)."""
        self._check_player_hits_enemy()
        self._check_enemy_hits_player()

    def _check_player_hits_enemy(self):
        """Обробляє влучання гравця по ворогу."""
        pf = self.player_fighter
        if not (pf.attack_hitbox and pf.attack_active):
            return
        hp  = pf.attack_hitbox.body.position
        ep  = self.enemy_fighter.body.position
        if ((hp.x - ep.x) ** 2 + (hp.y - ep.y) ** 2) ** 0.5 >= HIT_RANGE:
            return

        heavy = self._consume_heavy_flag()

        if self._roll_miss(heavy):
            self.enemy_fighter.take_damage(0, is_miss=True)
            pf._remove_attack_hitbox()
            self._log_event("Промах!", (160, 200, 255))
            return

        damage, is_crit, combo_mult = self._calc_player_damage(heavy)
        knockback = self._calc_player_knockback(is_crit)

        if self._boss_phase_mgr:
            damage = self._boss_phase_mgr.absorb_damage(damage)
        if damage > 0:
            self.enemy_fighter.take_damage(damage, knockback, is_crit=is_crit)
        pf._remove_attack_hitbox()
        self.enemy_ai.on_hit()
        self.enemy_ai.on_received_hit()
        sounds.play("sword_hit")

        self.stat_damage_dealt += damage
        self.stat_hits_landed  += 1
        if is_crit:
            self.stat_crits += 1

        self._log_player_hit(damage, is_crit, heavy)
        self._update_focus_on_hit(damage, is_crit)
        self._battle_logger.hit(damage, is_crit=is_crit)
        if combo_mult > 1.0:
            self._battle_logger.combo(pf.combo_count)

        self._apply_on_hit_perks(damage, is_crit, heavy)
        pf._just_parried = False

    # ── Допоміжні методи для _check_player_hits_enemy ────────────────────

    def _consume_heavy_flag(self) -> bool:
        """Знімає та повертає прапорець важкого удару."""
        heavy = getattr(self.player_fighter, "_pending_heavy", False)
        if heavy:
            self.player_fighter._pending_heavy = False
        return heavy

    def _roll_miss(self, heavy: bool) -> bool:
        """Повертає True якщо удар промахнувся."""
        p_lvl = self.player.level
        e_lvl = getattr(self.enemy_data, "level", p_lvl)
        miss  = self._calc_miss_chance(p_lvl, e_lvl)
        if heavy:
            miss += HEAVY_MISS_BONUS
        return random.random() < miss

    def _calc_player_damage(self, heavy: bool) -> tuple[int, bool, float]:
        """Повертає (damage, is_crit, combo_mult) для удару гравця."""
        pf = self.player_fighter
        multiplier = getattr(pf.attack_hitbox, "damage_multiplier", 1.0)

        if heavy:
            multiplier *= HEAVY_DAMAGE_MULT

        if (self.player.has_perk("dodge_attack") and
                getattr(pf, "_post_dodge_bonus", False)):
            multiplier *= 1.4
            pf._post_dodge_bonus = False

        combo_mult = pf.get_attack_damage_multiplier()

        ghost_crit = (self.player.has_perk("ghost_dodge") and
                      getattr(pf, "_post_dodge_bonus", False))
        is_crit = ghost_crit or pf._roll_crit()
        pf.last_hit_crit = is_crit

        damage = int(pf.attack_damage * multiplier * combo_mult * (2.0 if is_crit else 1.0))
        return damage, is_crit, combo_mult

    def _calc_player_knockback(self, is_crit: bool) -> int:
        """Обраховує відкидання для удару гравця."""
        pf        = self.player_fighter
        direction = 1 if pf.facing_right else -1
        base      = 400 if pf.combo_count >= 3 else 300
        knockback = base * direction
        if is_crit and self.player.has_perk("crit_knockback"):
            knockback = int(knockback * HEAVY_DAMAGE_MULT)
        if self.player.has_perk("auto_knockback"):
            knockback = int(knockback * 1.3)
        return knockback

    def _log_player_hit(self, damage: int, is_crit: bool, heavy: bool):
        """Shake + inline лог для удару гравця."""
        if is_crit:
            self._shake(12, 0.22)
            self._log_event(f"КРИТ! -{damage}", (255, 220, 50))
        elif heavy:
            self._shake(9, 0.22)
            self._log_event(f"💥 ВАЖКИЙ -{damage}", (255, 160, 50))
        elif damage >= 30:
            self._shake(7, 0.14)
            self._log_event(f"-{damage}", (255, 160, 50))
        else:
            self._log_event(f"-{damage}", (220, 160, 140))

    def _update_focus_on_hit(self, damage: int, is_crit: bool):
        """Нараховує Focus за влучний удар."""
        self.focus.gain(FocusBar.GAIN_HEAVY if (is_crit or damage >= 25) else FocusBar.GAIN_LIGHT)
        if is_crit:
            self.focus.gain(FocusBar.GAIN_CRIT)

    def _apply_on_hit_perks(self, damage: int, is_crit: bool, heavy: bool):
        """Пасивні перки що спрацьовують при влучному ударі."""
        pf           = self.player_fighter
        just_parried = getattr(pf, "_just_parried", False)

        if self.player.has_perk("stun_10") and random.random() < 0.10:
            self.enemy_fighter.stun_timer = 0.7
            self._battle_logger.stun()
            self._log_event("Ворога оглушено!", (200, 180, 255))

        if is_crit and self.player.has_perk("crit_burn"):
            self.enemy_fighter.burn_timer = 2.0
            self._battle_logger.burn()
            self._log_event("🔥 Підпал!", (255, 120, 40))

        bleed_chance = 0.08 + (0.25 if heavy else 0) + (0.15 if is_crit else 0)
        if random.random() < bleed_chance:
            duration = 5.0 if (self.player.has_perk("counter_bleed") and just_parried) else 4.0
            self.enemy_fighter.bleed_timer = max(self.enemy_fighter.bleed_timer, duration)
            self._log_event("🩸 Кровотеча!", (180, 30, 30))
            self.stat_bleed_applied += 1

        if self.player.has_perk("lifesteal"):
            heal = max(1, int(damage * LIFESTEAL_RATE))
            pf.hp = min(pf.max_hp, pf.hp + heal)
            self._battle_logger.lifesteal(heal)
            self._log_event(f"💚 +{heal} HP", (100, 220, 100))

        if self.player.has_perk("parry_heal") and just_parried:
            heal = max(1, int(pf.max_hp * 0.08))
            pf.hp = min(pf.max_hp, pf.hp + heal)
            self._log_event(f"⚔ Парирування +{heal} HP", (180, 255, 180))

    def _check_enemy_hits_player(self):
        """Обробляє влучання ворога по гравцю."""
        if not (self.enemy_fighter.attack_hitbox and self.enemy_fighter.attack_active):
            return

        hitbox_pos = self.enemy_fighter.attack_hitbox.body.position
        player_pos = self.player_fighter.body.position
        distance   = ((hitbox_pos.x - player_pos.x) ** 2 +
                      (hitbox_pos.y - player_pos.y) ** 2) ** 0.5

        if distance >= HIT_RANGE:
            return

        damage    = self.enemy_fighter.attack_damage
        knockback = -300 if self.enemy_fighter.facing_right else 300

        # ── Захист: −60% урону ──
        if self._defend_active:
            damage = max(1, int(damage * BLOCK_REDUCTION))
            self._defend_active = False
            self._log_event(f"🛡 Поглинуто! -{damage}", (100, 180, 255))
        else:
            rage_tag = " [RAGE]" if self.enemy_fighter.rage_mode else ""
            if damage >= 25:
                self._shake(10, 0.20)
                self._log_event(f"Ворог: -{damage}{rage_tag}", (255, 80, 80))
            else:
                self._log_event(f"Ворог: -{damage}", (220, 130, 130))

        # Counter Stance — перехоплюємо удар
        for sk in self.skill_bar.slots:
            if isinstance(sk, CounterStance) and sk.is_active:
                damage = sk.on_hit_received(
                    self.player_fighter, damage,
                    self.enemy_fighter, self)
                break
        self.player_fighter.take_damage(damage, knockback)
        self.enemy_fighter._remove_attack_hitbox()
        sounds.play("sword_hit")
        self.stat_damage_taken += damage
        self.stat_hits_taken   += 1
        self._battle_logger.enemy_hit(damage)

    # ══════════════════════════════════════════
    #  ЗАВЕРШЕННЯ БОЮ
    # ══════════════════════════════════════════

    def _end_battle(self, player_won: bool):
        """Завершення бою."""
        self.battle_over = True
        self.player_won = player_won
        self.end_timer = 2.5
        sounds.stop_music()

        # Бестіарій — відмічаємо зустріч незалежно від результату
        self.player.enemies_seen.add(self.enemy_data.sprite_name)

        if player_won:
            log.info("Перемога над %s", self.enemy_data.name)
            self._battle_logger.kill()

            prev_level = self.player.level
            self.player.gain_xp(self.enemy_data.xp_reward)
            self.player.gold += self.enemy_data.gold_reward
            self.player.total_gold_earned += self.enemy_data.gold_reward

            notify(f"💰 +{self.enemy_data.gold_reward}  ⭐ +{self.enemy_data.xp_reward} XP",
                   kind="gold", duration=2.5)

            loot_names = []
            for item in self.enemy_data.loot_items:
                if random.random() < 0.55:
                    self.player.inventory.append(item)
                    self.loot_gained.append(("item", item.icon, item.name, 1))
                    loot_names.append(f"{item.icon} {item.name}")

            for mat_id, qty in self.enemy_data.loot_materials.items():
                if qty <= 0:
                    continue
                self.player.add_material(mat_id, qty)
                mat = MATERIALS.get(mat_id)
                if mat:
                    self.loot_gained.append(("mat", mat.icon, mat.name, qty))
                    loot_names.append(f"{mat.icon}×{qty}")

            if loot_names:
                notify("  ".join(loot_names[:4]), kind="item", duration=3.0,
                       subtitle=f"Лут з {self.enemy_data.name}")

            if self.player.level > prev_level:
                notify(f"⭐ РІВЕНЬ {self.player.level}!", kind="level", duration=4.0)

            self.player.hp = self.player_fighter.hp

            # Статистика для досягнень
            self.player.enemies_killed += 1
            enemy_name = self.enemy_data.name.lower()
            if "гоблін" in enemy_name:
                self.player.goblins_killed += 1
            elif "орк" in enemy_name:
                self.player.orcs_killed += 1
            elif "лицар" in enemy_name:
                self.player.knights_killed += 1
            elif "дракон" in enemy_name:
                self.player.dragons_killed += 1

            newly_unlocked = AchievementManager.check_all(self.player)
            for ach_id in newly_unlocked:
                self.game.show_achievement(ach_id)

            # Щоденні завдання
            self.player.daily_quests.on_battle_end({
                "won":             True,
                "enemy_name":      self.enemy_data.name,
                "damage_dealt":    self.stat_damage_dealt,
                "crits":           self.stat_crits,
                "dodges":          self.stat_dodges,
                "parries":         self.stat_parries,
                "potions_used":    self.stat_potions_used,
                "no_damage_taken": self.stat_damage_taken == 0,
                "heavy_kill":      self.stat_heavy_kill,
                "bleed_applied":   self.stat_bleed_applied,
            })

            autosave(self.player)
        else:
            log.info("Поразка")
            self._battle_logger.death()
            self.player.deaths += 1
            autosave(self.player)

        # Зберігаємо запис бою в game для перегляду
        loot_simple = [(icon, name, qty) for (_, icon, name, qty) in self.loot_gained]
        self.game.last_battle_record = self._battle_logger.build_record(
            player_won   = player_won,
            damage_dealt = self.stat_damage_dealt,
            damage_taken = self.stat_damage_taken,
            hits_landed  = self.stat_hits_landed,
            hits_taken   = self.stat_hits_taken,
            crits        = self.stat_crits,
            blocks       = self.stat_blocks_done,
            xp_gained    = self.enemy_data.xp_reward if player_won else 0,
            gold_gained  = self.enemy_data.gold_reward if player_won else 0,
            loot         = loot_simple,
        )

    def _quick_use_potion(self):
        """Швидке використання зілля прямо під час бою (Q)."""
        potion = next((i for i in self.player.inventory
                       if i.item_type == "potion" and i.hp_restore > 0), None)
        if not potion:
            self._log_event("Зілля немає!", (160, 160, 160))
            return
        if self.player_fighter.hp >= self.player_fighter.max_hp:
            self._log_event("HP вже повний!", (160, 160, 160))
            return
        msg = self.player.use_potion(potion)
        healed = self.player_fighter.max_hp - self.player_fighter.hp
        self.player_fighter.hp = min(self.player_fighter.max_hp,
                                     self.player_fighter.hp + potion.hp_restore)
        notify(f"🧪 {msg}", kind="craft", duration=1.5)
        self._log_event(f"🧪 +{potion.hp_restore} HP", (80, 220, 120))

    # ══════════════════════════════════════════
    #  ПОДІЇ ТА ОНОВЛЕННЯ
    # ══════════════════════════════════════════

    def handle_event(self, event: pygame.event.Event):
        """Обробка подій."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not self.battle_over:
                self._unpause() if self.paused else self._pause()
            self.keys_pressed.add(event.key)
            if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                self.jump_pressed = True
            # Q — швидке зілля прямо під час бою
            if event.key == pygame.K_q and not self.battle_over and not self.paused:
                self._quick_use_potion()

            # ── Double-tap ухилення (A/A або D/D) ──────────────
            if not self.battle_over and not self.paused:
                self._handle_double_tap(event.key)

            # ── Скіли 1-4 ──────────────────────────────────────────
            if not self.battle_over and not self.paused:
                skill_keys = {
                    pygame.K_1: 0,
                    pygame.K_2: 1,
                    pygame.K_3: 2,
                    pygame.K_4: 3,
                }
                if event.key in skill_keys:
                    idx = skill_keys[event.key]
                    self.skill_bar.try_use(
                        idx,
                        self.player_fighter,
                        self.enemy_fighter,
                        self.focus,
                        self,
                    )

            # ── J натиснуто — починаємо відлік заряду ──────────
            if event.key == pygame.K_j and not self.battle_over and not self.paused:
                if not self._j_held:
                    self._j_held   = True
                    self._j_hold_t = 0.0
                    self.player_fighter.start_charge()

        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)
            if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                self.jump_pressed = False

            # ── J відпущено — відпускаємо заряджений удар ──────
            if event.key == pygame.K_j and self._j_held:
                self._j_held   = False
                charged = self.player_fighter.release_charge()
                if charged:
                    self._log_event("⚡ ЗАРЯДЖЕНИЙ УДАР!", (255, 230, 60))

        if self.result_screen and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if event.button == 1:
                for btn in self.result_buttons:
                    btn.update(mouse_pos, True)
            elif event.button == 4:  # scroll up
                self.loot_scroll_y = max(0, self.loot_scroll_y - 30)
            elif event.button == 5:  # scroll down
                self.loot_scroll_y = min(
                    getattr(self, "_loot_max_scroll", 0),
                    self.loot_scroll_y + 30
                )
            return

        if self.paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            # Діалог підтвердження
            if getattr(self, "_confirm_exit", None):
                self._confirm_exit.handle_event(event)
                if self._confirm_exit.done:
                    self._confirm_exit = None
                return
            if self.show_settings:
                self._handle_settings_click(mouse_pos)
            else:
                for btn in self.pause_buttons:
                    btn.update(mouse_pos, True)

    def update(self, dt: float):
        """Оновлення."""
        if self.battle_over:
            self.end_timer -= dt
            if self.end_timer <= 0 and not self.result_screen:
                self.result_screen = True
                self._build_result_buttons()
            if self.result_screen:
                mouse_pos = pygame.mouse.get_pos()
                for btn in self.result_buttons:
                    btn.update(mouse_pos, False)
            return

        if self.paused:
            mouse_pos = pygame.mouse.get_pos()
            if not self.show_settings:
                for btn in self.pause_buttons:
                    btn.update(mouse_pos, False)
            return

        # Таймер бою
        self.battle_elapsed += dt
        self._battle_logger.tick(dt)
        if self.battle_time_limit - self.battle_elapsed <= 0:
            self._end_battle(self.player_fighter.hp >= self.enemy_fighter.hp)
            return

        # ── Slow-motion ─────────────────────────────────────────
        if self._slowmo_timer > 0:
            self._slowmo_timer -= dt
            if self._slowmo_timer <= 0:
                self._slowmo_factor = 1.0
        # Ефективний dt для фізики та AI
        edt = dt * self._slowmo_factor

        # ── Боссові фази ────────────────────────────────────────
        if self._boss_phase_mgr:
            self._boss_phase_mgr.update(dt)   # фази завжди в реальному часі

        # ── Shake екрану ──
        if self._shake_timer > 0:
            self._shake_timer -= dt
            m = self._shake_mag
            self._shake_offset = (random.randint(-m, m), random.randint(-m, m))
            if self._shake_timer <= 0:
                self._shake_offset = (0, 0)
                self._shake_mag    = 0

        # ── Finish flash таймер ──
        if self._finish_flash_timer > 0:
            self._finish_flash_timer -= dt

        # ── Enemy speech таймери ──
        if self._enemy_speech_timer > 0:
            self._enemy_speech_timer -= dt
        if self._enemy_speech_cd > 0:
            self._enemy_speech_cd -= dt
        # Тригер репліки: ворог вдарив гравця або здоров'я низьке
        self._maybe_enemy_speech()

        # ── Inline лог: зменшуємо таймери ──
        for entry in self._inline_log:
            entry["timer"] -= dt
        self._inline_log = [e for e in self._inline_log if e["timer"] > 0]

        # Заряджений удар — оновлюємо таймер поки J тримається
        if self._j_held:
            self.player_fighter.update_charge(edt)

        self.skill_bar.update(edt)
        self.focus.update(edt)
        self._handle_player_input()
        self.enemy_ai.update(edt, self.player_fighter)
        self.space.step(edt)
        self.player_fighter.update(edt, ground_y=560)
        self.enemy_fighter.update(edt, ground_y=560)

        # Обмеження бійців в межах арени
        for fighter in [self.player_fighter, self.enemy_fighter]:
            x = fighter.body.position.x
            if x < ARENA_MARGIN:
                fighter.body.position = (ARENA_MARGIN, fighter.body.position.y)
                fighter.body.velocity = (max(0, fighter.body.velocity.x), fighter.body.velocity.y)
            elif x > SCREEN_WIDTH - ARENA_MARGIN:
                fighter.body.position = (SCREEN_WIDTH - ARENA_MARGIN, fighter.body.position.y)
                fighter.body.velocity = (min(0, fighter.body.velocity.x), fighter.body.velocity.y)

        self.camera_x = 0
        self._check_collisions()

        if self.player_fighter.hp <= 0:
            self._end_battle(False)
        elif self.enemy_fighter.hp <= 0:
            # Finishing blow — крит або важкий удар
            if self.player_fighter.last_hit_crit:
                self._finish_flash_text  = "НОКАУТ!"
                self._finish_flash_timer = FINISH_FLASH_TIME
                self.stat_heavy_kill     = True
                self._shake(20, 0.5)
            elif getattr(self.player_fighter, "_pending_heavy", False):
                self._finish_flash_text  = "НИЩІВНИЙ УДАР!"
                self._finish_flash_timer = FINISH_FLASH_TIME
                self.stat_heavy_kill     = True
                self._shake(15, 0.4)
            self._end_battle(True)

    def _handle_player_input(self):
        """Обробка керування гравцем."""
        pf = self.player_fighter

        # Рух — не рухатись під час ухилення або заряду
        if pf.state != pf.STATE_DODGING and pf._charge_held <= 0:
            if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
                pf.move_left()
            elif pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
                pf.move_right()
            else:
                pf.stop_move()

        if self.jump_pressed and pf.is_grounded:
            pf.jump()
            self.jump_pressed = False

        # J тепер повністю керується через KEYDOWN/KEYUP у handle_event
        # Але оновлюємо charge таймер поки тримаємо
        if self._j_held:
            self._j_hold_t += 0   # tick відбувається в update
            pf.update_charge(0)   # пустий — реальний dt передається в update

        # U — важкий удар (toggle)
        if pygame.K_u in self.keys_pressed:
            if not self._heavy_pending:
                self._heavy_pending = True
                self._log_event("[U] Важкий удар готовий…", (255, 200, 80))
            else:
                self._heavy_pending = False
                self._log_event("Важкий удар скасовано", (160, 160, 160))
            self.keys_pressed.discard(pygame.K_u)

        # I — зілля або атака2
        if pygame.K_i in self.keys_pressed:
            used = self._try_use_potion()
            if not used:
                pf.attack2()
            self.keys_pressed.discard(pygame.K_i)

        # O — атака3
        if pygame.K_o in self.keys_pressed:
            pf.attack3()
            self.keys_pressed.discard(pygame.K_o)

        # K — блок / парирування
        if pygame.K_k in self.keys_pressed:
            # Спроба парирування якщо щойно отримали удар
            parried = pf.try_parry()
            if parried:
                self._on_parry_success()
            else:
                pf.block()
                if not self._defend_active:
                    self._defend_active = True
                    self._log_event("🛡 Захист!", (100, 180, 255))
        elif pf.is_blocking:
            pf.stop_block()
            self._defend_active = False

    def _on_parry_success(self):
        """Реакція на вдале парирування."""
        self.focus.gain(30)  # parry bonus
        self._log_event("⚔ ПАРИРУВАННЯ!", (180, 255, 180))
        self.stat_parries += 1
        self._shake(6, 0.15)
        # Slow-motion 0.3 секунди на 20% швидкості
        self._slowmo_timer  = 0.30
        self._slowmo_factor = 0.20   # 20% швидкості під час slow-mo
        # Оглушуємо ворога
        self.enemy_fighter.stun_timer = max(self.enemy_fighter.stun_timer, 1.0)
        # Наступний удар гравця ×1.5
        self.player_fighter._pending_heavy = True

    def _try_use_potion(self) -> bool:
        """Використовує перше доступне зілля. Повертає True якщо вжито."""
        potions = [p for p in self.player.inventory
                   if p.item_type == "potion" and p.hp_restore > 0]
        if not potions:
            self._log_event("Немає зілля!", (220, 100, 100))
            return False
        if self.player_fighter.hp >= self.player_fighter.max_hp:
            self._log_event("HP вже повне!", (160, 200, 160))
            return False
        potion = potions[0]
        healed = min(potion.hp_restore,
                     self.player_fighter.max_hp - self.player_fighter.hp)
        self.player_fighter.hp += healed
        # Синхронізуємо displayed_hp
        self.player_fighter.displayed_hp = min(
            float(self.player_fighter.max_hp),
            self.player_fighter.displayed_hp + healed)
        self.player.inventory.remove(potion)
        self.stat_potions_used += 1
        self._log_event(f"🧪 +{healed} HP ({potion.name})", (100, 220, 120))
        autosave(self.player)
        return True

    # ══════════════════════════════════════════
    #  МАЛЮВАННЯ
    # ══════════════════════════════════════════