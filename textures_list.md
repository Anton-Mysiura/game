# Список усіх текстур для гри

**Стиль всіх текстур:** 2D pixel art, dark fantasy, середньовіччя. Палітра темна — чорні/темно-сірі фони, золоті та помаранчеві акценти, глибокі кольори. Роздільна здатність — pixel art без антиаліасингу.

---

## 🗺 ЛОКАЦІЇ (фони сцен)
`assets/textures/locations/`  
Розмір: **1280×720 px**

---

### `main_menu_bg.png`
**Де:** головне меню гри  
**Промт:**
> Pixel art 1280x720 dark fantasy RPG main menu background. A medieval village silhouette at dusk, tall stone castle in the far background, torches flickering along a stone path leading into the distance, dramatic purple and orange sky with clouds, fog creeping along the ground, detailed pixel art style, dark moody atmosphere, no UI elements, no text.

---

### `village.png`
**Де:** сцена села (головний хаб), також використовується для сцени Старійшини  
**Промт:**
> Pixel art 1280x720 dark fantasy RPG village scene background. Cobblestone village square, wooden buildings with warm torch light from windows, central well, blacksmith forge glowing in the background, stone paved road, cloudy sky with stars peeking through, night or late evening atmosphere, rich warm colors contrasting dark surroundings, no characters, no UI.

---

### `forest.png`
**Де:** сцена лісу (вибір ворога)  
**Промт:**
> Pixel art 1280x720 dark fantasy forest scene background. Dense ancient forest with massive twisted dark trees, bioluminescent mushrooms and plants glowing faintly, thick fog near the ground, moonlight filtering through the canopy, eerie mysterious atmosphere, dark greens and deep blues, no characters, no UI.

---

### `forest_battle.png`
**Де:** бойова арена у лісі  
**Промт:**
> Pixel art 1280x720 dark fantasy forest battle arena background. A clearing in a dark forest, fallen logs on the sides, dirt arena floor visible, dark trees surrounding the clearing, dramatic moonlight from above illuminating the center, fog at the edges, battle-ready atmosphere, horizontal composition with clear open space in the middle for sprites.

---

### `ruins.png`
**Де:** сцена руїн (вибір ворога)  
**Промт:**
> Pixel art 1280x720 dark fantasy ancient ruins scene background. Crumbling stone temple pillars, overgrown with dark vines and moss, broken stone floor, mysterious glowing runes on the walls, torches in iron brackets still burning, dark sky with a large moon, ominous purple magical aura in the air, no characters, no UI.

---

### `ruins_free.png` / `ruins` (battle)
**Де:** бойова арена в руїнах  
**Промт:**
> Pixel art 1280x720 dark fantasy ruins battle arena background. Open arena floor made of cracked ancient stone tiles, broken pillars on left and right sides as frame, ruined arches in the background, magical glowing cracks in the floor, dark night sky, dramatic atmospheric lighting, clear horizontal open space in center for fighter sprites.

---

### `tower.png`
**Де:** сцена вежі (вибір ворога)  
**Промт:**
> Pixel art 1280x720 dark fantasy dark tower scene background. Interior of a tall stone tower, stone spiral staircase visible, iron chandeliers with candles casting orange glow, weapon racks on walls, banners with skull emblems, dark stone brick texture, narrow slit windows with moonlight, dungeon atmosphere, no characters, no UI.

---

### `tower_free.png` / `tower` (battle)
**Де:** бойова арена у вежі  
**Промт:**
> Pixel art 1280x720 dark fantasy tower interior battle arena. Large stone hall inside a tower, torch sconces on left and right walls, stone floor with a central dark emblem/crest, stone archways framing the scene, dramatic torchlight casting long shadows, clear open horizontal space in the center for fighter sprites, no characters, no UI.

---

