#    **also need to add:**
# (we can do this after presenting tho)

# # win/lose screens with stats
# # an attack animation or something
# # damage animation (could just be sprite flashes white / red) for all


import pygame
import math
import random
import heapq
import asyncio

_p = list(range(256))
random.Random(0).shuffle(_p)
_p += _p
# replaced pnoise 2 with the above cause pnoise2 used c++ and my computer was tweaking tryna download the c++ compiler. the pnoise2 function is defined below

pygame.init()

#for terrain:
TERRAIN_COLORS = {
 "grass": (67, 117, 55),
 "mud": (87, 57, 24),
 "water": (64, 77, 115),
 "rock": (84, 86, 89)
}

WIDTH = 800
HEIGHT = 600
MAP_SIZE = 10 # number of screens
screen = pygame.display.set_mode((WIDTH, HEIGHT))

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


SCALE = 300.0
OCTAVES = random.randint(2, 3)
PERSISTENCE = random.randint(3, 5) / 10
LACUNARITY = random.randint(1, 3)
TILE_SIZE=10
NOISE_W= WIDTH*MAP_SIZE//TILE_SIZE
NOISE_H= HEIGHT*MAP_SIZE//TILE_SIZE

def noise_surface():
   small = pygame.Surface((NOISE_W, NOISE_H))
   arr = pygame.PixelArray(small)
   for y in range(NOISE_H):
       for x in range(NOISE_W):
           n = pnoise2(x*TILE_SIZE/SCALE, y*TILE_SIZE/SCALE, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY)
           if n < -0.3:   type = TERRAIN_COLORS["water"]
           elif n < -0.11: type = TERRAIN_COLORS["mud"]
           elif n < 0.31:  type = TERRAIN_COLORS["grass"]
           else:          type = TERRAIN_COLORS["rock"]
           arr[x, y] = type
   for i in range(NOISE_W):
       arr[i, 0] = TERRAIN_COLORS["rock"]
       arr[i, NOISE_H - 1] = TERRAIN_COLORS["rock"]
   for i in range(NOISE_H):
       arr[0, i] = TERRAIN_COLORS["rock"]
       arr[NOISE_W - 1, i] = TERRAIN_COLORS["rock"]








   del arr
   return pygame.transform.scale(small, (WIDTH*MAP_SIZE, HEIGHT*MAP_SIZE))

noise = noise_surface()

