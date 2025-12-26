import pygame
import sys

from typing import Tuple
from color import Color, DISC_ID_TO_COLOR
from tower import Tower

class Renderer:
    """
    A simple renderer class to manage the drawing of all game elements.
    """
    def __init__(self, screen: pygame.surface.Surface, background_color=Color.PASTEL_WHITE.value):
        self.screen = screen
        width, height = screen.get_size()
        self.screen_width = width
        self.screen_height = height
        self.background_color = background_color
        # A list to keep track of objects that need a custom render method called
        self.renderable_objects = []

    def add_element(self, element):
        """Add an element to be rendered every frame."""
        if hasattr(element, "render"):
            self.renderable_objects.append(element)
        else:
            print((
                f"Warning: Element {element} does not have a render method " 
                "and will not be rendered by the Renderer class."
            ))
        
    def remove_element(self, element):
        """Remove an element from the render list."""
        if element in self.renderable_objects:
            self.renderable_objects.remove(element)

    def render_all(self):
        """
        Clear the screen and draw all elements.
        """
        # Fill the screen with the background color to erase the previous frame
        self.screen.fill(self.background_color)

        # Call the custom render method for each object in the list
        for element in self.renderable_objects:
            element.render(self.screen)

        # Update the display to make the changes visible
        pygame.display.update() # or pygame.display.flip()
    
    def update_all(self, game_state: Tuple[Tuple[int]]):
        """Call update() method for all updatable elements."""
        # For now, tower is the only updatable element
        # It encapsulates the rods and discs, of which discs are updatable
        for element in self.renderable_objects:
            if hasattr(element, "update"):
                element.update(game_state)


if __name__ == "__main__":
    pygame.init()
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tower of Hanoi")

    # Set up the renderer
    renderer = Renderer(screen, background_color=Color.PASTEL_WHITE.value)

    tower = Tower(
        screen_width=SCREEN_WIDTH, 
        screen_height=SCREEN_HEIGHT, 
        num_rods=3, 
        num_discs=5
    )
    renderer.add_element(tower)

    # Main game loop
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        renderer.update_all() # game logic update
        renderer.render_all() # rendering
        clock.tick(60) # cap frame rate
    
    pygame.quit()
    sys.exit()