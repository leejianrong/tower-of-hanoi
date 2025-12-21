from game import TowerGame

def play_tower_game():
    tower_game = TowerGame()
    num_moves = 0
    while tower_game.current_state != tower_game.terminal_state:
        print(f"\nNumber of Moves: {num_moves}")
        print(f"Current State: {tower_game.current_state}")

        start_rod_idx =int(input("Enter start rod index: "))
        target_rod_idx =int(input("Enter target rod index: "))
        moving_disc_id = tower_game.move(start_rod_idx, target_rod_idx)
        if moving_disc_id is None:
            print("\nInvalid move, please try again.")
        else:
            print(f"\nMoved disc id={moving_disc_id} from {start_rod_idx} to {target_rod_idx}")
            num_moves += 1

    print(f"You win! Finished game in {num_moves} moves.")

if __name__ == "__main__":
    play_tower_game()
