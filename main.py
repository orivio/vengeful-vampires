import pygame
import numpy
import sys
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
OCTAVES = 2
PERSISTENCE = 0.5
LACUNARITY = 2

def noise_surface():
    surf = pygame.Surface((WIDTH, HEIGHT))
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
    def __init__(self,x, y, hp ):
        self.pos = pygame.math.Vector2(x, y)
        self.dir = pygame.math.Vector2(0, 0)
        self.health = hp
        self.current_state = "Wander"
        self.states = ["Wander", "Chase", "Flee"]
    def get_hit(self):
         self.health -= 1
         if self.health <= 0:
              NPCS.remove() 
    def fsm(self, NPCS, player): 
        for enemy in NPCS:
            if enemy.distanceto(player):
                enemy.current_state = "Chase"
    def track(self, player):
        if self.current_state == "Wander":
            pass #to write
        elif self.current_state == "Chase":
            pass #to write
        elif self.current_state == "Flee":
            pass #to write

#player_movement_tracking_MDP = zeros(9,9,9,9) # this is for 3 context and 2-step prediction. the first step prediction is not relevant though as it only aims two steps ahead anyway, so only the final lcoation needs to be recorded (e.g, left,right and nothing would be recorded the same over 2 steps) 

gameloop = True

while gameloop:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            gameloop = False



    screen.blit(noise, (0, 0))
    pygame.display.flip()

pygame.quit()