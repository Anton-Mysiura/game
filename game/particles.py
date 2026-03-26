"""
Система частинок для бойових VFX.

Використання:
    from game.particles import HitEffects

    # У take_damage():
    HitEffects.spawn_hit(emitter, x, y, damage, facing_right)
    HitEffects.spawn_crit(emitter, x, y, damage)
    HitEffects.spawn_block(emitter, x, y)
    HitEffects.spawn_dodge(emitter, x, y, direction)
    HitEffects.spawn_blood(emitter, x, y)

    # У draw() — після blit спрайта:
    emitter.draw(screen, camera_offset)

    # У update():
    emitter.update(dt)
"""

import math
import random
import pygame
from typing import List, Tuple


# ══════════════════════════════════════════
#  ОДНА ЧАСТИНКА
# ══════════════════════════════════════════

class Particle:
    """Одна частинка з фізикою."""

    __slots__ = (
        "x", "y", "vx", "vy",
        "life", "max_life",
        "size", "size_end",
        "color", "color_end",
        "gravity",
        "angle", "spin",       # для намальованих зірочок / іскор
        "shape",               # "circle" | "spark" | "square" | "line"
        "alpha_start", "alpha_end",
        "trail",               # bool — чи залишати слід
    )

    def __init__(
        self,
        x: float, y: float,
        vx: float, vy: float,
        life: float,
        size: float, size_end: float,
        color: Tuple[int, int, int],
        color_end: Tuple[int, int, int] = None,
        gravity: float = 400.0,
        shape: str = "circle",
        alpha_start: int = 255,
        alpha_end: int = 0,
        trail: bool = False,
    ):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.size = size
        self.size_end = size_end
        self.color = color
        self.color_end = color_end if color_end is not None else color
        self.gravity = gravity
        self.angle = random.uniform(0, math.tau)
        self.spin = random.uniform(-8.0, 8.0)
        self.shape = shape
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.trail = trail

    @property
    def t(self) -> float:
        """Normalized life progress 0→1."""
        return 1.0 - self.life / self.max_life

    def update(self, dt: float) -> bool:
        """Оновлює частинку. Повертає False якщо мертва."""
        self.life -= dt
        if self.life <= 0:
            return False
        self.vy += self.gravity * dt
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        # Тертя повітря
        self.vx *= 0.97
        self.vy *= 0.97
        self.angle += self.spin * dt
        return True

    def _lerp_color(self) -> Tuple[int, int, int]:
        t = self.t
        r = int(self.color[0] + (self.color_end[0] - self.color[0]) * t)
        g = int(self.color[1] + (self.color_end[1] - self.color[1]) * t)
        b = int(self.color[2] + (self.color_end[2] - self.color[2]) * t)
        return (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
        )

    def draw(self, surface: pygame.Surface, ox: float = 0, oy: float = 0):
        """Малює частинку."""
        t    = self.t
        sz   = max(0.5, self.size + (self.size_end - self.size) * t)
        col  = self._lerp_color()
        alp  = int(self.alpha_start + (self.alpha_end - self.alpha_start) * t)
        alp  = max(0, min(255, alp))
        px   = int(self.x + ox)
        py   = int(self.y + oy)
        isz  = max(1, int(sz))

        if self.shape == "circle":
            tmp = pygame.Surface((isz * 2, isz * 2), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (*col, alp), (isz, isz), isz)
            surface.blit(tmp, (px - isz, py - isz))

        elif self.shape == "spark":
            # Тонкий витягнутий ромб — виглядає як іскра
            length = max(2, int(sz * 3))
            thick  = max(1, int(sz * 0.5))
            cos_a  = math.cos(self.angle)
            sin_a  = math.sin(self.angle)
            pts = [
                (px + cos_a * length, py + sin_a * length),
                (px - sin_a * thick,  py + cos_a * thick),
                (px - cos_a * length, py - sin_a * length),
                (px + sin_a * thick,  py - cos_a * thick),
            ]
            tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(tmp, (*col, alp), pts)
            surface.blit(tmp, (0, 0))

        elif self.shape == "square":
            tmp = pygame.Surface((isz * 2, isz * 2), pygame.SRCALPHA)
            pygame.draw.rect(tmp, (*col, alp), (0, 0, isz * 2, isz * 2))
            surface.blit(tmp, (px - isz, py - isz))

        elif self.shape == "line":
            length = max(2, int(sz * 4))
            cos_a  = math.cos(self.angle)
            sin_a  = math.sin(self.angle)
            x2 = px + int(cos_a * length)
            y2 = py + int(sin_a * length)
            # alpha через Surface
            tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.line(tmp, (*col, alp), (px, py), (x2, y2), max(1, int(sz)))
            surface.blit(tmp, (0, 0))


