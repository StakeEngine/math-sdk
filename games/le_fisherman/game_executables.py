from game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from game_events import (
    super_cascade_event,
    golden_square_update_event,
    rainbow_activation_event,
    bucket_collection_event,
    clover_multiplier_event,
    bar_update_event,
    bonus_mode_enter_event,
    coin_reveal_event,
)
from src.events.events import (
    set_win_event,
    set_total_event,
    update_freespin_event,
    update_tumble_win_event,
)


class GameExecutables(GameCalculations):
    """Game dependent grouped functions."""

    def reset_golden_squares(self):
        self.golden_squares = [[False] * self.config.num_rows[reel] for reel in range(self.config.num_reels)]

    def reset_bar(self):
        self.bar_count = 0
        self.bar_level = 0
        self.extra_spins_awarded = 0

    def get_clusters_update_wins_super(self):
        """Find clusters, evaluate with Super Cascade, update win manager."""
        clusters = Cluster.get_clusters(self.board, "wild")
        return_data = {"totalWin": 0, "wins": []}

        self.board, self.win_data, self.golden_squares = self.evaluate_super_cascade_clusters(
            config=self.config,
            board=self.board,
            clusters=clusters,
            golden_squares=self.golden_squares,
            global_multiplier=self.global_multiplier,
            return_data=return_data,
        )

        # Emit super cascade events for each removed symbol type
        super_cascade_data = self.win_data.get("super_cascade", {})
        for sym, positions in super_cascade_data.items():
            if positions:
                super_cascade_event(self, sym, positions)

        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    def process_rainbow_on_board(self):
        """Check for Rainbow/Epic Rainbow and activate golden squares."""
        has_rainbow = False
        has_epic = False

        for reel in range(self.config.num_reels):
            for row in range(self.config.num_rows[reel]):
                if self.board[reel][row].name == "RB":
                    has_rainbow = True
                elif self.board[reel][row].name == "ERB":
                    has_epic = True

        if not has_rainbow and not has_epic:
            return

        # Epic Rainbow converts ALL positions to golden first
        if has_epic:
            for reel in range(self.config.num_reels):
                for row in range(self.config.num_rows[reel]):
                    self.golden_squares[reel][row] = True

        # Check if there are any golden squares to activate
        has_golden = any(self.golden_squares[r][c] for r in range(self.config.num_reels) for c in range(self.config.num_rows[r]))
        if not has_golden:
            return

        rainbow_type = "ERB" if has_epic else "RB"

        # Activate golden squares
        revealed_items, total_coin_value = self.activate_rainbow(
            self.board, self.golden_squares, self.bar_level, self.config
        )

        if not revealed_items:
            return

        # Emit coin reveal events
        for item in revealed_items:
            if item["value"] > 0:
                coin_reveal_event(self, (item["reel"], item["row"]), item["symbol"], item["value"])

        # Process bucket collection
        collections, collected_total = self.evaluate_bucket_collection(revealed_items)
        total_value = total_coin_value + collected_total

        for coll in collections:
            bucket_collection_event(self, coll["bucket_pos"], coll["bucket_type"], coll["collected"], coll["total"])

        # Apply clover multipliers
        final_value, clover_events = self.apply_clover_multipliers(revealed_items, total_value)

        for ce in clover_events:
            clover_multiplier_event(self, ce["pos"], ce["type"], ce["multiplier"], ce["affected"], ce["boosted_value"])

        # Emit rainbow activation event
        rainbow_activation_event(self, rainbow_type, revealed_items, final_value)

        # Add rainbow wins to win manager
        if final_value > 0:
            self.win_manager.update_spinwin(final_value)

        # Update golden squares event
        golden_square_update_event(self)

    def update_bar_on_scatter(self):
        """Update Big Catch Bar with scatters found on current board."""
        scatter_count = self.count_special_symbols("scatter")
        if scatter_count <= 0:
            return

        self.extra_spins_awarded = 0
        for _ in range(scatter_count):
            self.bar_count += 1
            if self.bar_count % self.config.bar_threshold == 0:
                self.bar_level = min(self.bar_level + 1, 4)
                self.tot_fs += 5
                self.extra_spins_awarded += 5

        bar_update_event(self)

    def determine_bonus_mode(self, scatter_count):
        """Map scatter count to bonus mode configuration."""
        scatter_count = min(scatter_count, 5)  # Cap at 5
        mode_config = self.config.bonus_modes.get(scatter_count, self.config.bonus_modes[3])
        self.bonus_mode_name = mode_config["name"]
        self.bar_level = mode_config["bar_level"]
        self.persistent_golden = mode_config["persistent_golden"]

    def set_end_tumble_event(self):
        """After tumble chain ends, emit win summary events."""
        if self.win_manager.spin_win > 0:
            set_win_event(self)
        set_total_event(self)

    def update_freespin(self):
        """Called before each new free spin."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.win_data = {}
        self.extra_spins_awarded = 0

        # Reset golden squares if NOT persistent mode
        if not self.persistent_golden:
            self.reset_golden_squares()
