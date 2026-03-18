# 🎮 Темне Королівство — Гайд розробника

> Весь контент гри зосереджений у папці **`config/`**.
> Не потрібно шукати щось по 30 файлах.

---
## ⚡ Швидка шпаргалка

| Що хочу зробити | Файл |
|----------------|------|
| Змінити колір фону | `config/theme.py` → `COLOR_BG` |
| Змінити розмір вікна | `config/theme.py` → `SCREEN_WIDTH/HEIGHT` |
| Додати нового ворога | `config/enemies.py` → `ENEMY_DEFINITIONS` |
| Змінити де спавниться ворог | `config/enemies.py` → `SPAWN_TABLES` |
| Додати матеріал | `config/loot.py` → `MATERIALS_DATA` |
| Додати предмет | `config/loot.py` → `ITEMS_DATA` |
| Додати кресленик | `config/loot.py` → `BLUEPRINTS_DATA` |
| Додати героя | `config/heroes.py` → `HEROES_DATA` |
| Змінити шанси рулетки | `config/heroes.py` → `RARITY_WEIGHTS` |
| Додати квест | `config/quests.py` → `QUESTS_DATA` |
| Додати щоденне завдання | `config/quests.py` → `DAILY_QUESTS_POOL` |
| Змінити товар у крамниці | `config/shop.py` |
| Додати перк | `config/perks.py` → `PERKS_DATA` |
| Змінити скіл-три | `config/perks.py` → `SKILL_NODES_DATA` |
| Додати локацію | `config/locations.py` → `LOCATIONS` |
| Поставити фон сцени | `config/ui.py` → `SCENE_BACKGROUNDS` |
| Змінити стиль кнопок | `config/ui.py` → `BUTTON_STYLES` |
| Підключити свій шрифт | `config/ui.py` → `FONTS` |
| Застосувати зміни без перезапуску | `Ctrl+F5` в грі |

---

## 🎨 Тема та дизайн (`config/theme.py`)

```python
# Розмір вікна
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

# Основні кольори
COLOR_BG    = (20, 15, 10)    # фон
COLOR_PANEL = (40, 30, 20)    # панелі
COLOR_GOLD  = (255, 215, 0)   # золото, рамки

# Кольори рідкостей
COLOR_LEGENDARY = (255, 165, 0)   # можна змінити на будь-який
COLOR_EPIC      = (200, 100, 255)

# Кнопки
COLOR_BTN_NORMAL = (80, 60, 40)
COLOR_BTN_HOVER  = (120, 90, 60)
```

---

## 🖼️ UI та текстури (`config/ui.py`)

### Фони сцен

1. Поклади `forest_bg.png` (1280×720) у `assets/textures/ui/bg/`
2. Пропиши в конфігу:

```python
SCENE_BACKGROUNDS = {
    "forest":    "forest_bg",
    "village":   "village_bg",
    "battle":    "battle_bg",
    # ключі: main_menu, village, forest, tower, ruins,
    #        mine, battle, inventory, workshop, shop...
}
```

### Стилі кнопок

```python
BUTTON_STYLES = {
    "default": {
        "normal":  None,           # None = малюємо кольором
        "hover":   None,           # або "my_btn_hover" = PNG файл
        "pressed": None,
        "color_normal":  (80, 60, 40),
        "color_hover":   (120, 90, 60),
        "border_color":  (200, 170, 100),
        "corner_radius": 4,
        "font_size":     20,
        "text_color":    (220, 200, 180),
    },
    # Готові стилі: "default", "small", "danger", "success", "gold"
    # Додавай свої скільки завгодно
    "my_style": {
        "color_normal": (80, 30, 100),
        "color_hover":  (120, 50, 160),
        "border_color": (200, 100, 255),
    }
}
```

Використання в коді:
```python
btn = Button(x, y, 200, 50, "Текст", callback, style="gold")
```

### Панелі

