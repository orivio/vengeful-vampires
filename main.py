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

SCALE = 100.0
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
    def track(self, player):
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
        self.speed = 10
        self.stamina = 100 #make subtract by 2 for every second shift is held
        self.current_surface = "grass"
    def get_hit(self):
        hp -= 10
    def Walk(self, direction):
        if self.current_surface == "mud":
            move = self.dir * direction * pygame.math.Vector2(0.6, 0.6)
            self.pos += move
        if self.current_surface == "water":
            move =  self.dir * direction * pygame.math.Vector2(0.4, 0.4)
            self.pos += move
        if self.current_surface == "rock":
             if self.dir.x < 0:
                  self.dir.x += 1
             elif self.dir.x > 0:
                  self.dir.x -= 1
             if self.dir.y < 0:
                  self.dir.y += 1
             elif self.dir.y > 0:
                  self.dir.y -= 1
    def Sprint(self): #WIP
        if not self.dir.length_squared > 225:
            self.dir *= pygame.math.Vector2(1.5, 1.5)
    def Apply_GarlicEffect(self):
        pass
    def draw(self):
         pygame.draw.rect(screen, (255, 255, 255), self.hitbox)
    def check_surface(self): #could use some work, like implementing the hitbox instead of player coords
        temp = noise.get_at(self.pos)
        match temp:
            case (84, 86, 89):
                return "rock"
            case (87, 57, 24):
                return "mud"
            case (64, 77, 115):
                return "water"
            case _:
                return "grass"
    def upd(self):
        self.current_surface = self.check_surface()
        self.draw()
            
enemies = []
player = Player(100, 100, 100)
gameloop = True

while gameloop:
    for event in pygame.event.get(): #event loop
        if event.type == pygame.QUIT:
            gameloop = False
    screen.blit(noise, (0, 0))
    player.upd()

    keys = pygame.key.get_pressed() #input
    if keys[pygame.K_w]:
        player.Walk(pygame.math.Vector2(0, -1))
        if keys[pygame.K_LSHIFT]:
            player.Sprint()
    if keys[pygame.K_s]:
            player.Walk(pygame.math.Vector2(0, 1))
            if keys[pygame.K_LSHIFT]:
                player.Sprint()
    if keys[pygame.K_a]:
            player.Walk(pygame.math.Vector2(-1, 0))
            if keys[pygame.K_LSHIFT]:
                player.Sprint()
    if keys[pygame.K_d]:
            player.Walk(pygame.math.Vector2(1, 0))
            if keys[pygame.K_LSHIFT]:
                player.Sprint()

    
    pygame.display.flip()

pygame.quit()