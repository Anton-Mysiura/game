"""
╔══════════════════════════════════════════════════════════════╗
║  HOT-RELOAD                                                  ║
║  Натисни F5 в грі — зміни в config/ застосуються відразу   ║
║  без перезапуску!                                            ║
╚══════════════════════════════════════════════════════════════╝

Що перезавантажується:
  ✅ config/enemies.py   — нові вороги, лут, спавн-таблиці
  ✅ config/loot.py      — матеріали, предмети, кресленники
  ✅ config/heroes.py    — герої та навички
  ✅ config/theme.py     — кольори, розміри
  ✅ config/ui.py        — стилі кнопок, фони, панелі
  ✅ config/quests.py    — квести і щоденні завдання
  ✅ assets/textures/    — нові PNG файли підхоплюються

Що НЕ перезавантажується (потребує перезапуску):
  ❌ Збережена гра (saves/)
  ❌ Поточний прогрес гравця в сесії
  ❌ Основний код гри (game/, scenes/, ui/)
"""
from __future__ import annotations
import importlib
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.core import Game


# Модулі що перезавантажуються
_RELOAD_MODULES = [
    "config.theme",
    "config.ui",
    "config.enemies",
    "config.loot",
    "config.heroes",
    "config.quests",
    "config.loader",
    "config.quest_loader",
]

# Відстеження часу змін файлів
_file_mtimes: dict[str, float] = {}


def _get_config_files() -> list[Path]:
    """Повертає всі файли в config/ та assets/textures/."""
    config_dir = Path(__file__).parent
    texture_dir = config_dir.parent / "assets" / "textures"
    files = list(config_dir.glob("*.py"))
    if texture_dir.exists():
        files += list(texture_dir.rglob("*.png"))
    return files


def check_changed() -> bool:
    """
    Перевіряє чи змінились файли конфігів з останньої перевірки.
    Викликати в game loop якщо хочеш автоматичний reload.
    """
    changed = False
    for path in _get_config_files():
        try:
            mtime = path.stat().st_mtime
            key = str(path)
            if key in _file_mtimes and _file_mtimes[key] != mtime:
                changed = True
            _file_mtimes[key] = mtime
        except OSError:
            pass
    return changed


def reload_all(game: "Game" = None) -> dict:
    """
    Перезавантажує всі конфіги і повертає результат.

    Використання в грі:
        from config.hot_reload import reload_all
        result = reload_all(game)

    Або прив'яжи до клавіші F5 у game/core.py.
    """
    t0 = time.time()
    errors = []
    reloaded = []

    # Перезавантажуємо Python модулі
    for module_name in _RELOAD_MODULES:
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
                reloaded.append(module_name)
            except Exception as e:
                errors.append(f"{module_name}: {e}")

    # Очищаємо кеш loader
    try:
        from config import loader
        loader._cache.clear()
    except Exception:
        pass

    # Очищаємо кеш текстур (підхопить нові PNG)
    try:
        from ui.assets import assets
        assets.reload()
    except Exception:
        pass

    # Оновлюємо квести у грі якщо передано game
    if game is not None:
        _apply_to_game(game, errors)

    elapsed = time.time() - t0
    return {
        "ok":       len(errors) == 0,
        "reloaded": reloaded,
        "errors":   errors,
        "time_ms":  round(elapsed * 1000),
    }


def _apply_to_game(game: "Game", errors: list):
    """Застосовує перезавантажені дані до запущеної гри."""

    # Оновлюємо квести старости
    try:
        from config.quest_loader import build_quests
        from game.quests import QUESTS
        new_quests = build_quests()
        QUESTS.clear()
        QUESTS.update(new_quests)
    except Exception as e:
        errors.append(f"quests: {e}")

    # Оновлюємо пул щоденних завдань
    try:
        from config.quest_loader import build_daily_pool
        from game import daily_quests as dq_module
        dq_module._POOL = build_daily_pool()
    except Exception as e:
        errors.append(f"daily_quests: {e}")

    # Оновлюємо таблиці спавну ворогів
    try:
        from config.loader import load_all
        _, items, _, _, spawn_tables = load_all()
        from game import spawn_table as st_module
        st_module.SPAWN_TABLES.clear()
        st_module.SPAWN_TABLES.update(spawn_tables)
    except Exception as e:
        errors.append(f"spawn_tables: {e}")


# ══════════════════════════════════════════
#  ІНТЕГРАЦІЯ З game/core.py
# ══════════════════════════════════════════
#
# Додай у game/core.py в метод handle_event():
#
#   elif event.key == pygame.K_F5:
#       from config.hot_reload import reload_all, show_result
#       result = reload_all(self)
#       show_result(result, self)
#
# Або просто виклич setup_hotkey(game) один раз при старті.


def setup_hotkey(game: "Game"):
    """
    Реєструє F5 як клавішу hot-reload.
    Виклич один раз у game/__init__ або core.py після ініціалізації.

    Приклад у core.py:
        from config.hot_reload import setup_hotkey
        setup_hotkey(self)
    """
    # Зберігаємо посилання на гру для подальшого використання
    _state["game"] = game


def handle_keydown(key: int, game: "Game" = None) -> bool:
    """
    Виклич у handle_event() для перехоплення F5.
    Повертає True якщо клавіша була оброблена.

    Приклад:
        import pygame
        from config.hot_reload import handle_keydown
        if event.type == pygame.KEYDOWN:
            if handle_keydown(event.key, self):
                return
    """
    import pygame
    if key != pygame.K_F5:
        return False

    g = game or _state.get("game")
    result = reload_all(g)
    show_result(result, g)
    return True


def show_result(result: dict, game: "Game" = None):
    """Показує результат hot-reload у консолі і (якщо є нотифікації) в грі."""
    if result["ok"]:
        msg = f"🔄 Hot-reload OK ({result['time_ms']}ms) — {len(result['reloaded'])} модулів"
        print(msg)
    else:
        print(f"⚠ Hot-reload з помилками ({result['time_ms']}ms):")
        for err in result["errors"]:
            print(f"   ❌ {err}")

    # Показуємо нотифікацію в грі якщо є
    if game is not None:
        try:
            from ui.notifications import notifications
            if result["ok"]:
                notifications.add(
                    f"🔄 Конфіги перезавантажено ({result['time_ms']}ms)",
                    color=(80, 200, 120), duration=2.5
                )
            else:
                notifications.add(
                    f"⚠ Помилка reload: {result['errors'][0]}",
                    color=(220, 80, 80), duration=4.0
                )
        except Exception:
            pass


_state: dict = {}
