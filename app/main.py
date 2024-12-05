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
    try:
        response = requests.get(QUOTA_API)
        response.raise_for_status()

        return response.text
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

@app.get('/check_quota')
async def quota_checker():
    return check_quota()
    
