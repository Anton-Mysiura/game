"""
Система анімацій для персонажів.
"""

import logging

log = logging.getLogger(__name__)

import pygame
from typing import List, Optional
from pathlib import Path


class Animation:
    """Одна анімація (наприклад, idle, attack, block)."""

    def __init__(self, name: str, frames: List[pygame.Surface],
                 frame_duration: float = 0.1, loop: bool = True):
        self.name = name
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        self.current_frame = 0
        self.time_accumulated = 0.0
        self.finished = False
        # Кешовані дзеркальні кадри — створюються один раз при першому зверненні
        self._flipped_frames: List[pygame.Surface] | None = None

    def get_flipped_frame(self) -> pygame.Surface:
        """Повертає поточний кадр, відзеркалений по горизонталі (з кешу)."""
        if self._flipped_frames is None:
            self._flipped_frames = [
                pygame.transform.flip(f, True, False) for f in self.frames
            ]
        return self._flipped_frames[self.current_frame]

    def update(self, dt: float):
        """Оновлює анімацію."""
        self.time_accumulated += dt

        if self.time_accumulated >= self.frame_duration:
            self.time_accumulated = 0
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True

    def reset(self):
        """Скидає анімацію на початок."""
        self.current_frame = 0
        self.time_accumulated = 0.0
        self.finished = False

    def get_current_frame(self) -> pygame.Surface:
        """Повертає поточний кадр."""
        return self.frames[self.current_frame]


class AnimationController:
    """Контролер анімацій персонажа."""

    IDLE_VARIANT_MIN = 5.0   # мін. секунд до наступного idle variant
    IDLE_VARIANT_MAX = 11.0  # макс. секунд (8±3)

    def __init__(self):
        self.animations = {}
        self.current_animation: Optional[Animation] = None
        self.current_name = ""

        # Idle variant таймер
        self._idle_variant_timer = self._next_idle_interval()
        self._playing_idle_variant = False

    def _next_idle_interval(self) -> float:
        """Повертає випадковий інтервал до наступного idle variant."""
        import random
        return random.uniform(self.IDLE_VARIANT_MIN, self.IDLE_VARIANT_MAX)

    def _idle_variants(self) -> list:
        """Повертає список доступних idle variant назв."""
        return [name for name in self.animations
                if name.startswith("idle") and name != "idle"]

    def add_animation(self, name: str, animation: Animation):
        """Додає анімацію."""
        self.animations[name] = animation
        if not self.current_animation:
            self.current_animation = animation
            self.current_name = name

    def play(self, name: str, force_restart: bool = False):
        """Грає анімацію."""
        if name not in self.animations:
            return

        if self.current_name == name and not force_restart:
            return

        # Якщо переривається idle variant — скидаємо прапор і таймер
        if self._playing_idle_variant and name != self.current_name:
            self._playing_idle_variant = False
            self._idle_variant_timer = self._next_idle_interval()

        self.current_animation = self.animations[name]
        self.current_name = name
        self.current_animation.reset()

    def update(self, dt: float):
        """Оновлює поточну анімацію та керує idle variants."""
        if not self.current_animation:
            return

        self.current_animation.update(dt)

        # Якщо зараз грає idle variant і він закінчився — повертаємось до idle
        if self._playing_idle_variant and self.current_animation.finished:
            self._playing_idle_variant = False  # скидаємо ДО play() щоб play() не переписав таймер
            self._idle_variant_timer = self._next_idle_interval()
            # Напряму перемикаємо без play() щоб уникнути побічних ефектів
            self.current_animation = self.animations["idle"]
            self.current_name = "idle"
            self.current_animation.reset()
            return

        # Рахуємо час до наступного idle variant
        if self.current_name == "idle" and not self._playing_idle_variant:
            self._idle_variant_timer -= dt
            if self._idle_variant_timer <= 0:
                variants = self._idle_variants()
                if variants:
                    import random
                    variant = random.choice(variants)
                    self._playing_idle_variant = True
                    self.current_animation = self.animations[variant]
                    self.current_name = variant
                    self.current_animation.reset()
                else:
                    self._idle_variant_timer = self._next_idle_interval()

    def get_current_frame(self) -> pygame.Surface:
        """Повертає поточний кадр."""
        if not self.current_animation:
            log.warning("AnimationController: немає активної анімації!")
            return None
        return self.current_animation.get_current_frame()

    def get_flipped_frame(self) -> pygame.Surface:
        """Повертає поточний кадр, відзеркалений (з кешу)."""
        if not self.current_animation:
            return None
        return self.current_animation.get_flipped_frame()

    def is_finished(self) -> bool:
        """Перевіряє чи анімація завершилась."""
        return self.current_animation.finished if self.current_animation else True


class AnimationLoader:
    """Завантажувач анімацій."""

    @staticmethod
    def count_frames(path: Path, frame_width: int) -> int:
        """Рахує кількість кадрів у spritesheet за шириною кадру."""
        try:
            import pygame
            img = pygame.image.load(str(path))
            return max(1, img.get_width() // frame_width)
        except Exception:
            return 1

    @staticmethod
    def load_spritesheet(path: Path, frame_width: int, frame_height: int,
                         frame_count: int, scale: float = 1.0) -> List[pygame.Surface]:
        """Завантажує анімацію з spritesheet."""
        if not path.exists():
            log.warning("Spritesheet не знайдено: %s", path)
            return AnimationLoader._create_placeholder_frames(frame_width, frame_height, frame_count, scale)

        try:
            spritesheet = pygame.image.load(str(path)).convert_alpha()
            frames = []

            for i in range(frame_count):
                x = i * frame_width
                frame_rect = pygame.Rect(x, 0, frame_width, frame_height)
                frame = spritesheet.subsurface(frame_rect)

                if scale != 1.0:
                    new_width = int(frame_width * scale)
                    new_height = int(frame_height * scale)
                    frame = pygame.transform.scale(frame, (new_width, new_height))

                frames.append(frame)

            log.info("Завантажено %d кадрів з %s", frame_count, path.name)
            return frames

        except Exception as e:
            log.error("Помилка завантаження анімації: %s", e)
            return AnimationLoader._create_placeholder_frames(frame_width, frame_height, frame_count, scale)

    @staticmethod
    def _create_placeholder_frames(width: int, height: int, count: int, scale: float = 1.0) -> List[pygame.Surface]:
        """Створює плейсхолдер кадри."""
        frames = []
        w = int(width * scale)
        h = int(height * scale)

        for i in range(count):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)

            # Безпечний колір (0-255)
            r = min(255, 100 + i * 20)
            g = min(255, 150 + i * 10)
            b = min(255, 200)
            color = (r, g, b)

            surf.fill(color)
            pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 3)

            # Номер кадру
            font = pygame.font.Font(None, 32)
            text = font.render(str(i + 1), True, (255, 255, 255))
            text_rect = text.get_rect(center=(w // 2, h // 2))
            surf.blit(text, text_rect)

            frames.append(surf)

        log.warning("Створено %d плейсхолдер кадрів (%dx%d)", count, w, h)
        return frames