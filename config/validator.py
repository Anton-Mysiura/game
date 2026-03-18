"""
╔══════════════════════════════════════════════════════════════╗
║  ВАЛІДАТОР КОНФІГІВ                                          ║
║  Запускається автоматично при старті гри                    ║
║  Знаходить помилки ДО того як гра крашнеться                ║
╚══════════════════════════════════════════════════════════════╝

Використання — додай у main.py перед game.run():
    from config.validator import validate_all, print_report
    report = validate_all()
    print_report(report)
    if report["errors"]:
        sys.exit(1)   # зупинити якщо є критичні помилки
"""
from __future__ import annotations
from pathlib import Path
from typing import Any


class ValidationReport:
    def __init__(self):
        self.errors:   list[str] = []
        self.warnings: list[str] = []
        self.ok:       list[str] = []

    def error(self, msg: str):
        self.errors.append(f"❌ {msg}")

    def warn(self, msg: str):
        self.warnings.append(f"⚠  {msg}")

    def good(self, msg: str):
        self.ok.append(f"✅ {msg}")

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def summary(self) -> str:
        return (f"{len(self.errors)} помилок, "
                f"{len(self.warnings)} попереджень, "
                f"{len(self.ok)} ОК")


def validate_all() -> ValidationReport:
    """Запускає всі перевірки і повертає звіт."""
    r = ValidationReport()
    _check_loot(r)
    _check_enemies(r)
    _check_heroes(r)
    _check_quests(r)
    _check_shop(r)
    _check_perks(r)
    _check_locations(r)
    _check_ui(r)
    _check_assets(r)
    return r


# ══════════════════════════════════════════
#  ПЕРЕВІРКИ
# ══════════════════════════════════════════

def _check_loot(r: ValidationReport):
    try:
        from config.loot import MATERIALS_DATA, ITEMS_DATA, BLUEPRINTS_DATA
    except Exception as e:
        r.error(f"config/loot.py не завантажується: {e}"); return

    r.good(f"Матеріали: {len(MATERIALS_DATA)} шт.")
    r.good(f"Предмети: {len(ITEMS_DATA)} шт.")

    # Перевіряємо кресленики
    bp_errors = 0
    for bp_id, d in BLUEPRINTS_DATA.items():
        # Рецепт посилається на існуючі матеріали
        for mat_id in d.get("recipe", {}):
            if mat_id not in MATERIALS_DATA:
                r.error(f"Blueprint '{bp_id}': матеріал '{mat_id}' не існує в MATERIALS_DATA")
                bp_errors += 1
        # bonus_materials теж мають існувати
        for mat_id in d.get("bonus_materials", []):
            if mat_id not in MATERIALS_DATA:
                r.warn(f"Blueprint '{bp_id}': bonus_material '{mat_id}' не існує")
        # result tuple має правильну довжину
        res = d.get("result", ())
        if len(res) != 5:
            r.error(f"Blueprint '{bp_id}': result має бути (id, name, value, icon, desc), отримано {len(res)} полів")
            bp_errors += 1
        # unlock_cost > 0
        if d.get("unlock_cost", 0) <= 0:
            r.warn(f"Blueprint '{bp_id}': unlock_cost = {d.get('unlock_cost')} (має бути > 0)")

    if bp_errors == 0:
        r.good(f"Кресленики: {len(BLUEPRINTS_DATA)} шт., всі рецепти ОК")


