import pygame
from enum import Enum
from typing import Dict

class Color(Enum):
    PASTEL_WHITE = pygame.Color("#faf8f6")
    PASTEL_GRAY = pygame.Color("#cfcfc4")
    PASTEL_ROSE = pygame.Color("#f6b8d0")
    PASTEL_AMBER = pygame.Color("#F8C57C")
    PASTEL_LIME = pygame.Color("#d1feb8")
    PASTEL_SKY = pygame.Color("#beddf1")
    PASTEL_MAUVE = pygame.Color("#ebccff")


DISC_ID_TO_COLOR: Dict[int, pygame.Color] = {
    0: Color.PASTEL_ROSE.value,
    1: Color.PASTEL_AMBER.value,
    2: Color.PASTEL_LIME.value,
    3: Color.PASTEL_SKY.value,
    4: Color.PASTEL_MAUVE.value,
}