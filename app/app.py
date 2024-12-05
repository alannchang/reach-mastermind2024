from flask import Flask
import requests

app = Flask(__name__)

RANDOM_NUM_API = 'https://www.random.org/integers/'

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


@app.route('/random_numbers', methods=['GET'])
def random_numbers():
    numbers = generate_random_numbers()
    if numbers:
        return numbers
    else:
        return "Error fetching random numbers", 500

if __name__ == '__main__':
    app.run(debug=True)
