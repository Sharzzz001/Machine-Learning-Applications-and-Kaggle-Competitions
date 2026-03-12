import pygame
import math
from game_state import HexTile

# --- Constants ---
HEX_SIZE = 45
COLORS = {
    "Wood": (34, 139, 34), "Brick": (178, 34, 34), "Sheep": (154, 205, 50),
    "Wheat": (218, 165, 32), "Ore": (112, 128, 144), "Desert": (244, 164, 96),
    "None": (200, 200, 200)
}

# Add this concept to board.py
class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.piece = None # "Settlement" or "City"
        self.owner = None # Player name/color

class Edge:
    def __init__(self, node1, node2):
        self.n1 = node1
        self.n2 = node2
        self.owner = None # Player name/color

class BoardRenderer:
    def __init__(self, surface):
        self.surface = surface
        self.font = pygame.font.SysFont(None, 24)
        self.hex_data = [] # Stores dicts of {rect, tile_obj, center}
        self.resource_cycle = ["Wood", "Brick", "Sheep", "Wheat", "Ore", "Desert", "None"]
        self.number_cycle = [2, 3, 4, 5, 6, 8, 9, 10, 11, 12, None]

    def generate_layout(self, start_x, start_y):
        layout = [
            (0, -2), (1, -2), (2, -2),
            (-1, -1), (0, -1), (1, -1), (2, -1),
            (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
            (-2, 1), (-1, 1), (0, 1), (1, 1),
            (-2, 2), (-1, 2), (0, 2)
        ]
        hex_width = math.sqrt(3) * HEX_SIZE
        hex_height = 2 * HEX_SIZE

        for q, r in layout:
            x = start_x + hex_width * (q + r/2)
            y = start_y + hex_height * (3/4 * r)
            tile = HexTile(q=q, r=r, resource="None")
            self.hex_data.append({"tile": tile, "center": (x, y)})
        return [h["tile"] for h in self.hex_data]

    def draw(self):
        for h in self.hex_data:
            tile = h["tile"]
            cx, cy = h["center"]
            
            # Calculate vertices
            vertices = []
            for i in range(6):
                angle_deg = 60 * i - 30
                angle_rad = math.pi / 180 * angle_deg
                vertices.append((cx + HEX_SIZE * math.cos(angle_rad), cy + HEX_SIZE * math.sin(angle_rad)))
            
            pygame.draw.polygon(self.surface, COLORS[tile.resource], vertices)
            pygame.draw.polygon(self.surface, (0, 0, 0), vertices, 2)

            if tile.number and tile.resource != "Desert":
                text = self.font.render(str(tile.number), True, (0, 0, 0))
                text_rect = text.get_rect(center=(cx, cy))
                
                # Draw white circle behind number
                pygame.draw.circle(self.surface, (255, 255, 255), (cx, cy), 15)
                self.surface.blit(text, text_rect)

    def handle_click(self, pos, button):
        # Button 1 is Left Click (Resource), Button 3 is Right Click (Number)
        for h in self.hex_data:
            cx, cy = h["center"]
            # Simple distance check for clicking inside a hex
            if math.hypot(cx - pos[0], cy - pos[1]) < HEX_SIZE:
                tile = h["tile"]
                if button == 1:
                    idx = (self.resource_cycle.index(tile.resource) + 1) % len(self.resource_cycle)
                    tile.resource = self.resource_cycle[idx]
                elif button == 3:
                    idx = (self.number_cycle.index(tile.number) + 1) % len(self.number_cycle)
                    tile.number = self.number_cycle[idx]