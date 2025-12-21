from .disc import Disc
from typing import List

class Rod:
    """
    Representation of the rods in the Tower of Hanoi game.
    Each rod has a numeric ID (e.g., 0, 1, 2 from left to right).
    Discs can only be added to or removed from the top of the stack.
    Stack implemented using a simple Python list.
    """
    def __init__(self, id: int, discs: List[Disc]):
        self.id = id
        self.discs = discs

    def __str__(self):
        rod_info = f"Rod(id={self.id})"

        disc_descriptions = []
        for disc in self.discs:
            # call the __str__ of each nested Disc object, with indentation
            disc_descriptions.append(str(disc))

        return rod_info + " | " + ", ".join(disc_descriptions)
    
    @property
    def top_disc(self):
        """Retrieve the disc object at the top of the stack."""
        return self.discs[-1]
    

if __name__ == "__main__":
    rod = Rod(id=0, discs=[Disc(id=0), Disc(id=1)])
    print(rod)