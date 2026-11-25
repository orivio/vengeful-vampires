import pygame
import math
import random
import heapq
import asyncio
import traceback

_p = list(range(256))
random.Random(0).shuffle(_p)
_p += _p

# Terrain colors
TERRAIN_COLORS = {
    "grass": (67, 117, 55),
    "mud": (87, 57, 24),
    "water": (64, 77, 115),
    "rock": (84, 86, 89),
}

WIDTH = 800
HEIGHT = 600
MAP_SIZE = 10  # number of screens

SCALE = 300.0
OCTAVES = random.randint(2, 3)
PERSISTENCE = random.randint(3, 5) / 10
LACUNARITY = random.randint(1, 3)
TILE_SIZE = 25
NOISE_W = WIDTH * MAP_SIZE // TILE_SIZE
NOISE_H = HEIGHT * MAP_SIZE // TILE_SIZE

screen = None
noise_small = None
terrain_grid = None
camera_x = 0
camera_y = 0
missing_sprites = []


def load_sprite(path, size, fallback_color=(255, 0, 255)):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except Exception as e:
        print(f"Sprite load failed ({path}): {e}")
        if path not in missing_sprites:
            missing_sprites.append(path)
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill(fallback_color)
        return surf


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(t, a, b):
    return a + t * (b - a)


def _grad(h, x, y):
    u = x if (h & 1) == 0 else -x
    v = y if (h & 2) == 0 else -y
    return u + v


def pnoise2(x, y, octaves=1, persistence=0.5, lacunarity=2.0):
    total = 0.0
    freq = 1.0
    amp = 1.0
    max_val = 0.0
    for _ in range(octaves):
        xi = math.floor(x * freq) & 255
        yi = math.floor(y * freq) & 255
        xf = (x * freq) - math.floor(x * freq)
        yf = (y * freq) - math.floor(y * freq)
        u = _fade(xf)
        v = _fade(yf)
        aa = _p[_p[xi] + yi]
        ab = _p[_p[xi] + yi + 1]
        ba = _p[_p[xi + 1] + yi]
        bb = _p[_p[xi + 1] + yi + 1]
        x1 = _lerp(u, _grad(aa, xf, yf), _grad(ba, xf - 1, yf))
        x2 = _lerp(u, _grad(ab, xf, yf - 1), _grad(bb, xf - 1, yf - 1))
        total += _lerp(v, x1, x2) * amp
        max_val += amp
        amp *= persistence
        freq *= lacunarity
    return total / max_val