def _check_enemies(r: ValidationReport):
    try:
        from config.enemies import ENEMY_DEFINITIONS, SPAWN_TABLES
        from config.loot import ITEMS_DATA, MATERIALS_DATA
    except Exception as e:
        r.error(f"config/enemies.py не завантажується: {e}"); return

    enemy_errors = 0
    for key, d in ENEMY_DEFINITIONS.items():
        # Обов'язкові поля
        for field in ("name", "hp", "attack", "defense", "xp", "gold", "sprite"):
            if field not in d:
                r.error(f"Ворог '{key}': відсутнє поле '{field}'")
                enemy_errors += 1
        # Від'ємні значення
        for stat in ("hp", "attack", "defense", "xp", "gold"):
            if d.get(stat, 1) <= 0:
                r.error(f"Ворог '{key}': {stat} = {d.get(stat)} (має бути > 0)")
                enemy_errors += 1
        # loot_items посилаються на існуючі предмети
        for iid in d.get("loot_items", []):
            if iid not in ITEMS_DATA:
                r.warn(f"Ворог '{key}': loot_item '{iid}' не існує в ITEMS_DATA")
        # loot_materials посилаються на існуючі матеріали
        for mid in d.get("loot_materials", {}):
            if mid not in MATERIALS_DATA:
                r.warn(f"Ворог '{key}': loot_material '{mid}' не існує в MATERIALS_DATA")

    if enemy_errors == 0:
        r.good(f"Вороги: {len(ENEMY_DEFINITIONS)} шт., всі поля ОК")

    # Таблиці спавну посилаються на існуючих ворогів
    spawn_errors = 0
    for location, entries in SPAWN_TABLES.items():
        for (enemy_key, weight, min_level) in entries:
            if enemy_key not in ENEMY_DEFINITIONS:
                r.error(f"SPAWN_TABLES['{location}']: ворог '{enemy_key}' не існує в ENEMY_DEFINITIONS")
                spawn_errors += 1
            if weight <= 0:
                r.warn(f"SPAWN_TABLES['{location}']['{enemy_key}']: weight = {weight} (має бути > 0)")

    if spawn_errors == 0:
        r.good(f"Таблиці спавну: {len(SPAWN_TABLES)} локацій, всі посилання ОК")


def _check_heroes(r: ValidationReport):
    try:
        from config.heroes import HEROES_DATA
    except Exception as e:
        r.error(f"config/heroes.py не завантажується: {e}"); return

    from ui.constants import ANIMATIONS_DIR
    anim_errors = 0
    hero_errors = 0

    valid_rarities = {"common", "rare", "epic", "legendary"}

    for hero_id, d in HEROES_DATA.items():
        # Обов'язкові поля
        for field in ("name", "group", "rarity", "icon", "lore", "anim_folder"):
            if field not in d:
                r.error(f"Герой '{hero_id}': відсутнє поле '{field}'")
                hero_errors += 1

        # Рідкість
        if d.get("rarity") not in valid_rarities:
            r.error(f"Герой '{hero_id}': невірна рідкість '{d.get('rarity')}' (допустимі: {valid_rarities})")
            hero_errors += 1

        # Папка анімацій існує
        anim_path = ANIMATIONS_DIR / d.get("anim_folder", "")
        if not anim_path.exists():
            r.warn(f"Герой '{hero_id}': папка анімацій не знайдена: {anim_path}")
            anim_errors += 1

        # Базові стати не від'ємні
        base = d.get("base", {})
        for stat in ("hp", "attack", "defense"):
            if base.get(stat, 0) < 0:
                r.warn(f"Герой '{hero_id}': base.{stat} = {base.get(stat)} (від'ємне значення)")

    if hero_errors == 0:
        r.good(f"Герої: {len(HEROES_DATA)} шт., всі поля ОК")
    if anim_errors == 0:
        r.good("Анімації героїв: всі папки знайдено")
    else:
        r.warn(f"Анімації: {anim_errors} папок не знайдено (герої будуть без анімацій)")