```python
PANEL_STYLES = {
    "dark":    {"color": (40, 30, 20), "border_color": (100, 82, 45)},
    "wood":    {"texture": "panel_wood"},   # PNG з assets/textures/ui/panel/
    "stone":   {"texture": "panel_stone"},
}
```

### Шрифт

```python
FONTS = {
    "main":  "MyFont.ttf",    # з assets/fonts/
    "title": "MyTitle.ttf",
}
```

### Курсор

```python
CURSOR = {
    "use_custom": True,
    "texture":    "cursor",   # cursor.png з assets/textures/ui/
    "hotspot":    (0, 0),
}
```

### Куди кидати файли

| Що | Папка |
|----|-------|
| Фони сцен | `assets/textures/ui/bg/` |
| Текстури кнопок | `assets/textures/ui/button/` |
| Текстури панелей | `assets/textures/ui/panel/` |
| UI іконки | `assets/textures/ui/icon/` |
| Слоти інвентарю | `assets/textures/ui/slot/` |
| Шрифти | `assets/fonts/` |

---

## 👹 Вороги (`config/enemies.py`)

```python
ENEMY_DEFINITIONS = {
    "my_enemy": {
        "name":     "Мій Ворог",
        "hp":       60,
        "attack":   15,
        "defense":  3,
        "xp":       35,
        "gold":     15,
        "level":    3,           # базовий рівень для скейлінгу
        "sprite":   "goblin",    # goblin / orc / dark_knight / dragon
        "behavior": "balanced",  # balanced / aggressive / defensive
                                 # berserker / skirmisher
        "loot_items":     ["small_potion"],
        "loot_materials": {"bone": (1, 3), "iron_ore": 2},
        "loot_chance":    {"bone": 0.7},   # 70% шанс
    },
}
```

Де спавниться:
```python
SPAWN_TABLES = {
    "forest": [
        ("my_enemy", 20, 2),  # (ключ, вага, мін_рівень_гравця)
    ],
}
```

---

## ⚗️ Лут (`config/loot.py`)

### Матеріал

```python
MATERIALS_DATA = {
    "my_material": (
        "Назва",    # name
        "🌟",       # icon
        "Опис",     # description
        "rare",     # rarity: common/uncommon/rare/epic/legendary
        3,          # bonus_attack
        0,          # bonus_defense
        0,          # bonus_hp
        0.02,       # bonus_crit
        2.5,        # multiplier (якість крафту)
        False,      # is_metal (True = слот "Лезо")
    ),
}
```

### Предмет

```python
ITEMS_DATA = {
    "my_sword": (
        "Мій меч",  # name
        "weapon",   # type: weapon / armor / potion / tool
        150,        # ціна
        "🗡",        # icon
        "Опис",     # description
        20,  0,  0,  0,  0.05,  # attack, defense, hp, hp_restore, crit
    ),
}
```

### Кресленик

```python
BLUEPRINTS_DATA = {
    "bp_my_sword": {
        "name":   "Кресленик: Мій меч",
        "result": ("my_sword", "Мій меч", 150, "🗡", "Опис"),
        "recipe": {"enchanted_wood": 3, "magic_core": 2},
        "bonus_materials": ["magic_core"],
        "unlock_cost": 45,
        "type":   "weapon",
        "attack": 20,
        # "defense": 10,  # для armor
        # "hp": 15,
        "rarity": "rare",  # common/uncommon/rare/epic/legendary
    },
}
```

---

## 🦸 Герої (`config/heroes.py`)

```python
HEROES_DATA = {
    "my_hero": {
        "name": "Мій Герой", "group": "warrior",
        "rarity": "rare",    # common/rare/epic/legendary
        "icon": "🗡",
        "lore": "Легенда...",
        "anim_folder": "knight/Knight_1",  # папка в assets/animations/
        "frame_h": 128,
        "anim": {
            "idle":    ("Idle",     6),  # (файл без .png, кількість кадрів)
            "attack1": ("Attack 1", 5),
            "hurt":    ("Hurt",     3),
            "dead":    ("Dead",     6),
            "run":     ("Run",      8),
            "walk":    ("Walk",     8),
        },
        "base": {"hp": 5, "attack": 8, "defense": 2, "crit": 0.03},
        "skills": [
            {"passive": True,  "name": "Сила",        "desc": "+12 атаки", "attack": 12},
            {"passive": False, "name": "Сильний удар", "desc": "+80% урону",
             "active_id": "charge_attack"},
        ],
    },
}

# Шанси у рулетці
RARITY_WEIGHTS = {
    "common": 50.0, "rare": 30.0, "epic": 15.0, "legendary": 5.0,
}
```

