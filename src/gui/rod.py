import pygame
from color import Color

class Rod:
    """Rod that will be rendered as static objects."""
    def __init__(self, center_x, center_y, width=30, height=320):
        self.surf: pygame.Surface = pygame.Surface((width, height))
        self.surf.fill(Color.PASTEL_GRAY.value)
        
        self.rect: pygame.Rect = self.surf.get_rect()
        self.rect.center = (center_x, center_y)

    def render(self, surface):
        surface.blit(source=self.surf, dest=self.rect)