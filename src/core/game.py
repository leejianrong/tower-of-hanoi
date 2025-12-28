import json
import os

from typing import Tuple
from datetime import datetime
from pathlib import Path
from tower import Tower


class Game:
    """
    Runs the loop and logic for the Tower of Hanoi Game.
    Handles users inputs and allows for recording of moves.
    """
    def __init__(self, json_filename: str = "record.json"):
        self.num_moves = 0
        self.tower = Tower()
        self.history = []

        parent_dir = Path(__file__).resolve().parent.parent
        save_dir = os.path.join(parent_dir, "records")
        os.makedirs(save_dir, exist_ok=True)
        self.json_filepath = os.path.join(save_dir, json_filename)
        print(f"JSON filepath for saving records: {self.json_filepath}")

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

    def save_to_file(self, json_filepath):
        with open(json_filepath, "w") as f:
            json.dump(self.history, f)

    def play(self):
        self.tower = Tower()
        self.num_moves = 0
        while not self.tower.is_solved:
            print(f"\nNumber of Moves: {self.num_moves}")
            print(f"Current State: {self.tower.current_state}")

            source_rod_idx =int(input("Enter start rod index: "))
            target_rod_idx =int(input("Enter target rod index: "))
            moving_disc_id = self.tower.move(source_rod_idx, target_rod_idx)
            if moving_disc_id is not None:
                print(f"\nMoved disc id={moving_disc_id} from {source_rod_idx} to {target_rod_idx}")
                self.record_history(
                    disc_id=moving_disc_id, 
                    source_rod_idx=source_rod_idx, 
                    target_rod_idx=target_rod_idx, 
                    new_state=self.tower.current_state
                )
                self.num_moves += 1
            else:
                print("\nInvalid move, please try again.")
                
        print(f"\nNumber of Moves: {self.num_moves}")
        print(f"Current State: {self.tower.current_state}")
        print(f"You win! Finished game in {self.num_moves} moves.")

        self.save_to_file(json_filepath=self.json_filepath)
        print(f"Saved move history to {self.json_filepath}.")


if __name__ == "__main__":
    now = datetime.now()
    dt_now = now.strftime("%Y_%m_%d_%H_%M_%S")
    tower_game = Game(json_filename=f"record_{dt_now}.json")
    tower_game.play()
