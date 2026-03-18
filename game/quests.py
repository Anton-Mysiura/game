"""
Система квестів від голови села.
Квести мають сюжет, умови виконання, нагороди.
Деякі розблоковуються після виконання попередніх (ланцюжок).
"""
from dataclasses import dataclass, field
from typing import Optional, Callable


# ── Типи умов ─────────────────────────────────────────────────────
# Умова — lambda(player) -> bool

@dataclass
class Quest:
    quest_id:       str
    title:          str
    icon:           str
    # Сюжетний діалог — список рядків (сторінки)
    story_lines:    list[str]
    # Умова прийняття (розблокування)
    unlock_cond:    Callable   # (player) -> bool
    # Умова виконання
    complete_cond:  Callable   # (player) -> bool
    # Опис що треба зробити
    objective:      str
    # Нагороди
    reward_gold:    int   = 0
    reward_xp:      int   = 0
    reward_mats:    dict  = field(default_factory=dict)   # {mat_id: qty}
    reward_item_id: str   = ""   # item_id з ITEMS (зілля тощо)
    reward_spins:   int   = 0    # спіни рулетки героїв
    # Ланцюжок — цей квест відкриває наступний
    unlocks:        str   = ""   # quest_id наступного квесту
    # Повторюваний (щоразу можна брати)
    repeatable:     bool  = False


# ── Всі квести ────────────────────────────────────────────────────

