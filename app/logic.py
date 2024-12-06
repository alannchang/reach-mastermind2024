import random


def temp_random_list(nums):
    '''
    This function will be replaced with the random.org API for generating random numbers
    '''
    random_nums = []
    for x in range(0, nums):
        random_nums.append(random.randint(0, 7))
    return random_nums


class GameSession:


    def __init__(self, total_random_nums=4, max_attempts=10):
        self.secret_code = temp_random_list(total_random_nums)
        self.max_attempts = max_attempts
        self.victory = False


    def validate_input(self, player_code):
        if len(player_code) != len(self.secret_code):
            return False
        return True


    def code_check(self, player_code):
        correct_num, correct_loc = self.find_matches(player_code)
        self.max_attempts -= 1
        if correct_loc == len(self.secret_code):
            self.victory = True
        return correct_num, correct_loc


    def find_matches(self, player_code):
        correct_num = 0
        correct_loc = 0
        incorrect_secret = []
        incorrect_player = []

        for i in range(0, len(player_code)):
            if self.secret_code[i] == player_code[i]:
                correct_loc += 1
                correct_num += 1
            else:
                incorrect_secret.append(self.secret_code[i])
                incorrect_player.append(player_code[i])
        
        secret_count = {}

        for num in incorrect_secret:
            secret_count[num] = secret_count.get(num, 0) + 1

        for num in incorrect_player:
            if num in secret_count and secret_count[num] > 0:
                correct_num += 1
                secret_count[num] -= 1

        return correct_num, correct_loc


    def print_result(self, correct_num, correct_loc): 
        if correct_num == 0 and correct_loc == 0:
            print("All incorrect.")
        else:
            print(f"{correct_num} correct number(s) and {correct_loc} correct location(s).")

        if correct_loc == len(self.secret_code) and correct_num == len(self.secret_code):
              self.victory = True
              return

        self.max_attempts -= 1
        print(f"{self.max_attempts} attempts remaining.")


    def game_loop(self):
        print(self.secret_code)     # For debugging
        
        while self.victory == False and self.max_attempts > 0:
            player_input = input("What's your guess? Please follow this format: 1 2 3 4\n")
            player_code = list(map(int, player_input.split()))

            if self.validate_input(player_code) == False:
                continue

            self.code_check(player_code)

        if self.victory:
            print("YOU WIN!")
        else:
            print("YOU LOSE!")

