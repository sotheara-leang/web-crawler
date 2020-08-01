import re
import os
from tqdm import tqdm

from text_normalize import remove_url, remove_words_w_bracket, normalize

lek_to_tag = re.compile('([\u1780-\u17e9]+) ([\u1780-\u17e9]+) ៗ')

CONT_SEP = '|@@@|'
CONT_SEP_SEG = r'\| ?@ ?@ ?@ ?\|'

ENG_WORD_PATTERN = r" [,.'#’→^<>!?()\w]+( [,.'#’→^<>!?()\w]+)+ "  # we leave in the text only english name

SENT_SEP = '។'
OTHER_SENT_SEP = ['៕', '?']

BEFORE_FILTER = {
    r'RFA( ?/ ?[a-zA-Z]+)+': '',
    r'(រូប ៖ )?RFA ': '',
}

AFTER_FILTER = {
    r'^RFA': '',
    r'Photo': '',
    r'PhotoProvided': '',
    r'Provided': '',
    r'PhotoScreenshot': '',
    r'RFAPhoto': '',
    r'VideoPlatformVideoManagementVideoSolutionsVideoPlayer': '',
    r'YO': '',
    r'^\w+$': ''
}

def extract_text_for_segment(file_in, file_out):
    with open(file_in, 'r', encoding='utf-8') as reader, open(file_out, 'w', encoding='utf-8') as writer:
        for line in reader:
            line = line.strip()
            line = remove_words_w_bracket(line)
            line = remove_url(line)

            line = re.sub(r"\s+", "", line)
            writer.write('%s\n' % line)

def extract_text_for_segment_corpus(corpus_dir, output_dir):
    for module_name in os.listdir(corpus_dir):
        if module_name.startswith('.'):
            continue

        module_dir = os.path.join(corpus_dir, module_name)
        if not os.path.isdir(module_dir):
            continue

        print('Processing %s ...' % module_name)

        articles_file = '%s/articles.txt' % module_dir
        output_file = '%s/%s.txt' % (output_dir, module_name)
        extract_text_for_segment(articles_file, output_file)

def clean_text(file_in, file_out):
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
                    # before filter
                    for k, v in BEFORE_FILTER.items():
                        sent = re.sub(k, v, sent)

                    # normalize text
                    sent = re.sub(ENG_WORD_PATTERN, '', sent)
                    sent = normalize(sent, clean_num=False)
                    
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

def clean_text_corpus(corpus_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for module in os.listdir(corpus_dir):
        module_file = os.path.join(corpus_dir, module)
        if os.path.isdir(module_file) or module.startswith('.') or module.endswith('.w'):
            continue

        print('Processing %s ...' % module)

        output_file = '%s/%s' % (output_dir, module)
        clean_text(module_file, output_file)

def extract_lek_to(corpus_dir, file_out):
    records = []

    for module_name in os.listdir(corpus_dir):
        if module_name.startswith('.'):
            continue

        module_dir = os.path.join(corpus_dir, module_name)
        if not os.path.isdir(module_dir):
            continue

        print('Processing %s ...' % module_name)

        articles_file = '%s/articles.csv' % module_dir
        with open(articles_file, 'r', encoding='utf-8') as reader:
            for line in reader:
                search = lek_to_tag.search(line)
                if search is not None:
                    data = search.group()
                    records.append(data)

    with open(file_out, 'w', encoding='utf-8') as writer:
        records = set(records)
        records = list(records)
        records.sort()
        for record in records:
            writer.write('%s\n' % record)

if __name__ == '__main__':
    # extract_lek_to('work/raw/rfa', 'work/lek_to.txt')
    # extract_text_for_segment_corpus('work/raw/rfa', 'work/extract/rfa')
    # clean_text('work/segment/rfa/politics.txt.c', 'work/clean/rfa/politics.txt.c')
    # clean_text('work/test.txt', 'work/clean/rfa/economy.c')
    clean_text_corpus('work/segment/rfa', 'work/clean/rfa')
