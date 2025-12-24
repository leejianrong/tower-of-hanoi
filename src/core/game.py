from disc import Disc
from rod import Rod
from typing import List, Tuple, Optional

class TowerGame:
    """
    Contains rods, discs, and logic for the Tower of Hanoi game.

    Allows movement of discs from one rod to another and checks if moves are valid.

    Attributes:
        num_rods (int): Number of rods in the game (default = 3).
        num_discs (int): Number of discs in the game (default = 5).
        rods (List[Rod]): List of rods, where each rod contains a stack of discs.
        terminal_state (Tuple[Tuple[int]]): Pre-defined terminal state to check for end of game.
    """
    def __init__(
        self, 
        num_rods: int = 3, 
        num_discs: int = 5,
    ):
        self.num_rods = num_rods
        self.num_discs = num_discs
        self.rods: List[Rod] = [
            Rod(id=id, discs=[]) for id in range(self.num_rods)
        ]
        self.terminal_state: Tuple[Tuple[int]] = self.init_terminal_state()
        self.reset()

    def __str__(self):
        game_info = (
            f"TowerGame(num_rods={self.num_rods}, "
            f"num_discs={self.num_discs})\n"
        )

        rod_descriptions = []
        for rod in self.rods:
            rod_descriptions.append(f"  {str(rod)}")
        
        return game_info + "\n".join(rod_descriptions)

    def reset(self):
        """
        Resets the game to the beginning state, where all discs
        are stacked on the first rod (i.e., rod with index=0).
        """
        for rod_idx in range(self.num_rods):
            if rod_idx == 0:
                self.rods[rod_idx] = Rod(
                    id=rod_idx, 
                    discs=[Disc(id=disc_id) for disc_id in range(self.num_discs, 0, -1)]
                )
            else:
                self.rods[rod_idx] = Rod(id=rod_idx, discs=[])

    def move(self, start_rod_idx: int, target_rod_idx: int) -> Optional[int]:
        """
        Move a disc from the top of one rod to another rod.
        Takes in two indexes - one for starting and one for target rod.
        If the move is valid, move is executed and the disc ID is returned.
        If the move is invalid, no move is executed and `None` is returned.
        """
        if self.is_valid_move(start_rod_idx, target_rod_idx):
            moving_disc = self.rods[start_rod_idx].discs.pop()
            self.rods[target_rod_idx].discs.append(moving_disc)
            return moving_disc.id
        
        return None

    def is_valid_move(self, start_rod_idx: int, target_rod_idx: int) -> bool:
        """
        Checks the validity of a move. Invalid moves include:
            - Moving from a rod to itself (same start and target index).
            - Moving from a rod that has no discs on it (empty stack).
            - Moving a disc that is bigger than the top disc of the target stack.
        """
        if start_rod_idx == target_rod_idx:
            # Disallow rod from moving to itself
            return False
        
        start_rod = self.rods[start_rod_idx]
        target_rod = self.rods[target_rod_idx]
        
        if not start_rod.discs:
            # Starting rod has no discs on it; invalid move
            return False
        
        # Compare moving disc size to top disc on target rod
        if not target_rod.discs:
            # target_rod is empty, so move is valid
            return True
        else:
            moving_disc_size = start_rod.top_disc.id
            target_top_disc_size = target_rod.top_disc.id
            return moving_disc_size < target_top_disc_size

    def get_valid_moves(self) -> Tuple[Tuple[int]]:
        """
        Goes through all combinations of start and target indexes
        and returns all the valid moves as a tuple of tuples. 
        For example `((s1, t1), (s2, t2))`.
        """
        valid_moves: List[Tuple[int]] = []
        for start_rod_idx in range(self.num_rods):
            for target_rod_idx in range(self.num_rods):
                if self.is_valid_move(start_rod_idx, target_rod_idx):
                    valid_moves.append((start_rod_idx, target_rod_idx))

        return tuple(valid_moves)
    
    def init_terminal_state(self) -> Tuple[Tuple[int]]:
        """
        Represent the terminal state as a tuple of tuples so that
        it can be stored as a class attribute for future reference.
        """
        terminal_state = [tuple() for _ in range(self.num_rods - 1)]
        terminal_state.append(tuple(disc_idx for disc_idx in range(self.num_discs, 0, -1)))
        return tuple(terminal_state)
    
    @property
    def current_state(self) -> Tuple[Tuple[int]]:
        """
        Represent the current game state as a tuple of tuples.
        Each stack of discs on a rod is represented using a tuple of disc IDs.
        Bigger discs come earlier in the tuple (bottom of the rod).
        Smaller discs come later in the tuple (top of the rod).
        For example: ((4, 3, 2), (5, 1), ())
        """
        game_state = []
        for rod in self.rods:
            disc_ids = []
            for disc in rod.discs:
                disc_ids.append(disc.id)
            game_state.append(tuple(disc_ids))

        return tuple(game_state)
    
    @property
    def is_solved(self) -> bool:
        return self.current_state == self.terminal_state
    

if __name__ == "__main__":
    tower_game = TowerGame()
    print(tower_game)
    print(f"starting state: {tower_game.current_state}")
    print(f"terminal state: {tower_game.terminal_state}")
    print(f"valid moves: {tower_game.get_valid_moves()}")