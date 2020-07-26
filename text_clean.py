import re
import os
import text_normalize as tn 

lek_to_tag = re.compile('([\u1780-\u17e9]+) ([\u1780-\u17e9]+) ៗ')

CONT_SEP = '|@@@|'
CONT_SEP_SEG = '|@ @@|'

FILTERS_REGX = {
    r"^\s+": ''
}

def remove_words_w_bracket(text):
    return re.sub(r'\(.*\)', '', text)

def remove_url(text):
    return re.sub(r'https?:\/\/.*[\r\n]*', '', text)

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
        for line in reader:
            parts = line.split(CONT_SEP_SEG)
            for text in parts:
                # normalize text
                text = tn.normalize(text, clean_num=False)
                
                # split sents
                text = text.replace('៕', '។')
                sents = text.split('។')
                for sent in sents:
                    lines.append(sent)
                    
            break
    
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
    for module in os.listdir(corpus_dir):
        module_file = os.path.join(corpus_dir, module)
        if module.startswith('.') or os.path.isdir(module_file):
            continue

        print('Processing %s ...' % module)
        
        output_file = '%s/%s.txt' % (output_dir, module)
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
    clean_text('work/segment/rfa/economy.txt.c', 'work/clean/rfa/economy.c')