def _check_quests(r: ValidationReport):
    try:
        from config.quests import QUESTS_DATA, DAILY_QUESTS_POOL
    except Exception as e:
        r.error(f"config/quests.py не завантажується: {e}"); return

    ids = {d["id"] for d in QUESTS_DATA}
    quest_errors = 0

    for d in QUESTS_DATA:
        # Обов'язкові поля
        for field in ("id", "title", "icon", "objective"):
            if field not in d:
                r.error(f"Квест '{d.get('id','?')}': відсутнє поле '{field}'")
                quest_errors += 1

        # unlocks посилається на існуючий квест
        unlocks = d.get("unlocks", "")
        if unlocks and unlocks not in ids:
            r.warn(f"Квест '{d['id']}': unlocks='{unlocks}' не існує в QUESTS_DATA")

        # unlock_when: quest:X — X має існувати
        uw = d.get("unlock_when", "always")
        if uw.startswith("quest:"):
            ref = uw[6:]
            if ref not in ids:
                r.warn(f"Квест '{d['id']}': unlock_when='quest:{ref}' — квест '{ref}' не існує")

    if quest_errors == 0:
        r.good(f"Квести: {len(QUESTS_DATA)} шт., щоденних: {len(DAILY_QUESTS_POOL)} шт.")


def _check_shop(r: ValidationReport):
    try:
        from config.shop import SHOP_ITEMS, SHOP_BLUEPRINTS
        from config.loot import ITEMS_DATA, BLUEPRINTS_DATA
    except Exception as e:
        r.error(f"config/shop.py не завантажується: {e}"); return

    shop_errors = 0
    for (item_id, price) in SHOP_ITEMS:
        if item_id not in ITEMS_DATA:
            r.error(f"Крамниця: предмет '{item_id}' не існує в ITEMS_DATA")
            shop_errors += 1
        if price <= 0:
            r.warn(f"Крамниця: ціна предмету '{item_id}' = {price}")

    for (bp_id, price) in SHOP_BLUEPRINTS:
        if bp_id not in BLUEPRINTS_DATA:
            r.error(f"Крамниця: кресленик '{bp_id}' не існує в BLUEPRINTS_DATA")
            shop_errors += 1
        if price <= 0:
            r.warn(f"Крамниця: ціна кресленика '{bp_id}' = {price}")

    if shop_errors == 0:
        r.good(f"Крамниця: {len(SHOP_ITEMS)} предметів, {len(SHOP_BLUEPRINTS)} кресленників, всі посилання ОК")


def _check_perks(r: ValidationReport):
    try:
        from config.perks import PERKS_DATA, SKILL_NODES_DATA, SKILL_BRANCHES
    except Exception as e:
        r.error(f"config/perks.py не завантажується: {e}"); return

    valid_rarities = {"common","uncommon","rare","epic","mythic","legendary","god"}
    perk_errors = 0
    for pid, d in PERKS_DATA.items():
        if d.get("rarity") not in valid_rarities:
            r.error(f"Перк '{pid}': невірна рідкість '{d.get('rarity')}'")
            perk_errors += 1
        if not d.get("effect"):
            r.warn(f"Перк '{pid}': порожній effect")

    # Скіл-три: requires посилається на існуючий вузол
    node_ids = set(SKILL_NODES_DATA.keys())
    skill_errors = 0
    for nid, d in SKILL_NODES_DATA.items():
        req = d.get("requires")
        if req and req not in node_ids:
            r.error(f"Скіл-три вузол '{nid}': requires='{req}' не існує")
            skill_errors += 1
        if d.get("tier", 0) not in range(1, 6):
            r.warn(f"Скіл-три вузол '{nid}': tier={d.get('tier')} не в діапазоні 1-5")

    if perk_errors == 0:
        r.good(f"Перки: {len(PERKS_DATA)} шт.")
    if skill_errors == 0:
        r.good(f"Скіл-три: {len(SKILL_NODES_DATA)} вузлів, {len(SKILL_BRANCHES)} гілок")


