import pygame
import logging
from color import Color

logger = logging.getLogger(__name__)

Y_COORD_LATERAL_MOVEMENT = 100
MOVEMENT_SPEED = 25

class Disc:
    def __init__(
        self, 
        center_x: int, 
        center_y: int, 
        width: int, 
        height: int, 
        color: Color, 
        id: int,
        label_color: pygame.Color = Color.PASTEL_WHITE.value,
        movement_speed: int = MOVEMENT_SPEED
    ) -> None:
        
        self.surf: pygame.Surface = pygame.Surface((width, height))
        self.surf.fill(color)

        self.rect: pygame.Rect = self.surf.get_rect()
        self.rect.center = (center_x, center_y)

        # Original and target coordinates to handle disc movement and pathing
        self.source_x = center_x
        self.source_y = center_y
        self.target_x = center_x
        self.target_y = center_y
        self.speed = movement_speed

        label_font = pygame.font.SysFont(None, 16)
        label_surf = label_font.render(str(id), True, label_color)
        label_rect = label_surf.get_rect(center=(width - 15, height - 15))
        self.surf.blit(label_surf, label_rect)

    def set_target(self, x: int, y: int):
        """Called by the Renderer when a move is made within the game logic"""
        self.target_x = x
        self.target_y = y

    def get_new_coord(self, current, target, step):
        if current < target:
            new_coord = min(current + step, target)
        elif current > target:
            new_coord = max(current - step, target)
        else:
            new_coord = current
        return new_coord

    def update(self):
        """Move the disc incrementally towards its target position each frame"""
        if self.rect.center == (self.target_x, self.target_y):
            return
        
        curr_x, curr_y = self.rect.center

        # Handle upward movement to move disc up and out of original rod
        if curr_x == self.source_x and curr_y > Y_COORD_LATERAL_MOVEMENT:
            new_y = self.get_new_coord(curr_y, Y_COORD_LATERAL_MOVEMENT, self.speed)

        # Handle downward movement to move disc down and into target rod
        elif curr_x == self.target_x and curr_y <= self.target_y:
            new_y = self.get_new_coord(curr_y, self.target_y, self.speed)
        else:
            new_y = curr_y

        # Handle lateral movement when disc is above rods
        if curr_y <= Y_COORD_LATERAL_MOVEMENT:
            new_x = self.get_new_coord(curr_x, self.target_x, self.speed)
        else:
            new_x = curr_x

        self.rect.center = (new_x, new_y)

        # Update source coords when disc has stopped moving
        if not self.is_moving:
            self.source_x, self.source_y = self.rect.center

        # new_x = self.get_new_coord(curr_x, self.target_x, self.speed)
        # new_y = self.get_new_coord(curr_y, self.target_y, self.speed)

    @property
    def is_moving(self) -> bool:
        """Helper to check if the animation is finished"""
        return self.rect.center != (self.target_x, self.target_y)

    def render(self, surface):
        # Draw the player onto the provided surface (the main screen)
        surface.blit(self.surf, self.rect)