### `dragon_lair.png`
**Де:** лігво дракона (фінальна битва)  
**Промт:**
> Pixel art 1280x720 dark fantasy dragon lair background. Massive volcanic cave interior, rivers of glowing lava on the sides, huge stalactites hanging from the ceiling, bones and treasure scattered on the stone floor, orange-red dramatic glow from the lava, smoke and embers floating in the air, epic and intimidating atmosphere, no characters, no UI.

---

### `workshop.png`
**Де:** майстерня коваля  
**Промт:**
> Pixel art 1280x720 dark fantasy blacksmith workshop background. Stone forge with roaring fire glowing orange-red, anvil and hammers in the foreground area, weapon racks on walls, tools hanging from the ceiling, barrels and crates of materials, warm firelight contrast with cool stone walls, soot and ash on surfaces, no characters, no UI.

---

### `shop.png`
**Де:** крамниця  
**Промт:**
> Pixel art 1280x720 dark fantasy medieval shop interior background. Wooden merchant shelves lined with potions, scrolls and goods, a worn wooden counter at the front, warm candlelight chandeliers, dusty wooden floor, barrels and chests in corners, cozy but slightly rundown atmosphere, rich browns and warm tones, no characters, no UI.

---

### `market.png`
**Де:** чорний ринок  
**Промт:**
> Pixel art 1280x720 dark fantasy black market underground scene background. Dark cellar or underground vault, stone brick walls with cracks, tables covered in mysterious goods under dim lantern light, shadows everywhere, purple and dark teal color palette, suspicious secretive atmosphere, hanging cloth banners with skull symbols, no characters, no UI.

---

## 🧍 ПЕРСОНАЖІ — спрайтшити анімацій
`assets/animations/{folder}/`  
Формат: **горизонтальний spritesheet**, один рядок кадрів  
Розмір кожного кадру: **128×128 px**  
Кадри: записані поруч без пробілів, загальна ширина = 128 × кількість_кадрів

---

### `player/` — Гравець (персонаж 1)
Воїн у сталевому обладунку, меч і щит

| Файл | Кадрів | Промт |
|------|--------|-------|
| `idle.png` | 13 | Pixel art 128x128 per frame, horizontal spritesheet 13 frames, dark fantasy armored warrior standing idle, slight breathing animation, sword at side, steel armor, dark color scheme, transparent background |
| `idle2.png` | 13 | Same character as idle but slightly different idle pose variation, looking around or adjusting grip |
| `attack.png` | 6 | Pixel art 128x128 per frame, 6 frames, armored warrior performing a horizontal sword slash from right to left, full swing animation |
| `attack2.png` | 4 | 4 frames, armored warrior doing an upward diagonal slash attack |
| `attack3.png` | 6 | 6 frames, armored warrior doing a powerful charged overhead smash attack |
| `block.png` | 7 | 7 frames, armored warrior raising shield into block stance, holding position |
| `hit.png` | 4 | 4 frames, armored warrior recoiling from a hit, staggering backward |
| `knocked.png` | 5 | 5 frames, armored warrior being knocked down to the ground, falling animation |
| `jump.png` | 10 | 10 frames, armored warrior jumping upward and landing, full arc animation |
| `walk.png` | 8 | 8 frames, armored warrior walking forward smoothly |

**Загальний промт-шаблон:**
> Pixel art spritesheet, {N} frames of 128x128 pixels each, arranged horizontally in a single row, total width {N*128}x128 pixels. Dark fantasy armored warrior, steel plate armor, sword and shield, dark color palette with gold trim, transparent background (PNG). Animation: {дія}. No gaps between frames, consistent character position across frames.

---

### `character2/` — Персонаж 2
Легкий лучник/розвідник у шкіряній броні

| Файл | Кадрів |
|------|--------|
| `idle.png` | 6 |
| `idle2.png` | 6 |
| `attack.png` | 5 |
| `attack2.png` | 3 |
| `block.png` | 6 |
| `hit.png` | 3 |
| `knocked.png` | 4 |
| `jump.png` | 16 |

