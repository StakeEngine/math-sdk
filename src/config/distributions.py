"""Set and verify simulation parameters."""

from typing import Union
import json


class Distribution:
    """Setup simulation conditions."""

    def __init__(
        self,
        criteria: str = None,
        quota: int = None,
        fixed_amt: int = None,
        win_criteria: Union[float, None] = None,
        conditions: dict = {},
        required_distribution_conditions: list = [
            "reel_weights",
        ],
        default_distribution_conditions: dict = {"force_wincap": False, "force_freegame": False},
    ):

        if fixed_amt is None:
            assert quota > 0, "non-zero quota value must be assigned"
        assert sum([quota is None, fixed_amt is None]) == 1, "must define either quota or fixed simulation amount"

        self._quota = quota
        self._criteria = criteria
        self._fixed_amt = fixed_amt
        self._required_distribution_conditions = required_distribution_conditions
        self._default_distribution_conditions = default_distribution_conditions
        self._win_criteria = win_criteria
        self.verify_and_set_conditions(conditions)

    def verify_and_set_conditions(self, conditions):
        """Enforce required conditions for distribution setup."""
        condition_keys = list(conditions.keys())
        for rk in self._required_distribution_conditions:
            assert rk in condition_keys, f"condition missing required key: {rk}\n condition_keys"

        for rk in list(self._default_distribution_conditions.keys()):
            if rk not in condition_keys:
                conditions[rk] = self._default_distribution_conditions[rk]

        self._conditions = conditions

    def get_criteria(self):
        """Return distribution criteria value."""
        return self._criteria

    def get_quota(self):
        """Return distribution simulation quota."""
        return self._quota

    def get_win_criteria(self):
        """Return criteria for simulation to pass."""
        return self._win_criteria

    def get_required_distribution_conditions(self):
        """Return what win conditions must be specified."""
        return self._required_distribution_conditions

    def get_fixed_amt(self):
        """Return fixed simulation amount for distribtuion"""
        return self._fixed_amt

    def __str__(self):
        return f"Criteria: {self._criteria}\nConditions: {json.dumps(self._conditions)}"
