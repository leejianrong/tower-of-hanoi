import os
import json
import logging

from pathlib import Path
from tower import Tower

logger = logging.getLogger(__name__)


class ReplayManager:
    def __init__(self, tower_instance: Tower, record_json: str):
        self.tower = tower_instance
        self.move_idx = 0
        self.game_record = self.read_game_record(filename=record_json)
        self.current_disc_id = None

    def read_game_record(self, filename: str):  
        parent_dir = Path(__file__).resolve().parent.parent
        json_filepath = os.path.join(parent_dir, "records", filename)

        with open(json_filepath, "r") as f:
            game_record = json.load(f)
            logger.info(f"Successfully read game record from {json_filepath}")
            return game_record

    def trigger_next_move(self):
        if self.move_idx < len(self.game_record):
            new_game_state = self.game_record[self.move_idx]["new_state"]
            self.current_disc_id = self.game_record[self.move_idx]["move"]["disc_id"]

            desired_disc_positions = self.tower.compute_disc_positions_from_state(new_game_state)
            desired_x, desired_y = desired_disc_positions[self.current_disc_id]
            self.tower.discs[self.current_disc_id].set_target(desired_x, desired_y)
            self.move_idx += 1

    @property
    def is_busy(self):
        if self.current_disc_id is not None:
            return self.tower.discs[self.current_disc_id].is_moving
        # Start of the game where we have not moved any discs: not busy
        return False
