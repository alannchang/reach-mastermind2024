from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from redis import Redis
from datetime import datetime
import json
import asyncio
import requests

LOW_COUNT_THRESHOLD = 10    # qty where warning will be triggered
AUTO_REGEN_THRESHOLD = 5    # qty where numbers will be added to number store automatically
RESUPPLY_QTY = 15           # qty (1 <= qty <= 1000) to generate when auto_regen_threshold met
CHECK_INTERVAL = 60         # seconds between automated checks

RANDOM_NUM_API = 'https://www.random.org/integers/'
QUOTA_API = 'https://www.random.org/quota/?format=plain'

app = FastAPI(root_path="/number_factory")

redis_num_store = Redis(host="redis_number_store_primary", port=6379, decode_responses=True)

# Request models
class GenerateRequest(BaseModel):
    qty: int


def generate_random_numbers(qty=4):
    '''
    Random integer generator api docs: https://www.random.org/clients/http/api/
    Possible values for 'num'.....1-1000
    For generating in bulk, set to 1000
    '''
    params = {
            'num': qty,
            'min': 0,
            'max': 7,
            'col': 1,
            'base': 10,
            'format': 'plain',
            'rnd': 'new',
            }

    try:
        response = requests.get(RANDOM_NUM_API, params=params)
        response.raise_for_status()

        numbers = response.text.strip().split()
        return list(map(int, numbers))

    except requests.RequestException as e:
            print(f"Error fetching data from www.random.org: {e}")
            return []


def check_quota():
    '''
    Quota checker api docs: https://www.random.org/clients/http/#quota
    Base quota = 1,000,000 bits
    Quota is decreased by number of bits required for each request, replenished daily.
    '''
    try:
        response = requests.get(QUOTA_API)
        response.raise_for_status()

        return int(response.text[:-1])      # [:-1] to remove newline character
    except requests.RequestException as e:
        print(f"Error fetching data from www.random.org: {e}")
        return ""


async def check_num_count():
    while True:
        count = redis_num_store.llen("random_numbers")
        if count < LOW_COUNT_THRESHOLD:
            print("WARNING: RANDOM NUMBER STORE VOLUME LOWER THAN THRESHOLD!\n" * 3)
        if count < AUTO_REGEN_THRESHOLD:
            numbers = generate_random_numbers(RESUPPLY_QTY) 
            redis_num_store.rpush("random_numbers", *numbers)
            print(f"WARNING: AUTO-REGEN THRESHOLD REACHED, {RESUPPLY_QTY} numbers added.")

        await asyncio.sleep(CHECK_INTERVAL)


@app.on_event("startup")
async def start_background_task():
    asyncio.create_task(check_num_count())


@app.get("/")
async def read_root():
    return {"docs_url": app.docs_url, "redoc_url": app.redoc_url}


@app.post('/generate')
def generate(request: GenerateRequest):
    '''
    Generate random numbers and stores them in Redis. (Synchronous operation to reduce burden on random.org server)
    Args:
        qty (int): The quantity of random numbers to generate.
    Returns:
        message (dict): Confirmation generation and storage in Redis.
    '''
    if not (1 <= request.qty <= 1000):
        raise HTTPException(status_code=400, detail="qty must be between 1 and 1000.")

    numbers = generate_random_numbers(request.qty)

    if not numbers:
        raise HTTPException(status_code=500, detail="Error fetching random numbers.")
    
    redis_num_store.rpush("random_numbers", *numbers)

    return {
        "message": f"{len(numbers)} random number(s) generated and stored in Redis.",
    }

'''
To monitor redis activity while the serveris running:
docker exec -it redis_number_store_primary redis-cli monitor
'''

@app.get('/quota')
async def quota_checker():
    '''
    Check on your current bit allowance.
    Args:
        None
    Returns:
        Allowance (string): Your current bit allowance in string format.
    '''
    return check_quota()

