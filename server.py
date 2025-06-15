# server.py

from flask import Flask, jsonify
from blonderabbit_logic import run_game_round # Make sure this import is correct
from flask_cors import CORS # <--- ADD THIS LINE

app = Flask(__name__)
CORS(app) # <--- AND ADD THIS LINE RIGHT AFTER CREATING THE APP

@app.route('/play', methods=['POST', 'OPTIONS'])
def play_game():
    """
    This endpoint runs one round of the Blonderabbit game.
    It now accepts POST requests, as is standard for actions.
    """
    try:
        # Run your game logic from the imported script
        game_result = run_game_round()
        
        # The result should be a dictionary. We'll return it as JSON.
        # Ensure your run_game_round() returns a dict like:
        # { 'board': ..., 'win_details': ..., 'total_win': ... }
        return jsonify(game_result)

    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == '__main__':
    # Make sure to run on port 5000 to match the frontend
    app.run(debug=True, port=5000)