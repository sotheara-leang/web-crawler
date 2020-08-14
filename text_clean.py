import re
import os
from tqdm import tqdm

from text_normalize import *

CONT_SEP = '|@@@|'
CONT_SEP_SEG = r'\| ?@ ?@ ?@ ?\|'

SENT_SEP = '។'
OTHER_SENT_SEP = ['៕', '?', '៘']

REDU_PHR_EN_REGX    = r'([a-zA-Z0-9\']+( [a-zA-Z0-9\']+)*)( \1)'

BEFORE_FILTER = {

}

AFTER_FILTER = {
    r'^\b([a-zA-Z0-9\']+)( \1\b)+': '',
    r"^[a-zA-Z0-9.,?! \@']+$": '',          # exclude sentences contain only english words
    r'^\.| ?\.$| \. |\.{2,}': '',           # remove .
}

def extract_text_for_segment_corpus(corpus_dir, output_dir, correct_word_file):
    for module_name in os.listdir(corpus_dir):
        if module_name.startswith('.'):
            continue
        
        print('Processing %s ...' % module_name)

        articles_file = '%s/%s' % (corpus_dir, module_name)
        output_file = '%s/%s' % (output_dir, module_name)
        extract_text_for_segment(articles_file, output_file, correct_word_file)

def clean_text(file_in, file_out, correct_word_map=dict()):
    # read text
    lines = []
    with open(file_in, 'r', encoding='utf-8') as reader:
        for line in tqdm(reader):
            parts = re.split(CONT_SEP_SEG, line)
            for text in parts:
                # split sents
                for sep in OTHER_SENT_SEP:
                    text = text.replace(sep, SENT_SEP)

                # split sents
                sents = text.split(SENT_SEP)
                for sent in sents:
                    
                    sent = remove_segment_tags(sent)
                    
                    # before filter
                    for k, v in BEFORE_FILTER.items():
                        sent = re.sub(k, v, sent)
                        
                    # correct words
                    for k, v in correct_word_map.items():
                        if isinstance(k, re.Pattern):
                            sent = re.sub(k, v, text)
                        else:
                            sent = sent.replace(k, v)

                    # remove redundancy en phrases
                    redu_phrases = re.findall(REDU_PHR_EN_REGX, text)
                    for phrase, _, _ in redu_phrases:
                        text = text.replace('%s %s' % (phrase, phrase), phrase)

                    # normalize text
                    sent = normalize(sent, clean_num=True)

                    # after filter
                    for k, v in AFTER_FILTER.items():
                        sent = re.sub(k, v, sent)

                    if sent == '':
                        continue

                    lines.append(sent)

    # write
    with open(file_out, 'w', encoding='utf-8') as writer:
        lines = set(lines)
        lines = list(lines)
        lines.sort()

        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue

            writer.write('%s\n' % line)

def clean_text_corpus(corpus_dir, output_dir, word_to_correct_file):
    # read word to correct file
    correct_word_map = {}
    if word_to_correct_file is not None:
        regx = re.compile(r"^r'.*'$")
        with open(word_to_correct_file, 'r') as reader:
            for line in reader:
                if line.startswith('#'):
                    continue

                lines = line.split(',')
                if regx.match(lines[0]):
                    regx_ = re.compile(lines[0])
                    correct_word_map[regx_] = lines[1]
                else:
                    correct_word_map[lines[0]] = lines[1]
                    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for module in os.listdir(corpus_dir):
        module_file = os.path.join(corpus_dir, module)
        if os.path.isdir(module_file) or module.startswith('.') or module.endswith('.w'):
            continue

        print('Processing %s ...' % module)

        output_file = '%s/%s' % (output_dir, module)
        clean_text(module_file, output_file, correct_word_map)

def checkvocab(corpus_file, lexicon_file, output_file):
    # lexicon
    lexicon = dict()
    with open(lexicon_file, 'r', encoding='utf-8') as reader:
        for line in tqdm(reader):
            parts = line.split('\t')
            lexicon[parts[0]] = ''
    
    # vocab file
    vocab_counter = Counter()
    
    with open(corpus_file, 'r', encoding='utf-8') as reader:
        for line in tqdm(reader):
            if line == '':
                continue

            # vocab
            word_map = {}
            for word in line.split():
                if lexicon.get(word) is None:
                    num = word_map.get(word)
                    if num is None:
                        word_map[word] = 1
                    else:
                        word_map[word] = num + 1

            vocab_counter.update(word_map)

    with open(output_file, 'w', encoding='utf-8') as writer:
        lexicon = sorted(vocab_counter.items(), key=lambda item: item[1])
        
        for word, n in lexicon:
            writer.write('%s %s\n' % (word, n))

def clean_rfa_narrator_tags(corpus_dir, output_dir):
    NARRATOR_TAG = {
        r'(Photo)?( ?:)?( [a-zA-Z0-9\/\']+)*': '',
        r'AFP( ?/ ?[ a-zA-Z0-9\']+)*': '',
        r'RFA( ?/ ?[ a-zA-Z0-9\']+)+': '',
        r'រូប ?៖ ?RFA': '',
        r'។ ?RFA ?': '។'
    }

    for module_name in os.listdir(corpus_dir):
        if module_name.startswith('.'):
            continue

        module_dir = os.path.join(corpus_dir, module_name)
        if not os.path.isdir(module_dir):
            continue

        print('Processing %s ...' % module_name)
        
        lines = []
        articles_file = '%s/articles.txt' % module_dir
        # articles_file = '/Users/sotheara/PycharmProjects/web-crawler/work/text/text.txt'
        
        with open(articles_file, 'r', encoding='utf-8') as reader:
            for line in reader:
                line = line.strip()
                for k, v in NARRATOR_TAG.items():
                    line = re.sub(k, v, line, flags=re.IGNORECASE)

                lines.append(line)

        output_file = '%s/%s.txt' % (output_dir, module_name)
        # output_file = '/Users/sotheara/PycharmProjects/web-crawler/work/text/clean.txt'
        with open(output_file, 'w', encoding='utf-8') as writer:
            for line in lines:
                writer.write('%s\n' % line)
                
        # break

if __name__ == '__main__':
    correct_extract = 'work/text/correct-extract.txt'
    correct_word = 'work/text/correct-words.txt'
    # extract_lek_to('work/raw/rfa', 'work/lek_to.txt')
    # extract_text_for_segment('work/text/raw/cambodiadaily/news/articles.txt', 'work/text/extract/cambodiadaily/corpus.txt', None)
    # extract_text_for_segment_corpus('work/text/work', 'work/text/extract/rfa', correct_extract)
    # clean_text('work/text/segment/rfa/politics.txt.c', 'work/text/politics.txt.c', 'correct-words.txt')
    # clean_text('work/text/text.txt', 'work/text/clean.txt', correct_word)
    # clean_text_corpus('work/text/segment/cambodiadaily', 'work/text/clean', None)
    # merge_corpus('work/text/clean/rfa', 'work/text/final/rfa', filter_word_tags)
    # generate_vocab('work/text/work/rfa.txt', 'work/text/work/vocab.txt', [r'[a-zA-Z]+', r'[០-៩,.]+'])
    # clean_rfa_narrator_tags('work/text/raw/rfa', 'work/text/work')
    # merge_corpus('work/text/clean/rfa', 'work/text/clean')
