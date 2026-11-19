
# #fix interactions
# # implement death n allat
# # fix FOV, speed, and player tracking problems


# # stuff I'm doing: 
# # boss n allat
# # # i need to do mdp can ygs work on the rest of the game in the meantime maybe even js ship a playable version rn for the github link so we have something while i keep working on the boss (we can add the sprites for our final version)






import pygame
import math
import random
from noise import pnoise2
import heapq


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


SCALE = 300.0
OCTAVES = random.randint(2, 3)
PERSISTENCE = random.randint(3, 5) / 10
LACUNARITY = random.randint(1, 3)
TILE_SIZE=40
NOISE_W= WIDTH*MAP_SIZE//TILE_SIZE
NOISE_H= HEIGHT*MAP_SIZE//TILE_SIZE
def noise_surface():
    small = pygame.Surface((NOISE_W, NOISE_H))
    arr = pygame.PixelArray(small)
    for y in range(NOISE_H):
        for x in range(NOISE_W):
            n = pnoise2(x*TILE_SIZE/SCALE, y*TILE_SIZE/SCALE, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY)
            if n < -0.3:   type = TERRAIN_COLORS["water"]
            elif n < -0.1: type = TERRAIN_COLORS["mud"]
            elif n < 0.3:  type = TERRAIN_COLORS["grass"]
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


class Enemy: ## class define enemy NPCs
    def __init__(self,x, y, hp):
        self.pos = pygame.math.Vector2(x, y)
        self.dir = pygame.math.Vector2(1, 0)
        self.path = []
        self.path_index = 0
        self.path_timer = 0
        self.health = hp
        self.current_state = "Wander"
        self.states = ["Wander", "Chase", "Flee"]
    def get_hit(self, NPCS):
         self.health = max(0,self.health-10)
         if self.health <= 0:
              NPCS.remove(self)
    def check_is_dead(self):
          if self.health <= 0:
            pass
    def detect_Check(self, player_pos):
        if self.pos.distance_to(player_pos) > 250: return False
        dir = (player_pos - self.pos).normalize()
        return self.dir.dot(dir) >= 0.7071 #60 degree FOV
    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 255), (self.pos.x - camera_x, self.pos.y - camera_y, 20, 20))
    def fsm(self, player):
      if player.garlic_timer > 0:
           self.current_state = "Flee"
           return
      if self.current_state == "Flee":
           self.current_state = "Wander"
           return
      if self.current_state == "Wander":
           if self.detect_Check(player.pos):
               self.current_state = "Chase"
      elif self.current_state == "Chase":
           if not self.detect_Check(player.pos):
               self.current_state = "Wander"
           return
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
            for i in range(10):                       #avoid rock
                xi = wx + random.randint(-8, 8)
                yi = wy + random.randint(-8, 8)
                if maze.not_rock(xi, yi):
                    return maze.convert_from_tile(xi, yi)
            return None  #if 10 tries are rock give up
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
        speed = {"Wander": 160, "Chase": 300, "Flee": 320}[self.current_state]
        if d.length() <= speed * dt:
            self.pos = pygame.math.Vector2(target)
            self.path_index += 1
        else:
            self.dir = d.normalize()
            self.pos += self.dir * speed * dt




