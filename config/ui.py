"""
╔══════════════════════════════════════════════════════════════╗
║  UI КАСТОМІЗАЦІЯ                                             ║
║  Кнопки, фони, панелі — все налаштовується тут              ║
╚══════════════════════════════════════════════════════════════╝

──────────────────────────────────────────────────────────────
ЯК ДОДАТИ СВОЇ ТЕКСТУРИ (покрокова інструкція):

  1. Поклади PNG файл у відповідну папку:
       assets/textures/ui/button/    ← кнопки
       assets/textures/ui/bg/        ← фони сцен
       assets/textures/ui/panel/     ← панелі/рамки
       assets/textures/ui/icon/      ← іконки

  2. Пропиши назву файлу нижче у потрібний розділ.
     Наприклад, якщо поклав "my_button.png":
       BUTTON_STYLE["default"]["normal"] = "my_button"

  3. Запусти гру — все завантажиться автоматично.

Якщо текстура не знайдена — гра намалює кольорову заглушку.
──────────────────────────────────────────────────────────────
"""

# ══════════════════════════════════════════
#  СТИЛІ КНОПОК
# ══════════════════════════════════════════
#
# Кожен стиль — словник з 4 станами:
#   normal   — звичайний стан
#   hover    — при наведенні миші
#   pressed  — при натисканні
#   disabled — недоступна кнопка
#
# Значення: "назва_файлу" (без .png) з папки assets/textures/ui/button/
#   або None → малює кольоровий прямокутник (з config/theme.py)
#
# Приклад: якщо normal = "wood_btn", шукає файл
#   assets/textures/ui/button/wood_btn.png

BUTTON_STYLES = {

    # ── Стиль за замовчуванням ────────────────────────────────
    "default": {
        "normal":   None,            # ← замін на "wood_btn" якщо є файл
        "hover":    None,            # ← замін на "wood_btn_hover"
        "pressed":  None,
        "disabled": None,
        # Якщо файл не вказано (None) — використовуються ці кольори:
        "color_normal":   (80,  60,  40),
        "color_hover":    (120, 90,  60),
        "color_pressed":  (60,  45,  30),
        "color_disabled": (50,  40,  30),
        "border_color":   (200, 170, 100),  # колір рамки
        "border_width":   2,
        "text_color":     (220, 200, 180),
        "text_color_dis": (120, 110, 100),
        "font_size":      20,
        "corner_radius":  4,       # заокруглення кутів (0 = гострі)
    },

    # ── Маленька кнопка (для інвентарю, підтверджень) ─────────
    "small": {
        "normal":   None,
        "hover":    None,
        "pressed":  None,
        "disabled": None,
        "color_normal":   (70,  55,  35),
        "color_hover":    (110, 85,  55),
        "color_pressed":  (55,  42,  28),
        "color_disabled": (45,  38,  28),
        "border_color":   (180, 150, 80),
        "border_width":   1,
        "text_color":     (220, 200, 180),
        "text_color_dis": (110, 100, 90),
        "font_size":      16,
        "corner_radius":  3,
    },

    # ── Небезпечна кнопка (видалення, вихід) ─────────────────
    "danger": {
        "normal":   None,
        "hover":    None,
        "pressed":  None,
        "disabled": None,
        "color_normal":   (100, 30,  30),
        "color_hover":    (160, 50,  50),
        "color_pressed":  (80,  25,  25),
        "color_disabled": (60,  40,  40),
        "border_color":   (220, 80,  80),
        "border_width":   2,
        "text_color":     (255, 210, 210),
        "text_color_dis": (140, 110, 110),
        "font_size":      20,
        "corner_radius":  4,
    },

    # ── Успішна / підтверджувальна кнопка ────────────────────
    "success": {
        "normal":   None,
        "hover":    None,
        "pressed":  None,
        "disabled": None,
        "color_normal":   (30,  80,  30),
        "color_hover":    (50,  130, 50),
        "color_pressed":  (25,  65,  25),
        "color_disabled": (35,  55,  35),
        "border_color":   (80,  200, 80),
        "border_width":   2,
        "text_color":     (210, 255, 210),
        "text_color_dis": (120, 150, 120),
        "font_size":      20,
        "corner_radius":  4,
    },

    # ── Золота кнопка (для важливих дій) ─────────────────────
    "gold": {
        "normal":   None,    # ← наприклад "gold_btn_normal"
        "hover":    None,
        "pressed":  None,
        "disabled": None,
        "color_normal":   (120, 90,  20),
        "color_hover":    (170, 130, 30),
        "color_pressed":  (90,  70,  15),
        "color_disabled": (70,  60,  30),
        "border_color":   (255, 215, 0),
        "border_width":   2,
        "text_color":     (255, 245, 180),
        "text_color_dis": (160, 145, 90),
        "font_size":      22,
        "corner_radius":  5,
    },
}


