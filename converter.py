import json

with open("wordle_dictionary.txt") as f:
    all_words = [x.strip() for x in f.readlines()]

with open('wordle_dict.json','w') as out:
    json.dump(all_words, out)