**Промт-шаблон:**
> Pixel art spritesheet, {N} frames of 128x128 pixels each, horizontal single row. Dark fantasy rogue/scout character, light leather armor, hood, daggers, dark green and brown palette, transparent background PNG. Animation: {дія}.

---

### `character3/` — Персонаж 3
Маг у мантії з посохом

| Файл | Кадрів |
|------|--------|
| `idle.png` | 7 |
| `idle2.png` | 7 |
| `attack.png` | 10 |
| `attack2.png` | 4 |
| `attack3.png` | 4 |
| `block.png` | 7 |
| `hit.png` | 3 |
| `knocked.png` | 4 |
| `jump.png` | 12 |

**Промт-шаблон:**
> Pixel art spritesheet, {N} frames of 128x128 pixels each, horizontal single row. Dark fantasy mage character, dark purple robes, glowing staff, arcane runes floating around, purple and blue magical aura, transparent background PNG. Animation: {дія}.

---

### `character4/` — Персонаж 4
Важкий берсерк із дворучним мечем

| Файл | Кадрів |
|------|--------|
| `idle.png` | 6 |
| `idle2.png` | 6 |
| `attack.png` | 5 |
| `attack2.png` | 5 |
| `attack3.png` | 4 |
| `block.png` | 6 |
| `hit.png` | 2 |
| `knocked.png` | 4 |
| `jump.png` | 8 |

**Промт-шаблон:**
> Pixel art spritesheet, {N} frames of 128x128 pixels each, horizontal single row. Dark fantasy berserker character, heavy dark iron armor with spikes, massive two-handed greatsword, wild red eyes, fur cloak, dark red and black palette, transparent background PNG. Animation: {дія}.

---

### `enemy/` — Ворог (всі звичайні вороги використовують одну папку)
Універсальний ворог — лицар темряви / скелет-воїн

| Файл | Кадрів |
|------|--------|
| `idle.png` | 13 |
| `idle2.png` | 13 |
| `attack.png` | 6 |
| `attack2.png` | 4 |
| `attack3.png` | 6 |
| `block.png` | 7 |
| `hit.png` | 4 |
| `knocked.png` | 5 |
| `jump.png` | 10 |
| `walk.png` | 8 |

**Промт-шаблон:**
> Pixel art spritesheet, {N} frames of 128x128 pixels each, horizontal single row. Dark fantasy enemy warrior, dark knight or skeleton soldier, black armor with glowing red eyes, rusty sword, menacing aggressive posture, dark grey and red palette, transparent background PNG. Animation: {дія}.

---

## 🐉 ПЕРСОНАЖІ — окремі статичні зображення
`assets/textures/characters/`

---

### `player_idle.png` — 128×128
**Де:** застарілий показ в old battle screen  
**Промт:**
> Pixel art 128x128, dark fantasy armored warrior standing idle, steel plate armor, sword held ready, front-facing view, transparent background PNG.

### `player_attack.png` — 128×128
**Промт:**
> Pixel art 128x128, dark fantasy armored warrior mid sword swing attack, dynamic pose, transparent background PNG.

### `goblin.png` — 128×128
**Де:** іконка/спрайт гобліна у старому battle screen та бестіарії  
**Промт:**
> Pixel art 128x128, dark fantasy goblin enemy, small hunched creature, green-grey skin, wearing scraps of leather armor, holding a rusty knife, aggressive expression, transparent background PNG.

### `orc.png` — 128×128
**Де:** орк у battle screen та бестіарії  
**Промт:**
> Pixel art 128x128, dark fantasy orc warrior, large muscular humanoid, grey-green skin, heavy iron armor, large axe, tusks, aggressive battle stance, transparent background PNG.

### `dark_knight.png` — 128×128
**Де:** темний лицар  
**Промт:**
> Pixel art 128x128, dark fantasy dark knight enemy, full black plate armor with glowing red visor, long dark sword, menacing aura, dark energy effects, transparent background PNG.

