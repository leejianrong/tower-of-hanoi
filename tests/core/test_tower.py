from src.core.tower import Tower


def test_tower_starts_with_all_discs_on_first_rod():
    tower = Tower(num_discs=3)

    assert tower.current_state == ((2, 1, 0), (), ())
    assert tower.terminal_state == ((), (), (2, 1, 0))
    assert not tower.is_solved


def test_valid_move_updates_state_and_returns_disc_id():
    tower = Tower(num_discs=3)

    moved_disc_id = tower.move(0, 2)

    assert moved_disc_id == 0
    assert tower.current_state == ((2, 1), (), (0,))


def test_invalid_move_does_not_change_state():
    tower = Tower(num_discs=3)
    tower.move(0, 2)

    before = tower.current_state
    moved_disc_id = tower.move(0, 2)

    assert moved_disc_id is None
    assert tower.current_state == before


def test_get_valid_moves_returns_only_legal_moves():
    tower = Tower(num_discs=3)

    assert tower.get_valid_moves() == ((0, 1), (0, 2))
