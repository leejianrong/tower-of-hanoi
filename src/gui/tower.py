import logging

from typing import Tuple

try:
    from .color import DISC_ID_TO_COLOR
    from .disc import Disc
    from .rod import Rod
except ImportError:
    from color import DISC_ID_TO_COLOR
    from disc import Disc
    from rod import Rod

logger = logging.getLogger(__name__)

ROD_WIDTH = 30
ROD_HEIGHT = 320
DISC_STEP_Y = 50
DISC_START_POS_Y = 495
DISC_BASE_WIDTH = 270
DISC_WIDTH_DELTA = 40
DISC_HEIGHT = 50

class Tower:
    """
    Class that encapsulates the rod and disc Pygame elements for rendering.
    """
    def __init__(self, screen_width, screen_height, num_rods=3, num_discs=5):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.num_rods = num_rods
        self.num_discs = num_discs
        self.start_state = (tuple(range(self.num_discs - 1, -1, -1)), (), ())
        self.rods = {}
        self.discs = {}
        self.reset()

    def reset(self):
        self.reset_rods()
        self.reset_discs()

    def reset_rods(self):
        """Add rods as static objects to list of renderable objects during init."""
        self.rods = {}
        start_x_pos = self.screen_width // 8
        step_x = start_x_pos * 2
        stop_x_pos = step_x * 3

        for id, center_x in enumerate(range(start_x_pos, stop_x_pos, step_x)):
            center_y = self.screen_height // 2
            logger.debug(f"adding rod at ({center_x}, {center_y}) of width={ROD_WIDTH}, height={ROD_HEIGHT}")
            rod = Rod(center_x=center_x, center_y=center_y, width=ROD_WIDTH, height=ROD_HEIGHT, id=id)
            self.rods[id] = rod

    def reset_discs(self):
        # Initialize the discs
        self.discs = {}
        disc_positions = self.compute_disc_positions_from_state(game_state=self.start_state)

        for idx in range(self.num_discs):
            # create discs from largest (bottom) to smallest (top)
            disc_id = self.num_discs - idx - 1
            center_x, center_y = disc_positions[disc_id]
            width = DISC_BASE_WIDTH - DISC_WIDTH_DELTA * idx

            disc = Disc(
                center_x=center_x,
                center_y=center_y,
                width=width,
                height=DISC_HEIGHT,
                color=DISC_ID_TO_COLOR[disc_id],
                id=disc_id
            )
            self.discs[disc_id] = disc

    def set_state(self, game_state: Tuple[Tuple[int]]) -> None:
        disc_positions = self.compute_disc_positions_from_state(game_state=game_state)
        for disc_id, (center_x, center_y) in enumerate(disc_positions):
            disc = self.discs[disc_id]
            disc.rect.center = (center_x, center_y)
            disc.source_x = center_x
            disc.source_y = center_y
            disc.target_x = center_x
            disc.target_y = center_y

    def render(self, surface):
        for _, rod in self.rods.items():
            rod.render(surface)
        for _, disc in self.discs.items():
            disc.render(surface)

    def update(self):
        # desired_disc_positions = self.compute_disc_positions_from_state(game_state)
        for disc in self.discs.values():
            # desired_x, desired_y = desired_disc_positions[disc_idx]
            # disc.set_target(desired_x, desired_y)
            disc.update()

    def compute_disc_positions_from_state(self, game_state: Tuple[Tuple[int]]) -> Tuple[Tuple[int]]:
        """
        Given a certain game state like ((4, 3, 2), (1), (0)),
        compute the disc coordinates in pygame.
        Returns the disc coordinates as a tuple of tuples:
        ((x0, y0), (x1, y1), ... (x4, y4))
        """
        disc_positions = [() for _ in range(self.num_discs)]
        for rod_idx, rod_state in enumerate(game_state):
            center_x = self.rods[rod_idx].rect.center[0]

            for pos_idx, disc_idx in enumerate(rod_state):
                center_y = DISC_START_POS_Y - DISC_STEP_Y * pos_idx
                disc_positions[disc_idx] = (center_x, center_y)

        return tuple(disc_positions)
