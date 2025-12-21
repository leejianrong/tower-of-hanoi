import pygame
from color import Color, DISC_ID_TO_COLOR

class Rod:
    """Rod that will be rendered as static objects."""
    def __init__(self, id, center_x, center_y, width=30, height=320):
        self.image = pygame.Surface((width, height))
        self.image.fill(Color.PASTEL_GRAY.value)
        self.rect = self.image.get_rect()
        self.rect.center = (center_x, center_y)

    def render(self, surface):
        surface.blit(self.image, self.rect)


class Disc:
    def __init__(self, id, center_x, center_y, width, height, color):
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (center_x, center_y)
        self.speed = 5

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

    
class Tower:
    """
    Class that encapsulates the rod and disc elements for rendering.
    """
    def __init__(num_rods=3, num_discs=5):
        pass

    
    def init_renderable_objects(self):
        """Add static objects like the rods and base plate during init."""
        start_x_pos = self.screen_width // 8
        step_x = start_x_pos * 2
        stop_x_pos = step_x * 3

        for id, center_x in enumerate(range(start_x_pos, stop_x_pos, step_x)):
            center_y = self.screen_height // 2
            # print(f"adding rod at ({center_x}, {center_y})")
            rod = Rod(id=id, center_x=center_x, center_y=center_y)
            self.add_element(rod)

        # Initialize the discs
        step_y = 50
        start_y_pos = 520
        start_width = 270
        width_delta = 40
        disc_height = 50
        num_discs = 5
        for idx in range(num_discs):
            center_y = start_y_pos - step_y * idx
            width = start_width - width_delta * idx
            disc_id = num_discs - idx - 1
            disc = Disc(
                id=disc_id, 
                center_x=start_x_pos, 
                center_y=center_y,
                width=width,
                height=disc_height,
                color=DISC_ID_TO_COLOR[disc_id]
            )
            self.add_element(disc)