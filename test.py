#!/usr/bin/env python3

from collections import Counter
from typing import Callable, Tuple

class Word:
    def __init__(self, word_length: int):
        self.word = [" " for _ in range(word_length)]
        self.word_length = word_length
        self.correct = set()
        self.present = {}
        self.absent = set()
        self.word_list = ["hello", "pouts", "joust", "ground", "bouts", "helps", "aeros", "soare", "cower", "hells", "lilts", "plane", "gross", "twist", "prove"]

    def process_correct(self, correct_list: list[str]):
        '''Where list contains spaces and known letters'''
        for i, char in enumerate(correct_list):
            if char != " " and self.word[i] == " ":
                self.word[i] = char
        correct_letters = [char for char in correct_list if char != " "]
        self.correct.update(correct_letters)

    def process_present(self, present_dict: dict[str, set[int]]):
        '''Where present_dict is of the form {char: set(locations it is not)'''
        for char in present_dict.keys():
            if char in self.present:
                self.present[char].update(present_dict[char])
            else:
                self.present[char] = present_dict[char]

    def process_absent(self, absent_set: set):
        self.absent.update(absent_set)

    def process_word_list(self) -> bool:
        def is_absent(word_class, word: str) -> bool:
            for char in word:
                if char in word_class.absent:
                    return False
            return True

        def is_present(word_class: Word, word: str) -> bool:
            if not word_class.present:
                return True
            for char, locations in word_class.present.items():
                if char in word:
                    for i in locations:
                        if word[i] == char:
                            return False
                    return True
                else:
                    return False

        def is_correct(word_class, word: str) -> bool:
            for i, char in enumerate(word_class.word):
                if char != " " and char != word[i]:
                    return False
            return True

        new_word_list = []
        for word in self.word_list:
            if not (is_absent(self, word) and is_present(self, word) and is_correct(self, word)):
                continue
            new_word_list.append(word)
        self.word_list = new_word_list

    def update_word(self, guess_score: list[list[str, int]]):
        '''Where guess_score is in the form [[char, score], ...]'''
        correct = []
        present = {}
        absent = set()
        for i, info in enumerate(guess_score):
            if info[1] == 0:
                absent.add(info[0])
            if info[1] == 1:
                if info[0] in present:
                    present[info[0]].add(i)
                else:
                    present[info[0]] = {i}
            if info[1] == 2:
                correct.append(info[0])
            else:
                correct.append(" ")
        self.process_correct(correct)
        self.process_absent(absent)
        self.process_present(present)
        self.process_word_list()

def get_most_common_letters(word_list: list[str]) -> list[str]:
    char_counter = Counter("".join(word_list))
    most_common_chars = [ele[0] for ele in char_counter.most_common()]
    most_common_chars.reverse()
    return most_common_chars

def guess_basic(word_list: list[str], _word_length: int, _pattern_length: int) -> str:
    '''Returns a guess containing the the most common letters in the remaining list'''
    most_common_letters = get_most_common_letters(word_list)
    counter = Counter()

    for word in word_list:
        for i, letter in enumerate(most_common_letters):
            if letter in word:
                counter[word] += i
    print(len(word_list))
    print(counter.most_common(1))
    return counter.most_common(1)[0][0]

def run_basic_trial(answer: str, guess_func: Callable[[list[str], int, int], str], pattern: int = 1) -> Tuple[bool, str, int, dict[int: int]]:
    '''Runs a trial using the given algorithm on the given answer and returns a tuple of data about the run'''
    def check_doubles(answer: str, char: str, known: str) -> bool:
        '''Returns true if char is present elsewhere in the answer than it is already known'''
        short_answer = "".join([lett for i, lett in enumerate(answer) if not (lett == char and known[i] == char)])
        return char in short_answer

    def get_score(answer: str, guess: str, known: str) -> list[list[str, int]]:
        guess_score = []
        for i, char in enumerate(guess):
            if char == answer[i]:
                guess_score.append([char, 2])
            elif char in answer and check_doubles(answer, char, known):
                guess_score.append([char, 1])
            else:
                guess_score.append([char, 0])
        return guess_score

    word = Word(len(answer))
    guess_count = 0
    knowns_per_guess = {}
    prior_knowns = 0

    while "".join(word.word) != answer and guess_count < 6:
        guess_count += 1
        guess_score = get_score(answer, guess_func(word.word_list, word.word_length, pattern), "".join(word.word))
        word.update_word(guess_score)
        all_knowns = [ele[1] for ele in guess_score].count(2)
        knowns_per_guess[guess_count] =  all_knowns - prior_knowns
        prior_knowns = all_knowns
        print("".join(word.word))
    
    if "".join(word.word) != answer:
        return (False, answer, guess_count, knowns_per_guess)
    else:
        return (True, answer, guess_count, knowns_per_guess)

def get_unique_words(word_list: list[str], word_length: int) -> list[str]:
    '''Returns a list containing only words with all unique letters'''
    return [word for word in word_list if len(set(word)) == word_length]

word = Word(5)
print(get_unique_words(word.word_list, word.word_length))