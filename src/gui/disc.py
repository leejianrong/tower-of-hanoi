import pygame
from color import Color, DISC_ID_TO_COLOR


DISC_MOVEMENT_SPEED = 5

class Disc:
    def __init__(self, center_x, center_y, width, height, color):
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (center_x, center_y)
        self.speed = DISC_MOVEMENT_SPEED

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
        surface.blit(self.image, self.rect)