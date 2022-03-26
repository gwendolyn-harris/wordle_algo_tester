#!/usr/bin/env python3

import json
from math import ceil
from tqdm import tqdm
from os import cpu_count
from functools import partial
from collections import Counter
from typing import Callable, Tuple, List, Set, Dict
from multiprocessing import Pool, set_start_method


def get_word_list(length):
    if length == 5:
        with open("dictionaries/wordle_dictionary.txt") as f:
            words = [x.strip() for x in f.readlines()]
    else:
        with open('dictionaries/words_alpha.txt') as f:
            all_words = [x.strip() for x in f.readlines()]
            words = [word for word in all_words if len(word) == length]
    return words


class Word:
    def __init__(self, word_length: int):
        self.word = [" " for _ in range(word_length)]
        self.word_length = word_length
        self.correct = set()
        self.present = {}
        self.absent = set()
        self.word_list = get_word_list(word_length)

    def process_correct(self, correct_list: List[str]):
        '''Where list contains spaces and known letters'''
        self.correct.update(correct_list)
        for i, char in enumerate(correct_list):
            if char != " " and self.word[i] == " ":
                self.word[i] = char

    def process_present(self, present_dict: Dict[str, Set[int]]):
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

    def update_word(self, guess_score: List[List[str, int]]):
        '''Where guess_score is in the form [[char, score], ...]'''
        correct = []
        present = {}
        absent = set()
        for i, info in enumerate(guess_score):
            if info[1] == 0 and info[0] not in self.word:
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


def get_most_common_letters(word_list: List[str]) -> List[str]:
    char_counter = Counter("".join(word_list))
    most_common_chars = [ele[0] for ele in char_counter.most_common()]
    most_common_chars.reverse()
    return most_common_chars


def guess_basic(word_list: List[str], _word_length: int, _pattern_length: int) -> str:
    '''Returns a guess containing the the most common letters in the remaining list'''
    most_common_letters = get_most_common_letters(word_list)
    counter = Counter()

    for word in word_list:
        for i, letter in enumerate(most_common_letters):
            if letter in word:
                counter[word] += i

    return counter.most_common(1)[0][0]


def get_unique_words(word_list: List[str], word_length: int) -> List[str]:
    '''Returns a list containing only words with all unique letters'''
    return [word for word in word_list if len(set(word)) == word_length]


def guess_unique(word_list: List[str], word_length: int, _pattern_length: int) -> str:
    '''Returns a guess containing the most common characters that are unique in the remaining list'''
    most_common_letters = get_most_common_letters(word_list)
    unique_char_word_list = get_unique_words(word_list, word_length)
    if not unique_char_word_list:
        return guess_basic(word_list, word_length, _pattern_length)

    counter = Counter()
    for word in unique_char_word_list:
        for i, letter in enumerate(most_common_letters):
            if letter in word:
                counter[word] += i
    
    return counter.most_common(1)[0][0]


def guess_column(word_list: List[str], word_length: int, _pattern_length: int) -> str:
    '''Returns a guess containing the most common characters for each place in the word'''
    column_chars = []
    for i in range(word_length):
        column_chars.append("".join([word[i] for word in word_list]))

    column_counters = [Counter() for _ in column_chars]
    for i, column in enumerate(column_chars):
        for char in column:
            column_counters[i][char] += 1
    
    word_counter = Counter()
    for word in word_list:
        for i, char in enumerate(word):
            word_counter[word] += column_counters[i][char]
    
    return word_counter.most_common(1)[0][0]


def guess_column_unique(word_list: List[str], word_length: int, _pattern_length: int) -> str:
    '''Returns a guess containing the most common characters for each place in the word with all unique letters'''
    column_chars = []
    for i in range(word_length):
        column_chars.append("".join([word[i] for word in word_list]))

    column_counters = [Counter(column) for column in column_chars]

    unique_char_words = get_unique_words(word_list, word_length)
    if not unique_char_words:
        return guess_column(word_list, word_length, _pattern_length)

    word_counter = Counter()
    for word in unique_char_words:
        for i, char in enumerate(word):
            word_counter[word] += column_counters[i][char] 

    return word_counter.most_common(1)[0][0]


def guess_pattern(word_list: List[str], word_length: int, pattern_length: int) -> str:
    '''Returns a guess containing the most common pattern of the given length and the most common letters'''
    pattern_counter = Counter([word[i : i + pattern_length] for word in word_list for i in range(word_length - pattern_length + 1)])
    most_common_letters = get_most_common_letters(word_list)
    pattern_word_list = [word for word in word_list if pattern_counter.most_common(1)[0][0] in word]
    word_counter = Counter()

    for word in pattern_word_list:
        for i, letter in enumerate(most_common_letters):
            if letter in word:
                word_counter[word] += i

    return word_counter.most_common(1)[0][0]


def guess_pattern_unique(word_list: List[str], word_length: int, pattern_length: int) -> str:
    '''Returns a guess containing the most common pattern of the given length and the most common unique letters'''
    pattern_counter = Counter([word[i : i + pattern_length] for word in word_list for i in range(word_length - pattern_length + 1)])
    most_common_letters = get_most_common_letters(word_list)
    pattern_word_list = [word for word in word_list if pattern_counter.most_common(1)[0][0] in word]
    unique_char_words = get_unique_words(pattern_word_list, word_length)
    if not unique_char_words:
        return guess_pattern(word_list, word_length, pattern_length)
    word_counter = Counter()

    for word in unique_char_words:
        for i, letter in enumerate(most_common_letters):
            if letter in word:
                word_counter[word] += i

    return word_counter.most_common(1)[0][0]


def run_basic_trial(answer: str, guess_func: Callable[[List[str], int, int], str], pattern: int = 1) -> Tuple[bool, str, int, Dict[int: int]]:
    '''Runs a trial using the given algorithm on the given answer and returns a tuple of data about the run'''
    def check_doubles(answer: str, char: str, known: str) -> bool:
        '''Returns true if char is present elsewhere in the answer than it is already known'''
        short_answer = "".join([lett for i, lett in enumerate(answer) if not (lett == char and known[i] == char)])
        return char in short_answer

    def get_score(answer: str, guess: str, known: str) -> List[List[str, int]]:
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

    return ("".join(word.word) == answer, answer, guess_count, knowns_per_guess)

if __name__ == '__main__':
    set_start_method('fork')
    test_params = [(guess_basic, 1), (guess_unique, 1), (guess_column, 1), (guess_column_unique, 1), (guess_pattern, 2), (guess_pattern, 3), (guess_pattern_unique, 2), (guess_pattern_unique, 3)]
    all_stats = {}

    for func, pattern in tqdm(test_params, desc="Tests completed", units="tests"):
        stats = {"Success": [], "Guesses": [], "Knowns Gained Per Guess": {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}, "Failures": []}
        word_list = get_word_list(5)
        with Pool(ceil(cpu_count() * 1.1)) as pool:
            for success, answer, guess_count, knowns_per_guess in tqdm(pool.imap(partial(run_basic_trial, guess_func=func, pattern=pattern), word_list), total=len(word_list), desc=func.__name__, units="words"):
                stats["Success"].append(success)
                stats["Guesses"].append(guess_count)
                if not success:
                    stats["Failures"].append(answer)
                for guess, knowns_gained in knowns_per_guess.items():
                    stats["Knowns Gained Per Guess"][guess].append(knowns_gained)
        all_stats[func.__name__ + str(pattern) if pattern != 1 else None] = stats

    with open('Basic_Test_Data.json', 'w') as out:
        json.dump(all_stats, out)