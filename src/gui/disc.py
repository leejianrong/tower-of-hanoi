import pygame
from color import Color, DISC_ID_TO_COLOR


class Disc:
    def __init__(
        self, 
        center_x: int, 
        center_y: int, 
        width: int, 
        height: int, 
        color: Color, 
        movement_speed: int = 5
    ) -> None:
        self.surf: pygame.Surface = pygame.Surface((width, height))
        self.surf.fill(color)

        self.rect: pygame.Rect = self.surf.get_rect()
        self.rect.center = (center_x, center_y)

        self.speed: int = movement_speed

    def update(self):
        # Update player position (simplified movement)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

    def render(self, surface):
        # Draw the player onto the provided surface (the main screen)
        surface.blit(self.surf, self.rect)