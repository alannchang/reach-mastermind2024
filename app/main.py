import random
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from logic import GameSession

app = FastAPI()

# Temporary in-memory store for game sessions
games = {}

# Request models
class NewGameRequest(BaseModel):
    total_random_nums: int = 4
    max_attempts: int = 10


class GuessRequest(BaseModel):
    session_id: str
    guess: List[int]


@app.post("/start_game/")
def start_game(request: NewGameRequest):
    # Create a new game session
    session_id = str(uuid.uuid4())
    game = GameSession(request.total_random_nums, request.max_attempts)
    games[session_id] = game
    return {"session_id": session_id, "message": "Game started!"}


@app.post("/guess/")
def guess(request: GuessRequest):
    session_id = request.session_id
    player_code = request.guess

    # Fetch the game session
    game = games.get(session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")

    if game.victory:
        return {"message": "Game already won!"}

    if game.max_attempts <= 0:
        return {"message": "Game over. You've used all attempts."}

    if not game.validate_input(player_code):
        raise HTTPException(status_code=400, detail="Invalid input length.")

    correct_num, correct_loc = game.code_check(player_code)
    if game.victory:
        return {"message": "You win!", "secret_code": game.secret_code}

    if game.max_attempts <= 0:
        return {"message": "You lose!", "secret_code": game.secret_code}

    return {
        "correct_numbers": correct_num,
        "correct_locations": correct_loc,
        "attempts_remaining": game.max_attempts,
    }