QUESTS: dict[str, Quest] = {

    # ════════════════════════════════════════════
    # АКТ 1 — Перші кроки
    # ════════════════════════════════════════════

    "q_welcome": Quest(
        "q_welcome",
        "Перші кроки",
        "🏘",
        [
            "Слухай, мандрівнику...",
            "Наше село оточене небезпекою. Гобліни щодня\n"
            "нападають на поля й забирають нашу їжу.",
            "Ти виглядаєш як боєць. Допоможи нам —\n"
            "переможи кількох гоблінів у лісі.",
            "Ось золото на початок. Більше отримаєш\n"
            "коли повернешся з перемогою.",
        ],
        unlock_cond   = lambda p: True,
        complete_cond = lambda p: p.goblins_killed >= 3,
        objective     = "Вбий 3 гоблінів у лісі",
        reward_gold   = 40,
        reward_xp     = 30,
        unlocks       = "q_iron_for_village",
    ),

    "q_iron_for_village": Quest(
        "q_iron_for_village",
        "Залізо для села",
        "⚒",
        [
            "Добре, добре! Ти справжній воїн.",
            "Але нашому ковалю потрібне залізо.\n"
            "Без нього ми не зможемо зробити нові інструменти.",
            "У лісі є місця де можна знайти руду.\n"
            "Принеси мені кілька залізних зливків.",
        ],
        unlock_cond   = lambda p: "q_welcome" in p.quests_done,
        complete_cond = lambda p: p.materials.get("iron_bar", 0) >= 5,
        objective     = "Мати 5 залізних зливків",
        reward_gold   = 50,
        reward_xp     = 25,
        reward_mats   = {"leather": 3, "bone": 4},
        unlocks       = "q_first_sword",
    ),

    "q_first_sword": Quest(
        "q_first_sword",
        "Справжній клинок",
        "⚔",
        [
            "Ти вже не новачок, це видно.",
            "Але з тим іржавим залізом далеко не підеш.\n"
            "Час скувати щось гідне.",
            "Піди до майстерні й скуй собі залізний меч\n"
            "або щось краще. Я буду чекати.",
        ],
        unlock_cond   = lambda p: "q_iron_for_village" in p.quests_done,
        complete_cond = lambda p: any(
            getattr(i, "attack_bonus", 0) >= 13 for i in p.inventory
        ) or (p.equipped_weapon and p.equipped_weapon.attack_bonus >= 13),
        objective     = "Скрафтити зброю з атакою 13+",
        reward_gold   = 60,
        reward_xp     = 40,
        reward_mats   = {"silver_ore": 3},
        unlocks       = "q_orc_threat",
    ),

    # ════════════════════════════════════════════
    # АКТ 2 — Загроза орків
    # ════════════════════════════════════════════

    "q_orc_threat": Quest(
        "q_orc_threat",
        "Загроза з півночі",
        "🧟",
        [
            "Є погані новини, герою...",
            "Розвідники донесли що орки збираються\n"
            "в лісі на північ від села.",
            "Якщо ми не зупинимо їх — вони спалять\n"
            "наші поля до останнього колоска.",
            "Переможи кількох орків. Вони повинні\n"
            "знати що цей ліс — не для них.",
        ],
        unlock_cond   = lambda p: "q_first_sword" in p.quests_done,
        complete_cond = lambda p: p.orcs_killed >= 5,
        objective     = "Вбий 5 орків",
        reward_gold   = 80,
        reward_xp     = 60,
        reward_mats   = {"dark_steel": 2, "magic_core": 1},
        unlocks       = "q_dark_materials",
    ),

    "q_dark_materials": Quest(
        "q_dark_materials",
        "Темні матеріали",
        "🖤",
        [
            "Ти чув про темну сталь?",
            "Старий коваль казав — з неї можна кувати\n"
            "зброю що ріже навіть магічний захист.",
            "Зберери трохи темної сталі та магічних ядер.\n"
            "Такі матеріали падають з сильних ворогів.",
        ],
        unlock_cond   = lambda p: "q_orc_threat" in p.quests_done,
        complete_cond = lambda p: (
            p.materials.get("dark_steel", 0) >= 3
            and p.materials.get("magic_core", 0) >= 2
        ),
        objective     = "Зібрати 3 темної сталі та 2 магічних ядра",
        reward_gold   = 100,
        reward_xp     = 70,
        reward_mats   = {"mithril_ore": 2, "enchanted_wood": 2},
        unlocks       = "q_dark_blade_quest",
    ),

    "q_dark_blade_quest": Quest(
        "q_dark_blade_quest",
        "Клинок що п'є тінь",
        "🌑",
        [
            "Старий Бромар залишив кресленик...",
            "Темний клинок — зброя що вбирає тінь ворога\n"
            "і стає сильнішою з кожним ударом.",
            "Скуй його. Він знадобиться тобі\n"
            "коли підеш до Вежі.",
        ],
        unlock_cond   = lambda p: "q_dark_materials" in p.quests_done,
        complete_cond = lambda p: any(
            getattr(i, "attack_bonus", 0) >= 22 for i in p.inventory
        ) or (p.equipped_weapon and p.equipped_weapon.attack_bonus >= 22),
        objective     = "Скрафтити зброю з атакою 22+",
        reward_gold   = 120,
        reward_xp     = 80,
        reward_mats   = {"dragon_scale": 1, "void_essence": 1},
        unlocks       = "q_tower_mission",
    ),

    # ════════════════════════════════════════════
    # АКТ 3 — Вежа і Руїни
    # ════════════════════════════════════════════

    "q_tower_mission": Quest(
        "q_tower_mission",
        "Місія у Вежі",
        "🏰",
        [
            "Прийшов час...",
            "У Темній Вежі на сході живе Темний Лицар.\n"
            "Він командує арміями що тероризують наш край.",
            "Я не прошу тебе вмирати — але якщо ти\n"
            "переможеш його, ми будемо врятовані.",
            "Будь обережний. Він не звичайний ворог.",
        ],
        unlock_cond   = lambda p: "q_dark_blade_quest" in p.quests_done,
        complete_cond = lambda p: p.knights_killed >= 1,
        objective     = "Переможи Темного Лицаря у Вежі",
        reward_gold   = 200,
        reward_xp     = 150,
        reward_mats   = {"mithril_bar": 2, "magic_core": 2},
        unlocks       = "q_ruins_secret",
    ),

    "q_ruins_secret": Quest(
        "q_ruins_secret",
        "Таємниця Руїн",
        "🗿",
        [
            "Ти повернувся! Я вже не сподівався...",
            "Але є ще одна справа. У Руїнах на заході\n"
            "сховані стародавні скрижалі.",
            "Кажуть — той хто їх знайде, дізнається\n"
            "як перемогти дракона Морвета.",
            "Дослідж Руїни. Повернися живим.",
        ],
        unlock_cond   = lambda p: "q_tower_mission" in p.quests_done,
        complete_cond = lambda p: "ruins" in p.locations_visited,
        objective     = "Відвідай Руїни",
        reward_gold   = 150,
        reward_xp     = 100,
        reward_mats   = {"dragon_scale": 2, "phoenix_feather": 1},
        unlocks       = "q_dragon_final",
    ),

    # ════════════════════════════════════════════
    # АКТ 4 — Дракон
    # ════════════════════════════════════════════

    "q_dragon_final": Quest(
        "q_dragon_final",
        "Кінець легенди",
        "🐉",
        [
            "Скрижалі... я прочитав їх всю ніч.",
            "Морвет — не просто дракон. Він — прокляття\n"
            "що лежить на нашому краї вже сто років.",
            "Поки він живий — темрява буде повертатись\n"
            "знову і знову, скільки б ми не билися.",
            "Є лише один спосіб покінчити з цим.\n"
            "Ти знаєш що робити, герою.",
        ],
        unlock_cond   = lambda p: "q_ruins_secret" in p.quests_done,
        complete_cond = lambda p: p.dragons_killed >= 1,
        objective     = "Переможи дракона Морвета",
        reward_gold   = 500,
        reward_xp     = 300,
        reward_mats   = {"star_metal": 2, "ancient_core": 1, "void_essence": 3},
        unlocks       = "",
    ),

    # ════════════════════════════════════════════
    # Побічні квести — доступні паралельно
    # ════════════════════════════════════════════

    "q_side_potions": Quest(
        "q_side_potions",
        "Запаси цілителя",
        "🧪",
        [
            "Наш лікар просить про допомогу.",
            "Зілля здоров'я закінчились — поранені\n"
            "солдати помирають без лікування.",
            "Принеси хоч щось. Будь-яке зілля.",
        ],
        unlock_cond   = lambda p: p.level >= 2,
        complete_cond = lambda p: sum(
            1 for i in p.inventory if getattr(i, "hp_restore", 0) > 0
        ) >= 3,
        objective     = "Мати 3+ зілля здоров'я в інвентарі",
        reward_gold   = 45,
        reward_xp     = 20,
        reward_mats   = {"leather": 5, "bone": 3},
        repeatable    = True,
    ),

    "q_side_bones": Quest(
        "q_side_bones",
        "Кістки для будівництва",
        "🦴",
        [
            "Нам потрібно відновити паркан навколо села.",
            "Коваль каже що кістки добре тримають\n"
            "дерево разом. Дивно, але правда.",
            "Принеси десяток кісток — і ми заплатимо.",
        ],
        unlock_cond   = lambda p: p.level >= 2,
        complete_cond = lambda p: p.materials.get("bone", 0) >= 10,
        objective     = "Зібрати 10 кісток",
        reward_gold   = 35,
        reward_xp     = 15,
        reward_mats   = {"iron_ore": 4},
        repeatable    = True,
    ),

    "q_side_slayer": Quest(
        "q_side_slayer",
        "Зачистка лісу",
        "🌲",
        [
            "Мисливці бояться виходити в ліс.",
            "Гоблінів і орків стало забагато —\n"
            "вони нападають навіть вдень.",
            "Зроби прогулянку. Тільки більш... кривавою.",
        ],
        unlock_cond   = lambda p: p.level >= 3,
        complete_cond = lambda p: p.enemies_killed >= 20,
        objective     = "Загалом вбити 20 ворогів",
        reward_gold   = 70,
        reward_xp     = 50,
        reward_mats   = {"dark_steel": 1, "silver_ore": 3},
        repeatable    = False,
    ),

    "q_side_crafter": Quest(
        "q_side_crafter",
        "Майстер ковалі",
        "🔨",
        [
            "Стара Мірта хвалила твою зброю.",
            "Казала — таких клинків не бачила\n"
            "відколи старий Бромар пішов на спокій.",
            "Скуй ще кілька предметів — покажи\n"
            "що твої руки не забудуть ремесло.",
        ],
        unlock_cond   = lambda p: p.items_crafted >= 1,
        complete_cond = lambda p: p.items_crafted >= 5,
        objective     = "Скрафтити 5 предметів загалом",
        reward_gold   = 55,
        reward_xp     = 35,
        reward_mats   = {"enchanted_wood": 3, "quartz": 2},
        unlocks       = "q_side_master",
    ),

    "q_side_master": Quest(
        "q_side_master",
        "Легендарний коваль",
        "⚒",
        [
            "Ти вже майстер, але чи ти легенда?",
            "Бромар скував за своє життя сто клинків.\n"
            "Кожен — твір мистецтва.",
            "Скуй десять предметів і твоє ім'я\n"
            "буде висічено на стіні кузні.",
        ],
        unlock_cond   = lambda p: "q_side_crafter" in p.quests_done,
        complete_cond = lambda p: p.items_crafted >= 10,
        objective     = "Скрафтити 10 предметів загалом",
        reward_gold   = 100,
        reward_xp     = 60,
        reward_mats   = {"mithril_ore": 3, "fire_gem": 2},
        repeatable    = False,
    ),

    "q_side_rich": Quest(
        "q_side_rich",
        "Торговець поневолі",
        "💰",
        [
            "Бачу — ти непогано заробляєш.",
            "Поділися мудрістю. Як це — мати\n"
            "повний гаманець золота?",
            "Накопич 300 золотих — і я розповім\n"
            "де шукати справжні скарби.",
        ],
        unlock_cond   = lambda p: p.level >= 2,
        complete_cond = lambda p: p.gold >= 300,
        objective     = "Накопичити 300 золота",
        reward_gold   = 80,
        reward_xp     = 30,
        reward_mats   = {"blood_crystal": 1, "void_essence": 1},
        repeatable    = False,
    ),

    "q_side_armor": Quest(
        "q_side_armor",
        "Броня — не розкіш",
        "🛡",
        [
            "Гляджу — ти ходиш в чому мати народила.",
            "Ну майже. Броня важлива, хлопче.",
            "Одягни щось що тримає удар —\n"
            "і я дам тобі нагороду.",
        ],
        unlock_cond   = lambda p: p.level >= 2,
        complete_cond = lambda p: (
            p.equipped_armor is not None and
            p.equipped_armor.defense_bonus >= 8
        ),
        objective     = "Екіпірувати броню з захистом 8+",
        reward_gold   = 60,
        reward_xp     = 25,
        reward_mats   = {"shadow_cloth": 2, "iron_chain": 2},
        repeatable    = False,
    ),

    # ════════════════════════════════════════════
    # ШАХТА — розблокування і квести Бориса
    # ════════════════════════════════════════════

    "q_unlock_mine": Quest(
        "q_unlock_mine",
        "Стара шахта",
        "⛏",
        [
            "Слухай, є одна справа...",
            "На північ від села є стара шахта.\n"
            "Колись там добували руду, але потім кинули.",
            "Я знаю шахтаря — Бориса. Він готовий\n"
            "повернутись, але йому потрібен надійний партнер.",
            "Принеси 5 залізних зливків — покажи серйозність.",
        ],
        unlock_cond   = lambda p: p.level >= 3 and "q_first_sword" in p.quests_done,
        complete_cond = lambda p: p.materials.get("iron_bar", 0) >= 5,
        objective     = "Мати 5 залізних зливків (рівень 3+)",
        reward_gold   = 30,
        reward_xp     = 40,
        reward_mats   = {"iron_ore": 5},
        unlocks       = "q_mine_first_run",
    ),

    "q_mine_first_run": Quest(
        "q_mine_first_run",
        "Перший спуск",
        "🪨",
        [
            "Борис готовий! Він вже чекає біля шахти.",
            "Купи йому кайло в крамниці й відправ\n"
            "на перший тариф — Поверхня.",
        ],
        unlock_cond   = lambda p: "q_unlock_mine" in p.quests_done,
        complete_cond = lambda p: getattr(p, "mine_trips", 0) >= 1,
        objective     = "Відправити шахтаря хоча б раз",
        reward_gold   = 50,
        reward_xp     = 30,
        unlocks       = "q_boris_hungry",
        repeatable    = False,
    ),

    "q_boris_hungry": Quest(
        "q_boris_hungry",
        "Борис голодний",
        "🍖",
        [
            "Гей, мандрівнику!",
            "Я цілий день в шахті, а їжі нема.\n"
            "Принеси мені зілля — хоч якесь.",
            "Тоді я піду на глибший рівень,\n"
            "принесу тобі щось цікаве.",
        ],
        unlock_cond   = lambda p: "q_mine_first_run" in p.quests_done,
        complete_cond = lambda p: any(
            getattr(i, "item_id", "") in ("small_potion", "big_potion")
            for i in p.inventory),
        objective     = "Мати зілля в інвентарі (мале або велике)",
        reward_gold   = 35,
        reward_xp     = 20,
        reward_mats   = {"ruby_ore": 2, "garnet_ore": 3},
        unlocks       = "q_boris_deep",
    ),

    "q_boris_deep": Quest(
        "q_boris_deep",
        "На глибину!",
        "💎",
        [
            "Ось дякую! Тепер я повний сил.",
            "Там на глибині бачив щось дивне —\n"
            "схоже на астральну руду.",
            "Відправ мене на найглибший тариф.",
        ],
        unlock_cond   = lambda p: "q_boris_hungry" in p.quests_done,
        complete_cond = lambda p: getattr(p, "mine_deep_trips", 0) >= 1,
        objective     = "Відправити шахтаря на Глибину",
        reward_gold   = 80,
        reward_xp     = 50,
        reward_mats   = {"astral_ore": 1, "iron_bar": 5},
        unlocks       = "q_boris_rest",
    ),

    "q_boris_rest": Quest(
        "q_boris_rest",
        "Заслужений відпочинок",
        "😴",
        [
            "Стільки походів — і жодного дня відпочинку.",
            "Дай мені відпочити хоч раз.\n"
            "Я прийду на роботу свіжим і заплачу менше.",
        ],
        unlock_cond   = lambda p: "q_boris_deep" in p.quests_done,
        complete_cond = lambda p: (
            hasattr(p, "miner") and
            getattr(p.miner, "trips_since_rest", 99) == 0
        ),
        objective     = "Дати шахтарю відпочити (кнопка 'Відпочити' в шахті)",
        reward_gold   = 40,
        reward_xp     = 25,
        repeatable    = False,
    ),
}