# ══════════════════════════════════════════
#  ФОНИ СЦЕН
# ══════════════════════════════════════════
#
# Файли повинні бути в: assets/textures/ui/bg/
# Формат: "назва_файлу" (без .png)
# Якщо None → однотонний фон з COLOR_BG (config/theme.py)
#
# Рекомендований розмір: 1280×720 px (або більше)

SCENE_BACKGROUNDS = {
    "main_menu":    "main_menu",   # ← "main_menu_bg"  якщо є файл
    "village":      "village",   # ← "village_bg"
    "forest":       "forest",    # ← "forest_bg"
    "tower":        "tower",     # ← "tower_bg"
    "ruins":        "ruins",     # ← "ruins_bg"
    "mine":         "mine",      # ← "mine_bg"
    "battle":       "battle",   # ← "battle_bg"
    "inventory":    "inventory",   # ← "inventory_bg"
    "workshop":     "workshop",   # ← "workshop_bg"
    "shop":         "shop",   # ← "shop_bg"
    "world_map":    "world_map",   # ← "world_map_bg"
    "hero_roulette":"roulette",   # ← "roulette_bg"
    "victory":      "victory",   # ← "victory_bg"
    "death":        "death",   # ← "death_bg"
}

# Тайловий фон — якщо True, малий PNG буде тайлитись по всьому екрану
# (корисно для паттернів типу бруківки, дерева, каменю)
SCENE_BACKGROUND_TILE = {
    "main_menu":    False,
    "village":      False,
    "forest":       False,
    "battle":       False,
    # ... решта також False
}


# ══════════════════════════════════════════
#  СТИЛІ ПАНЕЛЕЙ
# ══════════════════════════════════════════
#
# Файли в: assets/textures/ui/panel/

PANEL_STYLES = {
    # Основна темна панель
    "dark": {
        "texture": None,      # ← "panel_dark" якщо є файл
        "color":   (40, 30, 20),
        "border_color":  (200, 170, 100),
        "border_width":  2,
        "corner_radius": 6,
        "alpha":   255,       # 0=прозора, 255=повністю непрозора
    },
    # Напівпрозора панель (для підказок)
    "overlay": {
        "texture": None,
        "color":   (20, 15, 10),
        "border_color":  (150, 130, 80),
        "border_width":  1,
        "corner_radius": 4,
        "alpha":   200,
    },
    # Дерев'яна рамка (для магазину, майстерні)
    "wood": {
        "texture": None,      # ← "panel_wood"
        "color":   (60, 40, 20),
        "border_color":  (180, 130, 60),
        "border_width":  3,
        "corner_radius": 8,
        "alpha":   255,
    },
    # Кам'яна рамка (для руїн, вежі)
    "stone": {
        "texture": None,      # ← "panel_stone"
        "color":   (50, 50, 60),
        "border_color":  (130, 130, 150),
        "border_width":  3,
        "corner_radius": 2,
        "alpha":   255,
    },
}


# ══════════════════════════════════════════
#  СЛОТИ ІНВЕНТАРЮ
# ══════════════════════════════════════════

SLOT_STYLE = {
    "empty_texture": None,       # ← "slot_empty" якщо є файл
    "hover_texture": None,       # ← "slot_hover"
    "selected_texture": None,    # ← "slot_selected"
    "color_empty":    (35, 28, 18),
    "color_hover":    (60, 50, 30),
    "color_selected": (80, 65, 25),
    "border_color":   (100, 85, 55),
    "border_width":   1,
    "corner_radius":  3,
}


# ══════════════════════════════════════════
#  ШРИФТИ
# ══════════════════════════════════════════
#
# Файли в: assets/fonts/
# Якщо None — використовується системний шрифт pygame

FONTS = {
    "main":    None,     # ← "main.ttf"   основний шрифт
    "title":   None,     # ← "title.ttf"  для заголовків
    "numbers": None,     # ← "numbers.ttf" для цифр (HP, XP)
    # Якщо "title" = None — береться "main"
    # Якщо "main" = None — береться pygame default
}


# ══════════════════════════════════════════
#  ІКОНКИ UI
# ══════════════════════════════════════════
#
# Файли в: assets/textures/ui/icon/

UI_ICONS = {
    "gold":       None,   # ← "gold_coin"    монета золота
    "hp":         None,   # ← "heart"        серце HP
    "xp":         None,   # ← "star_xp"      зірка XP
    "sword":      None,   # ← "sword_icon"   іконка атаки
    "shield":     None,   # ← "shield_icon"  іконка захисту
    "slot_empty": None,   # ← "slot_empty"   порожній слот
    "slot_hover": None,   # ← "slot_hover"
    "scroll":     None,   # ← "scroll"       кресленик
}


# ══════════════════════════════════════════
#  КУРСОР
# ══════════════════════════════════════════

CURSOR = {
    "use_custom": False,     # True → завантажити свій курсор
    "texture":    None,      # ← "cursor" з assets/textures/ui/
    "hotspot":    (0, 0),    # точка кліку на зображенні курсора
}