def _check_locations(r: ValidationReport):
    try:
        from config.locations import LOCATIONS, EVENTS, WORLD_MAP
        from config.enemies import SPAWN_TABLES
    except Exception as e:
        r.error(f"config/locations.py не завантажується: {e}"); return

    loc_errors = 0
    for loc_id, d in LOCATIONS.items():
        # Обов'язкові поля
        for field in ("name", "icon", "description"):
            if field not in d:
                r.error(f"Локація '{loc_id}': відсутнє поле '{field}'")
                loc_errors += 1

        # Бойові локації мають таблицю спавну
        if d.get("min_level", 1) > 0 and loc_id not in ("village", "mine"):
            if loc_id not in SPAWN_TABLES:
                r.warn(f"Локація '{loc_id}': немає таблиці спавну в config/enemies.py → SPAWN_TABLES")

        # События посилаються на існуючі
        for ev_id in d.get("events", []):
            if ev_id not in EVENTS:
                r.warn(f"Локація '{loc_id}': подія '{ev_id}' не існує в EVENTS")

    if loc_errors == 0:
        r.good(f"Локації: {len(LOCATIONS)} шт., {len(EVENTS)} подій")


def _check_ui(r: ValidationReport):
    try:
        from config.ui import BUTTON_STYLES, PANEL_STYLES, SCENE_BACKGROUNDS
    except Exception as e:
        r.error(f"config/ui.py не завантажується: {e}"); return

    r.good(f"UI: {len(BUTTON_STYLES)} стилів кнопок, {len(PANEL_STYLES)} стилів панелей")

    # Перевіряємо що кольори — кортежі RGB
    for style_name, style in BUTTON_STYLES.items():
        for key in ("color_normal", "color_hover", "color_pressed"):
            color = style.get(key)
            if color and (not isinstance(color, tuple) or len(color) != 3):
                r.warn(f"UI Button '{style_name}': {key} має бути кортеж (R,G,B)")


def _check_assets(r: ValidationReport):
    """Перевіряє наявність критично важливих файлів."""
    from pathlib import Path

    try:
        from ui.constants import ASSETS_DIR, FONTS_DIR, SOUNDS_DIR
    except Exception as e:
        r.warn(f"Не вдалось перевірити assets: {e}"); return

    # Папки
    for name, path in [("assets/", ASSETS_DIR), ("assets/fonts/", FONTS_DIR),
                        ("assets/sounds/", SOUNDS_DIR)]:
        if path.exists():
            r.good(f"Папка {name} існує")
        else:
            r.warn(f"Папка {name} не знайдена — деякі функції можуть не працювати")

    # Звуки
    for sound in ("sword_swing.wav", "sword_hit.wav", "hurt.ogg", "jump.wav"):
        p = SOUNDS_DIR / sound
        if not p.exists():
            r.warn(f"Звук не знайдено: {sound}")


# ══════════════════════════════════════════
#  ФОРМАТУВАННЯ ЗВІТУ
# ══════════════════════════════════════════

def print_report(report: ValidationReport, verbose: bool = False):
    """Виводить звіт у консоль."""
    print("\n" + "═" * 55)
    print("  ПЕРЕВІРКА КОНФІГІВ")
    print("═" * 55)

    if report.errors:
        print(f"\n🔴 ПОМИЛКИ ({len(report.errors)}):")
        for e in report.errors:
            print(f"  {e}")

    if report.warnings:
        print(f"\n🟡 ПОПЕРЕДЖЕННЯ ({len(report.warnings)}):")
        for w in report.warnings:
            print(f"  {w}")

    if verbose and report.ok:
        print(f"\n🟢 ОК ({len(report.ok)}):")
        for o in report.ok:
            print(f"  {o}")

    print(f"\n{'═' * 55}")
    print(f"  {report.summary}")
    print("═" * 55 + "\n")


def validate_and_warn() -> bool:
    """
    Зручна функція для main.py.
    Запускає валідацію, виводить звіт, повертає True якщо є помилки.

    Використання в main.py:
        from config.validator import validate_and_warn
        if validate_and_warn():
            print("Виправ помилки перед запуском!")
            # можна або зупинитись або продовжити
    """
    report = validate_all()
    print_report(report, verbose=False)
    return report.has_errors
