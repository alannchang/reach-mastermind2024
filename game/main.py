from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from redis import Redis
import uuid
import json

from logic import GameSession

app = FastAPI(root_path="/mastermind")


# Connect to both game state and number store Redis instances
redis_game_state = Redis(host="redis_game_state_primary", port=6379, decode_responses=True)
redis_num_store = Redis(host="redis_number_store_primary", port=6379, decode_responses=True)

# Request models
class NewGameRequest(BaseModel):
    total_random_nums: int = 4
    max_attempts: int = 10


class GuessRequest(BaseModel):
    session_id: str
    guess: List[int]


class StatsRequest(BaseModel):
    session_id: str


def save_game(session_id: str, game: GameSession):
    data = game.to_dict()
    print("Saving to Redis:", data)      # debug
    redis_game_state.hset(session_id, mapping=game.to_dict())


def load_game(session_id: str) -> GameSession:
    data = redis_game_state.hgetall(session_id)
    if not data:
        return None
    print("Loaded from Redis:", data)   # debug

    data["secret_code"] = json.loads(data["secret_code"])
    data["history"] = json.loads(data["history"])
    data["max_attempts"] = int(data["max_attempts"])
    data["attempts_remaining"] = int(data["attempts_remaining"])
    data["victory"] = data["victory"].lower() == "true"
    return GameSession.from_dict(data)


def generate_secret_code(qty):
    pipeline = redis_num_store.pipeline()
    pipeline.lrange("random_numbers", 0, qty - 1)
    pipeline.ltrim("random_numbers", qty, -1)
    result = pipeline.execute()

    if not result[0]:
        return []
    return list(map(int, result[0]))


@app.get("/")
async def root():
    return {"docs_url": app.docs_url, "redoc_url": app.redoc_url}


@app.post("/start_game")
async def start_game(request: NewGameRequest):
    '''
    Create a new game session.
    Args:
        {"total_random_nums": 4, "max_attempts": 10}
    Returns:
        {"session_id": session_id, "message": "Game started!"}
    '''
    secret_code = generate_secret_code(request.total_random_nums)
    if not secret_code:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.  Please try again later.")

    session_id = str(uuid.uuid4())
    game = GameSession(secret_code, total_random_nums=request.total_random_nums, max_attempts=request.max_attempts)
    save_game(session_id, game)
    return {"session_id": session_id, "message": "Game started!"}


@app.post("/guess")
async def guess(request: GuessRequest):
    '''
    Submit a guess as to what the number combination/code is.
    Args:
        session_id (str): The ID provided when you started your game session.
        player_code (list): Your guess in the form of a list of integers.
    Returns:
        correct_numbers (int): How many numbers are correct regardless of location.
        correct_locations (int): How many numbers are in the correct location.
        attempts_remaining (int): How many attempts you have remaining.
    '''
    session_id = request.session_id
    player_code = request.guess

    # Fetch the game session
    game = load_game(session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Unable to locate game session.")

    if game.victory:
        return {"message": "Game already won!", "secret_code": game.secret_code}

    if game.attempts_remaining <= 0:
        return {"message": "Game over. You've used all attempts.", "secret_code": game.secret_code}

    if not game.validate_input(player_code):
        raise HTTPException(status_code=400, detail="Invalid input length.")

    correct_num, correct_loc = game.code_check(player_code)

    save_game(session_id, game)

    if game.victory:
        return {"message": "You win!", "secret_code": game.secret_code}

    if game.attempts_remaining <= 0:
        return {"message": "You lose!", "secret_code": game.secret_code}

    return {
        "correct_numbers": correct_num,
        "correct_locations": correct_loc,
        "attempts_remaining": game.attempts_remaining,
    }

@app.post("/stats")
async def retrieve_stats(request: StatsRequest):
    '''
    Get information on your game session.
    Args:
        session_id (str): The ID provided when you started your game session.
    Returns:
        attempts_remaining (int): The number of attempts remaining.
        max_attempts (int): The number of attempts you started with.
        history (list): History of guesses and their feedback.
    '''
    game = load_game(request.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Unable to locate game session.")

    return {
        "attempts_remaining": game.attempts_remaining,
        "max_attempts": game.max_attempts,
        "history": game.history
    }