---

## 📜 Квести (`config/quests.py`)

```python
QUESTS_DATA = [
    {
        "id":      "my_quest",
        "title":   "Моє завдання",
        "icon":    "🗡",
        "story":   ["Герою, нам потрібна допомога...", "Другий рядок діалогу."],
        "unlock_when":   "quest:q_welcome",  # після якого квесту
        "complete_when": "kills:goblin:5",   # умова виконання
        "objective":     "Вбий 5 гоблінів",
        "reward_gold":   80,
        "reward_xp":     60,
        "reward_mats":   {"iron_bar": 3},    # необов'язково
        "reward_spins":  1,                  # спіни рулетки
        "unlocks":       "next_quest_id",    # що відкриє
        "repeatable":    False,
    },
]
```

**Умови** (`unlock_when` / `complete_when`):

| Рядок | Значення |
|-------|----------|
| `"always"` | завжди доступний |
| `"quest:q_welcome"` | після виконання квесту |
| `"level:5"` | рівень >= 5 |
| `"kills:goblin:3"` | вбито >= 3 гоблінів |
| `"kills:any:10"` | будь-які 10 вбивств |
| `"material:iron_bar:5"` | є >= 5 матеріалу |
| `"gold:100"` | є >= 100 золота |
| `"weapon_attack:13"` | є зброя з атакою >= 13 |

### Щоденні завдання

```python
DAILY_QUESTS_POOL = [
    {"id": "my_daily", "title": "Завдання", "icon": "⚔",
     "desc": "Опис", "type": "kill_goblin", "target": 5,
     "gold": 80, "xp": 120},
]
```

**Типи** (`type`): `kill_goblin`, `kill_orc`, `kill_knight`, `kill_any`,
`deal_damage`, `crit_hit`, `use_dodge`, `use_parry`, `win_nodamage`,
`win_battles`, `use_potion`, `heavy_kill`, `apply_bleed`

---

## 🏪 Крамниця (`config/shop.py`)

```python
SHOP_ITEMS = [
    ("small_potion", 10),   # (item_id, ціна)
    ("chainmail",    80),
]

SHOP_BLUEPRINTS = [
    ("bp_iron_sword", 20),  # (blueprint_id, ціна)
    ("bp_dark_blade", 50),
]
```

---

## ✨ Перки і скіл-три (`config/perks.py`)

### Перк

```python
PERKS_DATA = {
    "my_perk": {
        "name":   "+10% шкоди",
        "desc":   "Всі удари наносять більше шкоди",
        "rarity": "rare",   # common/uncommon/rare/epic/mythic/legendary/god
        "icon":   "⚔",
        "effect": {
            "attack":      10,     # +10 до атаки
            "attack_pct":  0.10,   # +10% до атаки
            "defense":     5,
            "max_hp":      50,
            "crit_chance": 0.10,   # +10%
            "gold_bonus":  0.20,   # +20% золота
            "xp_bonus":    0.15,
        },
    },
}
```

### Вузол скіл-три

```python
SKILL_NODES_DATA = {
    "my_node": {
        "name": "Нова навичка",  "desc": "+10 атаки",
        "icon": "⚔",  "branch": "strength",  # strength/endurance/agility
        "tier": 3,               # 1-5 (позиція в гілці)
        "stat": "attack",        "value": 10,
        "extra_stat": "crit_chance", "extra_value": 0.05,  # необов'язково
        "requires": "str_2",     # попередній вузол або None
    },
}
```

