import numpy as np
from lib.color_print import print_error, print_info, print_warning

class PartOfSpeech:
    def __init__(self, dictionary='data/dictionary.npy'):
        self.dictionary = np.load(dictionary,allow_pickle=True).item()
    def get_part_of_speech(self, word):
        # sourcery skip: remove-unnecessary-else, swap-if-else-branches
        heading = word[0]
        part_of_speechs = []
        for part_of_speech, content in self.dictionary.items():
            if heading not in list(content.keys()):
                continue
            if word in content[heading]:
                part_of_speechs.append(part_of_speech)
        if not part_of_speechs:
            print_warning(f"Word: {word} is not in the dictionary. Part of speech will be None!")
        return part_of_speechs
    def get_all_part_of_speech(self):
        return list(self.dictionary.keys())
    def get_dictionary(self):
        return self.dictionary
        