class Disc:
    """
    Representation of a disc in the Tower of Hanoi game.
    Each disc will be added onto rods in the game.
    Each disc has an ID which relates to its size - larger ID => larger sized disc.
    """
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"Disc(id={self.id})"