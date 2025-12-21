import pygame
from color import Color, DISC_ID_TO_COLOR
from disc import Disc
from rod import Rod
    

class Tower:
    """
    Class that encapsulates the rod and disc Pygame elements for rendering.
    """
    def __init__(self, screen_width, screen_height, num_rods=3, num_discs=5):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.num_rods = num_rods
        self.num_discs = num_discs
        self.rods = {}
        self.discs = {}
        self.init_rods()
        self.init_discs()

    def init_rods(self):
        """Add rods as static objects to list of renderable objects during init."""
        start_x_pos = self.screen_width // 8
        step_x = start_x_pos * 2
        stop_x_pos = step_x * 3

        for id, center_x in enumerate(range(start_x_pos, stop_x_pos, step_x)):
            center_y = self.screen_height // 2
            # print(f"adding rod at ({center_x}, {center_y})")
            rod = Rod(center_x=center_x, center_y=center_y)
            self.rods[id] = rod

    def init_discs(self):
        # Initialize the discs
        start_x_pos = self.screen_width // 8
        step_y = 50
        start_y_pos = 520
        start_width = 270
        width_delta = 40
        disc_height = 50
        for idx in range(self.num_discs):
            center_y = start_y_pos - step_y * idx
            width = start_width - width_delta * idx
            disc_id = self.num_discs - idx - 1
            disc = Disc( 
                center_x=start_x_pos, 
                center_y=center_y,
                width=width,
                height=disc_height,
                color=DISC_ID_TO_COLOR[disc_id]
            )
            self.discs[disc_id] = disc

    def render_rods(self, surface):
        for _, rod in self.rods.items():
            rod.render(surface)
    
    def render_discs(self, surface):
        for _, disc in self.discs.items():
            disc.render(surface)
    
    def render(self, surface):
        self.render_rods(surface)
        self.render_discs(surface)