class Enemy: ## class define enemy NPCs  ##  loads sprites once now rather than for each enemy instance
    forward_sprite = pygame.transform.scale(
        pygame.image.load(r"sprites/vampire png/vampire forward.png").convert_alpha(), (50, 50))
    left_sprite = pygame.transform.scale(
        pygame.image.load(r"sprites/vampire png/sideways vampire left.png").convert_alpha(), (50, 50))
    right_sprite = pygame.transform.scale(
        pygame.image.load(r"sprites/vampire png/sideways vampire right.png").convert_alpha(), (50, 50))
    back_sprite = pygame.transform.scale(
        pygame.image.load(r"sprites/vampire png/vampire back.png").convert_alpha(), (50, 50))
   def __init__(self,x, y, hp):
       self.pos = pygame.math.Vector2(x, y)
       self.dir = pygame.math.Vector2(1, 0)
       self.path = []
       self.path_index = 0
       self.path_timer = 0
       self.health = hp
       self.current_state = "Wander"
       self.states = ["Wander", "Chase", "Flee"]
       self.hitbox = pygame.Rect(x - 10, y - 10, 20, 20)
       # sprites ugggghhhh
       self.current_sprite = Enemy.forward_sprite
   def get_hit(self, NPCS, amt = 10):
        self.health = max(0,self.health-amt)
        if self.health <= 0:
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
   def draw(self, screen):
       #pygame.draw.rect(screen, (255, 0, 255), (self.pos.x - camera_x, self.pos.y - camera_y, 20, 20))
       screen.blit(self.current_sprite, (self.pos.x - camera_x - 15, self.pos.y - camera_y - 23))
       self.sprite_upd()
   def fsm(self, player):
     Old = self.current_state
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
     if Old != self.current_state:
          self.path_timer=0
          self.path = []
   def track(self, player, dt, maze):
       self.path_timer -= dt
       if (not self.path) or self.path_timer <= 0:
           goal = self._choose_goal(player, maze)
           if goal is not None:
               self.path = maze.find_path(self.pos, goal)
               self.path_index = 0
               self.path_timer = 0.5 if self.current_state == "Chase" else 2.0
       self._follow_path(dt)
   def _choose_goal(self, player, maze):
       if self.current_state == "Wander": # random tile
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
               return self.pos + d.normalize()*400
           return self.pos + pygame.math.Vector2(400, 0)
       return None
   def _follow_path(self, dt):
       if not self.path or self.path_index >= len(self.path):
           self.path = []
           self.path_index = 0
           return
       target = self.path[self.path_index]
       d = target-self.pos
       speed = {"Wander": 160, "Chase": 205, "Flee": 250}[self.current_state]
       if d.length() <= speed * dt:
           self.pos = pygame.math.Vector2(target)
           self.path_index += 1
           self.hitbox = pygame.Rect(self.pos.x - 10, self.pos.y - 10, 20, 20)
       else:
           self.dir = d.normalize()
           self.pos += self.dir * speed * dt
           self.hitbox = pygame.Rect(self.pos.x - 10, self.pos.y - 10, 20, 20)
   def sprite_upd(self):
       temp = self.dir.normalize()
       if temp.y > 0:
           self.current_sprite = self.forward_sprite
       elif temp.y < 0:
           self.current_sprite = self.back_sprite
       if temp.x > 0:
           self.current_sprite = self.right_sprite
       elif temp.x < 0:
            self.current_sprite = self.left_sprite

