# # the colors are detected correctly, but aren't compared with the values correctly so the player speed never changes




# # fix sprint so it updates the player input method
# # fix the enemy.detect_Check method
# # fix enemy fsm


# # # change walk so that at each frame it 
# # # checks one pixel in up/down/left/right 
# # # and then if rock then speed in that 
# # # direction gets set to 0. (e.g. if there’s
# # # rock to the left, then speed.x = max(0,speed.x)
# # # this accomplishes. Opposite for right (min) 
# # #and then same for up/down with y)


# # change the Walk() check for rock so it checks if the player is moving into a rock, and if it is set movement in that direction = 0
# # after noise generation, change the edges to rocks so that players can't escape




# # fix camera, expand map
# # implement damage and health for enemies and player, implement death for both


# stuff I'm doing: fsm, a*, paths, etc


import pygame
import random
from noise import pnoise2


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
screen = pygame.display.set_mode((WIDTH, HEIGHT))


SCALE = 300.0
OCTAVES = random.randint(2, 3)
PERSISTENCE = random.randint(3, 5) / 10
LACUNARITY = random.randint(1, 3)


def noise_surface():
   surf = pygame.Surface((WIDTH*10, HEIGHT*10))
   arr = pygame.PixelArray(surf)


   for y in range(HEIGHT):
        for x in range(WIDTH):
               n = pnoise2(x/SCALE, y/SCALE, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY)


               type = (0, 0, 0)
               if n < -0.3:
                    type = TERRAIN_COLORS["water"]
               elif -0.3 <= n < -0.1:
                    type = TERRAIN_COLORS["mud"]
               elif -0.1 <= n < 0.3:
                    type = TERRAIN_COLORS["grass"]
               else:
                    type = TERRAIN_COLORS["rock"]


               arr[x, y] = type
   del arr
   return surf


noise = noise_surface()  


         


class Enemy: ## class define enemy NPCs
   def __init__(self,x, y, hp):
       self.pos = pygame.math.Vector2(x, y)
       self.dir = pygame.math.Vector2(0, 0)
       self.health = hp
       self.current_state = "Wander"
       self.states = ["Wander", "Chase", "Flee"]
   def get_hit(self, NPCS):
        self.health -= 1
        if self.health <= 0:
             NPCS.remove()
   def remove(self):
       pass
   def detect_Check(self, player_pos):
       distance = self.pos.distance_to(player_pos)
       if distance > 20:
           return False
       distance = distance.normalize()
       dot = self.dir.dot(distance)
       if dot >= 0.8666: ### CHECks if in 60 degree veiw
           return True
       else:
           return False
   def draw(self, screen):
       pygame.draw.rect(screen, (255, 0, 255), (self.pos.x, self.pos.y, 20, 20))
   def fsm(self, NPCS, player):
       for enemy in NPCS:
           if enemy.current_state == "Wander":
               if enemy.detect_Check(player.getPos()):
                   enemy.current_state = "Chase"
               if player.Garlic_On() and enemy.detect_Check(player.getPos()):
                   enemy.current_state = "Flee"
           elif enemy.current_state == "Chase":
               if enemy.detect_Check(player):#WIP
                       pass
   def track(self, player, dt):
       if self.current_state == "Wander":
           pass #to write
       elif self.current_state == "Chase":
           pass #to write
       elif self.current_state == "Flee":
           pass #to write


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
   def get_hit(self):
       self.health -= 10
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
           self.Walk(dt, speed_adjust)
   def Walk(self, dt, s_a):
       if self.current_surface == "rock":
           return
       terrain_speed_mult = {“grass”: 1, “mud”: 0.6, “water”: 0.4}[self.current_surface]
       self.pos += self.dir*self.speed*terrain_speed_mult*speed_adjust*dt
   def Apply_GarlicEffect(self):
       pass
   def draw(self):
        pygame.draw.rect(screen, (255, 255, 255), self.hitbox)
   def update_surface(self): #could use some work, like implementing the hitbox instead of player coords
       temp = noise.get_at((int(self.pos.x), int(self.pos.y))) 
       print(temp)
       match temp:
           case ((84, 86, 89, 255)):
               self.current_surface = "rock" #return "rock"
               print("rock")
           case ((87, 57, 24, 255)):
               self.current_surface = "mud" #return "mud"
               print("mud")
           case ((64, 77, 115, 255)):
               self.current_surface = "water"# return "water"
               print("water")
           case _:
               self.current_surface = "grass"# return "grass"
               print("grass")
   def update(self):
       self.update_surface()
       self.hitbox.left = self.pos.x - 5
       self.hitbox.top = self.pos.y - 10
       self.draw()


# placeholders:
class MazeGen:
   def __init__(self):
       pass
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
       pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), 8)




class Boss:
   def __init__(self, x, y):
       self.pos = pygame.math.Vector2(x, y)
       self.hp = 100
       self.state = "Ambush"
   def update(self, player, maze, predictor, dt):
       pass # markov/a* logic here
   def draw(self, screen):
       pygame.draw.rect(screen, (200, 0, 0), (self.pos.x, self.pos.y, 50, 50)) #replace with sprite


## main loop:


Clock = pygame.time.Clock()
Font = pygame.font.SysFont("Arial", 24)




running = True
debug_mode = False
game_over = False
game_won = False
night_time = 360.0 # 6 minutes?
dracula_spawned = False


player = Player(50, 100, 100)
maze = MazeGen()
predictor = Markov()
enemies = []
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
           print("Sunrise...... Dracula's coming O.O")
           boss = Boss(player.pos.x + 100, player.pos.y + 100) #spawn boss (we should make a random spawning method)
           dracula_spawned = True
          
       player.update() # surface and terrain interaction
       predictor.recordMoves(player.pos)
      
       for enemy in enemies:
           enemy.fsm(enemies, player)
           enemy.track(player, dt) # need to rewrite track to take dt
          
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
   screen.blit(noise, (0, 0))
  
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
       debug_text = Font.render("debug mode activated (F1)", True, (255, 0, 0))
       screen.blit(debug_text, (10, 70))
       # need to draw A* path & boss predictions
   if game_over:
       screen.blit(Font.render("Game Over. (r.i.p. lmao)", True, (255, 0, 0)), (WIDTH//2 - 150, HEIGHT//2))
   elif game_won:
       screen.blit(Font.render("Dracula hath been slain. good job mh", True, (0, 255, 0)), (WIDTH//2 - 200, HEIGHT//2))


   # display the screen update
   pygame.display.flip()


pygame.quit()