# ══════════════════════════════════════════
#  ЕМІТЕР (контейнер частинок)
# ══════════════════════════════════════════

class ParticleEmitter:
    """Зберігає і оновлює всі частинки сцени."""

    # Ліміт — щоб не завалити CPU
    MAX_PARTICLES = 400

    def __init__(self):
        self.particles: List[Particle] = []

    def add(self, p: Particle):
        if len(self.particles) < self.MAX_PARTICLES:
            self.particles.append(p)

    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[float, float] = (0, 0)):
        ox, oy = camera_offset
        for p in self.particles:
            p.draw(surface, ox, oy)

    def clear(self):
        self.particles.clear()


# ══════════════════════════════════════════
#  ФАБРИКА БОЙОВИХ ЕФЕКТІВ
# ══════════════════════════════════════════

class HitEffects:
    """
    Статичні методи-фабрики для різних типів ефектів.
    Кожен метод генерує пачку частинок в емітер.
    """

    # ── Звичайний удар ────────────────────────────────────────
    @staticmethod
    def spawn_hit(
        emitter: ParticleEmitter,
        x: float, y: float,
        damage: int = 15,
        facing_right: bool = True,
    ):
        """Іскри + пил при звичайному ударі."""
        count   = min(6 + damage // 5, 18)
        dir_x   = 1.0 if facing_right else -1.0

        for _ in range(count):
            angle  = random.uniform(-0.9, 0.9) + (0 if facing_right else math.pi)
            speed  = random.uniform(120, 340)
            vx     = math.cos(angle) * speed * dir_x
            vy     = math.sin(angle) * speed - random.uniform(60, 180)
            size   = random.uniform(2.5, 5.0)

            # Іскра: помаранчево-жовта → червона
            col1   = (255, random.randint(160, 240), random.randint(0, 60))
            col2   = (random.randint(180, 255), 40, 0)
            shape  = random.choice(["spark", "spark", "circle"])

            emitter.add(Particle(
                x + random.uniform(-12, 12),
                y + random.uniform(-10, 10),
                vx, vy,
                life    = random.uniform(0.18, 0.55),
                size    = size,
                size_end= 0.0,
                color   = col1,
                color_end=col2,
                gravity = 500,
                shape   = shape,
            ))

        # Пил (3-5 штук)
        for _ in range(random.randint(3, 5)):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(40, 100)
            gray  = random.randint(120, 200)
            emitter.add(Particle(
                x + random.uniform(-8, 8),
                y + random.uniform(-5, 5),
                math.cos(angle) * speed,
                math.sin(angle) * speed - 40,
                life    = random.uniform(0.3, 0.7),
                size    = random.uniform(4, 9),
                size_end= 0.0,
                color   = (gray, gray, gray),
                gravity = 80,
                shape   = "circle",
                alpha_start=160,
                alpha_end  = 0,
            ))

    # ── Критичний удар ────────────────────────────────────────
    @staticmethod
    def spawn_crit(
        emitter: ParticleEmitter,
        x: float, y: float,
        damage: int = 30,
    ):
        """Спалах + багато іскор при критичному ударі."""

        # Більше іскор
        HitEffects.spawn_hit(emitter, x, y, damage * 2)

        # Жовтий спалах — велике коло що розширюється і зникає
        for r in [30, 22, 14]:
            emitter.add(Particle(
                x, y,
                vx=0, vy=0,
                life    = 0.22,
                size    = r,
                size_end= r * 2.5,
                color   = (255, 240, 80),
                color_end=(255, 120, 0),
                gravity = 0,
                shape   = "circle",
                alpha_start=200,
                alpha_end  = 0,
            ))

        # Білі іскри вибухом
        for _ in range(12):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(200, 500)
            emitter.add(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                life    = random.uniform(0.3, 0.65),
                size    = random.uniform(3, 6),
                size_end= 0.0,
                color   = (255, 255, 200),
                color_end=(255, 180, 0),
                gravity = 350,
                shape   = "spark",
            ))

    # ── Блок ────────────────────────────────────────────────
    @staticmethod
    def spawn_block(emitter: ParticleEmitter, x: float, y: float):
        """Синьо-білі частинки при блокуванні."""
        for _ in range(8):
            angle = random.uniform(math.pi * 0.7, math.pi * 1.3)
            speed = random.uniform(80, 200)
            emitter.add(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed - 60,
                life    = random.uniform(0.25, 0.5),
                size    = random.uniform(3, 7),
                size_end= 0.0,
                color   = (180, 210, 255),
                color_end=(80, 120, 220),
                gravity = 300,
                shape   = random.choice(["circle", "spark"]),
                alpha_start=220,
                alpha_end=0,
            ))

    # ── Ухилення ────────────────────────────────────────────
    @staticmethod
    def spawn_dodge(emitter: ParticleEmitter, x: float, y: float, direction: int = 1):
        """Синій слід при перекаті."""
        for i in range(10):
            t_offset = i * 0.015
            emitter.add(Particle(
                x - direction * i * 12 + random.uniform(-6, 6),
                y + random.uniform(-15, 15),
                vx   = -direction * random.uniform(20, 60),
                vy   = random.uniform(-30, 30),
                life = random.uniform(0.2, 0.45),
                size = random.uniform(5, 12),
                size_end=0.0,
                color=(60, 140, 255),
                color_end=(20, 40, 120),
                gravity=0,
                shape="circle",
                alpha_start=180,
                alpha_end=0,
            ))

    # ── Кров при важкому ударі ─────────────────────────────
    @staticmethod
    def spawn_blood(emitter: ParticleEmitter, x: float, y: float, facing_right: bool = True):
        """Краплі крові при тяжкому ударі / великому damage."""
        dir_x = 1.0 if facing_right else -1.0
        for _ in range(random.randint(5, 10)):
            angle = random.uniform(-0.7, 0.7) + (0 if facing_right else math.pi)
            speed = random.uniform(80, 260)
            r_val = random.randint(160, 210)
            emitter.add(Particle(
                x + random.uniform(-8, 8),
                y + random.uniform(-20, 10),
                math.cos(angle) * speed * dir_x,
                math.sin(angle) * speed - random.uniform(50, 150),
                life    = random.uniform(0.35, 0.8),
                size    = random.uniform(2, 5),
                size_end= 0.0,
                color   = (r_val, 10, 10),
                color_end=(80, 0, 0),
                gravity = 600,
                shape   = random.choice(["circle", "square"]),
                alpha_start=230,
                alpha_end=0,
            ))

    # ── Rage вспалах (ворог увійшов у rage) ───────────────
    @staticmethod
    def spawn_rage_burst(emitter: ParticleEmitter, x: float, y: float):
        """Вибух червоних частинок коли ворог переходить у rage."""
        for _ in range(25):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(100, 400)
            emitter.add(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                life    = random.uniform(0.4, 1.0),
                size    = random.uniform(4, 10),
                size_end= 0.0,
                color   = (255, random.randint(30, 80), 0),
                color_end=(120, 0, 0),
                gravity = 200,
                shape   = random.choice(["spark", "circle"]),
                alpha_start=255,
                alpha_end=0,
            ))

    # ── Parry контратака ──────────────────────────────────
    @staticmethod
    def spawn_parry(emitter: ParticleEmitter, x: float, y: float):
        """Зелено-білий спалах при успішному парируванні."""
        for _ in range(15):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(150, 380)
            emitter.add(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                life    = random.uniform(0.3, 0.6),
                size    = random.uniform(3, 7),
                size_end= 0.0,
                color   = (180, 255, 180),
                color_end=(0, 200, 80),
                gravity = 250,
                shape   = "spark",
                alpha_start=240,
                alpha_end=0,
            ))
        # Велике кільце
        emitter.add(Particle(
            x, y, 0, 0,
            life=0.3,
            size=10, size_end=60,
            color=(200, 255, 200),
            color_end=(0, 180, 80),
            gravity=0, shape="circle",
            alpha_start=180, alpha_end=0,
        ))