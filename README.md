# REACH Backend Take Home Challenge
## Objective

To implement a mastermind game, where a user plays against the computer and tries to guess a number combination or "code".
At the end of each attempt, the computer will tell the player how many numbers are correct numbers and how
many numbers are in the correct position/location.  Players are only allowed a fixed number of attempts to correctly
guess the number combination.

## Requirements

- The user must have a way to interact/interface(i.e. command line, mobile app, web page, etc.):
  - Ability to guess
  - Ability to view previous guesses and receive feedback from the application
  - Number of guesses remaining

- Random Integer Generator API (https://www.random.org/clients/http/api/) must be utilized for generating true random numbers.

## Features



## Stack/Technologies

- FastAPI 
- Nginx (load balancing) 
- Docker
- Redis (caching)
- 

## How to get started

Git clone to download the repo:
```
git clone https://github.com/alannchang/reach-mastermind2024.git
```

Assuming you have Docker Engine installed and running, run these docker commands in the project directory:
```
docker compose build
docker compose up -d
```

The servers will be running in Docker containers now.

At this point, there are many ways to play the game in its current state:
- Manually sending API requests (using the curl command)
- By accessing the FastAPI docs for the game server and sending requests from there 
- By executing the play.py (in progress) script

### Game server API endpoints:

- POST /mastermind/start_game 
    - Send a POST request to create a new game session, specifying how many numbers to include 
      in the number combination and maximum number of attempts.
    - You'll receive a session_id to track your game session. Please keep this session_id.

Example using curl:

```
curl -X POST "http://127.0.0.1:80/mastermind/start_game" -H "Content-Type: application/json" -d '{"total_random_nums": 4, "max_attempts": 10}'
```

- POST /mastermind/guess
    - Send a POST request using the "session_id" provided from "start_game" request and your guess (list of integers).
    - You'll receive a response indicating how many numbers and positions are correct, and how many attempts are remaining.

Example using curl:

```
curl -X POST "http://127.0.0.1:80/mastermind/guess" -H "Content-Type: application/json" -d '{"session_id": "your-session-id", "guess": [1, 2, 3, 4]}'
```

- POST /mastermind/stats
  - Send a POST request with your "session_id" to get information on your game session
  - Information provided includes:
    - Maximum number of attempts
    - Number of attempts remaining
    - Prior history of guesses

Example using curl:

```
curl -X POST "http://127.0.0.1:80/mastermind/stats" -H "Content-Type: application/json" -d '{"session_id": "your-session-id"}'
```

### Number Factory API endpoints:

- POST /number_factory/generate
  - Send a POST request to generate random numbers 

Example using curl:

```
curl -X POST "http://127.0.0.1:80/number_factory/generate" -H "Content-Type: application/json" -d '{"qty": 4}'
```

- GET /number_factory/quota
  - Send a GET request to check on your current bit allowance.  Your bit allowance is used for generating random numbers.
    - Once your bit allowance is exhausted, the number factory will not longer be able to generate new random numbers 
      at its current IP address.  More details can be found at: https://www.random.org/clients/http/#quota
  - This endpoint is simply an internal wrapper of the quota checking API service provided by random.org.


To stop all activity and remove all containers, images, and builds:
```
docker-compose down --volumes --rmi all
```
Note: removing volumes will remove all data including data stored on databases.

## TO DO List
- Set up database (Postgres?) for persistent storage
- Implement proper (input) data validation, especially for the player guesses
- Implement a dashboard, logging, etc. for better visibility on system
- Set up Redis Sentinels, Master-Slave architecture

