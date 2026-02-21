import re
from collections import Counter
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


class HangmanSolver:
    def __init__(self, dictionary_path="words_alpha.txt"):
        self.load_dictionary(dictionary_path)
        self.word_length = 0
        self.current_pattern = []
        self.possible_words = []
        self.guessed_letters = set()
        self.match_found = False  # Switch from optimal order to frequency analysis

        # Optimal guessing order by word length
        self.optimal_order_map = {
            1: list("AI"),
            2: list("AOEIUMBH"),
            3: list("AEOIUYHBCK"),
            4: list("AEOIUYSBF"),
            5: list("SEAOIUYH"),
            6: list("EAIOUSY"),
            7: list("EIAOUS"),
            8: list("EIAOU"),
            9: list("EIAOU"),
            10: list("EIOAU"),
            11: list("EIOAD"),
            12: list("EIOAF"),
            13: list("IEOA"),
            14: list("IEO"),
            15: list("IEA"),
            16: list("IEH"),
            17: list("IER"),
            18: list("IEA"),
            19: list("IEA"),
            20: list("IE")
        }
        self.optimal_queue = []

    def load_dictionary(self, dictionary_path):
        try:
            with open(dictionary_path, 'r') as file:
                self.dictionary = [word.strip().upper() for word in file.readlines()]
        except FileNotFoundError:
            print(f"Dictionary file {dictionary_path} not found. Using a default dictionary.")
            self.dictionary = ["HANGMAN", "PYTHON", "DICTIONARY", "SOLVER", "GAME", 
                               "COMPUTER", "PROGRAMMING", "ALGORITHM", "CHALLENGE"]

    def start_solve(self, word_length):
        self.word_length = word_length
        self.current_pattern = ['_'] * word_length
        self.possible_words = [word for word in self.dictionary if len(word) == word_length]
        self.guessed_letters = set()
        self.match_found = False
        self.optimal_queue = self.optimal_order_map.get(word_length, list("ETAOINSHRDLU"))  # fallback
        
        if not self.possible_words:
            print(f"No {word_length}-letter words found in the dictionary.")
            return None

        return self.get_best_letter()

    def update_with_feedback(self, letter, positions):
        self.guessed_letters.add(letter)

        if positions == [0]:  # Letter not in word
            self.possible_words = [word for word in self.possible_words if letter not in word]
        else:
            self.match_found = True
            for pos in positions:
                self.current_pattern[pos-1] = letter

            new_possible_words = []
            for word in self.possible_words:
                match = True

                for pos in positions:
                    if word[pos-1] != letter:
                        match = False
                        break

                if match:
                    for i in range(self.word_length):
                        if self.current_pattern[i] == '_' and i+1 not in positions and word[i] == letter:
                            match = False
                            break

                if match:
                    for i in range(self.word_length):
                        if self.current_pattern[i] != '_' and word[i] != self.current_pattern[i]:
                            match = False
                            break

                if match:
                    new_possible_words.append(word)

            self.possible_words = new_possible_words

        return self.get_best_letter()

    def get_best_letter(self):
        if not self.possible_words:
            return "No matching words found in dictionary."

        if '_' not in self.current_pattern:
            return "Word solved: " + ''.join(self.current_pattern)

        if not self.match_found:
            while self.optimal_queue:
                next_letter = self.optimal_queue.pop(0)
                if next_letter not in self.guessed_letters:
                    return next_letter

        # Frequency analysis
        letter_counts = Counter()
        for word in self.possible_words:
            for char in set(word):
                if char not in self.guessed_letters:
                    letter_counts[char] += 1

        if not letter_counts:
            return "No more valid letters to guess."

        best_letter = letter_counts.most_common(1)[0][0]
        return best_letter

    def get_status(self):
        return {
            'pattern': ''.join(self.current_pattern),
            'possible_words_count': len(self.possible_words),
            'possible_words': self.possible_words[:10] if len(self.possible_words) <= 10 else []
        }

def main():
    print("Hangman Solver")
    print("==============")

    dict_path = input("Enter path to dictionary file (or press Enter for default): ")
    if not dict_path:
        dict_path = "words_alpha.txt"

    solver = HangmanSolver(dict_path)
    word_length = int(input("Enter the length of the word: "))

    next_letter = solver.start_solve(word_length)
    if next_letter is None:
        return

    status = solver.get_status()
    print(f"Current pattern: {status['pattern']}")
    print(f"Possible words: {status['possible_words_count']}")
    print(f"Next letter to try: {next_letter}")

    while '_' in solver.current_pattern:
        positions_input = input(f"Enter positions for letter '{next_letter}' (comma-separated, or 0 if not in word): ")

        try:
            positions = [int(pos) for pos in positions_input.split(',') if pos.strip()]
            next_letter = solver.update_with_feedback(next_letter, positions)
            status = solver.get_status()

            print(f"Current pattern: {status['pattern']}")
            print(f"Possible words: {status['possible_words_count']}")
            if status['possible_words_count'] <= 10 and status['possible_words']:
                print(f"Possible words: {', '.join(status['possible_words'])}")

            if isinstance(next_letter, str) and next_letter.startswith("Word solved"):
                print(next_letter)
                break
            elif "No more" in next_letter or "No matching" in next_letter:
                print(next_letter)
                break
            else:
                print(f"Next letter to try: {next_letter}")

        except ValueError:
            print("Please enter valid numbers separated by commas.")

if __name__ == "__main__":
    main()
# The code above is a Hangman solver that uses a dictionary to guess letters in a word.