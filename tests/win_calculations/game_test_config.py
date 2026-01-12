from src.state.state import GeneralGameState


class GamestateTest(GeneralGameState):
    """Simple gamestate setup with abstract methods defined."""

    def __init__(self, config):
        self.config = config

    def assign_special_sym_function(self):
        self.special_symbol_functions = {"M": [self.assign_mult_property], "WM": [self.assign_mult_property]}

    def assign_mult_property(self, symbol) -> dict:
        symbol.assign_attribute({"multiplier": 3})

    def create_symbol(self, name: str) -> object:
        if name not in self.symbol_storage.symbol_defs.keys():
            raise ValueError(f"Symbol '{name}' is not registered.")
        symObject = self.symbol_storage.create_symbol(name)
        if name in self.special_symbol_functions:
            for func in self.special_symbol_functions[name]:
                func(symObject)

        return symObject

    def run_spin(self):
        pass

    def run_freespin(self):
        pass


def create_blank_board(reels, rows):
    """Initialise an empty array for the board."""
    board = [[[] for _ in range(rows[x])] for x in range(reels)]
    return board
