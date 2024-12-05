import random

def temp_random_list(nums):
    random_nums = []
    for x in range(0, nums):
        random_nums.append(random.randint(0, 7))
    return random_nums


class GameSession:

    def __init__(self, total_random_nums=4, max_attempts=10):
        self.random_list = temp_random_list(total_random_nums)
        self.max_attempts = max_attempts
        self.victory = False
        
    def check_correct(self, player_guess):
        if len(self.random_list) != len(player_guess):
            print("Invalid guess! Try again!")
            return

        correct_num = 0
        correct_loc = 0

        for i in range(0, len(player_guess)):
            if self.random_list[i] == player_guess[i]:
                correct_num += 1
                correct_loc += 1
            elif int(player_guess[i]) in self.random_list[i:]:
                correct_num += 1

        print(f"{correct_num} correct number(s) and {correct_loc} correct location(s).")
        if correct_loc == len(self.random_list):
              self.victory = True
              return

        self.max_attempts -= 1
        print(f"{self.max_attempts} guesses remaining.")

    def game_loop(self):
        print(self.random_list)
        while self.victory == False and self.max_attempts > 0:
            player_input = input("What's your guess?")
            # validate input here
            guess_list = list(map(int, player_input.split()))
            self.check_correct(guess_list)
        if self.victory:
            print("YOU WIN!")
        else:
            print("YOU LOSE!")

 
