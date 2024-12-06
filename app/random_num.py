from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

RANDOM_NUM_API = 'https://www.random.org/integers/'
QUOTA_API = 'https://www.random.org/quota/?format=plain'

def generate_random_numbers():
    params = {
            'num': 4,
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


@app.get("/")
async def read_root():
    return {"message": "FastAPI is set up!"}


@app.get('/random_numbers')
async def random_numbers():
    numbers = generate_random_numbers()
    if numbers:
        return numbers
    else:
        return HTTPException(status_code=500, detail="Error fetching random numbers")


@app.get('/quota')
async def quota_checker():
    return check_quota()
    
