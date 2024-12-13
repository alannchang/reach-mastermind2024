# REACH Backend Take Home Challenge
## Objective

To implement a Mastermind game, where a user plays against the computer and tries to guess a number combination or "code".
At the end of each attempt, the computer will tell the player how many numbers are correct numbers and how
many numbers are in the correct position/location.  Players are only allowed a fixed number of attempts to correctly
guess the number combination.

## Requirements

The user must have a way to interact/interface(i.e. command line, mobile app, web page, etc.) including:
- Ability to guess the combination of numbers
- Ability to view history of guesses and feedback received
- Ability to view number of guesses remaining

Random Integer Generator API (https://www.random.org/clients/http/api/) must be utilized for generating true random numbers.

The following parameters should be used to make the call to the API:
|URL Parameter|Recommended Value|Purpose|
|-|-|-|
|num|4|Number of integers requested|
|min|0|The smallest value returned|
|max|7|The largest value returned|
|col|1|Number of columns used to display the returned values|
|base|10|Use base 10 system|
|format|plain|Returns response in a plain text|
|rnd|new|Generate a new random numbers|

Any choice/combination of programming languages, tools, frameworks, etc. are permitted within reason(e.g. a game framework should not be used to implement the Mastermind game) 

## Stack/Technologies

- FastAPI 
- Nginx (load balancing) 
- Docker
- Redis (caching)
- MySQL (?) 

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

At this point, there are two ways to play the game in its current state:
- Manually sending API requests (using the curl command)
- By accessing the FastAPI docs for the game server and sending requests from there 

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

- POST /mastermind/end_game
  - Send a POST request with your "session_id" to end your game session

Example using curl:
```
curl -X POST "http://127.0.0.1:80/mastermind/end_game" -H "Content-Type: application/json" -d '{"session_id": "your-session-id"}'
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

To clean up the project by stopping and removing all containers, images, and builds:
```
docker-compose down --volumes --rmi all
```
Remove the "--volumes" flag to preserve the volumes for future use (i.e. to keep the data).

## Implementation Details and Rationale

```
                                            USERS                                       
                                            │││││                                       
                                            │││││                                       
                                            │││││                                       
                                            ▼▼▼▼▼                                       
                                      ┌───────────────┐                                 
                                      │┌─────┐ ┌─────┐│                                 
                     ┌─────────────── ││NGINX│ │NGINX││ ──────────────┐                 
                     │                │└─────┘ └─────┘│               │                 
                     │                └───────────────┘               │                 
                     │                                                │                 
                     │                                                │                 
                     ▼                                                ▼                 
┌─────────────────────────────────────────┐          ┌─────────────────────────────────┐
│┌───────────┐ ┌───────────┐ ┌───────────┐│          │┌──────────────┐ ┌──────────────┐│
││GAME SERVER│ │GAME SERVER│ │GAME SERVER││          ││NUMBER FACTORY│ │NUMBER FACTORY││
││ (FASTAPI) │ │ (FASTAPI) │ │ (FASTAPI) ││          ││  (FASTAPI)   │ │  (FASTAPI)   ││
│└───────────┘ └───────────┘ └───────────┘│          │└──────────────┘ └──────────────┘│
└─────┬──────────────┬──────────────┬─────┘          └────────────────┬────────────────┘
      │              │▲             │▲                                │▲                
      │              ││             ││                                ││                
      │              ││             ││                                ││                
      │              ││             ││                                ││                
      │              ▼│             ││                                ▼│                
      │   ┌───────────┴────────┐    ││                     ┌───────────┴──────────┐     
      │   │┌──────────────────┐│    ││                     │┌────────────────────┐│     
      │   ││GAME STATE PRIMARY││    ││                     ││NUMBER STORE PRIMARY││     
      │   ││     (REDIS)      ││    │└─────────────────────┤│      (REDIS)       ││     
      │   │└──────────────────┘│    └─────────────────────►│└────────────────────┘│     
      │   │┌──────────────────┐│                           │┌────────────────────┐│     
      │   ││GAME STATE REPLICA││                           ││NUMBER STORE REPLICA││     
      │   ││     (REDIS)      ││                           ││      (REDIS)       ││     
      │   │└──────────────────┘│                           │└────────────────────┘│     
      │   └────────────────────┘                           └──────────────────────┘     
      │                                                                                 
      │                                                                                 
      │                            ┌────────────────┐                                   
      │                            │┌──────────────┐│                                   
      │                            ││STORAGE/BACKUP││                                   
      └───────────────────────────►││   (MySQL)    ││                                   
                                   │└──────────────┘│                                   
                                   └────────────────┘                                   
```

When considering which language to use, Python was selected over C++ for the following reasons:
- rapid development time
- extensive libraries, especially for backend frameworks
- ease of use

When considering backend frameworks, FastAPI was selected over Flask for the following reasons:
- performance (one of the fastest python web frameworks)
- excellent async support
- automated API generation (SwaggerUI and ReDoc)

I considered using Apache Kafka but decided that the project would not be big enough to merit use
of a microservice architecture.  That could change if I were to continue working on this project.

Docker was used in this project for the following reasons:
- easy deployment and scaling
- consistency and reproducibility across different OSes
- easier to run applications relying on multiple services

Nginx was used for load balancing (round robin).

Throughout the project, consideration was given to scalability, redundancy, and performance to 
create a robust and efficient backend.


From the project directory, there are two directories, "game" and "number_factory":

Game:
- logic.py: where the actual "Mastermind" game logic resides and can be altered into a standalone CLI game
- main.py: imports from logic.py to integrate the game logic into a functioning API server

Number_factory:
- number_factory.py: responsible for managing random number generation, supply, etc.


### Additional Extensions 

Game extensions include but are not limited to:
- Ability to adjust the number of random numbers in the mastermind code
- Ability to decide how many attempts can be made before the game is over
- Games will automatically expire after 5 minutes (developer can adjust this)
- Games will automatically expire after the player either wins or runs out of guesses
- Ability to end games prematurely
- Players can share their session_id with others if they want to "collaborate"


Other extensions include but are not limited to:
- Data validation using Pydantic
- Error handling
- API documentation (SwaggerUI/ReDoc)
- A separate server, or "number_factory", that generates random numbers using random.org, stores
  them in a database for use, and replenishes the database as needed.


Extensions that were attempted:
- A database (like MySQL, PostgreSQL) that will act as persistent storage/backup for game state
- Multiple Nginx instances for redundancy, but sharing the same IP and port. 


## TO DO List
- Set up some way to rate limit requests made to API 
- Implement error messaging in case Redis goes down or is unavailable for any reason
- Set up database (MySQL?) for persistent storage
- Implement a dashboard, logging, etc. for better visibility on system
- Set up Redis Sentinels, Master-Slave architecture
- Create automated tests to test endpoints, stress test the system, etc.
- Consider WebSockets over REST, or maybe even WASM
- Consider using something like Apache Kafka and using microservice architecture as more features get added
