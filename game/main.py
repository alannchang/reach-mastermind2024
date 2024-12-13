import json
import uuid
from typing import List

from fastapi import FastAPI, HTTPException
from logic import GameSession
from pydantic import BaseModel, Field, ValidationError
from redis import Redis

GAME_SESSION_TIMEOUT = 300  # Games will expire 5 minutes from creation

app = FastAPI(root_path="/mastermind")

# Connect to both game state and number store
redis_game_state = Redis(
    host="redis_game_state_primary", port=6379, decode_responses=True
)
redis_num_store = Redis(
    host="redis_number_store_primary", port=6379, decode_responses=True
)

# Request models
class NewGameRequest(BaseModel):
    total_random_nums: int = Field(
        ..., ge=1, le=1000, description="Number of random numbers (1-1000)."
    )
    max_attempts: int = Field(
        ..., ge=1, description="Maximum number of attempts(must be greater than 0)."
    )


class GuessRequest(BaseModel):
    session_id: str
    guess: List[int] = Field(..., description="Your guess as a list of integers.")


class StatsRequest(BaseModel):
    session_id: str


class EndGameRequest(BaseModel):
    session_id: str


def save_game(session_id: str, game: GameSession):
    data = game.to_dict()
    redis_game_state.hset(session_id, mapping=data)


def load_game(session_id: str):
    data = redis_game_state.hgetall(session_id)
    if not data:
        return None

    # Deserialize
    data["secret_code"] = json.loads(data["secret_code"])
    data["history"] = json.loads(data["history"])
    data["max_attempts"] = int(data["max_attempts"])
    data["attempts_remaining"] = int(data["attempts_remaining"])
    data["victory"] = data["victory"].lower() == "true"
    return GameSession.from_dict(data)


def remove_game(session_id: str):
    result = redis_game_state.delete(session_id)
    return result > 0


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
    """
    Create a new game session.
    Args:
        {"total_random_nums": 4, "max_attempts": 10}
    Returns:
        {"session_id": session_id, "message": "Game started! You have {GAME_SESSION_TIMEOUT} seconds to guess the secret code before this session expires.  Good luck!"}
    """
    try:
        secret_code = generate_secret_code(request.total_random_nums)
        if not secret_code:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable.  Please try again later.",
            )

        session_id = str(uuid.uuid4())
        game = GameSession(secret_code, max_attempts=request.max_attempts)
        save_game(session_id, game)
        redis_game_state.expire(session_id, GAME_SESSION_TIMEOUT)
        return {
            "session_id": session_id,
            "message": f"Game started! You have {GAME_SESSION_TIMEOUT} seconds to guess the secret code before this session expires.  Good luck!",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/guess")
async def guess(request: GuessRequest):
    """
    Submit a guess as to what the number combination/code is.
    Args:
        session_id (str): The ID provided when you started your game session.
        player_code (list): Your guess in the form of a list of integers.
    Returns:
        correct_numbers (int): How many numbers are correct regardless of location.
        correct_locations (int): How many numbers are in the correct location.
        attempts_remaining (int): How many attempts you have remaining.
    """
    session_id = request.session_id
    player_code = request.guess

    game = load_game(session_id)
    if not game:
        raise HTTPException(
            status_code=404,
            detail="Unable to locate game session.  Session may have timed out.",
        )

    if not game.valid_len(player_code):
        raise HTTPException(status_code=400, detail="Invalid input length.")

    if not game.in_range(player_code):
        raise HTTPException(
            status_code=400, detail="Please select numbers within the range of 0 to 7."
        )

    correct_num, correct_loc = game.code_check(player_code)

    save_game(session_id, game)

    if game.victory and remove_game(session_id):
        return {
            "message": "You win! Start a new game session to play again.",
            "secret_code": game.secret_code,
        }

    if game.attempts_remaining <= 0 and remove_game(session_id):
        return {
            "message": "You lose! Start a new game session to try again.",
            "secret_code": game.secret_code,
        }

    return {
        "correct_numbers": correct_num,
        "correct_locations": correct_loc,
        "attempts_remaining": game.attempts_remaining,
    }


@app.post("/stats")
async def retrieve_stats(request: StatsRequest):
    """
    Get information on your game session.
    Args:
        session_id (str): The ID provided when you started your game session.
    Returns:
        attempts_remaining (int): The number of attempts remaining.
        max_attempts (int): The number of attempts you started with.
        history (list): History of guesses and their feedback.
    """
    game = load_game(request.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Unable to locate game session.")

    return {
        "attempts_remaining": game.attempts_remaining,
        "max_attempts": game.max_attempts,
        "history": game.history,
    }


@app.post("/end_game")
async def end_game(request: EndGameRequest):
    """
    Manually end a game session.
    Args:
        session_id (str): The ID provided when you started your game session.
    Returns:
        None
    """
    if remove_game(request.session_id):
        return {
            "session_id": request.session_id,
            "message": "Game session successfully removed.",
        }
    else:
        raise HTTPException(status_code=404, detail="Game session not found.")
