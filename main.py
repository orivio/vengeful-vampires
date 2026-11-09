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

SCALE = 80.0
OCTAVES = 2

#states 
states = ["Wander", "Chase", "Flee"]

player_movement_tracking_MDP = zeros(9,9,9,9) # this is for 3 context and 2-step prediction. the first step prediction is not relevant though as it only aims two steps ahead anyway, so only the final lcoation needs to be recorded (e.g, left,right and nothing would be recorded the same over 2 steps) 