#player_movement_tracking_MDP = zeros(9,9,9,9) # this is for 3 context and 2-step prediction. the first step prediction is not relevant though as it only aims two steps ahead anyway, so only the final lcoation needs to be recorded (e.g, left,right and nothing would be recorded the same over 2 steps)
class Player: ## define player
  def __init__(self, x, y, hp):
      self.pos = pygame.math.Vector2(x, y)
      self.dir = pygame.math.Vector2(0, 0)
      self.health = hp
      self.hitbox = pygame.Rect(self.pos.x + 10, self.pos.y + 20, 20, 40)
      self.speed = 200
      self.stamina = 100 #make subtract by 2 for every second shift is held
      self.current_surface = "grass"
      self.garlic_timer = 0
    # self.cam =
  def get_hit(self, amount = 10):
      self.health = max(0,self.health - 10)
  def player_input(self, keys, dt):
      direction = pygame.math.Vector2(0, 0)
      if keys[pygame.K_w]: direction.y -= 1
      if keys[pygame.K_s]: direction.y += 1
      if keys[pygame.K_a]: direction.x -= 1
      if keys[pygame.K_d]: direction.x += 1
      if direction.length_squared() > 0:
          self.dir = direction.normalize()
          speed_adjust = 1
          if keys[pygame.K_LSHIFT]:
              speed_adjust=1.5
              self.stamina = max(0,self.stamina-20*dt)
          else:
              self.stamina = min(100,self.stamina+30*dt)
          self.Walk(dt, speed_adjust)
      
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
       pygame.draw.rect(screen, (255, 255, 255), (self.hitbox.x - camera_x, self.hitbox.y - camera_y, self.hitbox.width, self.hitbox.height))
  def update_surface(self): #could use some work, like implementing the hitbox instead of player coords
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
  def __init__(self):
      pass
  def recordMoves(self, player_pos):
      pass # object storing player movement history
  def returnPredictions(self):
      return [] # needs to return predicted cells


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
      self.hp = 100
      self.state = "Ambush"
  def update(self, player, maze, predictor, dt):
      pass # markov/a* logic here
  def get_hit(self, dmg=10):
      self.hp = max(0,self.hp-dmg)
  def draw(self, screen):
      pygame.draw.rect(screen, (200, 0, 0), (self.pos.x - camera_x, self.pos.y - camera_y, 50, 50)) #replace with sprite


## main loop:
Clock = pygame.time.Clock()
Font = pygame.font.SysFont("Arial", 24)


camera_x = 0
camera_y = 0


running = True
debug_mode = False
game_over = False
game_won = False
night_time = 360.0 # 6 minutes? yup
dracula_spawned = False


maze = MazeGen()
while True:
  player = Player(random.randint(100,WIDTH*MAP_SIZE-100),random.randint(100,HEIGHT*MAP_SIZE-100), 100)
  player.update_surface()
  if player.current_surface != "rock":
    break
predictor = Markov()
enemies = []
for i in range(3):
    while True:
        x_i = player.pos.x + 100 #random.randint(100, WIDTH*MAP_SIZE - 100)
        y_i = player.pos.y + 100#TEMPORARY COMMENT FOR DEBUG#random.randint(100, HEIGHT*MAP_SIZE - 100)
        colour = noise.get_at((x_i, y_i))
        if (colour.r, colour.g, colour.b) != TERRAIN_COLORS["rock"]:
            enemies.append(Enemy(x_i, y_i, 30))
            break
items = []
boss = None


# test items
items.append(Item(200, 200, "bread"))
items.append(Item(300, 300, "quiver"))


# main loop!!
while running:
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
          elif event.key == pygame.K_f and not game_over and not game_won:
              # shooting method
              print("Player shot bow")
           
  keys = pygame.key.get_pressed()
  if not game_over and not game_won:
      player.player_input(keys, dt) # need to change player to use this


  if not (game_over or game_won):
      night_time -= dt
      if night_time <= 0 and not dracula_spawned:
          print("Come on. You idiots haven't caught that human yet!?")
          print("I'm taking matters into my own hands.")
          print("Dracula approaches as the sun rises.")
          boss = Boss(player.pos.x + 100, player.pos.y + 100) #spawn boss (we should make a random spawning method)
          dracula_spawned = True
       
      player.update() # surface and terrain interaction
      
      camera_x = max(0,min(player.pos.x - WIDTH//2, WIDTH*MAP_SIZE-WIDTH))
      camera_y = max(0,min(player.pos.y - HEIGHT//2, HEIGHT*MAP_SIZE-HEIGHT))


      predictor.recordMoves(player.pos)
   
      for enemy in enemies:
          enemy.fsm(player)
          enemy.track(player, dt, maze)
       
      if player.health <= 0:
          game_over = True
      if boss:
          boss.update(player, maze, predictor, dt)
          if boss.hp <= 0:
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

  if game_over:
      screen.blit(Font.render("Game Over. (r.i.p. lmao)", True, (255, 0, 0)), (WIDTH//2 - 150, HEIGHT//2))
  elif game_won:
      screen.blit(Font.render("Dracula hath been slain. good job mh", True, (0, 255, 0)), (WIDTH//2 - 200, HEIGHT//2))


  pygame.display.flip()


pygame.quit()