---

## 🗺️ Локації (`config/locations.py`)

```python
LOCATIONS = {
    "my_dungeon": {
        "name":        "Моє Підземелля",
        "icon":        "🏚",
        "description": "Темне та небезпечне місце.",
        "bg_music":    "battle music loop.flac",
        "bg_scene":    "dungeon",      # ключ з SCENE_BACKGROUNDS
        "bonus_attack":  3,            # бонус гравця в цій локації
        "bonus_defense": 0,
        "bonus_hp":      0,
        "min_level":   4,
        "events":      ["find_chest", "ambush"],
        "loot_bonus":  1.3,            # +30% до дропу
    },
}
```

Додай ворогів у `config/enemies.py → SPAWN_TABLES["my_dungeon"]`.

### Події

```python
EVENTS = {
    "my_event": {
        "name":   "Щось трапилось!",
        "icon":   "💎",
        "chance": 0.10,    # 10% при кожному бою
        "desc":   "Опис події.",
        "reward": {"gold": (20, 50)},  # (мін, макс) або фіксоване число
    },
}
```

---

## 🔄 Hot-reload (`Ctrl+F5`)

Зміни в будь-якому `config/*.py` файлі застосовуються **без перезапуску гри**.

Натисни `Ctrl+F5` — у правому верхньому куті з'явиться повідомлення.

**Що перезавантажується:** вороги, лут, герої, квести, тема, UI, нові PNG файли.

**Що НЕ перезавантажується:** збережена гра, поточний прогрес сесії.

---

## ✅ Валідатор конфігів

При кожному запуску гри автоматично перевіряються всі конфіги.
Помилки виводяться в консоль **до** запуску гри:

```
═══════════════════════════════════════════════
  ПЕРЕВІРКА КОНФІГІВ
═══════════════════════════════════════════════
❌ Blueprint 'bp_my_sword': матеріал 'xyz' не існує
⚠  Герой 'my_hero': папка анімацій не знайдена
✅ Вороги: 14 шт., всі поля ОК
✅ Кресленики: 42 шт., всі рецепти ОК
═══════════════════════════════════════════════
  1 помилок, 1 попереджень, 6 ОК
```

Запустити вручну:
```python
from config.validator import validate_and_warn
validate_and_warn()
```

---

## 🛠 Адмін-панель (`F12`)

Доступна під час гри. Вкладки:

| Вкладка | Що робить |
|---------|-----------|
| **Гравець** | Статистика + швидкі дії (+золото, +XP, +рівень) |
| **Матеріали** | Видати будь-який матеріал (пошук + скрол) |
| **Предмети** | Видати будь-який предмет |
| **Кресленики** | Видати будь-який кресленик |
| **Бій** | Статистика боїв, симуляція перемоги |
| **Скіп** | Пропустити очікування (крафт, ринок, шахтар, щоденні квести) |
| **Система** | Hot-reload, FPS, гарячі клавіші |

**Гарячі клавіші в адмін-панелі:**
- Просто друкуй — пошук по списку
- Колесо миші — прокрутка
- `Ctrl+Q` — змінити кількість матеріалів за клік
- `ESC` — назад / закрити

---

## 🏗 Структура сцен

Великі сцени розбиті на логіку і малювання:

| Логіка | Малювання |
|--------|-----------|
| `scenes/workshop.py` | `scenes/workshop_ui.py` |
| `scenes/battle_fighting.py` | `scenes/battle_draw.py` |

**Правило:** хочеш змінити як щось **виглядає** → відкриваєш `*_ui.py` або `*_draw.py`.
Хочеш змінити як щось **працює** → відкриваєш основний файл.

---

## 🔑 Гарячі клавіші гри

| Клавіша | Дія |
|---------|-----|
| `F5` | Зберегти гру |
| `Ctrl+F5` | Hot-reload конфігів |
| `F12` | Відкрити/закрити адмін-панель |
| `F11` або `Alt+Enter` | Повноекранний режим |
| `ESC` | Назад / вийти |