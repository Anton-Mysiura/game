"""
Рендерер для SkillTreeScene.

ТІЛЬКИ малювання — жодної логіки гри тут немає.
Дизайнер може вільно змінювати цей файл.

Логіка гри: scenes/core/skill_tree.py
"""
from scenes.core.elder import CLR_AVAILABLE
from scenes.core.skill_tree import BRANCH_Y, CLR_BORDER_AVAIL, CLR_BORDER_LOCKED, CLR_LOCKED, NODE_R, _node_center
from game.skill_tree import SKILL_NODES
from game.skill_tree import BRANCHES
import pygame
from scenes.ui.base_renderer import BaseRenderer

from ui.components import Button, Panel
from ui.constants import *
from ui.assets import assets


class SkillTreeRenderer(BaseRenderer):
    """
    Малює SkillTreeScene.
    Змінюй цей файл щоб налаштувати вигляд сцени.
    Всі атрибути сцени доступні через self.scene.<attr>
    """

    def draw(self, screen: pygame.Surface):
        screen.blit(self.scene._bg, (0, 0))
        Panel(30, 30, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60, alpha=True).draw(screen)

        self._draw_title(screen)
        self._draw_branches(screen)
        self._draw_nodes(screen)
        self._draw_tooltip(screen)
        self._draw_confirm_btn(screen)
        self.scene.close_btn.draw(screen)

    def _draw_title(self, screen):
        font_big = assets.get_font(FONT_SIZE_HUGE, bold=True)
        font_sm  = assets.get_font(FONT_SIZE_NORMAL)

        title = font_big.render("🌳 Дерево навичок", True, COLOR_GOLD)
        screen.blit(title, (60, 45))

        pts_color = (100, 220, 100) if self.scene.player.skill_points > 0 else COLOR_TEXT_DIM
        pts = font_sm.render(
            f"Очки навичок: {self.scene.player.skill_points}", True, pts_color)
        screen.blit(pts, (SCREEN_WIDTH - 280, 52))

    def _draw_branches(self, screen):
        """Мітки гілок та лінії між вузлами."""
        font = assets.get_font(FONT_SIZE_MEDIUM, bold=True)
        font_sm = assets.get_font(FONT_SIZE_SMALL)

        for branch_id, branch in BRANCHES.items():
            nodes = branch["nodes"]
            clr   = branch["color"]
            by    = BRANCH_Y[branch_id]

            # Назва гілки
            lbl = font.render(f"{branch['icon']} {branch['name']}", True, clr)
            screen.blit(lbl, (40, by - 16))

            # Лінії між вузлами
            for i in range(len(nodes) - 1):
                cx1, cy1 = _node_center(branch_id, i + 1)
                cx2, cy2 = _node_center(branch_id, i + 2)

                n1_done = nodes[i]     in self.scene.player.skill_nodes
                n2_done = nodes[i + 1] in self.scene.player.skill_nodes

                line_clr = clr if (n1_done and n2_done) else (70, 65, 60)
                line_w   = 4 if (n1_done and n2_done) else 2
                pygame.draw.line(screen, line_clr, (cx1 + NODE_R, cy1),
                                 (cx2 - NODE_R, cy2), line_w)

    def _draw_nodes(self, screen):
        font_ico  = assets.get_font(24)
        font_tier = assets.get_font(FONT_SIZE_SMALL)

        for branch_id, branch in BRANCHES.items():
            clr = branch["color"]
            for node_id in branch["nodes"]:
                node  = SKILL_NODES[node_id]
                state = self.scene._node_state(node_id)
                cx, cy = _node_center(branch_id, node.tier)

                is_selected = (node_id == self.scene._selected_node)
                is_hovered  = (node_id == self.scene._hovered_node)

                # Фон вузла
                if state == "unlocked":
                    # Залитий кольором гілки
                    pygame.draw.circle(screen, clr, (cx, cy), NODE_R)
                    pygame.draw.circle(screen, (255, 215, 0), (cx, cy), NODE_R, 3)
                elif state == "available":
                    glow_r = NODE_R + (6 if (is_selected or is_hovered) else 0)
                    pygame.draw.circle(screen, CLR_AVAILABLE, (cx, cy), NODE_R)
                    border = (255, 215, 0) if is_selected else CLR_BORDER_AVAIL
                    pygame.draw.circle(screen, border, (cx, cy), glow_r, 3)
                else:  # locked
                    pygame.draw.circle(screen, CLR_LOCKED, (cx, cy), NODE_R)
                    pygame.draw.circle(screen, CLR_BORDER_LOCKED, (cx, cy), NODE_R, 2)

                # Іконка
                ico_surf = font_ico.render(node.icon, True,
                    (255, 255, 255) if state != "locked" else (90, 85, 80))
                screen.blit(ico_surf, (cx - ico_surf.get_width() // 2,
                                       cy - ico_surf.get_height() // 2))

                # Галочка якщо вивчено
                if state == "unlocked":
                    check = font_tier.render("✓", True, (255, 255, 255))
                    screen.blit(check, (cx + NODE_R - 10, cy - NODE_R + 2))

                # Назва під вузлом
                name_surf = assets.get_font(FONT_SIZE_SMALL).render(
                    node.name, True,
                    (255, 215, 0) if state == "unlocked"
                    else (180, 160, 120) if state == "available"
                    else (80, 75, 70)
                )
                screen.blit(name_surf, (cx - name_surf.get_width() // 2, cy + NODE_R + 4))

    def _draw_tooltip(self, screen):
        """Підказка для наведеного або вибраного вузла."""
        node_id = self.scene._selected_node or self.scene._hovered_node
        if not node_id:
            return
        node  = SKILL_NODES[node_id]
        state = self.scene._node_state(node_id)

        cx, cy = _node_center(node.branch, node.tier)

        lines = [
            (node.name, assets.get_font(FONT_SIZE_MEDIUM, bold=True), COLOR_GOLD),
            (node.desc, assets.get_font(FONT_SIZE_SMALL),             COLOR_TEXT),
        ]

        if state == "unlocked":
            lines.append(("✓ Вже вивчено", assets.get_font(FONT_SIZE_SMALL), (100, 220, 100)))
        elif state == "available":
            if self.scene.player.skill_points > 0:
                lines.append(("Натисни щоб вибрати", assets.get_font(FONT_SIZE_SMALL), (200, 180, 100)))
            else:
                lines.append(("Немає очок навичок", assets.get_font(FONT_SIZE_SMALL), (200, 80, 80)))
        else:
            req = SKILL_NODES.get(node.requires)
            req_name = req.name if req else "?"
            lines.append((f"🔒 Потрібно: {req_name}", assets.get_font(FONT_SIZE_SMALL), (180, 100, 80)))

        # Розміри підказки
        pad  = 10
        widths = [fnt.size(txt)[0] for txt, fnt, _ in lines]
        w = max(widths) + pad * 2
        h = sum(fnt.size(txt)[1] + 4 for txt, fnt, _ in lines) + pad * 2

        # Позиція підказки — збоку від вузла
        tx = cx + NODE_R + 12
        ty = cy - h // 2
        # Не виходити за екран
        if tx + w > SCREEN_WIDTH - 20:
            tx = cx - NODE_R - w - 12
        ty = max(50, min(ty, SCREEN_HEIGHT - h - 50))

        tip_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        tip_surf.fill((20, 18, 15, 220))
        pygame.draw.rect(tip_surf, COLOR_GOLD, tip_surf.get_rect(), 1, border_radius=6)
        screen.blit(tip_surf, (tx, ty))

        y = ty + pad
        for txt, fnt, clr in lines:
            rendered = fnt.render(txt, True, clr)
            screen.blit(rendered, (tx + pad, y))
            y += fnt.size(txt)[1] + 4

    def _draw_confirm_btn(self, screen):
        if not self.scene._selected_node:
            return
        state = self.scene._node_state(self.scene._selected_node)
        if state != "available":
            return
        self.scene._confirm_btn.enabled = self.scene.player.skill_points > 0
        self.scene._confirm_btn.draw(screen)