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
        id: int,
        label_color: pygame.Color = Color.PASTEL_WHITE.value,
        movement_speed: int = 5
    ) -> None:
        
        self.surf: pygame.Surface = pygame.Surface((width, height))
        self.surf.fill(color)

        self.rect: pygame.Rect = self.surf.get_rect()
        self.rect.center = (center_x, center_y)

        # Target coordinates to track where disc is going
        self.target_x = center_x
        self.target_y = center_y
        self.speed: int = movement_speed

        label_font = pygame.font.SysFont(None, 16)
        label_surf = label_font.render(str(id), True, label_color)
        label_rect = label_surf.get_rect(center=(width - 15, height - 15))
        self.surf.blit(label_surf, label_rect)

    def set_target(self, x: int, y: int):
        """Called by the Renderer when a move is made within the game logic"""
        self.target_x = x
        self.target_y = y

    def update(self):
        """Move the disc incrementally towards its target position each frame"""
        curr_x, curr_y = self.rect.center

        # Move X towards target
        if curr_x < self.target_x:
            new_x = min(curr_x + self.speed, self.target_x)
        elif curr_x > self.target_x:
            new_x = max(curr_x - self.speed, self.target_x)
        else:
            new_x = curr_x
        
        # Move Y towards target
        if curr_y < self.target_y:
            new_y = min(curr_y + self.speed, self.target_y)
        elif curr_y > self.target_y:
            new_y = max(curr_y - self.speed, self.target_y)
        else:
            new_y = curr_y

        self.rect.center = (new_x, new_y)

    def is_moving(self) -> bool:
        """Helper to check if the animation is finished"""
        return self.rect.center != (self.target_x, self.target_y)

    def render(self, surface):
        # Draw the player onto the provided surface (the main screen)
        surface.blit(self.surf, self.rect)