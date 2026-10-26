"""State ids for the compact replay format (ADR-0008).

A state is the rod each disc sits on. Disc ``d`` on rod ``r`` contributes ``r * 3**d``, so a
5-disc game has 3**5 = 243 ids and the start state (every disc on rod 0) is id 0. Within a rod
the bigger disc is always below, so the id alone fixes the whole stack order. The browser
decodes ids the same way, which keeps the rules in one place: this file and ADR-0008.
"""

NUM_RODS = 3

# Action index -> (source rod, target rod). Mirrors TowerEnv.action_map.
ACTION_MAP: tuple[tuple[int, int], ...] = ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1))
NUM_ACTIONS = len(ACTION_MAP)


def num_states(num_discs: int) -> int:
    return NUM_RODS**num_discs


def encode_state(state, num_discs: int) -> int:
    """Encode a state given as one sequence of disc ids per rod (bottom to top)."""
    state_id = 0
    seen = 0
    for rod, stack in enumerate(state):
        for disc in stack:
            state_id += rod * NUM_RODS**disc
            seen += 1
    if seen != num_discs:
        raise ValueError(f"State holds {seen} discs, expected {num_discs}: {state!r}")
    return state_id


def rod_of_disc(state_id: int, disc: int) -> int:
    return (state_id // NUM_RODS**disc) % NUM_RODS


def decode_state(state_id: int, num_discs: int) -> tuple[tuple[int, ...], ...]:
    """Inverse of :func:`encode_state`: three stacks of disc ids, bottom to top."""
    if not 0 <= state_id < num_states(num_discs):
        raise ValueError(f"State id {state_id} out of range for {num_discs} discs")
    stacks: list[list[int]] = [[] for _ in range(NUM_RODS)]
    for disc in range(num_discs - 1, -1, -1):
        stacks[rod_of_disc(state_id, disc)].append(disc)
    return tuple(tuple(stack) for stack in stacks)


def top_disc(state_id: int, rod: int, num_discs: int) -> int | None:
    """The smallest disc on ``rod``, or None if the rod is empty."""
    for disc in range(num_discs):
        if rod_of_disc(state_id, disc) == rod:
            return disc
    return None


def legal_actions(state_id: int, num_discs: int) -> tuple[int, ...]:
    """Actions whose source rod has a disc smaller than the target rod's top disc."""
    legal = []
    for action, (source, target) in enumerate(ACTION_MAP):
        moving = top_disc(state_id, source, num_discs)
        if moving is None:
            continue
        landing = top_disc(state_id, target, num_discs)
        if landing is None or moving < landing:
            legal.append(action)
    return tuple(legal)


def legal_mask(state_id: int, num_discs: int) -> int:
    """Legal actions as a bitmask: bit ``a`` is set when action ``a`` is legal."""
    mask = 0
    for action in legal_actions(state_id, num_discs):
        mask |= 1 << action
    return mask


def apply_action(state_id: int, action: int, num_discs: int) -> tuple[int, int]:
    """Return ``(next_state_id, moved_disc)``. Raises ValueError for an illegal action."""
    if action not in legal_actions(state_id, num_discs):
        raise ValueError(f"Action {action} is not legal in state {state_id}")
    source, target = ACTION_MAP[action]
    disc = top_disc(state_id, source, num_discs)
    assert disc is not None
    return state_id + (target - source) * NUM_RODS**disc, disc