#player_movement_tracking_MDP = zeros(9,9,9,9) # this is for 3 context and 2-step prediction. the first step prediction is not relevant though as it only aims two steps ahead anyway, so only the final lcoation needs to be recorded (e.g, left,right and nothing would be recorded the same over 2 steps)
class Player: ## define player
 def __init__(self, x, y, hp):
     self.pos = pygame.math.Vector2(x, y)
     self.dir = pygame.math.Vector2(0, 1)
     self.health = hp
     self.hitbox = pygame.Rect(self.pos.x + 10, self.pos.y + 20, 20, 40)
     self.speed = 200
     self.stamina = 100 #make subtract by 2 for every second shift is held
     self.current_surface = "grass"
     self.garlic_timer = 0
     self.dmg_cd = 100
     self.dmg = 10
     self.range = 100
     self.attack_cd = 5
     self.forward_sprite = pygame.image.load(r"sprites/player/player forward.png").convert_alpha()
     self.forward_sprite = pygame.transform.scale(self.forward_sprite, (50, 50))
     self.left_sprite = pygame.image.load(r"sprites/player/player left.png").convert_alpha()
     self.left_sprite = pygame.transform.scale(self.left_sprite, (50, 50))
     self.right_sprite = pygame.image.load(r"sprites/player/player right.png").convert_alpha()
     self.right_sprite = pygame.transform.scale(self.right_sprite, (50, 50))
     self.back_sprite = pygame.image.load(r"sprites/player/player backward.png").convert_alpha()
     self.back_sprite = pygame.transform.scale(self.back_sprite, (50, 50))
     self.current_sprite = self.forward_sprite
 def get_hit(self, amount = 10):
     self.health = max(0,self.health - amount)
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
             speed_adjust=1.5
             self.stamina = max(0,self.stamina-20*dt)
         else:
             self.stamina = min(100,self.stamina+30*dt)
         self.Walk(dt, speed_adjust)
     if keys[pygame.K_f] and self.attack_cd <= 0:
         targets = list(enemies)
         if boss is not None:
             targets.append(boss)
         self.detect(targets)
         self.attack_cd = 30
   
 def Walk(self, dt, s_a):
     terrains = {"grass": 1.0, "mud": 0.6, "water": 0.4}
     terrain_speed_mult = terrains.get(self.current_surface)
   
     self.pos.x += self.dir.x*self.speed*terrain_speed_mult*s_a*dt
     self.update_surface()
     if self.current_surface == "rock":
      self.pos.x -= self.dir.x*self.speed*terrain_speed_mult*s_a*dt
      self.update_surface()
   
     self.pos.y += self.dir.y*self.speed*terrain_speed_mult*s_a*dt
     self.update_surface()
     if self.current_surface == "rock":
      self.pos.y -= self.dir.y*self.speed*terrain_speed_mult*s_a*dt
      self.update_surface()
 def Apply_GarlicEffect(self):
     pass
 def draw(self):
      #pygame.draw.rect(screen, (255, 255, 255), (self.hitbox.x - camera_x, self.hitbox.y - camera_y, self.hitbox.width, self.hitbox.height))
      screen.blit(self.current_sprite, (self.hitbox.x - camera_x - 15, self.hitbox.y - camera_y - 8))
 def update_surface(self): 
     temp = noise.get_at((int(self.pos.x), int(self.pos.y)))
     match ((temp.r, temp.g, temp.b)):
         case ((84, 86, 89)):
             self.current_surface = "rock" #return "rock"
             #print("rock")
         case ((87, 57, 24)):
             self.current_surface = "mud" #return "mud"
             #print("mud")
         case ((64, 77, 115)):
             self.current_surface = "water"# return "water"
             #print("water")
         case _:
             self.current_surface = "grass"# return "grass"
             #print("grass")
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
         if self.dir.length_squared() == 0:
             continue
         fov = (target.pos-self.pos).normalize()
         if self.dir.dot(fov) >= 0.5:
             self.attack(target)
 def attack(self, other):
     other.health = max(0,other.health-self.dmg)
    