### `dragon.png` — 256×256
**Де:** дракон у DragonScene і battle  
**Промт:**
> Pixel art 256x256, dark fantasy dragon, large black and dark red scaled dragon, wings spread, glowing orange eyes, fire breath ember effects, menacing posture facing left, detailed scales, transparent background PNG.

---

## 🎨 UI ЕЛЕМЕНТИ
`assets/textures/ui/`

---

### `button_normal.png` — 200×60
**Промт:**
> Pixel art UI button 200x60, dark fantasy style, dark brown wooden or stone texture button background, gold border frame, slightly embossed look, dark base color, suitable for tiling/stretching horizontally.

### `button_hover.png` — 200×60
**Промт:**
> Same as button_normal but brighter, golden glow on the border, slightly lighter center, hover state UI button, dark fantasy pixel art.

### `button_pressed.png` — 200×60
**Промт:**
> Same as button_normal but slightly darker and inset/depressed look, pressed state UI button, dark fantasy pixel art.

### `panel_dark.png` — 800×600
**Промт:**
> Pixel art UI panel 800x600, dark fantasy background panel, dark stone or dark wood texture, subtle gold corner ornaments, slightly transparent dark overlay feel, seamless tileable inner area, for use as modal/menu background.

### `panel_wood.png` — 600×500
**Промт:**
> Pixel art UI panel 600x500, dark fantasy wooden panel, rich dark walnut wood grain texture, carved gold border ornaments at corners, medieval scroll/tome aesthetic.

### `hp_bar_bg.png` — 400×30
**Промт:**
> Pixel art UI health bar background 400x30, dark stone or dark metal trough shape, slightly recessed, dark grey with subtle texture, for overlaying hp_bar_fill on top.

### `hp_bar_fill.png` — 400×30
**Промт:**
> Pixel art UI health bar fill 400x30, glowing red gradient, bright red center fading to dark red at edges, pulsing health bar fill texture, pixel art style.

### `xp_bar_fill.png` — 600×40
**Промт:**
> Pixel art UI experience bar fill 600x40, glowing blue-purple gradient, bright blue-white center fading to deep purple edges, magical glow feel, pixel art style.

### `gold_coin.png` — 32×32
**Промт:**
> Pixel art 32x32 gold coin icon, dark fantasy style, shiny golden coin with a crown or skull emblem, gold and yellow colors, subtle shine highlight, transparent background PNG.

### `slot_empty.png` — 64×64
**Промт:**
> Pixel art 64x64 inventory slot background, dark fantasy style, dark stone or iron inset frame, slightly recessed center, subtle inner shadow, for item inventory grid slot, transparent or very dark background.

Для генерації добре підійдут: Midjourney (найкращий pixel art), Adobe Firefly (легший контроль стилю), або Stable Diffusion з моделлю pixel-art-xl.
Для спрайтшитів анімацій найлегше генерувати окремі кадри і склеювати — або використати Itch.io готові asset паки у dark fantasy стилі.

Локально на своєму ПК (справді безліміт):

Stable Diffusion (AUTOMATIC1111 або ComfyUI) — встановлюєш один раз, генеруєш скільки хочеш. Потрібна відеокарта від 4GB VRAM. Є моделі спеціально для pixel art (pixel-art-xl, anything-v5)
InvokeAI — те саме, але зручніший інтерфейс

Онлайн без реєстрації/ліміту:

Mage.space — безкоштовний, без ліміту, Stable Diffusion онлайн
Tensor.art — багато безкоштовних кредитів щодня, є pixel art моделі
Craiyon (раніше DALL-E mini) — повністю безкоштовний, але якість слабша

З щоденним лімітом (але відновлюється):

Leonardo.ai — 150 кредитів/день безкоштовно, дуже гарна якість
Bing Image Creator — безкоштовний з Microsoft акаунтом, ~15 швидких генерацій/день потім повільніше але необмежено