# 🎨 Папка з текстурами UI

Сюди кладеш свої PNG файли і прописуєш їх назви в `config/ui.py`.

---

## 📁 Структура

```
assets/textures/ui/
│
├── bg/          ← ФОНИ СЦЕН
│   ├── main_menu_bg.png       (1280×720 рекомендовано)
│   ├── village_bg.png
│   ├── forest_bg.png
│   ├── battle_bg.png
│   └── ...
│
├── button/      ← ТЕКСТУРИ КНОПОК
│   ├── wood_btn.png           (будь-який розмір — масштабується)
│   ├── wood_btn_hover.png
│   ├── wood_btn_pressed.png
│   ├── gold_btn.png
│   └── ...
│
├── panel/       ← ТЕКСТУРИ ПАНЕЛЕЙ / РАМОК
│   ├── panel_dark.png
│   ├── panel_wood.png
│   ├── panel_stone.png
│   └── ...
│
├── icon/        ← UI ІКОНКИ
│   ├── gold_coin.png          (32×32 рекомендовано)
│   ├── heart.png
│   ├── star_xp.png
│   ├── sword_icon.png
│   └── ...
│
└── slot/        ← СЛОТИ ІНВЕНТАРЮ
    ├── slot_empty.png         (64×64 рекомендовано)
    ├── slot_hover.png
    └── slot_selected.png
```

---

## ⚡ Як підключити свій файл

1. Поклади `my_button.png` у `assets/textures/ui/button/`
2. Відкрий `config/ui.py`
3. Знайди потрібний стиль і заміни `None` на `"my_button"`:

```python
BUTTON_STYLES = {
    "default": {
        "normal":  "my_button",        # ← ось тут
        "hover":   "my_button_hover",
        "pressed": "my_button_pressed",
        ...
    }
}
```

4. Запусти гру — кнопки відразу зміняться!

---

## 💡 Поради

- PNG з прозорістю (RGBA) — підтримується повністю
- Файли автоматично масштабуються під розмір кнопки/панелі
- Якщо файл не знайдено — буде кольорова заглушка (гра не зламається)
- Для фонів рекомендується 1280×720 або більше
- Для кнопок — будь-який розмір, але пропорції збережуться краще
  якщо PNG приблизно того ж співвідношення що і кнопка
