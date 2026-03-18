"""
Система рандомних подій у лісі.
"""

import random
from dataclasses import dataclass, field
from typing import Callable, Optional
from .data import ITEMS, MATERIALS


# ══════════════════════════════════════════
#  РЕЗУЛЬТАТ ПОДІЇ
# ══════════════════════════════════════════

@dataclass
class EventResult:
    """Що сталось після вибору гравця."""
    text: str                              # текст результату
    gold_delta:      int       = 0
    hp_delta:        int       = 0
    items_gained:    list      = field(default_factory=list)   # list[Item]
    materials_gained: dict     = field(default_factory=dict)   # {mat_id: qty}
    items_lost:      list      = field(default_factory=list)
    enemy:           object    = None      # Enemy — якщо треба бій
    next_scene:      str       = "forest"  # куди після


# ══════════════════════════════════════════
#  ВИБІР У ПОДІЇ
# ══════════════════════════════════════════

@dataclass
class EventChoice:
    label: str                             # текст кнопки
    resolve: Callable                      # fn(player) -> EventResult


# ══════════════════════════════════════════
#  ПОДІЯ
# ══════════════════════════════════════════

@dataclass
class ForestEvent:
    event_id:    str
    title:       str
    icon:        str
    description: str
    choices:     list[EventChoice]
    weight:      float = 1.0               # відносна ймовірність


# ══════════════════════════════════════════
#  ВСІ ПОДІЇ
# ══════════════════════════════════════════

