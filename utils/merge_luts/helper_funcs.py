"""Helper functions for input/output verification"""

import hashlib
import matplotlib.pyplot as plt


def compare_payouts_array(array1, array2):
    """verify freegame payouts match"""
    array1_obj = hashlib.md5()
    array2_obj = hashlib.md5()
    for x, y in zip(array1, array2):
        array1_obj.update(str(x).encode("utf-8"))
        array2_obj.update(str(y).encode("utf-8"))

    if array1_obj.hexdigest() != array2_obj.hexdigest():
        return False
    return True


def plot_function_shapes(payouts, old_base_weights, new_base_weights, bonus_weights):
    """visual confirmstion that distribution shapes match"""
    plt.scatter(payouts, old_base_weights, color="b")
    plt.scatter(payouts, new_base_weights, color="g")
    plt.scatter(payouts, bonus_weights, color="r", marker="x")
    plt.grid(True)
    plt.legend(["old weights", "new weights", "bonus weights"])
    plt.show()


def print_solution_summary(Efg, H, fg_contribution_in_base, fg_act_hr, fg_act_contribution, new_rtp):
    """display swapped lookup statsb"""
    print(f"Expectation value from feature (avg per trigger): {Efg:.3f}x")
    print(f"Base FG contribution target: {fg_contribution_in_base:.3f}")
    print(f"Actual FG RTP contribtuion: {fg_act_contribution:.3f}")
    print(f"Target hit-rate: {H:.6f} (1 in {1/H:.2f})")
    print(f"Derived hit-rate: {fg_act_hr:.6f} (1 in {1/fg_act_hr:.2f})")
    print(f"New total RTP: {new_rtp:.6f}")
