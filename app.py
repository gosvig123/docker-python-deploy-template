import berserk
from dotenv import load_dotenv
import os
from flask import Flask, jsonify
import threading
import random

load_dotenv()
LICHESS_TOKEN = os.getenv('LICHESS_TOKEN')
if LICHESS_TOKEN is None:
    raise ValueError('LICHESS_TOKEN is not set')

session = berserk.TokenSession(LICHESS_TOKEN)
client = berserk.Client(session=session)

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/my_lichess_profile')
def my_lichess_profile():
    profile = client.account.get()
    return jsonify(profile)

def handle_game(client, game_id):
    """Handles game play logic for an active game."""
    stream = client.board.stream_game_state(game_id)
    for event in stream:
        if event['type'] == 'gameFull':
            print(f"Game {game_id} started.")
        elif event['type'] == 'gameState':
            is_my_turn = event['moves'].count(' ') % 2 == 0  # Adjust based on player color
            if is_my_turn:
                # Fetch the current game state to get legal moves
                game_state = client.board.get_game_state(game_id)
                legal_moves = game_state['moves'].split(' ')
                if legal_moves:
                    move = random.choice(legal_moves)  # Select a random legal move
                    client.board.make_move(game_id, move)
                    print(f"Made move {move} in game {game_id}")

def handle_events(client):
    """Listens for incoming events and handles them."""
    for event in client.board.stream_incoming_events():
        if event['type'] == 'challenge':
            challenge_id = event['challenge']['id']
            client.challenges.accept(challenge_id)
            print(f"Accepted challenge: {challenge_id}")
        elif event['type'] == 'gameStart':
            game_id = event['game']['id']
            threading.Thread(target=handle_game, args=(client, game_id)).start()
            print(f"Game started: {game_id}")

def run_event_listener():
    threading.Thread(target=handle_events, args=(client,)).start()

if __name__ == '__main__':
    run_event_listener()
    app.run(debug=True, host='0.0.0.0', port=9000)
