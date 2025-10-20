"""Set standard gamestate configuration with default values."""

from src.config.betmode import BetMode
from src.config.paths import PATH_TO_GAMES
import os


class Config:
    """
    Sets the default game-values required by the game-state.
    Custom values are set in the child class - gameConfig.py - located in the game directory
    """

    def __init__(self):
        self.rtp = 0.97
        self.game_id = "0_0_sample"
        self.provider_name = "sample_provider"
        self.provider_number = 1
        self.game_name = "sample_lines"
        self.output_regular_json = True  # if True, outputs .json if compression = False. If False, outputs .jsonl
        if self.game_id != "0_0_sample":
            self.construct_paths()

        # Win information
        self.min_denomination = 0.1
        self.wincap = 5000

        # Game details
        self.reels = 5
        self.row = 3
        self.paytable = {}  # Symbol information assumes ('kind','name) format
        self.special_symbols = {None: []}
        self.special_sybol_names = set()
        self.paying_symbol_names = set()
        self.all_valid_sym_names = set()

        # Define special Symbols properties - list all possible symbol states during game-play
        self.basegame_type = "basegame"
        self.freegame_type = "freegame"

        self.include_padding = True

        # Define the number of scatter-symbols required to award free-spins
        self.freespin_triggers = {}

        # Static game files
        self.reel_location = ""
        self.reels = {}
        self.padding_reels = {}  # symbol configuration displayed before the board reveal

        self.write_event_list = True

        self.bet_modes = []
        self.opt_params = {None: None}

        # Define win-levels for each game-mode, returned during win information events
        self.win_levels = {
            "standard": {
                1: (0, 0.1),
                2: (0.1, 1.0),
                3: (1.0, 2.0),
                4: (2.0, 5.0),
                5: (5.0, 15.0),
                6: (15.0, 30.0),
                7: (30.0, 50.0),
                8: (50.0, 100.0),
                9: (100.0, self.wincap),
                10: (self.wincap, float("inf")),
            },
            "endFeature": {
                1: (0.0, 1.0),
                2: (1.0, 5.0),
                3: (5.0, 10.0),
                4: (10.0, 20.0),
                5: (20.0, 50.0),
                6: (50.0, 100.0),
                7: (100.0, 500.0),
                8: (500.0, 2000.0),
                9: (2000.0, self.wincap),
                10: (self.wincap, float("inf")),
            },
        }

    def get_win_level(self, win_amount: float, winlevel_key: str) -> int:
        levels = self.win_levels[winlevel_key]
        for idx, pair in levels.items():
            if win_amount >= pair[0] and win_amount < pair[1]:
                return idx
        return RuntimeError(f"winLevel not found: {win_amount}")

    def get_special_symbol_names(self) -> None:
        """Get names of all special symbols"""
        self.special_sybol_names = set()
        for key in list(self.special_symbols.keys()):
            for sym in self.special_symbols[key]:
                self.special_sybol_names.add(sym)
        self.special_sybol_names = list(self.special_sybol_names)

    def get_paying_symbols(self) -> None:
        """Get names of all paying symbols."""
        self.paying_symbol_names = set()
        for tup in self.paytable:
            assert type(tup[1]) == str, "symbol name must be a string"
            self.paying_symbol_names.add(tup[1])
        self.payingSymbolnames = list(self.paying_symbol_names)

    def validate_reel_symbols(self, reel_strip: str) -> None:
        """Verify that all symbols on the reelstrip are valid."""
        uniqueSymbols = set()
        for reel in reel_strip:
            for row in reel:
                uniqueSymbols.add(row)

        isSubset = uniqueSymbols.issubset(set(self.all_valid_sym_names))
        if not isSubset:
            raise RuntimeError(
                f"Symbol identified in reel that does not exist in valid symbol names. \n"
                f"Valid Symbols: {self.all_valid_sym_names}\n"
                f"Detected Symbols: {list(uniqueSymbols)}"
            )

    def read_reels_csv(self, file_path):
        """Read csv from reelstrip path."""
        reelstrips = []
        count = 0
        with open(os.path.abspath(file_path), "r", encoding="UTF-8") as file:
            for line in file:
                split_line = line.strip().split(",")
                for reelIndex in range(len(split_line)):
                    if count == 0:
                        reelstrips.append(["".join([ch for ch in split_line[reelIndex] if ch.strip().isalnum()])])
                    else:
                        reelstrips[reelIndex].append(
                            "".join([ch for ch in split_line[reelIndex] if ch.strip().isalnum() and len(ch) > 0])
                        )

                    assert len(reelstrips[reelIndex][-1]) > 0, "Symbol is empty."
                count += 1

        return reelstrips

    def construct_paths(self) -> None:
        """Assign all output file paths"""
        self.reels_path = os.path.join(PATH_TO_GAMES, self.game_id, "reels")
        self.library_path = os.path.join(PATH_TO_GAMES, self.game_id, "library")
        self.publish_path = os.path.join(PATH_TO_GAMES, self.game_id, "library", "publish_files")

    def check_folder_exists(self, folder_path: str) -> None:
        """Check if target folder exists, and create if it does not."""
        if not (os.path.exists(folder_path)):
            os.makedirs(folder_path)

    def convert_range_table(self, pay_group: dict) -> dict:
        """
        requires self.pay_group to be defined
        for each symbol, define a pay-range dict structure: self.pay_group = {(x-y, 's'): z}
        where x-y defines the paying cluster size on the closed interval [x,y].
        e.g (5-5,'L1'): 0.1 will pay 0.1x for clusters of exactly 5 elements

        Function returns RuntimeError if there are overlapping ranges
        """
        paytable = {}
        for sym_details, payout in pay_group.items():
            min_connections, max_connections = sym_details[0][0], sym_details[0][1]
            symbol = sym_details[1]
            for i in range(min_connections, max_connections + 1):
                paytable[(i, symbol)] = payout

        return paytable
