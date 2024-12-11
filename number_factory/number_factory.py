from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from redis import Redis
import json
import requests

RANDOM_NUM_API = 'https://www.random.org/integers/'
QUOTA_API = 'https://www.random.org/quota/?format=plain'

app = FastAPI()

redis_host = "redis_game_state_primary"
redis_client = Redis(host=redis_host, port=6379, decode_responses=True)


# Request models
class GenerateNumbers(BaseModel):
    qty: int = 4


def generate_random_numbers(qty=4):
    '''
    possible values for 'num'.....1-1000
    for generating in bulk, set to 1000 (see bulk_generate())
    '''
    params = {
            'num': qty,
            'min': 0,
            'max': 7,
            'col': qty,
            'base': 10,
            'format': 'plain',
            'rnd': 'new',
            }

    try:
        response = requests.get(RANDOM_NUM_API, params=params)
        response.raise_for_status()

        # numbers = response.text.strip().split()
        # return list(map(int, numbers))
        return response.text

    except requests.RequestException as e:
            print(f"Error fetching data from www.random.org: {e}")
            return []


def bulk_generate():
    return generate_random_numbers(1000)


def check_quota():
    '''
    Documentation regarding quota/checker: https://www.random.org/clients/http/#quota
    Base quota = 1,000,000 bits
    Quota is decreased by number of bits required for each request
    Every day, shortly after midnight UTC, all quotas with less than 1,000,000 bits receive a free top-up of 200,000 bits. 
    If the server has spare capacity, you may get an additional free top-up earlier, but you should not count on it.
    '''
    try:
        response = requests.get(QUOTA_API)
        response.raise_for_status()

        return int(response.text[:-1])      # [:-1] to remove newline character
    except requests.RequestException as e:
        print(f"Error fetching data from www.random.org: {e}")
        return ""


@app.get("/number_factory/")
async def read_root():
    return {"message": "Random number factory up and running!"}


@app.get('/number_factory/generate')
async def generate(request: GenerateNumbers):
    numbers = generate_random_numbers(request.qty)
    if numbers:
        return numbers
    else:
        return HTTPException(status_code=500, detail="Error fetching random numbers")


@app.get('/number_factory/quota')
async def quota_checker():
    return check_quota()