def _make_events() -> list[ForestEvent]:
    events = []

    # ── 🎁 СКРИНЯ ──────────────────────────────────────────
    def chest_open(player):
        roll = random.random()
        if roll < 0.5:
            qty = random.randint(1, 3)
            mat = random.choice(["wood", "bone", "leather"])
            return EventResult(
                f"В скрині виявились {MATERIALS[mat].name} ({qty} шт.) та трохи золота!",
                gold_delta=random.randint(5, 15),
                materials_gained={mat: qty},
            )
        elif roll < 0.8:
            item = random.choice([ITEMS["small_potion"], ITEMS["big_potion"]])
            return EventResult(
                f"В скрині є {item.name}!",
                items_gained=[item],
                gold_delta=random.randint(0, 8),
            )
        else:
            return EventResult(
                "Скриня виявилась порожньою... але на дні блищить монета.",
                gold_delta=random.randint(2, 6),
            )

    def chest_ignore(player):
        return EventResult("Ти обережно обходиш скриню стороною.")

    events.append(ForestEvent(
        "chest", "Загадкова скриня", "🎁",
        "Посеред стежки стоїть стара дерев'яна скриня. "
        "Замок зламаний — хтось вже побував тут. Або щось вийшло назовні.",
        [
            EventChoice("🔓 Відкрити", chest_open),
            EventChoice("🚶 Обійти стороною", chest_ignore),
        ],
        weight=1.5,
    ))

    # ── 🧙 МАНДРІВНИЙ ТОРГОВЕЦЬ ────────────────────────────
    def trader_buy_potion(player):
        cost = 8
        if player.gold < cost:
            return EventResult("Недостатньо золота!", gold_delta=0)
        player.gold -= cost
        player.inventory.append(ITEMS["small_potion"])
        return EventResult(
            f"Ти купив зілля за {cost} золота.",
            items_gained=[ITEMS["small_potion"]],
            gold_delta=-cost,
        )

    def trader_buy_big_potion(player):
        cost = 20
        if player.gold < cost:
            return EventResult("Недостатньо золота!")
        player.gold -= cost
        player.inventory.append(ITEMS["big_potion"])
        return EventResult(
            f"Ти купив велике зілля за {cost} золота.",
            items_gained=[ITEMS["big_potion"]],
            gold_delta=-cost,
        )

    def trader_sell(player):
        potions = [i for i in player.inventory
                   if i.item_id in ("small_potion", "big_potion", "power_potion")]
        if not potions:
            return EventResult("Торговець роздчарований — тобі нічого продати.")
        item = potions[0]
        sell_price = max(1, item.value // 2)
        player.inventory.remove(item)
        player.gold += sell_price
        return EventResult(
            f"Ти продав {item.name} за {sell_price} золота.",
            gold_delta=sell_price,
        )

    def trader_leave(player):
        return EventResult("Ти пройшов повз. Торговець знизав плечима.")

    events.append(ForestEvent(
        "trader", "Мандрівний торговець", "🧙",
        "З-за дерева виходить невисокий чоловік в кольоровому плащі. "
        "«Товари! Найкращі товари в цьому темному лісі!» — кричить він.",
        [
            EventChoice("🧪 Купити зілля (8 🪙)", trader_buy_potion),
            EventChoice("🧪 Купити велике зілля (20 🪙)", trader_buy_big_potion),
            EventChoice("💰 Продати зілля", trader_sell),
            EventChoice("🚶 Пройти повз", trader_leave),
        ],
        weight=1.0,
    ))

    # ── 🪤 ПАСТКА ──────────────────────────────────────────
    def trap_dodge(player):
        if random.random() < 0.5:
            return EventResult("Ти помітив мотузку вчасно і перестрибнув!")
        dmg = random.randint(8, 20)
        player.hp = max(1, player.hp - dmg)
        return EventResult(
            f"Майже уникнув! Шипи зачепили тебе — -{dmg} HP.",
            hp_delta=-dmg,
        )

    def trap_careful(player):
        dmg = random.randint(3, 8)
        player.hp = max(1, player.hp - dmg)
        return EventResult(
            f"Ти обережно розібрав пастку, але трохи порізався — -{dmg} HP.",
            hp_delta=-dmg,
            materials_gained={"wood": 1},
        )

    def trap_triggered(player):
        dmg = random.randint(15, 30)
        player.hp = max(1, player.hp - dmg)
        return EventResult(
            f"БУМ! Пастка спрацювала — -{dmg} HP. Добре що живий.",
            hp_delta=-dmg,
        )

    events.append(ForestEvent(
        "trap", "Пастка мисливця", "🪤",
        "Ти помічаєш натягнуту між деревами мотузку. "
        "Попереду щось блищить — схоже на примітивну пастку.",
        [
            EventChoice("🏃 Стрибнути через", trap_dodge),
            EventChoice("🔧 Обережно розібрати", trap_careful),
            EventChoice("💨 Просто пройти (ризик)", trap_triggered),
        ],
        weight=1.2,
    ))

    # ── 💀 ДОДАТКОВИЙ ВОРОГ ─────────────────────────────────
    def ambush_fight(player):
        from .enemy import make_goblin, Enemy
        import random
        # Рандомно між гобліном та посиленим гобліном
        if random.random() < 0.6:
            enemy = make_goblin()
            return EventResult(
                "З кущів вистрибує гоблін з криком!",
                enemy=enemy,
            )
        else:
            enemy = Enemy(
                "Лісовий павук", 25, 9, 2, 12, 4,
                loot_materials={"bone": 1, "leather": random.randint(0, 1)},
                sprite_name="goblin",
            )
            return EventResult(
                "З темряви виповзає величезний павук!",
                enemy=enemy,
            )

    def ambush_run(player):
        if random.random() < 0.4:
            dmg = random.randint(5, 12)
            player.hp = max(1, player.hp - dmg)
            return EventResult(
                f"Ти тікаєш, але ворог встигає вдарити — -{dmg} HP.",
                hp_delta=-dmg,
            )
        return EventResult("Ти швидко втік. Ворог не встиг наздогнати.")

    events.append(ForestEvent(
        "ambush", "Засідка!", "💀",
        "Раптово з темряви між деревами з'являються очі. "
        "Щось чекало на тебе. Зараз воно нападає.",
        [
            EventChoice("⚔ Прийняти бій", ambush_fight),
            EventChoice("🏃 Тікати", ambush_run),
        ],
        weight=1.3,
    ))

    # ── 🌿 ЗНАХІДКА МАТЕРІАЛІВ ──────────────────────────────
    def gather_materials(player):
        mats = {
            "wood":    random.randint(1, 4),
            "bone":    random.randint(0, 2),
            "leather": random.randint(0, 1),
        }
        mats = {k: v for k, v in mats.items() if v > 0}
        for mat, qty in mats.items():
            player.add_material(mat, qty)
        desc = ", ".join(f"{MATERIALS[m].name} ×{q}" for m, q in mats.items())
        return EventResult(
            f"Ти зібрав: {desc}.",
            materials_gained=mats,
        )

    def gather_rare(player):
        roll = random.random()
        if roll < 0.3:
            player.add_material("iron_ore", 1)
            return EventResult(
                "Серед коренів дерева — шматок залізної руди! Рідкісна знахідка.",
                materials_gained={"iron_ore": 1},
            )
        elif roll < 0.7:
            player.add_material("magic_core", 1)
            return EventResult(
                "Ти знаходиш пульсуюче магічне ядро серед трав. Дивно.",
                materials_gained={"magic_core": 1},
            )
        else:
            player.add_material("dark_steel", 1)
            return EventResult(
                "В землі — шматок темної сталі. Звідки він тут?",
                materials_gained={"dark_steel": 1},
            )

    def gather_skip(player):
        return EventResult("Ти поспішаєш далі, не затримуючись.")

    events.append(ForestEvent(
        "materials", "Щедрий ліс", "🌿",
        "Ти помічаєш цікаве місце — поваленое дерево, гриби, "
        "сліди від звірів. Тут можна знайти корисні матеріали.",
        [
            EventChoice("🪵 Зібрати звичайні матеріали", gather_materials),
            EventChoice("✨ Пошукати рідкісне (30 сек)", gather_rare),
            EventChoice("⏩ Пройти повз", gather_skip),
        ],
        weight=1.4,
    ))

    # ── 📜 ТАЄМНИЧЕ ПОСЛАННЯ (ЛОР) ─────────────────────────
    LORE_TEXTS = [
        ("Стара табличка", "📜",
         "На дереві вирізано: «Темне Королівство існувало тисячу років. "
         "Його впав не від меча, а від зради зсередини. "
         "Дракон Морвет — лише сторож, не причина.»"),
        ("Розірваний щоденник", "📖",
         "«День 47. Лицар Валар пройшов через ліс і не повернувся. "
         "Кажуть, він знайшов щось у вежі. Щось, що змінило його назавжди.»"),
        ("Камінь з рунами", "🪨",
         "Руни на камені розповідають про давню магію: «Хто переможе дракона "
         "без ненависті в серці — отримає більше, ніж золото.»"),
        ("Лист на землі", "🍂",
         "«Якщо ти читаєш це — ти вже глибше в лісі ніж треба. "
         "Поверніться. Ліс запам'ятовує обличчя тих, хто заходить занадто далеко.»"),
        ("Кістяк мандрівника", "💀",
         "Біля кісток — монети та записка: «Не йди вночі до вежі. "
         "Лицар бачить у темряві, ти — ні.»"),
    ]

    for i, (name, icon, text) in enumerate(LORE_TEXTS):
        lore_text = text  # capture

        def read_lore(player, t=lore_text):
            if not hasattr(player, 'lore_found'):
                player.lore_found = []
            player.lore_found.append(t[:30])
            return EventResult(t)

        def ignore_lore(player):
            return EventResult("Ти не звертаєш уваги і йдеш далі.")

        events.append(ForestEvent(
            f"lore_{i}", name, icon,
            f"Ти помічаєш щось незвичайне — {name.lower()} серед дерев.",
            [
                EventChoice(f"📖 Дослідити", read_lore),
                EventChoice("🚶 Проігнорувати", ignore_lore),
            ],
            weight=0.6,
        ))

    return events


ALL_EVENTS = _make_events()


# ══════════════════════════════════════════
#  ВИБІРКА ПОДІЇ
# ══════════════════════════════════════════

def roll_event(chance: float = 0.45) -> Optional[ForestEvent]:
    """
    Після бою кидає кубик чи трапиться подія.
    chance — ймовірність що подія взагалі відбудеться.
    Повертає ForestEvent або None.
    """
    if random.random() > chance:
        return None
    weights = [e.weight for e in ALL_EVENTS]
    return random.choices(ALL_EVENTS, weights=weights, k=1)[0]