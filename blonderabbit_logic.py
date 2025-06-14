# blonderabbit_logic.py
# A self-contained Python script for the Blonderabbit game logic.

import random

# --- Configuration ---
GRID_WIDTH = 7
GRID_HEIGHT = 7
# The aliases MUST match the keys in the frontend's assetPaths
SYMBOLS = ['GF', 'CT', 'SU', 'MO', 'EM', 'BE']
MIN_CLUSTER_SIZE = 5

def create_board():
    """Generates a new 7x7 grid of random symbols."""
    return [[random.choice(SYMBOLS) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def find_clusters(board):
    """
    Finds all clusters of 5 or more identical symbols.
    
    Returns:
        A list of clusters, where each cluster is a dictionary containing:
        - 'symbol': The alias of the symbol in the cluster.
        - 'positions': A list of [row, col] coordinates.
        - 'count': The number of symbols in the cluster.
    """
    clusters = []
    visited = set()

    for r in range(GRID_HEIGHT):
        for c in range(GRID_WIDTH):
            if (r, c) not in visited:
                target_symbol = board[r][c]
                cluster_positions = []
                stack = [(r, c)]
                visited.add((r, c))

                while stack:
                    row, col = stack.pop()
                    cluster_positions.append([row, col])

                    # Check neighbors (up, down, left, right)
                    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nr, nc = row + dr, col + dc

                        if 0 <= nr < GRID_HEIGHT and 0 <= nc < GRID_WIDTH and \
                           (nr, nc) not in visited and board[nr][nc] == target_symbol:
                            visited.add((nr, nc))
                            stack.append((nr, nc))
                
                if len(cluster_positions) >= MIN_CLUSTER_SIZE:
                    clusters.append({
                        'symbol': target_symbol,
                        'positions': cluster_positions,
                        'count': len(cluster_positions)
                    })
    return clusters

def calculate_win(clusters):
    """
    Calculates the total win amount based on the found clusters.
    This is a simple placeholder calculation.
    """
    total_win = 0
    # Base value for each symbol type
    symbol_values = {'GF': 1, 'CT': 0.8, 'SU': 0.6, 'MO': 0.4, 'EM': 0.2, 'BE': 0.2}
    
    for cluster in clusters:
        symbol = cluster['symbol']
        count = cluster['count']
        # Win = (number of symbols in cluster - min size + 1) * symbol value
        win = (count - MIN_CLUSTER_SIZE + 1) * symbol_values.get(symbol, 0.1)
        total_win += win
        
    return total_win

# --- Main Game Function ---
# This is the function that server.py will import and call.
def run_game_round():
    """
    Executes a single, complete round of the Blonderabbit game.
    
    Returns:
        A dictionary containing the full game state for the frontend.
    """
    board = create_board()
    win_details = find_clusters(board)
    total_win = calculate_win(win_details)
    
    # This is the final data structure the frontend will receive as JSON
    game_result = {
        'board': board,
        'win_details': win_details,
        'total_win': round(total_win, 2)
    }
    
    return game_result

# Example of how to run it directly for testing:
if __name__ == '__main__':
    game_data = run_game_round()
    import json
    print(json.dumps(game_data, indent=2))
