import os
import re

def extract_english_words(file_in, file_out):
    with open(file_in, 'r', encoding='utf-8') as reader, open(file_out, 'w', encoding='utf-8') as writer:
        for line in reader:
            eng_words = re.findall('[a-zA-Z, ]+', line)
            eng_words = [e.strip() for e in eng_words if e.strip() != '' and e.strip() != ',']
            writer.write('%s\n' % (', '.join(eng_words)))

if __name__ == '__main__':
    extract_english_words('work/economy/articles.csv', 'work/economy/eng_words.txt')
