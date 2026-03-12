import pygame
import math
import sys
import random

# --- Configuration & Colors ---
WIDTH, HEIGHT = 1200, 800
HEX_SIZE = 50
SIDEBAR_WIDTH = 350
COLORS = {
    "Wood": (34, 139, 34), "Brick": (178, 34, 34), "Sheep": (154, 205, 50),
    "Wheat": (218, 165, 32), "Ore": (112, 128, 144), "Desert": (244, 164, 96),
    "Water": (30, 144, 255)
}
PLAYER_COLORS = [(255, 50, 50), (50, 50, 255), (255, 255, 50), (240, 240, 240)]
RESOURCE_WEIGHTS = {"Brick": 1.4, "Wood": 1.4, "Wheat": 1.1, "Ore": 1.2, "Sheep": 0.9, "Desert": 0}

class Player:
    def __init__(self, name, color, is_ai=False):
        self.name, self.color, self.is_ai = name, color, is_ai
        self.resources = {"Wood": 0, "Brick": 0, "Sheep": 0, "Wheat": 0, "Ore": 0}
        self.roads_count = 0

    def spend(self, cost):
        for res, amt in cost.items(): self.resources[res] -= amt

class Node:
    def __init__(self, pos):
        self.pos = pos
        self.owner = None 
        self.touching_tiles = []
        self.neighbors = []

class Edge:
    def __init__(self, node_a, node_b):
        self.nodes = (node_a, node_b)
        self.owner = None

class Tile:
    def __init__(self, pos):
        self.pos = pos
        self.resource = "Desert"
        self.number = None

class CatanEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.SysFont("Verdana", 16)
        self.clock = pygame.time.Clock()
        
        self.tiles, self.nodes, self.edges, self.players = [], [], [], []
        self.phase = "SETUP_BOARD"
        self.current_idx = 0
        self.setup_step = 0
        self.draft_order = [0, 1, 2, 2, 1, 0]
        self.placed_settlement = False 
        self.road_mode = False
        self.status_msg = "SETUP: Left Click = Resource | Right Click = Number. Press ENTER to Draft."
        
        self._init_world()

    def _init_world(self):
        layout = [(0,-2),(1,-2),(2,-2), (-1,-1),(0,-1),(1,-1),(2,-1), (-2,0),(-1,0),(0,0),(1,0),(2,0), (-2,1),(-1,1),(0,1),(1,1), (-2,2),(-1,2),(0,2)]
        start_x, start_y = (WIDTH - SIDEBAR_WIDTH) // 2, HEIGHT // 2
        node_map = {}
        edge_set = set()

        for q, r in layout:
            dx = HEX_SIZE * math.sqrt(3) * (q + r/2)
            dy = HEX_SIZE * (3/2 * r)
            center = (start_x + dx, start_y + dy)
            t = Tile(center)
            self.tiles.append(t)
            
            hex_nodes = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                nx, ny = center[0] + HEX_SIZE * math.cos(angle), center[1] + HEX_SIZE * math.sin(angle)
                key = (round(nx, 1), round(ny, 1))
                if key not in node_map: node_map[key] = Node(key)
                node_map[key].touching_tiles.append(t)
                hex_nodes.append(node_map[key])
            
            for i in range(6):
                n1, n2 = hex_nodes[i], hex_nodes[(i+1)%6]
                if n2 not in n1.neighbors: n1.neighbors.append(n2)
                if n1 not in n2.neighbors: n2.neighbors.append(n1)
                pair = tuple(sorted([id(n1), id(n2)]))
                if pair not in edge_set:
                    self.edges.append(Edge(n1, n2))
                    edge_set.add(pair)
        self.nodes = list(node_map.values())

    def get_dots(self, num):
        return {2:1, 12:1, 3:2, 11:2, 4:3, 10:3, 5:4, 9:4, 6:5, 8:5, 7:0, None:0}.get(num, 0)

    def evaluate_node(self, node):
        if node.owner: return 0
        if any(neighbor.owner for neighbor in node.neighbors): return 0
        score = 0
        for t in node.touching_tiles:
            score += self.get_dots(t.number) * RESOURCE_WEIGHTS.get(t.resource, 1.0)
        return score

    def ai_move(self):
        p = self.players[self.current_idx]
        if self.phase == "SETUP_PLACEMENTS":
            if not self.placed_settlement:
                best_node = max(self.nodes, key=lambda n: self.evaluate_node(n))
                best_node.owner = p
                self.placed_settlement = True
                self.status_msg = f"{p.name} (AI) placed settlement."
            else:
                # Road strategy: connect to best neighboring node
                node = next(n for n in self.nodes if n.owner == p and not any(e.owner == p for e in self.edges if n in e.nodes))
                best_edge = max([e for e in self.edges if node in e.nodes], key=lambda e: self.evaluate_node(e.nodes[1] if e.nodes[0] == node else e.nodes[0]))
                best_edge.owner = p
                p.roads_count += 1
                self.next_draft_step()

    def next_draft_step(self):
        self.placed_settlement = False
        self.setup_step += 1
        if self.setup_step >= len(self.draft_order):
            self.phase = "GAME_LOOP"; self.current_idx = 0
            self.status_msg = "Game Started! Use keys 2-9 for Dice."
        else:
            self.current_idx = self.draft_order[self.setup_step]

    def handle_click(self, pos, btn):
        if pos[0] > WIDTH - SIDEBAR_WIDTH: return
        p = self.players[self.current_idx] if self.players else None

        if self.phase == "SETUP_BOARD":
            for t in self.tiles:
                if math.dist(pos, t.pos) < 35:
                    if btn == 1: # Cycle Resource
                        res_list = list(COLORS.keys())[:-1]
                        t.resource = res_list[(res_list.index(t.resource)+1)%len(res_list)]
                    elif btn == 3: # Cycle Numbers
                        nums = [None, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12]
                        cur_idx = nums.index(t.number) if t.number in nums else 0
                        t.number = nums[(cur_idx + 1) % len(nums)]
            return

        if p and p.is_ai: return # Don't allow manual clicks for AI

        # Road Placement
        if self.road_mode or (self.phase == "SETUP_PLACEMENTS" and self.placed_settlement):
            for e in self.edges:
                mid = ((e.nodes[0].pos[0] + e.nodes[1].pos[0])/2, (e.nodes[0].pos[1] + e.nodes[1].pos[1])/2)
                if math.dist(pos, mid) < 25 and e.owner is None: # Increased radius
                    e.owner = p
                    p.roads_count += 1
                    if self.phase == "SETUP_PLACEMENTS": self.next_draft_step()
                    else: self.road_mode = False; self.status_msg = "Road placed."
                    return

        # Settlement Placement
        if self.phase == "SETUP_PLACEMENTS" and not self.placed_settlement:
            for n in self.nodes:
                if math.dist(pos, n.pos) < 20 and self.evaluate_node(n) > 0:
                    n.owner = p
                    self.placed_settlement = True
                    self.status_msg = f"{p.name}: Now place a Road."
                    # Grant resources on 2nd placement
                    if self.setup_step >= 3:
                        for t in n.touching_tiles:
                            if t.resource != "Desert": p.resources[t.resource] += 1
                    return

    def draw(self):
        self.screen.fill(COLORS["Water"])
        for t in self.tiles:
            pts = [(t.pos[0] + HEX_SIZE * math.cos(math.radians(60*i-30)), t.pos[1] + HEX_SIZE * math.sin(math.radians(60*i-30))) for i in range(6)]
            pygame.draw.polygon(self.screen, COLORS[t.resource], pts)
            pygame.draw.polygon(self.screen, (0,0,0), pts, 2)
            if t.number:
                pygame.draw.circle(self.screen, (255,255,255), (int(t.pos[0]), int(t.pos[1])), 18)
                self.screen.blit(self.font.render(str(t.number), True, (0,0,0) if t.number not in [6,8] else (200,0,0)), (t.pos[0]-10, t.pos[1]-10))

        for e in self.edges:
            if e.owner: pygame.draw.line(self.screen, e.owner.color, e.nodes[0].pos, e.nodes[1].pos, 8)

        for n in self.nodes:
            if n.owner:
                pygame.draw.circle(self.screen, n.owner.color, (int(n.pos[0]), int(n.pos[1])), 12)
                pygame.draw.circle(self.screen, (0,0,0), (int(n.pos[0]), int(n.pos[1])), 12, 2)
            elif self.phase != "SETUP_BOARD":
                pygame.draw.circle(self.screen, (200,200,200), (int(n.pos[0]), int(n.pos[1])), 4)

        # Sidebar & Status
        pygame.draw.rect(self.screen, (40,40,40), (WIDTH-SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT))
        y = 20
        for i, p in enumerate(self.players):
            bg = (80,80,80) if i == self.current_idx else (30,30,30)
            pygame.draw.rect(self.screen, bg, (WIDTH-SIDEBAR_WIDTH+10, y, SIDEBAR_WIDTH-20, 90))
            self.screen.blit(self.font.render(f"{p.name} ({'AI' if p.is_ai else 'Human'})", True, p.color), (WIDTH-SIDEBAR_WIDTH+20, y+10))
            res = f"W:{p.resources['Wood']} B:{p.resources['Brick']} S:{p.resources['Sheep']} Wh:{p.resources['Wheat']} O:{p.resources['Ore']}"
            self.screen.blit(self.font.render(res, True, (255,255,255)), (WIDTH-SIDEBAR_WIDTH+20, y+40))
            y += 100
        
        pygame.draw.rect(self.screen, (0,0,0), (0, HEIGHT-40, WIDTH, 40))
        self.screen.blit(self.font.render(self.status_msg, True, (0,255,0)), (20, HEIGHT-30))
        pygame.display.flip()

    def run(self):
        while True:
            curr_p = self.players[self.current_idx] if self.players else None
            if curr_p and curr_p.is_ai:
                pygame.time.delay(500)
                self.ai_move()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN: self.handle_click(event.pos, event.button)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.phase == "SETUP_BOARD":
                        self.players = [Player("Me", PLAYER_COLORS[0]), Player("Opp 1", PLAYER_COLORS[1], True), Player("Opp 2", PLAYER_COLORS[2], True)]
                        self.phase = "SETUP_PLACEMENTS"
                    if self.phase == "GAME_LOOP" and pygame.K_2 <= event.key <= pygame.K_9:
                        val = event.key - pygame.K_0
                        for t in self.tiles:
                            if t.number == val:
                                for n in self.nodes:
                                    if t in n.touching_tiles and n.owner: n.owner.resources[t.resource] += 1
                        self.current_idx = (self.current_idx + 1) % len(self.players)
                        self.status_msg = f"Dice: {val}. Next Turn: {self.players[self.current_idx].name}"

            self.draw(); self.clock.tick(30)

if __name__ == "__main__":
    CatanEngine().run()