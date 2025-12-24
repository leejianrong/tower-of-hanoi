import pygame
from color import Color

class Rod:
    """Rod that will be rendered as static objects."""
    def __init__(
        self, 
        center_x: int, 
        center_y: int, 
        id: int, 
        width: int = 30, 
        height: int = 320, 
        label_color: pygame.Color = Color.PASTEL_GRAY.value
    ):
        self.surf: pygame.Surface = pygame.Surface((width, height))
        self.surf.fill(Color.PASTEL_GRAY.value)
        
        self.rect: pygame.Rect = self.surf.get_rect()
        self.rect.center = (center_x, center_y)

        label_font = pygame.font.SysFont(None, 24)
        label_color = label_color
        label_text = str(id)
        self.label_surf = label_font.render(label_text, True, label_color)
        # Lock the top-center of the text to the bottom-center of the rod
        # Add a small y-offset (e.g., +30) for spacing
        self.label_rect = self.label_surf.get_rect(
            midtop=(self.rect.midbottom[0], self.rect.midbottom[1] + 40)
        )

    def render(self, surface):
        surface.blit(source=self.surf, dest=self.rect)
        surface.blit(source=self.label_surf, dest=self.label_rect)