# placeholders:
class MazeGen:
   def __init__(self):
       self.moves = [
           ( 1,  0, 1.0),
           (-1,  0, 1.0),
           ( 0,  1, 1.0),
           ( 0, -1, 1.0),
           ( 1,  1, math.sqrt(2)),
           ( 1, -1, math.sqrt(2)),
           (-1,  1, math.sqrt(2)),
           (-1, -1, math.sqrt(2)),
       ]               #all the moves that can be taken
   def convert_to_tile(self, x, y): # helper methods to convert between world/tile
       return int(x//TILE_SIZE), int(y//TILE_SIZE)
   def convert_from_tile(self, tx, ty):
       return pygame.math.Vector2(tx*TILE_SIZE + TILE_SIZE/2,ty*TILE_SIZE + TILE_SIZE/2)
   def terrain_at(self, tx, ty):
       if not (0 <= tx < NOISE_W and 0 <= ty < NOISE_H):
           return "rock"
       c = noise.get_at((tx * TILE_SIZE + TILE_SIZE // 2,
                         ty * TILE_SIZE + TILE_SIZE // 2))
       rgb = (c.r, c.g, c.b)
       if rgb == TERRAIN_COLORS["rock"]:  return "rock"
       if rgb == TERRAIN_COLORS["water"]: return "water"
       if rgb == TERRAIN_COLORS["mud"]:   return "mud"
       return "grass"
   def not_rock(self, tx, ty):
       return self.terrain_at(tx, ty) != "rock"
   def step_cost(self, tx, ty): # scalars from inverse of speed mult
       t = self.terrain_at(tx, ty)
       return {"grass": 1.0, "mud": 1 / 0.6, "water": 1 / 0.4}.get(t, float("inf"))
   def heuristic(self, a, b): #distances and diagonal too
       dx = abs(a[0] - b[0])
       dy = abs(a[1] - b[1])
       return max(dx, dy) + (math.sqrt(2) - 1)*min(dx, dy)
       #find path is search method vvvvv
   def find_path(self, start_env, aim_env): #returns a lost of vectors. first is next to start, and the last is the tile it's aiming for
       start = self.convert_to_tile(start_env.x, start_env.y)
       aim  = self.convert_to_tile(aim_env.x,  aim_env.y)

       if start == aim:
           return [self.convert_from_tile(aim[0], aim[1])]
       if not self.not_rock(*start) or not self.not_rock(aim[0], aim[1]):
           return []


       open_heap = [(0.0, 0, start)]
       g_score = {start: 0.0}
       came_from= {}
       closed=set()
       counter = 1

       while open_heap:
           current = heapq.heappop(open_heap)[2]
           if current in closed:
               continue
           closed.add(current)

           if current == aim: #reconstruct by going came_from back from aim
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


       return [] # if nothing found return empty list

   def draw(self, screen):
       pass #draw grid

class Markov:
    def __init__(self, order=4, sample_int=0.06, m=4):
        self.order = order
        self.sample_int = sample_int
        self.min_num = m
        self.corpus = []    # moves stored as (dx, dy)
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
        move = (tile[0] - self.prev_tile[0], tile[1] - self.prev_tile[1]) #moves are stored as (dx, dy) over sample interval
        self.prev_tile = tile
        if move == (0, 0) or abs(move[0]) > 1 or abs(move[1]) > 1:  #if movement didnt work it's skipped
            return
        for order in range(1, self.order + 1):
            if len(self.corpus) >= order:
                context = tuple(self.corpus[-order:])
                self.scores[order].setdefault(context, {})
                self.scores[order][context][move] = self.scores[order][context].get(move, 0) + 1
        self.corpus.append(move)
        if len(self.corpus) > 500:
            self.corpus = self.corpus[-500:]
    def _get_dist(self, corpus): # tries longer context then goes down
        for order in range(min(self.order, len(corpus)), 0, -1):
            context = tuple(corpus[-order:])
            arr = self.scores[order].get(context)
            if arr and sum(arr.values()) >= self.min_num:
                total = sum(arr.values())
                return {m: c/total for m, c in arr.items()}
        return None
    def returnPredictions(self, player_pos, maze): #top 10 sorted
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
                    predictions[total] = predictions.get(total, 0) + p1*p2
        results = []
        for (dx, dy), prob in predictions.items():
            tx, ty = cur[0] + dx, cur[1] + dy
            if maze.not_rock(tx, ty):
                results.append(((tx, ty), prob))
        results.sort(key=lambda x: -x[1])
        return results[:10]

class Item:
 def __init__(self, x, y, item_type):
     self.pos = pygame.math.Vector2(x,y)
     self.type = item_type
 
 def draw(self, screen):
     color = ((255, 255, 0) if self.type == "bread" else (0, 255, 255))
     pygame.draw.circle(screen, color, (int(self.pos.x - camera_x), int(self.pos.y - camera_y)), 8)

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
        self.forward_sprite = pygame.image.load(r"sprites/dracula/dracula forward.png").convert_alpha()
        self.forward_sprite = pygame.transform.scale(self.forward_sprite, (75, 75))
        self.left_sprite = pygame.image.load(r"sprites/dracula/dracula left.png").convert_alpha()
        self.left_sprite = pygame.transform.scale(self.left_sprite, (75, 75))
        self.right_sprite = pygame.image.load(r"sprites/dracula/dracula right.png").convert_alpha()
        self.right_sprite = pygame.transform.scale(self.right_sprite, (75, 75))
        self.back_sprite = pygame.image.load(r"sprites/dracula/dracula back.png").convert_alpha()
        self.back_sprite = pygame.transform.scale(self.back_sprite, (75, 75))
        self.current_sprite = self.forward_sprite
    def update(self, player, maze, predictor, dt):
        self.repath_timer -= dt
        if self.repath_timer <= 0:
            self.repath_timer = 0.6 # re-evaluation timer so update if boss is too slow (can make longer if laggy)
            predictions = predictor.returnPredictions(player.pos, maze)
            best_score, best_path, best_tile = -1, None, None
            for (tx, ty), prob in predictions:
                goal_pos = maze.convert_from_tile(tx, ty)
                path = maze.find_path(self.pos, goal_pos)
                if not path:
                    continue
                score = prob/(len(path) + 1)
                if score > best_score:
                    best_score, best_path, best_tile = score, path, (tx, ty)
            if best_path:
                self.path = best_path
                self.path_index = 0
                self.predicted_tile = best_tile
        self._follow_path(dt)
        if self.pos.distance_to(player.pos) < 40:
            player.get_hit(30*dt)

    def _follow_path(self, dt):
        if not self.path or self.path_index >= len(self.path):
            return
        target = self.path[self.path_index]
        d = target - self.pos
        speed = 180
        if d.length() <= speed * dt:
            self.dir = d.normalize() if d.length_squared() > 0 else self.dir # ternary in java still looks better imo
            self.pos = pygame.math.Vector2(target)
            self.path_index += 1
        else:
            self.dir = d.normalize()
            self.pos += self.dir*speed*dt
    def get_hit(self, dmg=10):
        self.health = max(0, self.health - dmg)
    def draw(self, screen):
       # pygame.draw.rect(screen, (200, 0, 0),(self.pos.x - camera_x, self.pos.y - camera_y, 50, 50)) # replace with sprite
        screen.blit(self.current_sprite, (self.pos.x - camera_x - 10, self.pos.y - camera_y - 15))
        self.sprite_upd()
    def sprite_upd(self):
        temp = self.dir.normalize()
        if temp.y > 0:
            self.current_sprite = self.forward_sprite
        elif temp.y < 0:
            self.current_sprite = self.back_sprite
        if temp.x > 0:
            self.current_sprite = self.right_sprite
        elif temp.x < 0:
            self.current_sprite = self.left_sprite 


## main loop:
Clock = pygame.time.Clock()
Font = pygame.font.Font(None, 28)
camera_x = 0
camera_y = 0
running = True
debug_mode = False
game_over = False
game_won = False
night_time = 120.0 # im adding a key to spawn boss in the debug menu
dracula_spawned = False
maze = MazeGen()
while True:
 player = Player(random.randint(100,WIDTH*MAP_SIZE-100),random.randint(100,HEIGHT*MAP_SIZE-100), 100)
 player.update_surface()
 if player.current_surface != "rock":
   break
predictor = Markov()
enemies = []
for i in range(100):
   while True:
       x_i = random.randint(100, WIDTH*MAP_SIZE - 100)
       y_i = random.randint(100, HEIGHT*MAP_SIZE - 100)
       colour = noise.get_at((x_i, y_i))
       if (colour.r, colour.g, colour.b) != TERRAIN_COLORS["rock"]:
           enemies.append(Enemy(x_i, y_i, 30))
           break
items = []
boss = None
# test items
#items.append(Item(200, 200, "bread"))
#items.append(Item(300, 300, "quiver"))
# main loop!!
async def main():
 # dt is seconds btw bcs clock tick does ms
 dt = Clock.tick(60)/1000.0
 for event in pygame.event.get():
     if event.type == pygame.QUIT:
         running = False
     elif event.type == pygame.KEYDOWN:
         if event.key == pygame.K_ESCAPE:
             running = False
         elif event.key == pygame.K_F1:
             debug_mode = not debug_mode # debug mode switching
         #elif event.key == pygame.K_f and not game_over and not game_won:
             # shooting method
          #   print("Player shot bow")
         elif event.key == pygame.K_b and debug_mode and not boss:
             for i in range(50):
                 xi = player.pos.x + random.randint(-300, 300)
                 yi = player.pos.y + random.randint(-300, 300)
                 c = noise.get_at((int(xi), int(yi)))
                 if (c.r, c.g, c.b) != TERRAIN_COLORS["rock"]:
                     boss = Boss(xi, yi)
                     dracula_spawned = True
                     break

        
 keys = pygame.key.get_pressed()
 if not game_over and not game_won:
     player.player_input(keys, dt, enemies, boss) # need to change player to use this

 if not (game_over or game_won):
     night_time -= dt
     if night_time <= 0 and not dracula_spawned:
         print("You idiots haven't caught that human yet!?")
         print("I'm taking matters into my own hands.")
         print("Dracula approaches as the sun rises.")
         boss = Boss(player.pos.x + 100 + random.randint(-200, 200), player.pos.y + 100 + random.randint(-200, 200)) #spawn boss (we should make a random spawning method)
         dracula_spawned = True
     
     player.update() # surface and terrain interaction
   
     camera_x = max(0,min(player.pos.x - WIDTH//2, WIDTH*MAP_SIZE-WIDTH))
     camera_y = max(0,min(player.pos.y - HEIGHT//2, HEIGHT*MAP_SIZE-HEIGHT))


     predictor.recordMoves(player.pos, maze, dt)
 
     for enemy in enemies:
         enemy.fsm(player)
         enemy.track(player, dt, maze) # add enemy death
     enemies = [e for e in enemies if e.health>0]
     if player.health <= 0:
         game_over = True
     if boss:
         boss.update(player, maze, predictor, dt)
         if boss.health <= 0:
             game_won = True

# We once sang/ Retrograde, we'd shake the frame of your car/
# Now I know your name, but not who you are/ It's all okay/
# There ain't a drop of bad blood, it's all my love


##########    rendering:
 screen.fill((0, 0, 0))
 maze.draw(screen)
 screen.blit(noise, (-camera_x, -camera_y))
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
 screen.blit(Font.render(f"HP: {player.health}", True, (255, 255, 255)), (10, 40))
 if debug_mode:
     debug_text = Font.render("debug mode activated (F1)", True, (255, 255, 255))
     player_info = Font.render(f"Current Terrain: {player.current_surface}", True, (255, 255, 255))
     screen.blit(debug_text, (10, 70))
     screen.blit(player_info, (10, 100))
            # # a* visual!!

     for enemy in enemies:
           if len(enemy.path) >= 2:
               points = [(int(p.x - camera_x), int(p.y - camera_y)) for p in enemy.path]
               pygame.draw.lines(screen, (255, 0, 0), False, points, 2)
           screen.blit(Font.render(enemy.current_state, True, (255, 255, 0)), (enemy.pos.x - camera_x, enemy.pos.y - camera_y - 22))
           

     if boss:
         if len(boss.path) >= 2:
             pts = [(int(p.x - camera_x), int(p.y - camera_y)) for p in boss.path]
             pygame.draw.lines(screen, (255, 0, 0), False, pts, 3)
         if boss.predicted_tile:
             tx, ty = boss.predicted_tile
             wx, wy = tx * TILE_SIZE - camera_x, ty * TILE_SIZE - camera_y
             pygame.draw.rect(screen, (255, 255, 0), (wx, wy, TILE_SIZE, TILE_SIZE), 2)
             screen.blit(Font.render("AMBUSH", True, (255, 255, 0)),
                         (wx, wy - 18))
 if game_over:
     screen.blit(Font.render("Game Over. (r.i.p. lmao)", True, (255, 255, 255), (0, 0, 0)), (WIDTH//2 - 150, HEIGHT//2))
 elif game_won:
     screen.blit(Font.render("Dracula hath been slain. good job mh", True, (0, 255, 0)), (WIDTH//2 - 200, HEIGHT//2))
 pygame.display.flip()
pygame.quit()
asyncio.run(main())
