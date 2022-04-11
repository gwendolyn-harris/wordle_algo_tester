from collections import Counter

def get_word_list(length):
    if length == 5:
        with open("dictionaries/wordle_dictionary.txt") as f:
            words = [x.strip() for x in f.readlines()]
    else:
        with open('dictionaries/words_alpha.txt') as f:
            all_words = [x.strip() for x in f.readlines()]
            words = [word for word in all_words if len(word) == length]
    return words

word_list = get_word_list(5)

PATTERN_COUNTER3 = Counter([word[i : i + 5] for word in word_list for i in range(5 - 3 + 1)])
PATTERN_WORD_LIST3 = [word for word in word_list if PATTERN_COUNTER3.most_common(1)[0][0] in word]

PATTERN_COUNTER2 = Counter([word[i : i + 5] for word in word_list for i in range(5 - 2 + 1)])
PATTERN_WORD_LIST2 = [word for word in word_list if PATTERN_COUNTER2.most_common(1)[0][0] in word]