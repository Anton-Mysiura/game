#!/usr/bin/env python3
"""
Темне Королівство — Графічна версія
Точка входу в гру.
"""
import logging
import logging.handlers
import sys
from pathlib import Path

# ── Налаштування логування ────────────────────────────────────────
LOG_DIR = Path.home() / ".dark_kingdom_saves"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "game.log"

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        # Лог у файл — зберігає останні 5 запусків (rotating)
        logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=1024 * 512,   # 512 KB
            backupCount=4,
            encoding="utf-8",
        ),
        # Лог в консоль тільки WARNING+
        logging.StreamHandler(sys.stdout),
    ],
)

log = logging.getLogger(__name__)
log.info("=== Запуск гри ===")


def main():
    # ── Перевірка конфігів перед запуском ────────────────────────
    try:
        from config.validator import validate_and_warn
        has_errors = validate_and_warn()
        if has_errors:
            print("\n⚠  Знайдено помилки в конфігах (див. вище).")
            print("   Гра запуститься, але деякі речі можуть не працювати.\n")
    except Exception as ve:
        print(f"[validator] Не вдалось запустити валідацію: {ve}")

    try:
        from game.core import Game
        game = Game()
        game.run()
    except Exception as e:
        log.exception("Критична помилка: %s", e)
        raise


if __name__ == "__main__":
    main()