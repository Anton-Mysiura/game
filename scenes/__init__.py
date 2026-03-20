"""
scenes — всі екрани гри.

  scenes/core/  — логіка (handle_event, update, on_enter)  ← програмісти
  scenes/ui/    — малювання (*_renderer.py)                 ← дизайнери

Зворотна сумісність збережена — імпортуй як раніше:
    from scenes import VillageScene
"""
from .core import *