# ── Хелпери ───────────────────────────────────────────────────────

def get_available_quests(player) -> list[Quest]:
    """Квести що можна взяти (умова виконана, ще не взяті або repeatable)."""
    result = []
    for q in QUESTS.values():
        if q.quest_id in player.quests_done and not q.repeatable:
            continue
        if q.quest_id in player.quests_active:
            continue
        if q.unlock_cond(player):
            result.append(q)
    return result


def get_active_quests(player) -> list[Quest]:
    """Активні квести гравця."""
    return [QUESTS[qid] for qid in player.quests_active if qid in QUESTS]


def get_completable_quests(player) -> list[Quest]:
    """Активні квести що вже виконані."""
    return [q for q in get_active_quests(player) if q.complete_cond(player)]


def accept_quest(player, quest_id: str) -> bool:
    if quest_id in player.quests_active:
        return False
    player.quests_active.add(quest_id)
    return True


def complete_quest(player, quest_id: str) -> Optional[Quest]:
    """Завершує квест, видає нагороди, відкриває наступний. Повертає Quest або None."""
    quest = QUESTS.get(quest_id)
    if not quest or quest_id not in player.quests_active:
        return None
    if not quest.complete_cond(player):
        return None

    player.quests_active.discard(quest_id)
    player.quests_done.add(quest_id)

    # Нагороди
    player.gold             += quest.reward_gold
    player.total_gold_earned += quest.reward_gold
    for xp_chunk in range(quest.reward_xp):
        pass  # XP додаємо одразу
    player.xp += quest.reward_xp
    # Перевірка level-up — без автоматичного left-up, просто накопичуємо
    while player.xp >= player.xp_next:
        player.level_up()

    for mat_id, qty in quest.reward_mats.items():
        player.add_material(mat_id, qty)

    if quest.reward_item_id:
        from .data import ITEMS
        item = ITEMS.get(quest.reward_item_id)
        if item:
            player.inventory.append(item)

    # Спіни рулетки героїв
    if getattr(quest, "reward_spins", 0):
        player.hero_roster.add_spins(quest.reward_spins)

    # Відкриваємо наступний квест в ланцюжку
    if quest.unlocks and quest.unlocks in QUESTS:
        pass  # буде доступний через get_available_quests

    return quest