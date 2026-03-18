"""
Каталог усіх 42 героїв гри.

Рідкості (4 тіри) і шанси у рулетці:
  common    50%  — базові бонуси, лише пасивна навичка
  rare      30%  — помірні бонуси, пасивна + 1 активна
  epic      15%  — сильні бонуси, 2 пасивні + 1 активна
  legendary  5%  — найкращі бонуси, 2 пасивні + 1 унікальна активна

Активні навички є лише там де є унікальна спеціальна анімація.
Пасивні бонуси збалансовані за тіром:
  common:    одна стата +6..12
  rare:      одна-дві стати +8..15
  epic:      дві стати +12..20
  legendary: три стати +18..30
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from ui.constants import ANIMATIONS_DIR

# ── Рідкість ─────────────────────────────────────────────────────────
HERO_RARITY_COLORS: dict[str, tuple] = {
    "common":    (180, 180, 180),
    "rare":      ( 80, 140, 220),
    "epic":      (180,  80, 220),
    "legendary": (255, 180,  40),
}
HERO_RARITY_NAMES_UA: dict[str, str] = {
    "common":    "Звичайний",
    "rare":      "Рідкісний",
    "epic":      "Епічний",
    "legendary": "Легендарний",
}
HERO_RARITY_WEIGHTS: dict[str, float] = {
    "common":    50.0,
    "rare":      30.0,
    "epic":      15.0,
    "legendary":  5.0,
}


# ── Навичка ───────────────────────────────────────────────────────────
@dataclass
class HeroSkill:
    name:        str
    desc:        str
    is_passive:  bool  = True
    bonus_hp:      int   = 0
    bonus_attack:  int   = 0
    bonus_defense: int   = 0
    bonus_crit:    float = 0.0
    bonus_dodge:   float = 0.0
    bonus_parry:   float = 0.0
    active_id:   str = ""


# ── Конфіг анімацій ───────────────────────────────────────────────────
@dataclass
class AnimConfig:
    folder:   str
    frame_h:  int = 128
    idle:     tuple = (None, 6)
    idle2:    tuple = (None, 0)
    attack1:  tuple = (None, 5)
    attack2:  tuple = (None, 0)
    attack3:  tuple = (None, 0)
    hurt:     tuple = (None, 3)
    dead:     tuple = (None, 5)
    run:      tuple = (None, 8)
    walk:     tuple = (None, 8)
    jump:     tuple = (None, 0)
    block:    tuple = (None, 0)
    special1: tuple = (None, 0)
    special2: tuple = (None, 0)

    def path(self) -> Path:
        return ANIMATIONS_DIR / self.folder


# ── Герой ─────────────────────────────────────────────────────────────
@dataclass
class Hero:
    hero_id:    str
    name:       str
    group:      str
    rarity:     str
    icon:       str
    lore:       str
    anim:       AnimConfig
    skills:     list = field(default_factory=list)
    base_hp:      int   = 0
    base_attack:  int   = 0
    base_defense: int   = 0
    base_crit:    float = 0.0
    base_dodge:   float = 0.0

    @property
    def rarity_color(self) -> tuple:
        return HERO_RARITY_COLORS.get(self.rarity, (180, 180, 180))

    @property
    def rarity_name_ua(self) -> str:
        return HERO_RARITY_NAMES_UA.get(self.rarity, self.rarity)

    def passive_bonuses(self) -> dict:
        hp = self.base_hp; atk = self.base_attack
        dfs = self.base_defense; crit = self.base_crit
        dodge = self.base_dodge; parry = 0.0
        for sk in self.skills:
            if sk.is_passive:
                hp    += sk.bonus_hp;      atk  += sk.bonus_attack
                dfs   += sk.bonus_defense; crit += sk.bonus_crit
                dodge += sk.bonus_dodge;   parry += sk.bonus_parry
        return {"hp": hp, "attack": atk, "defense": dfs,
                "crit": round(crit, 3), "dodge": round(dodge, 3),
                "parry": round(parry, 3)}

    def active_skills(self) -> list:
        return [s for s in self.skills if not s.is_passive]


# ── Фабрики ───────────────────────────────────────────────────────────
def _ac(folder, fh=128, **kw) -> AnimConfig:
    return AnimConfig(folder=folder, frame_h=fh, **kw)

def _p(name, desc, **kw) -> HeroSkill:
    return HeroSkill(name=name, desc=desc, is_passive=True, **kw)

def _a(name, desc, active_id) -> HeroSkill:
    return HeroSkill(name=name, desc=desc, is_passive=False, active_id=active_id)


# ════════════════════════════════════════════════════════════════════
#  КАТАЛОГ
# ════════════════════════════════════════════════════════════════════
HEROES: dict[str, Hero] = {

    # ══════════════════════ ЛИЦАР ══════════════════════
    "knight_1": Hero(
        "knight_1", "Лицар", "knight", "rare", "⚔",
        "Ветеран сотні битв. Щит тримає міцніше за скелю.",
        _ac("knight/Knight_1",
            idle=("Idle",4), attack1=("Attack 1",5), attack2=("Attack 2",4), attack3=("Attack 3",4),
            hurt=("Hurt",2), dead=("Dead",6), run=("Run",7), walk=("Walk",8), jump=("Jump",6),
            block=("Defend",5), special1=("Run+Attack",6)),
        [_p("Залізна шкіра", "+10 захисту", bonus_defense=10),
         _p("Загартований", "+12 HP", bonus_hp=12),
         _a("Натиск", "Атака з розбігу — подвійний урон", "charge_attack")],
        base_hp=8, base_defense=4,
    ),
    "knight_2": Hero(
        "knight_2", "Срібний Лицар", "knight", "epic", "🛡",
        "Обраний орденом. Срібні обладунки відбивають прокляття.",
        _ac("knight/Knight_2",
            idle=("Idle",4), attack1=("Attack 1",5), attack2=("Attack 2",4), attack3=("Attack 3",4),
            hurt=("Hurt",2), dead=("Dead",6), run=("Run",7), walk=("Walk",8), jump=("Jump",6),
            block=("Defend",5), special1=("Run+Attack",6)),
        [_p("Срібний щит", "+15 захисту, +5% парирування", bonus_defense=15, bonus_parry=0.05),
         _p("Загартоване серце", "+20 HP", bonus_hp=20),
         _a("Священний удар", "Заряджений удар — +60% урону", "holy_strike")],
        base_hp=12, base_defense=8,
    ),
    "knight_3": Hero(
        "knight_3", "Темний Лицар", "knight", "legendary", "🌑",
        "Впав у тінь, але сила не зменшилась.",
        _ac("knight/Knight_3",
            idle=("Idle",4), attack1=("Attack 1",5), attack2=("Attack 2",4), attack3=("Attack 3",4),
            hurt=("Hurt",2), dead=("Dead",6), run=("Run",7), walk=("Walk",8), jump=("Jump",6),
            block=("Defend",5), special1=("Run+Attack",6)),
        [_p("Темна сила", "+20 атаки, +8% крит", bonus_attack=20, bonus_crit=0.08),
         _p("Нічна броня", "+20 захисту, +22 HP", bonus_defense=20, bonus_hp=22),
         _a("Темний вихор", "АоЕ удар — ошелешує ворога", "dark_spin")],
        base_attack=8, base_defense=8, base_hp=8,
    ),

    # ══════════════════════ САМУРАЙ ══════════════════════
    "samurai": Hero(
        "samurai", "Самурай", "samurai", "rare", "⚔",
        "Кодекс бусідо у кожному ударі.",
        _ac("samurai/Samurai",
            idle=("Idle",6), attack1=("Attack_1",4), attack2=("Attack_2",5), attack3=("Attack_3",4),
            hurt=("Hurt",3), dead=("Dead",6), run=("Run",8), walk=("Walk",9), jump=("Jump",9),
            block=("Protection",2)),
        [_p("Концентрація", "+10 атаки, +5% крит", bonus_attack=10, bonus_crit=0.05),
         _a("Іайдо", "Блискавичний удар — ігнорує 30% захисту", "iaido")],
        base_attack=6,
    ),
    "samurai_archer": Hero(
        "samurai_archer", "Самурай-Лучник", "samurai", "epic", "🏹",
        "Клинок і лук — два шляхи, одна смерть.",
        _ac("samurai/Samurai_Archer",
            idle=("Idle",9), attack1=("Attack_1",5), attack2=("Attack_2",5), attack3=("Attack_3",6),
            hurt=("Hurt",3), dead=("Dead",5), run=("Run",8), walk=("Walk",8), jump=("Jump",9),
            special1=("Shot",14)),
        [_p("Снайпер", "+12 атаки, +10% крит", bonus_attack=12, bonus_crit=0.10),
         _p("Легкі кроки", "+8% ухилення", bonus_dodge=0.08),
         _a("Стріла долі", "Постріл з 200% урону", "fate_arrow")],
        base_attack=8, base_crit=0.04,
    ),
    "samurai_commander": Hero(
        "samurai_commander", "Командир Самураїв", "samurai", "epic", "🌟",
        "Його присутність надихає, його удар — вирок.",
        _ac("samurai/Samurai_Commander",
            idle=("Idle",5), attack1=("Attack_1",4), attack2=("Attack_2",5), attack3=("Attack_3",4),
            hurt=("Hurt",2), dead=("Dead",6), run=("Run",8), walk=("Walk",9), jump=("Jump",7),
            block=("Protect",2)),
        [_p("Бойовий клич", "+14 атаки", bonus_attack=14),
         _p("Командна воля", "+14 HP, +8 захисту", bonus_hp=14, bonus_defense=8),
         _a("Три удари", "Потрійний удар — кожен 80% урону", "triple_slash")],
        base_attack=10, base_hp=8,
    ),

    # ══════════════════════ НІНДЗЯ ══════════════════════
    "kunoichi": Hero(
        "kunoichi", "Куноїчі", "ninja", "rare", "🌸",
        "Тінь у ночі. Смерть приходить тихо.",
        _ac("ninja/Kunoichi",
            idle=("Idle",9), attack1=("Attack_1",6), attack2=("Attack_2",8),
            hurt=("Hurt",2), dead=("Dead",5), run=("Run",8), walk=("Walk",8), jump=("Jump",10),
            special1=("Cast",6)),
        [_p("Тіньовий крок", "+10% ухилення", bonus_dodge=0.10),
         _a("Отруйний укол", "Отруює ворога на 3 ходи", "poison_strike")],
        base_dodge=0.06, base_attack=4,
    ),
    "ninja_monk": Hero(
        "ninja_monk", "Монах-Ніндзя", "ninja", "epic", "🥋",
        "Роки медитації. Удари — як блискавка.",
        _ac("ninja/Ninja_Monk", fh=96,
            idle=("Idle",7), attack1=("Attack_1",5), attack2=("Attack_2",5),
            hurt=("Hurt",4), dead=("Dead",5), run=("Run",8), walk=("Walk",7), jump=("Jump",9),
            special1=("Cast",5), special2=("Blade",6)),
        [_p("Залізний кулак", "+15 атаки", bonus_attack=15),
         _p("Духовний захист", "+10 захисту, +5% парирування", bonus_defense=10, bonus_parry=0.05),
         _a("Кунай-шторм", "Кидає 3 кунаї — кожен 60% урону", "kunai_storm")],
        base_attack=8, base_defense=4,
    ),
    "ninja_peasant": Hero(
        "ninja_peasant", "Ніндзя-Селянин", "ninja", "common", "🌾",
        "Виглядає як простий фермер. Але за маскою — агент.",
        _ac("ninja/Ninja_Peasant",
            idle=("Idle",6), attack1=("Attack_1",6), attack2=("Attack_2",4),
            hurt=("Hurt",2), dead=("Dead",4), run=("Run",6), walk=("Walk",8), jump=("Jump",8),
            special1=("Shot",6), special2=("Disguise",9)),
        [_p("Маскування", "+8% ухилення, +4 атаки", bonus_dodge=0.08, bonus_attack=4)],
    ),

    # ══════════════════════ ШІНОБІ ══════════════════════
    "shinobi_1": Hero(
        "shinobi_1", "Шінобі", "shinobi", "common", "🗡",
        "Базова підготовка клану. Швидкий і непомітний.",
        _ac("sprites/1",
            idle=("Idle",6), attack1=("Attack_1",4), attack2=("Attack_2",3), attack3=("Attack_3",4),
            hurt=("Hurt",3), dead=("Dead",3), run=("Run",8), walk=("Walk",8), jump=("Jump",10),
            block=("Shield",2)),
        [_p("Легкі ноги", "+6% ухилення, +4 атаки", bonus_dodge=0.06, bonus_attack=4)],
    ),
    "shinobi_2": Hero(
        "shinobi_2", "Шінобі Майстер", "shinobi", "rare", "🗡",
        "Пройшов друге посвячення. Клинок не знає промахів.",
        _ac("sprites/2",
            idle=("Idle",6), attack1=("Attack_1",6), attack2=("Attack_2",4), attack3=("Attack_3",3),
            hurt=("Hurt",2), dead=("Dead",3), run=("Run",8), walk=("Walk",8), jump=("Jump",12),
            block=("Shield",2)),
        [_p("Подвійний клинок", "+10 атаки, +5% крит", bonus_attack=10, bonus_crit=0.05),
         _a("Вихор клинків", "АоЕ атака навколо", "blade_vortex")],
        base_attack=4,
    ),
    "shinobi_3": Hero(
        "shinobi_3", "Майстер Шінобі", "shinobi", "epic", "💀",
        "Майстер клану. Кожен удар — вирок.",
        _ac("sprites/3",
            idle=("Idle",6), attack1=("Attack_1",5), attack2=("Attack_2",3), attack3=("Attack_3",4),
            hurt=("Hurt",2), dead=("Dead",4), run=("Run",8), walk=("Walk",8), jump=("Jump",12),
            block=("Shield",4)),
        [_p("Тінь смерті", "+14 атаки, +8% крит", bonus_attack=14, bonus_crit=0.08),
         _p("Броня тіні", "+12 захисту", bonus_defense=12),
         _a("Крок вбивці", "Удар у спину — ×2 урону", "assassin_step")],
        base_attack=6, base_crit=0.04,
    ),

    # ══════════════════════ ГАНГСТЕР ══════════════════════
    "gangster_1": Hero(
        "gangster_1", "Гангстер", "gangster", "common", "🔫",
        "З вулиць міста. Не питає — стріляє.",
        _ac("gangster/1",
            idle=("Idle",6), idle2=("Idle_2",11), attack1=("Attack_1",3),
            hurt=("Hurt",5), dead=("Dead",5), run=("Run",10), walk=("Walk",10), jump=("Jump",10),
            special1=("Shot",4), special2=("Recharge",17)),
        [_p("Вуличний боєць", "+8 атаки", bonus_attack=8),
         _a("Постріл у коліно", "Сповільнює ворога на 1 хід", "kneecap_shot")],
    ),
    "gangster_2": Hero(
        "gangster_2", "Гангстер-Бос", "gangster", "rare", "💣",
        "Очолює вулицю. Три пістолі — один стиль.",
        _ac("gangster/2",
            idle=("Idle",7), idle2=("Idle_2",13),
            attack1=("Attack_1",6), attack2=("Attack_2",4), attack3=("Attack_3",6),
            hurt=("Hurt",4), dead=("Dead",5), run=("Run",10), walk=("Walk",10), jump=("Jump",10)),
        [_p("Подвійний пістоль", "+12 атаки, +6% крит", bonus_attack=12, bonus_crit=0.06),
         _p("Броньований жилет", "+8 захисту", bonus_defense=8)],
        base_attack=6,
    ),
    "gangster_3": Hero(
        "gangster_3", "Кілер", "gangster", "epic", "🎯",
        "Найнятий убивця. Одна куля — одна ціль.",
        _ac("gangster/3",
            idle=("Idle",7), idle2=("Idle_2",14), attack1=("Attack",5),
            hurt=("Hurt",4), dead=("Dead",5), run=("Run",10), walk=("Walk",10), jump=("Jump",10),
            special1=("Shot",12), special2=("Recharge",6)),
        [_p("Снайперська підготовка", "+15 атаки, +12% крит", bonus_attack=15, bonus_crit=0.12),
         _p("Холодна кров", "+5% ухилення", bonus_dodge=0.05),
         _a("Постріл між очей", "Критичний удар ×2.5 урону", "headshot")],
        base_attack=10, base_crit=0.06,
    ),

    # ══════════════════════ БЕЗДОМНИЙ ══════════════════════
    "homeless_1": Hero(
        "homeless_1", "Бездомний", "homeless", "common", "🧦",
        "Нічого не втрачав, бо нічого не мав.",
        _ac("homeless/1",
            idle=("Idle",6), idle2=("Idle_2",11), attack1=("Attack_1",5), attack2=("Attack_2",3),
            hurt=("Hurt",3), dead=("Dead",4), run=("Run",8), walk=("Walk",8), jump=("Jump",16),
            special1=("Special",13)),
        [_p("Вуличний інстинкт", "+8% ухилення", bonus_dodge=0.08)],
    ),
    "homeless_2": Hero(
        "homeless_2", "Старий Забіяка", "homeless", "rare", "🪓",
        "Десятиліття виживання. Все іще стоїть.",
        _ac("homeless/2",
            idle=("Idle",7), idle2=("Idle_2",9),
            attack1=("Attack_1",10), attack2=("Attack_2",4), attack3=("Attack_3",4),
            hurt=("Hurt",3), dead=("Dead",4), run=("Run",8), walk=("Walk",8), jump=("Jump",12)),
        [_p("Гарт вулиць", "+10 HP, +6 захисту", bonus_hp=10, bonus_defense=6),
         _p("Брудний удар", "+10 атаки", bonus_attack=10)],
        base_hp=4,
    ),
    "homeless_3": Hero(
        "homeless_3", "Легенда Вулиць", "homeless", "common", "🏚",
        "Міська легенда. Говорять що він безсмертний.",
        _ac("homeless/3",
            idle=("Idle",6), idle2=("Idle_2",11), attack1=("Attack_1",5), attack2=("Attack_2",3),
            hurt=("Hurt",3), dead=("Dead",4), run=("Run",8), walk=("Walk",8), jump=("Jump",16),
            special1=("Special",13)),
        [_p("Незнищенний", "+12 HP", bonus_hp=12)],
        base_hp=6,
    ),

    # ══════════════════════ РЕЙДЕР ══════════════════════
    "raider_1": Hero(
        "raider_1", "Рейдер", "raider", "common", "🪓",
        "Грабує каравани і не соромиться.",
        _ac("raider/1",
            idle=("Idle",6), attack1=("Attack_1",6), attack2=("Attack_2",3),
            hurt=("Hurt",2), dead=("Dead",4), run=("Run",8), walk=("Walk",8), jump=("Jump",11),
            special1=("Shot",12), special2=("Recharge",12)),
        [_p("Груба сила", "+8 атаки", bonus_attack=8),
         _a("Вогняна стріла", "Постріл що підпалює ворога", "fire_arrow")],
    ),
    "raider_2": Hero(
        "raider_2", "Рейдер-Стрілець", "raider", "rare", "🏹",
        "Луків у нього більше, ніж зубів.",
        _ac("raider/2",
            idle=("Idle",8), attack1=("Attack",4),
            hurt=("Hurt",3), dead=("Dead",5), run=("Run",8), walk=("Walk",7), jump=("Jump",7),
            special1=("Shot_1",4), special2=("Shot_2",4)),
        [_p("Подвійний лук", "+10 атаки, +6% крит", bonus_attack=10, bonus_crit=0.06),
         _a("Залп стріл", "Три стрілки — кожна 50% урону", "arrow_volley")],
        base_attack=4,
    ),
    "raider_3": Hero(
        "raider_3", "Ватажок Рейдерів", "raider", "epic", "💀",
        "Веде банду 20 років. Шрами — його медалі.",
        _ac("raider/3",
            idle=("Idle",6), idle2=("Idle_2",5),
            attack1=("Attack_1",5), attack2=("Attack_2",5), attack3=("Attack_3",4),
            hurt=("Hurt",2), dead=("Dead",4), run=("Run",8), walk=("Walk",7), jump=("Jump",8)),
        [_p("Ватажок", "+14 атаки, +8 HP", bonus_attack=14, bonus_hp=8),
         _p("Шрами досвіду", "+10 захисту", bonus_defense=10)],
        base_attack=6,
    ),

    # ══════════════════════ ГОРГОНА ══════════════════════
    "gorgon_1": Hero(
        "gorgon_1", "Горгона", "gorgon", "rare", "🐍",
        "Погляд що скам'янює. Краще не дивитись в очі.",
        _ac("gorgon/Gorgon_1",
            idle=("Idle",7), idle2=("Idle_2",5),
            attack1=("Attack_1",16), attack2=("Attack_2",7), attack3=("Attack_3",10),
            hurt=("Hurt",3), dead=("Dead",3), run=("Run",7), walk=("Walk",13),
            special1=("Special",5)),
        [_p("Зміїна кров", "+12 HP, +5 захисту", bonus_hp=12, bonus_defense=5),
         _a("Паралізуючий погляд", "Заморожує ворога на 1 хід", "petrify")],
        base_hp=6,
    ),
    "gorgon_2": Hero(
        "gorgon_2", "Горгона Отруйна", "gorgon", "epic", "☠",
        "Старша сестра. Отруйний укус смертельний.",
        _ac("gorgon/Gorgon_2",
            idle=("Idle",7), idle2=("Idle_2",5),
            attack1=("Attack_1",16), attack2=("Attack_2",7), attack3=("Attack_3",10),
            hurt=("Hurt",3), dead=("Dead",3), run=("Run",7), walk=("Walk",13),
            special1=("Special",5)),
        [_p("Отруйний укус", "+12 атаки", bonus_attack=12),
         _p("Лускова броня", "+14 захисту", bonus_defense=14),
         _a("Смертельний укус", "Отруює ворога на 4 ходи", "venom_bite")],
        base_attack=6, base_defense=6,
    ),
    "gorgon_3": Hero(
        "gorgon_3", "Цариця Горгон", "gorgon", "legendary", "🌀",
        "Найстарша і найстрашніша. Її погляд — кінець.",
        _ac("gorgon/Gorgon_3",
            idle=("Idle",7), idle2=("Idle_2",5),
            attack1=("Attack_1",16), attack2=("Attack_2",10), attack3=("Attack_3",7),
            hurt=("Hurt",3), dead=("Dead",3), run=("Run",7), walk=("Walk",13),
            special1=("Special",5)),
        [_p("Давня магія", "+18 атаки, +10% крит", bonus_attack=18, bonus_crit=0.10),
         _p("Безсмертна луска", "+18 HP, +18 захисту", bonus_hp=18, bonus_defense=18),
         _a("Аура жаху", "Знижує атаку ворога на 30%", "terror_aura")],
        base_attack=10, base_defense=8, base_hp=8,
    ),

    # ══════════════════════ МІНОТАВР ══════════════════════
    "minotaur_1": Hero(
        "minotaur_1", "Мінотавр", "minotaur", "common", "🐂",
        "Великий і повільний. Але один удар — і все.",
        _ac("minotaur/Minotaur_1",
            idle=("Idle",10), attack1=("Attack",5),
            hurt=("Hurt",3), dead=("Dead",5), walk=("Walk",12)),
        [_p("Бичача сила", "+8 атаки", bonus_attack=8)],
        base_attack=4, base_hp=2,
    ),
    "minotaur_2": Hero(
        "minotaur_2", "Мінотавр Берсерк", "minotaur", "rare", "🔥",
        "Коли лють охоплює — зупинити неможливо.",
        _ac("minotaur/Minotaur_2",
            idle=("Idle",10), attack1=("Attack",5),
            hurt=("Hurt",3), dead=("Dead",5), walk=("Walk",12)),
        [_p("Лють берсерка", "+12 атаки, +5% крит", bonus_attack=12, bonus_crit=0.05)],
        base_attack=6,
    ),
    "minotaur_3": Hero(
        "minotaur_3", "Король Мінотаврів", "minotaur", "epic", "👑",
        "Правитель лабіринту. Тисячолітня міць.",
        _ac("minotaur/Minotaur_3",
            idle=("Idle",10), attack1=("Attack",4),
            hurt=("Hurt",3), dead=("Dead",5), walk=("Walk",12)),
        [_p("Королівська сила", "+20 атаки, +10 HP", bonus_attack=20, bonus_hp=10),
         _p("Непохитність", "+14 захисту", bonus_defense=14)],
        base_attack=10, base_hp=6,
    ),

    # ══════════════════════ СКЕЛЕТ ══════════════════════
    "skeleton_warrior": Hero(
        "skeleton_warrior", "Скелет-Воїн", "skeleton", "common", "💀",
        "Мертвий але не спочиває.",
        _ac("skeleton/Skeleton_Warrior",
            idle=("Idle",7), attack1=("Attack_1",5), attack2=("Attack_2",6), attack3=("Attack_3",4),
            hurt=("Hurt",2), dead=("Dead",4), run=("Run",8), walk=("Walk",7),
            block=("Protect",1), special1=("Run+attack",7)),
        [_p("Кісткова броня", "+8 захисту, +6 HP", bonus_defense=8, bonus_hp=6)],
    ),
    "skeleton_archer": Hero(
        "skeleton_archer", "Скелет-Лучник", "skeleton", "rare", "🏹",
        "Кістяні пальці тримають тятиву вже сотні років.",
        _ac("skeleton/Skeleton_Archer",
            idle=("Idle",7), attack1=("Attack_1",5), attack2=("Attack_2",4), attack3=("Attack_3",3),
            hurt=("Hurt",2), dead=("Dead",5), walk=("Walk",8),
            special1=("Shot_1",15), special2=("Evasion",6)),
        [_p("Кістяний лук", "+12 атаки, +8% крит", bonus_attack=12, bonus_crit=0.08),
         _a("Смертельний дощ", "5 стріл — кожна 40% урону", "bone_rain")],
        base_attack=6, base_crit=0.04,
    ),
    "skeleton_spearman": Hero(
        "skeleton_spearman", "Скелет-Списоносець", "skeleton", "rare", "🏛",
        "Охороняє гробницю тисячу років.",
        _ac("skeleton/Skeleton_Spearman",
            idle=("Idle",7), attack1=("Attack_1",4), attack2=("Attack_2",4),
            hurt=("Hurt",3), dead=("Dead",5), run=("Run",6), walk=("Walk",7),
            block=("Protect",2), special1=("Run+attack",5)),
        [_p("Довгий спис", "+10 атаки", bonus_attack=10),
         _p("Щит гробниці", "+12 захисту", bonus_defense=12)],
        base_defense=6,
    ),

    # ══════════════════════ ВАМПІР ══════════════════════
    "vampire_1": Hero(
        "vampire_1", "Вампір", "vampire", "rare", "🧛",
        "Нічний мисливець. Кров — його сила.",
        _ac("vampire/1",
            idle=("Idle",5), attack1=("Attack_1",5), attack2=("Attack_2",4),
            attack3=("Attack_3",2), special1=("Attack_4",5),
            hurt=("Hurt",2), dead=("Dead",10), run=("Run",6), walk=("Walk",6), jump=("Jump",6)),
        [_p("Випивання крові", "+10 атаки, +8 HP", bonus_attack=10, bonus_hp=8)],
        base_attack=4,
    ),
    "vampire_2": Hero(
        "vampire_2", "Лорд Вампірів", "vampire", "legendary", "🩸",
        "Стародавній. Його крові тисяча років.",
        _ac("vampire/2",
            idle=("Idle",5), attack1=("Attack_1",6), attack2=("Attack_2",3),
            attack3=("Attack_3",1), special1=("Attack_4",6),
            hurt=("Hurt",2), dead=("Dead",8), run=("Run",6), walk=("Walk",6), jump=("Jump",6),
            special2=("Blood_Charge_1",4)),
        [_p("Кров тисячоліть", "+20 атаки, +14 HP", bonus_attack=20, bonus_hp=14),
         _p("Лордська аура", "+12 захисту, +10% крит", bonus_defense=12, bonus_crit=0.10),
         _a("Кривавий заряд", "4-фазова атака з поглинанням HP", "blood_charge")],
        base_attack=12, base_hp=8, base_crit=0.06,
    ),
    "vampire_3": Hero(
        "vampire_3", "Вампір-Захисник", "vampire", "epic", "🛡",
        "Рідкісний вампір що захищає своїх.",
        _ac("vampire/3",
            idle=("Idle",5), attack1=("Attack_1",5), attack2=("Attack_2",3), attack3=("Attack_3",4),
            hurt=("Hurt",1), dead=("Dead",8), run=("Run",8), walk=("Walk",8), jump=("Jump",7),
            block=("Protect",2)),
        [_p("Захист ночі", "+16 захисту, +10 HP", bonus_defense=16, bonus_hp=10),
         _a("Туманна форма", "Стає невразливим на 1 хід", "mist_form")],
        base_defense=8, base_hp=4,
    ),

    # ══════════════════════ ВЕРВОЛЬФ ══════════════════════
    "black_werewolf": Hero(
        "black_werewolf", "Чорний Вервольф", "werewolf", "rare", "🐺",
        "Темрява ночі — його стихія.",
        _ac("werewolf/Black_Werewolf",
            idle=("Idle",8), attack1=("Attack_1",6), attack2=("Attack_2",4), attack3=("Attack_3",5),
            hurt=("Hurt",2), dead=("Dead",2), run=("Run",9), walk=("walk",11), jump=("Jump",11),
            special1=("Run+Attack",7)),
        [_p("Чорна лють", "+12 атаки, +8% крит", bonus_attack=12, bonus_crit=0.08),
         _a("Атака зграї", "Серія з 3 укусів — кожен 70% урону", "pack_attack")],
        base_attack=6,
    ),
    "red_werewolf": Hero(
        "red_werewolf", "Червоний Вервольф", "werewolf", "epic", "🔴",
        "Кров на шерсті — не його. Завжди.",
        _ac("werewolf/Red_Werewolf",
            idle=("Idle",8), attack1=("Attack_1",6), attack2=("Attack_2",4), attack3=("Attack_3",5),
            hurt=("Hurt",2), dead=("Dead",2), run=("Run",9), walk=("Walk",11), jump=("Jump",11),
            special1=("Run+Attack",7)),
        [_p("Криваве шаленство", "+16 атаки при HP < 50%", bonus_attack=16),
         _p("Залізна воля", "+14 HP", bonus_hp=14),
         _a("Шквал кігтів", "5 ударів — кожен 50% урону", "claw_frenzy")],
        base_attack=10, base_hp=4,
    ),
    "white_werewolf": Hero(
        "white_werewolf", "Білий Вервольф", "werewolf", "legendary", "🌕",
        "Альфа усіх вервольфів. Місячна міць.",
        _ac("werewolf/White_Werewolf",
            idle=("Idle",8), attack1=("Attack_1",6), attack2=("Attack_2",4), attack3=("Attack_3",5),
            hurt=("Hurt",2), dead=("Dead",2), run=("Run",9), walk=("Walk",11), jump=("Jump",11),
            special1=("Run+Attack",7)),
        [_p("Місячна сила", "+22 атаки, +14 HP, +12% крит", bonus_attack=22, bonus_hp=14, bonus_crit=0.12),
         _p("Альфа-захист", "+16 захисту, +8% ухилення", bonus_defense=16, bonus_dodge=0.08),
         _a("Завивання місяця", "Подвоює атаку на 2 ходи", "lunar_howl")],
        base_attack=12, base_hp=8, base_defense=6,
    ),

    # ══════════════════════ МАГ ══════════════════════
    "fire_wizard": Hero(
        "fire_wizard", "Вогняний Маг", "wizard", "epic", "🔥",
        "Полум'я підкоряється його волі.",
        _ac("wizard/Fire Wizard",
            idle=("Idle",7), attack1=("Attack_1",4), attack2=("Attack_2",4),
            hurt=("Hurt",3), dead=("Dead",6), run=("Run",8), walk=("Walk",6), jump=("Jump",9),
            special1=("Charge",12), special2=("Fireball",8)),
        [_p("Вогняна аура", "+14 атаки", bonus_attack=14),
         _p("Магічний захист", "+10 захисту", bonus_defense=10),
         _a("Вогняна куля", "150% урону + підпалює ворога", "fireball")],
        base_attack=10,
    ),
    "lightning_mage": Hero(
        "lightning_mage", "Блискавичний Маг", "wizard", "legendary", "⚡",
        "Блискавка б'є де він стоїть.",
        _ac("wizard/Lightning Mage",
            idle=("Idle",7), attack1=("Attack_1",10), attack2=("Attack_2",4),
            hurt=("Hurt",3), dead=("Dead",5), run=("Run",8), walk=("Walk",7), jump=("Jump",8),
            special1=("Charge",10), special2=("Light_ball",7)),
        [_p("Блискавична швидкість", "+20 атаки, +12% крит", bonus_attack=20, bonus_crit=0.12),
         _p("Електрощит", "+12 захисту", bonus_defense=12),
         _a("Блискавичний розряд", "Миттєвий удар блискавкою ×2.5", "lightning_bolt")],
        base_attack=14, base_crit=0.06,
    ),
    "wanderer_mage": Hero(
        "wanderer_mage", "Мандрівний Маг", "wizard", "rare", "🌙",
        "Мандрує між світами. Знає забуті заклинання.",
        _ac("wizard/Wanderer Magican",
            idle=("Idle",8), attack1=("Attack_1",7), attack2=("Attack_2",9),
            hurt=("Hurt",4), dead=("Dead",4), run=("Run",8), walk=("Walk",7), jump=("Jump",8),
            special1=("Charge_1",4), special2=("Magic_sphere",16)),
        [_p("Заборонена магія", "+12 атаки, +8% крит", bonus_attack=12, bonus_crit=0.08),
         _a("Магічна сфера", "Потужна АоЕ атака", "magic_sphere")],
        base_attack=8, base_crit=0.04,
    ),

    # ══════════════════════ ЙОКАЙ ══════════════════════
    "karasu_tengu": Hero(
        "karasu_tengu", "Карасу Тенгу", "yokai", "rare", "🐦",
        "Ворон-демон з гір. Охороняє священні ліси.",
        _ac("yokai/Karasu_tengu",
            idle=("Idle",6), idle2=("Idle_2",5),
            attack1=("Attack_1",6), attack2=("Attack_2",4), attack3=("Attack_3",3),
            hurt=("Hurt",3), dead=("Dead",6), run=("Run",8), walk=("Walk",8), jump=("Jump",15)),
        [_p("Крила вітру", "+12% ухилення", bonus_dodge=0.12),
         _p("Кігті ворона", "+10 атаки", bonus_attack=10)],
        base_dodge=0.04,
    ),
    "kitsune": Hero(
        "kitsune", "Кіцуне", "yokai", "legendary", "🦊",
        "Дев'ятихвостий лис. Стародавня магія вогню.",
        _ac("yokai/Kitsune",
            idle=("Idle",8), idle2=("Idle_2",6),
            attack1=("Attack_1",10), attack2=("Attack_2",10), attack3=("Attack_3",7),
            hurt=("Hurt",2), dead=("Dead",10), run=("Run",8), walk=("Walk",8), jump=("Jump",10),
            special1=("Fire_1",14), special2=("Fire_2",11)),
        [_p("Дев'ять хвостів", "+20 атаки, +14% крит, +10 HP", bonus_attack=20, bonus_crit=0.14, bonus_hp=10),
         _p("Лисяча грація", "+16 захисту, +12% ухилення", bonus_defense=16, bonus_dodge=0.12),
         _a("Лисячий вогонь", "9 вогняних куль — кожна 30% урону", "fox_fire")],
        base_attack=14, base_hp=6, base_defense=8, base_crit=0.08,
    ),
    "yamabushi_tengu": Hero(
        "yamabushi_tengu", "Ямабуші Тенгу", "yokai", "epic", "⛩",
        "Гірський демон-монах. Мудрість і сила в одному.",
        _ac("yokai/Yamabushi_tengu",
            idle=("Idle",6), idle2=("Idle_2",5),
            attack1=("Attack_1",3), attack2=("Attack_2",6), attack3=("Attack_3",4),
            hurt=("Hurt",3), dead=("Dead",6), run=("Run",8), walk=("Walk",8), jump=("Jump",15)),
        [_p("Гірська міць", "+16 атаки, +10 HP", bonus_attack=16, bonus_hp=10),
         _p("Духовний щит", "+14 захисту, +6% парирування", bonus_defense=14, bonus_parry=0.06),
         _a("Духовний удар", "Ігнорує 40% захисту ворога", "spirit_strike")],
        base_attack=10, base_hp=4, base_defense=6,
    ),
}

# ── Групи ─────────────────────────────────────────────────────────────
HERO_GROUPS: dict[str, dict] = {
    "knight":   {"name": "Лицар",     "icon": "⚔",  "variants": ["knight_1", "knight_2", "knight_3"]},
    "samurai":  {"name": "Самурай",   "icon": "🗡",  "variants": ["samurai", "samurai_archer", "samurai_commander"]},
    "ninja":    {"name": "Ніндзя",    "icon": "🌸",  "variants": ["kunoichi", "ninja_monk", "ninja_peasant"]},
    "shinobi":  {"name": "Шінобі",    "icon": "💨",  "variants": ["shinobi_1", "shinobi_2", "shinobi_3"]},
    "gangster": {"name": "Гангстер",  "icon": "🔫",  "variants": ["gangster_1", "gangster_2", "gangster_3"]},
    "homeless": {"name": "Бездомний", "icon": "🧦",  "variants": ["homeless_1", "homeless_2", "homeless_3"]},
    "raider":   {"name": "Рейдер",    "icon": "🪓",  "variants": ["raider_1", "raider_2", "raider_3"]},
    "gorgon":   {"name": "Горгона",   "icon": "🐍",  "variants": ["gorgon_1", "gorgon_2", "gorgon_3"]},
    "minotaur": {"name": "Мінотавр",  "icon": "🐂",  "variants": ["minotaur_1", "minotaur_2", "minotaur_3"]},
    "skeleton": {"name": "Скелет",    "icon": "💀",  "variants": ["skeleton_warrior", "skeleton_archer", "skeleton_spearman"]},
    "vampire":  {"name": "Вампір",    "icon": "🧛",  "variants": ["vampire_1", "vampire_2", "vampire_3"]},
    "werewolf": {"name": "Вервольф",  "icon": "🐺",  "variants": ["black_werewolf", "red_werewolf", "white_werewolf"]},
    "wizard":   {"name": "Маг",       "icon": "🔮",  "variants": ["fire_wizard", "lightning_mage", "wanderer_mage"]},
    "yokai":    {"name": "Йокай",     "icon": "🦊",  "variants": ["karasu_tengu", "kitsune", "yamabushi_tengu"]},
}


# ── Рулетка ───────────────────────────────────────────────────────────
def build_roulette_pool() -> list:
    by_rarity: dict[str, list] = {}
    for hid, h in HEROES.items():
        by_rarity.setdefault(h.rarity, []).append(hid)
    pool = []
    for rar, hids in by_rarity.items():
        w = HERO_RARITY_WEIGHTS[rar] / len(hids)
        for hid in hids:
            pool.append((hid, w))
    return pool

ROULETTE_POOL = build_roulette_pool()

def roll_hero() -> Hero:
    import random
    ids = [p[0] for p in ROULETTE_POOL]
    weights = [p[1] for p in ROULETTE_POOL]
    return HEROES[random.choices(ids, weights=weights, k=1)[0]]