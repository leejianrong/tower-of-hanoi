import json
import logging

from typing import Tuple
from datetime import datetime
from pathlib import Path
from src.core.tower import Tower


logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
RECORD_DIR = REPO_ROOT / "records"


class GameHistoryRecorder:
    """
    Helper class for recording game moves and states in a
    dictionary and saving them as a JSON file.
    """
    def __init__(
        self,
        record_dir: str | Path = RECORD_DIR,
        json_filename: str = "record.json"
    ) -> None:
        self.history = []
        self.record_dir = Path(record_dir)
        self.record_dir.mkdir(parents=True, exist_ok=True)
        self.set_json_filepath(json_filename)
        logger.info(f"JSON file path for saving records: {self.json_filepath}")

    def set_json_filepath(self, json_filename: str | Path) -> None:
        json_path = Path(json_filename)
        if not json_path.is_absolute():
            json_path = self.record_dir / json_path
        self.json_filepath = json_path

    def record_history(
        self,
        disc_id: int,
        source_rod_idx: int,
        target_rod_idx: int,
        new_state: Tuple[Tuple[int]]
    ) -> None:
        """
        Records game info as a list of dictionaries.
        Each dictionary contains moving disc id, source and target rod indexes,
        and the new game state after the move.
        """
        move_info = {"disc_id": disc_id, "from": source_rod_idx, "to": target_rod_idx}
        self.history.append({"move": move_info, "new_state": new_state})

    def save_to_file(self):
        with self.json_filepath.open("w") as f:
            json.dump(self.history, f)
        logger.info(f"Saved move history to {self.json_filepath}.")

    def reset(self):
        self.set_json_filepath("record.json")
        self.history = []


class Game:
    """
    Runs the loop and logic for the Tower of Hanoi Game.
    Handles users inputs and allows for recording of moves.
    """
    def __init__(self, json_filename: str = "record.json"):
        self.num_moves = 0
        self.tower = Tower()
        self.recorder = GameHistoryRecorder(json_filename=json_filename)

    def play(self):
        self.tower = Tower()
        self.num_moves = 0
        while not self.tower.is_solved:
            logger.info(f"\nNumber of Moves: {self.num_moves}")
            logger.info(f"Current State: {self.tower.current_state}")

            source_rod_idx =int(input("Enter start rod index: "))
            target_rod_idx =int(input("Enter target rod index: "))
            moving_disc_id = self.tower.move(source_rod_idx, target_rod_idx)
            if moving_disc_id is not None:
                logger.info(f"\nMoved disc id={moving_disc_id} from {source_rod_idx} to {target_rod_idx}")
                self.recorder.record_history(
                    disc_id=moving_disc_id,
                    source_rod_idx=source_rod_idx,
                    target_rod_idx=target_rod_idx,
                    new_state=self.tower.current_state
                )
                self.num_moves += 1
            else:
                logger.info("\nInvalid move, please try again.")

        logger.info(f"\nNumber of Moves: {self.num_moves}")
        logger.info(f"Current State: {self.tower.current_state}")
        logger.info(f"You win! Finished game in {self.num_moves} moves.")

        self.recorder.save_to_file()


if __name__ == "__main__":
    now = datetime.now()
    dt_now = now.strftime("%Y_%m_%d_%H_%M_%S")
    tower_game = Game(json_filename=f"record_{dt_now}.json")
    tower_game.play()