async def generate_map(surf, font):
    small = pygame.Surface((NOISE_W, NOISE_H))
    grid = [["grass"] * NOISE_W for _ in range(NOISE_H)]

    for y in range(NOISE_H):
        for x in range(NOISE_W):
            if x == 0 or y == 0 or x == NOISE_W - 1 or y == NOISE_H - 1:
                t_name = "rock"
            else:
                n = pnoise2(
                    x * TILE_SIZE / SCALE,
                    y * TILE_SIZE / SCALE,
                    octaves=OCTAVES,
                    persistence=PERSISTENCE,
                    lacunarity=LACUNARITY,
                )
                if n < -0.3:
                    t_name = "water"
                elif n < -0.11:
                    t_name = "mud"
                elif n < 0.31:
                    t_name = "grass"
                else:
                    t_name = "rock"
            grid[y][x] = t_name
            small.set_at((x, y), TERRAIN_COLORS[t_name])

        if y % 12 == 0:
            pct = int((y / NOISE_H) * 100)
            surf.fill((20, 20, 20))
            surf.blit(
                font.render(f"Generating map... {pct}%", True, (255, 255, 255)),
                (WIDTH // 2 - 110, HEIGHT // 2),
            )
            pygame.display.flip()
            await asyncio.sleep(0)

    return small, grid


def draw_visible_map(surf):
    start_tx = max(0, int(camera_x // TILE_SIZE))
    start_ty = max(0, int(camera_y // TILE_SIZE))
    vis_w = min(NOISE_W - start_tx, WIDTH // TILE_SIZE + 2)
    vis_h = min(NOISE_H - start_ty, HEIGHT // TILE_SIZE + 2)
    sub = noise_small.subsurface((start_tx, start_ty, vis_w, vis_h))
    scaled = pygame.transform.scale(sub, (vis_w * TILE_SIZE, vis_h * TILE_SIZE))
    offset_x = -(camera_x - start_tx * TILE_SIZE)
    offset_y = -(camera_y - start_ty * TILE_SIZE)
    surf.blit(scaled, (offset_x, offset_y))


def random_walkable_pos(margin=100):
    for _ in range(500):
        x = random.randint(margin, WIDTH * MAP_SIZE - margin)
        y = random.randint(margin, HEIGHT * MAP_SIZE - margin)
        tx = max(0, min(x // TILE_SIZE, NOISE_W - 1))
        ty = max(0, min(y // TILE_SIZE, NOISE_H - 1))
        if terrain_grid[ty][tx] != "rock":
            return x, y
    return WIDTH // 2, HEIGHT // 2


class Enemy:
    forward_sprite = None
    left_sprite = None
    right_sprite = None
    back_sprite = None

    @classmethod
    def load_sprites(cls):
        if cls.forward_sprite is None:
            cls.forward_sprite = load_sprite("sprites/vampire png/vampire forward.png", (50, 50), (180, 40, 40))
            cls.left_sprite = load_sprite("sprites/vampire png/sideways vampire left.png", (50, 50), (180, 40, 40))
            cls.right_sprite = load_sprite("sprites/vampire png/sideways vampire right.png", (50, 50), (180, 40, 40))
            cls.back_sprite = load_sprite("sprites/vampire png/vampire back.png", (50, 50), (180, 40, 40))

    def __init__(self, x, y, hp):
        Enemy.load_sprites()
        self.pos = pygame.math.Vector2(x, y)
        self.dir = pygame.math.Vector2(1, 0)
        self.path = []
        self.path_index = 0
        self.path_timer = random.uniform(0.1, 2.5)
        self.health = hp
        self.current_state = "Wander"
        self.states = ["Wander", "Chase", "Flee"]
        self.hitbox = pygame.Rect(x - 10, y - 10, 20, 20)
        self.current_sprite = Enemy.forward_sprite

    def get_hit(self, NPCS, amt=10):
        self.health = max(0, self.health - amt)
        if self.health <= 0 and self in NPCS:
            NPCS.remove(self)

    def detect_Check(self, player_pos):
        dist = self.pos.distance_to(player_pos)
        if dist > 600:
            return False
        if dist < 0.01:
            return True
        dot = self.dir.dot((player_pos - self.pos).normalize())
        if dot <= 0.01:
            return False
        return dist / dot < 400

    def draw(self, surf):
        sx = self.pos.x - camera_x - 15
        sy = self.pos.y - camera_y - 23
        if -60 <= sx <= WIDTH + 60 and -60 <= sy <= HEIGHT + 60:
            surf.blit(self.current_sprite, (sx, sy))
        self.sprite_upd()

    def fsm(self, player):
        old = self.current_state
        if player.garlic_timer > 0:
            self.current_state = "Flee"
        elif self.current_state == "Flee":
            self.current_state = "Wander"
        elif self.current_state == "Wander":
            if self.detect_Check(player.pos):
                self.current_state = "Chase"
        elif self.current_state == "Chase":
            if not self.detect_Check(player.pos):
                self.current_state = "Wander"
        if old != self.current_state:
            self.path_timer = 0
            self.path = []

    def track(self, player, dt, maze, can_repath=True):
        repathed = False
        self.path_timer -= dt
        if can_repath and ((not self.path) or self.path_timer <= 0):
            goal = self._choose_goal(player, maze)
            if goal is not None:
                self.path = maze.find_path(self.pos, goal)
                self.path_index = 0
                self.path_timer = 0.5 if self.current_state == "Chase" else random.uniform(1.5, 2.5)
                repathed = True
        self._follow_path(dt)
        return repathed

    def _choose_goal(self, player, maze):
        if self.current_state == "Wander":
            wx, wy = maze.convert_to_tile(self.pos.x, self.pos.y)
            for _ in range(10):
                xi = wx + random.randint(-8, 8)
                yi = wy + random.randint(-8, 8)
                if maze.not_rock(xi, yi):
                    return maze.convert_from_tile(xi, yi)
            return None
        elif self.current_state == "Chase":
            return player.pos
        elif self.current_state == "Flee":
            d = self.pos - player.pos
            if d.length_squared() > 0:
                return self.pos + d.normalize() * 400
            return self.pos + pygame.math.Vector2(400, 0)
        return None

    def _follow_path(self, dt):
        if not self.path or self.path_index >= len(self.path):
            self.path = []
            self.path_index = 0
            return
        target = self.path[self.path_index]
        d = target - self.pos
        speed = {"Wander": 160, "Chase": 205, "Flee": 250}[self.current_state]
        if d.length() <= speed * dt:
            self.pos = pygame.math.Vector2(target)
            self.path_index += 1
        elif d.length_squared() > 0:
            self.dir = d.normalize()
            self.pos += self.dir * speed * dt
        self.hitbox = pygame.Rect(self.pos.x - 10, self.pos.y - 10, 20, 20)

    def sprite_upd(self):
        if self.dir.length_squared() == 0:
            return
        temp = self.dir.normalize()
        if temp.y > 0:
            self.current_sprite = self.forward_sprite
        elif temp.y < 0:
            self.current_sprite = self.back_sprite
        if temp.x > 0:
            self.current_sprite = self.right_sprite
        elif temp.x < 0:
            self.current_sprite = self.left_sprite


class Player:
    def __init__(self, x, y, hp):
        self.pos = pygame.math.Vector2(x, y)
        self.dir = pygame.math.Vector2(0, 1)
        self.health = hp
        self.hitbox = pygame.Rect(self.pos.x + 10, self.pos.y + 20, 20, 40)
        self.speed = 200
        self.stamina = 100
        self.current_surface = "grass"
        self.garlic_timer = 0
        self.dmg_cd = 100
        self.dmg = 10
        self.range = 100
        self.attack_cd = 5
        self.forward_sprite = load_sprite("sprites/player/player forward.png", (50, 50), (40, 140, 255))
        self.left_sprite = load_sprite("sprites/player/player left.png", (50, 50), (40, 140, 255))
        self.right_sprite = load_sprite("sprites/player/player right.png", (50, 50), (40, 140, 255))
        self.back_sprite = load_sprite("sprites/player/player backward.png", (50, 50), (40, 140, 255))
        self.current_sprite = self.forward_sprite

    def get_hit(self, amount=10):
        self.health = max(0, self.health - amount)
        self.dmg_cd = 20

    def player_input(self, keys, dt, enemies, boss=None):
        direction = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w]:
            direction.y -= 1
            self.current_sprite = self.back_sprite
        if keys[pygame.K_s]:
            direction.y += 1
            self.current_sprite = self.forward_sprite
        if keys[pygame.K_a]:
            direction.x -= 1
            self.current_sprite = self.left_sprite
        if keys[pygame.K_d]:
            direction.x += 1
            self.current_sprite = self.right_sprite
        if direction.length_squared() > 0:
            self.dir = direction.normalize()
            speed_adjust = 1
            if keys[pygame.K_LSHIFT]:
                speed_adjust = 1.5
                self.stamina = max(0, self.stamina - 20 * dt)
            else:
                self.stamina = min(100, self.stamina + 30 * dt)
            self.Walk(dt, speed_adjust)
        if keys[pygame.K_f] and self.attack_cd <= 0:
            targets = list(enemies)
            if boss is not None:
                targets.append(boss)
            self.detect(targets)
            self.attack_cd = 30

    def Walk(self, dt, s_a):
        terrains = {"grass": 1.0, "mud": 0.6, "water": 0.4}
        terrain_speed_mult = terrains.get(self.current_surface, 1.0)

        self.pos.x += self.dir.x * self.speed * terrain_speed_mult * s_a * dt
        self.update_surface()
        if self.current_surface == "rock":
            self.pos.x -= self.dir.x * self.speed * terrain_speed_mult * s_a * dt
            self.update_surface()

        self.pos.y += self.dir.y * self.speed * terrain_speed_mult * s_a * dt
        self.update_surface()
        if self.current_surface == "rock":
            self.pos.y -= self.dir.y * self.speed * terrain_speed_mult * s_a * dt
            self.update_surface()

    def Apply_GarlicEffect(self):
        pass

    def draw(self):
        screen.blit(self.current_sprite, (self.hitbox.x - camera_x - 15, self.hitbox.y - camera_y - 8))

    def update_surface(self):
        tx = max(0, min(int(self.pos.x // TILE_SIZE), NOISE_W - 1))
        ty = max(0, min(int(self.pos.y // TILE_SIZE), NOISE_H - 1))
        self.current_surface = terrain_grid[ty][tx]

    def update(self):
        self.update_surface()
        self.hitbox.left = self.pos.x - 5
        self.hitbox.top = self.pos.y - 10
        self.dmg_cd -= 1
        self.attack_cd -= 1

    def detect(self, targets):
        for target in targets[:]:
            dist = self.pos.distance_to(target.pos)
            if dist > self.range:
                continue
            if dist < 0.01:
                self.attack(target)
                continue
            if self.dir.length_squared() == 0:
                continue
            fov = (target.pos - self.pos).normalize()
            if self.dir.dot(fov) >= 0.5:
                self.attack(target)

    def attack(self, other):
        other.health = max(0, other.health - self.dmg)


class MazeGen:
    def __init__(self):
        self.moves = [
            (1, 0, 1.0),
            (-1, 0, 1.0),
            (0, 1, 1.0),
            (0, -1, 1.0),
            (1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)),
            (-1, -1, math.sqrt(2)),
        ]

    def convert_to_tile(self, x, y):
        return int(x // TILE_SIZE), int(y // TILE_SIZE)

    def convert_from_tile(self, tx, ty):
        return pygame.math.Vector2(tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)

    def terrain_at(self, tx, ty):
        if not (0 <= tx < NOISE_W and 0 <= ty < NOISE_H):
            return "rock"
        return terrain_grid[ty][tx]

    def not_rock(self, tx, ty):
        return self.terrain_at(tx, ty) != "rock"

    def step_cost(self, tx, ty):
        t = self.terrain_at(tx, ty)
        return {"grass": 1.0, "mud": 1 / 0.6, "water": 1 / 0.4}.get(t, float("inf"))

    def heuristic(self, a, b):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)

    def find_path(self, start_env, aim_env, max_nodes=400):
        start = self.convert_to_tile(start_env.x, start_env.y)
        aim = self.convert_to_tile(aim_env.x, aim_env.y)

        if start == aim:
            return [self.convert_from_tile(aim[0], aim[1])]
        if not self.not_rock(*start) or not self.not_rock(aim[0], aim[1]):
            return []

        open_heap = [(0.0, 0, start)]
        g_score = {start: 0.0}
        came_from = {}
        closed = set()
        counter = 1

        while open_heap and len(closed) < max_nodes:
            current = heapq.heappop(open_heap)[2]
            if current in closed:
                continue
            closed.add(current)

            if current == aim:
                path = []
                while current in came_from:
                    path.append(self.convert_from_tile(*current))
                    current = came_from[current]
                path.reverse()
                return path

            cx, cy = current
            for dx, dy, base_cost in self.moves:
                nx, ny = cx + dx, cy + dy
                if not self.not_rock(nx, ny):
                    continue
                if dx != 0 and dy != 0:
                    if not self.not_rock(cx + dx, cy) or not self.not_rock(cx, cy + dy):
                        continue

                neighbor = (nx, ny)
                if neighbor in closed:
                    continue

                tentative_g = g_score[current] + base_cost * self.step_cost(nx, ny)
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self.heuristic(neighbor, aim)
                    heapq.heappush(open_heap, (f, counter, neighbor))
                    counter += 1

        return []

    def draw(self, surf):
        pass


class Markov:
    def __init__(self, order=4, sample_int=0.06, m=4):
        self.order = order
        self.sample_int = sample_int
        self.min_num = m
        self.corpus = []
        self.scores = {i: {} for i in range(1, order + 1)}
        self.prev_tile = None
        self.sample_timer = 0

    def recordMoves(self, player_pos, maze, dt):
        self.sample_timer += dt
        if self.sample_timer < self.sample_int:
            return
        self.sample_timer = 0
        tile = maze.convert_to_tile(player_pos.x, player_pos.y)
        if self.prev_tile is None:
            self.prev_tile = tile
            return
        move = (tile[0] - self.prev_tile[0], tile[1] - self.prev_tile[1])
        self.prev_tile = tile
        if move == (0, 0) or abs(move[0]) > 1 or abs(move[1]) > 1:
            return
        for order in range(1, self.order + 1):
            if len(self.corpus) >= order:
                context = tuple(self.corpus[-order:])
                self.scores[order].setdefault(context, {})
                self.scores[order][context][move] = self.scores[order][context].get(move, 0) + 1
        self.corpus.append(move)
        if len(self.corpus) > 500:
            self.corpus = self.corpus[-500:]

    def _get_dist(self, corpus):
        for order in range(min(self.order, len(corpus)), 0, -1):
            context = tuple(corpus[-order:])
            arr = self.scores[order].get(context)
            if arr and sum(arr.values()) >= self.min_num:
                total = sum(arr.values())
                return {m: c / total for m, c in arr.items()}
        return None

    def returnPredictions(self, player_pos, maze):
        if not self.corpus:
            return []
        cur = maze.convert_to_tile(player_pos.x, player_pos.y)
        dist1 = self._get_dist(self.corpus)
        if not dist1:
            return []
        predictions = {}
        for move1, p1 in dist1.items():
            dist2 = self._get_dist(self.corpus + [move1])
            if not dist2:
                predictions[move1] = predictions.get(move1, 0) + p1
            else:
                for move2, p2 in dist2.items():
                    total = (move1[0] + move2[0], move1[1] + move2[1])
                    predictions[total] = predictions.get(total, 0) + p1 * p2
        results = []
        for (dx, dy), prob in predictions.items():
            tx, ty = cur[0] + dx, cur[1] + dy
            if maze.not_rock(tx, ty):
                results.append(((tx, ty), prob))
        results.sort(key=lambda x: -x[1])
        return results[:10]


class Item:
    def __init__(self, x, y, item_type):
        self.pos = pygame.math.Vector2(x, y)
        self.type = item_type

    def draw(self, surf):
        color = (255, 255, 0) if self.type == "bread" else (0, 255, 255)
        pygame.draw.circle(surf, color, (int(self.pos.x - camera_x), int(self.pos.y - camera_y)), 8)


class Boss:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.health = 450
        self.state = "Ambush"
        self.path = []
        self.path_index = 0
        self.repath_timer = 0
        self.predicted_tile = None
        self.dir = pygame.math.Vector2(1, 0)
        self.forward_sprite = load_sprite("sprites/dracula/dracula forward.png", (75, 75), (150, 0, 180))
        self.left_sprite = load_sprite("sprites/dracula/dracula left.png", (75, 75), (150, 0, 180))
        self.right_sprite = load_sprite("sprites/dracula/dracula right.png", (75, 75), (150, 0, 180))
        self.back_sprite = load_sprite("sprites/dracula/dracula back.png", (75, 75), (150, 0, 180))
        self.current_sprite = self.forward_sprite

    def update(self, player, maze, predictor, dt):
        self.repath_timer -= dt
        if self.repath_timer <= 0:
            self.repath_timer = 0.6
            predictions = predictor.returnPredictions(player.pos, maze)
            best_score, best_path, best_tile = -1, None, None
            for (tx, ty), prob in predictions:
                goal_pos = maze.convert_from_tile(tx, ty)
                path = maze.find_path(self.pos, goal_pos)
                if not path:
                    continue
                score = prob / (len(path) + 1)
                if score > best_score:
                    best_score, best_path, best_tile = score, path, (tx, ty)
            if best_path:
                self.path = best_path
                self.path_index = 0
                self.predicted_tile = best_tile
        self._follow_path(dt)
        if self.pos.distance_to(player.pos) < 40:
            player.get_hit(30 * dt)

    def _follow_path(self, dt):
        if not self.path or self.path_index >= len(self.path):
            return
        target = self.path[self.path_index]
        d = target - self.pos
        speed = 180
        if d.length() <= speed * dt:
            if d.length_squared() > 0:
                self.dir = d.normalize()
            self.pos = pygame.math.Vector2(target)
            self.path_index += 1
        elif d.length_squared() > 0:
            self.dir = d.normalize()
            self.pos += self.dir * speed * dt

    def get_hit(self, dmg=10):
        self.health = max(0, self.health - dmg)

    def draw(self, surf):
        surf.blit(self.current_sprite, (self.pos.x - camera_x - 10, self.pos.y - camera_y - 15))
        self.sprite_upd()

    def sprite_upd(self):
        if self.dir.length_squared() == 0:
            return
        temp = self.dir.normalize()
        if temp.y > 0:
            self.current_sprite = self.forward_sprite
        elif temp.y < 0:
            self.current_sprite = self.back_sprite
        if temp.x > 0:
            self.current_sprite = self.right_sprite
        elif temp.x < 0:
            self.current_sprite = self.left_sprite


def spawn_boss_near(player):
    for _ in range(50):
        xi = max(0, min(int(player.pos.x + random.randint(-300, 300)), WIDTH * MAP_SIZE - 1))
        yi = max(0, min(int(player.pos.y + random.randint(-300, 300)), HEIGHT * MAP_SIZE - 1))
        tx = max(0, min(xi // TILE_SIZE, NOISE_W - 1))
        ty = max(0, min(yi // TILE_SIZE, NOISE_H - 1))
        if terrain_grid[ty][tx] != "rock":
            return Boss(xi, yi)
    return Boss(player.pos.x, player.pos.y)


async def show_crash(surf, font, err_text):
    lines = err_text.splitlines()[-18:]
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        surf.fill((30, 0, 0))
        y = 15
        for line in lines:
            surf.blit(font.render(line[:85], True, (255, 180, 180)), (10, y))
            y += 26
        pygame.display.flip()
        await asyncio.sleep(0)


async def main():
    global screen, noise_small, terrain_grid, camera_x, camera_y

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    Clock = pygame.time.Clock()
    Font = pygame.font.Font(None, 28)
    SmallFont = pygame.font.Font(None, 22)

    try:
        screen.fill((20, 20, 20))
        screen.blit(Font.render("Starting...", True, (255, 255, 255)), (WIDTH // 2 - 50, HEIGHT // 2))
        pygame.display.flip()
        await asyncio.sleep(0)

        noise_small, terrain_grid = await generate_map(screen, Font)
        maze = MazeGen()

        camera_x = 0
        camera_y = 0
        running = True
        debug_mode = False
        game_over = False
        game_won = False
        night_time = 120.0
        dracula_spawned = False

        px, py = random_walkable_pos()
        player = Player(px, py, 100)
        player.update_surface()

        predictor = Markov()
        enemies = []
        for _ in range(100):
            ex, ey = random_walkable_pos()
            enemies.append(Enemy(ex, ey, 30))

        items = []
        boss = None

        while running:
            dt = min(Clock.tick(60) / 1000.0, 0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F1:
                        debug_mode = not debug_mode
                    elif event.key == pygame.K_b and debug_mode and not boss:
                        boss = spawn_boss_near(player)
                        dracula_spawned = True

            keys = pygame.key.get_pressed()
            if not game_over and not game_won:
                player.player_input(keys, dt, enemies, boss)

            if not (game_over or game_won):
                night_time -= dt
                if night_time <= 0 and not dracula_spawned:
                    print("You idiots haven't caught that human yet!?")
                    print("I'm taking matters into my own hands.")
                    print("Dracula approaches as the sun rises.")
                    boss = spawn_boss_near(player)
                    dracula_spawned = True

                player.update()

                camera_x = max(0, min(player.pos.x - WIDTH // 2, WIDTH * MAP_SIZE - WIDTH))
                camera_y = max(0, min(player.pos.y - HEIGHT // 2, HEIGHT * MAP_SIZE - HEIGHT))

                predictor.recordMoves(player.pos, maze, dt)

                repath_budget = 4
                for enemy in enemies:
                    enemy.fsm(player)
                    if enemy.track(player, dt, maze, can_repath=(repath_budget > 0)):
                        repath_budget -= 1
                enemies = [e for e in enemies if e.health > 0]
                if player.health <= 0:
                    game_over = True
                if boss:
                    boss.update(player, maze, predictor, dt)
                    if boss.health <= 0:
                        game_won = True

            # Rendering
            screen.fill((0, 0, 0))
            draw_visible_map(screen)
            for item in items:
                item.draw(screen)
            for enemy in enemies:
                enemy.draw(screen)
                if player.hitbox.colliderect(enemy.hitbox) and player.dmg_cd <= 0:
                    player.get_hit()
            if boss:
                boss.draw(screen)
            player.draw()
            screen.blit(Font.render(f"Time until dawn: {max(0, int(night_time))}s", True, (255, 255, 255)), (10, 10))
            screen.blit(Font.render(f"HP: {int(player.health)}", True, (255, 255, 255)), (10, 40))

            if missing_sprites:
                screen.blit(
                    SmallFont.render(f"Missing sprite(s): {missing_sprites[0]}", True, (255, 220, 80)),
                    (10, HEIGHT - 28),
                )

            if debug_mode:
                debug_text = Font.render("debug mode activated (F1)", True, (255, 255, 255))
                player_info = Font.render(f"Current Terrain: {player.current_surface}", True, (255, 255, 255))
                screen.blit(debug_text, (10, 70))
                screen.blit(player_info, (10, 100))

                for enemy in enemies:
                    if len(enemy.path) >= 2:
                        points = [(int(p.x - camera_x), int(p.y - camera_y)) for p in enemy.path]
                        pygame.draw.lines(screen, (255, 0, 0), False, points, 2)
                    screen.blit(
                        Font.render(enemy.current_state, True, (255, 255, 0)),
                        (enemy.pos.x - camera_x, enemy.pos.y - camera_y - 22),
                    )

                if boss:
                    if len(boss.path) >= 2:
                        pts = [(int(p.x - camera_x), int(p.y - camera_y)) for p in boss.path]
                        pygame.draw.lines(screen, (255, 0, 0), False, pts, 3)
                    if boss.predicted_tile:
                        tx, ty = boss.predicted_tile
                        wx, wy = tx * TILE_SIZE - camera_x, ty * TILE_SIZE - camera_y
                        pygame.draw.rect(screen, (255, 255, 0), (wx, wy, TILE_SIZE, TILE_SIZE), 2)
                        screen.blit(Font.render("AMBUSH", True, (255, 255, 0)), (wx, wy - 18))

            if game_over:
                screen.blit(
                    Font.render("Game Over. (r.i.p. lmao)", True, (255, 255, 255), (0, 0, 0)),
                    (WIDTH // 2 - 150, HEIGHT // 2),
                )
            elif game_won:
                screen.blit(
                    Font.render("Dracula hath been slain. good job mh", True, (0, 255, 0)),
                    (WIDTH // 2 - 200, HEIGHT // 2),
                )

            pygame.display.flip()
            await asyncio.sleep(0)

    except Exception:
        err = traceback.format_exc()
        print(err)
        await show_crash(screen, SmallFont, err)

    pygame.quit()


asyncio.run(main())
