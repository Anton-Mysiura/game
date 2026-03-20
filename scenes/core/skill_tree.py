"""
Сцена дерева навичок.
3 гілки × 5 вузлів. Очки за рівень. Тільки покращення параметрів.
"""
import pygame
from .base import Scene
from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets
from game.skill_tree import SKILL_NODES, BRANCHES, can_unlock, apply_skill_node
from game.save_manager import autosave

# ── Геометрія дерева ──────────────────────────────────────────────
NODE_R      = 36          # радіус вузла
NODE_GAP_X  = 210         # відстань між вузлами по горизонталі
BRANCH_SPACING = 180      # відстань між гілками по вертикалі

# Центри гілок по Y
BRANCH_Y = {
    "strength":  200,
    "endurance": 380,
    "agility":   560,
}
START_X = 130             # X першого вузла

# Кольори стану вузла
CLR_LOCKED    = (60,  55,  50)
CLR_AVAILABLE = (100, 90,  70)
CLR_UNLOCKED  = (50,  40,  30)    # фон буде залитий кольором гілки
CLR_BORDER_LOCKED = (90,  80,  70)
CLR_BORDER_AVAIL  = (200, 180, 100)
CLR_BORDER_DONE   = (255, 215,  0)


def _node_center(branch: str, tier: int):
    return (START_X + (tier - 1) * NODE_GAP_X, BRANCH_Y[branch])


class SkillTreeScene(Scene):

    def __init__(self, game):
        super().__init__(game)

        self.close_btn = Button(SCREEN_WIDTH - 230, 20, 200, 50,
                                "✖ Закрити", lambda: game.pop_scene())

        self._hovered_node: str | None = None
        self._selected_node: str | None = None

        # Поверхня для дерева (підкладка)
        self._bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._bg.fill((0, 0, 0, 160))

        # Кнопка підтвердження
        self._confirm_btn = Button(
            SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 80, 240, 50,
            "★ Вивчити навичку", self._confirm_unlock
        )

    # ── Логіка ────────────────────────────────────────────────────

        # Підключаємо renderer (малювання)
        from scenes.ui.skill_tree_renderer import SkillTreeRenderer
        self._renderer = SkillTreeRenderer(self)
    def _confirm_unlock(self):
        if not self._selected_node:
            return
        if not can_unlock(self.player, self._selected_node):
            return
        self.player.skill_nodes.add(self._selected_node)
        self.player.skill_points -= 1
        apply_skill_node(self.player, self._selected_node)
        autosave(self.player)
        self._selected_node = None

    def _node_at(self, pos) -> str | None:
        mx, my = pos
        for node_id, node in SKILL_NODES.items():
            cx, cy = _node_center(node.branch, node.tier)
            if (mx - cx) ** 2 + (my - cy) ** 2 <= (NODE_R + 6) ** 2:
                return node_id
        return None

    def _node_state(self, node_id: str) -> str:
        """locked | available | unlocked"""
        if node_id in self.player.skill_nodes:
            return "unlocked"
        node = SKILL_NODES[node_id]
        if node.requires and node.requires not in self.player.skill_nodes:
            return "locked"
        return "available"

    # ── Події ─────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.pop_scene()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            self.close_btn.update(mp, True)
            self._confirm_btn.update(mp, True)

            node_id = self._node_at(mp)
            if node_id:
                state = self._node_state(node_id)
                if state == "unlocked":
                    self._selected_node = None
                elif state == "available":
                    self._selected_node = node_id
                else:
                    self._selected_node = None

    def update(self, dt: float):
        mp = pygame.mouse.get_pos()
        self.close_btn.update(mp, False)
        self._confirm_btn.update(mp, False)
        self._hovered_node = self._node_at(mp)

    # ── Малювання ─────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Малювання делеговано до рендерера."""
        self._renderer.draw(screen)