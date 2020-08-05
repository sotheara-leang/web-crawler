import os
import re
import configparser
from collections import Counter
from operator import itemgetter

from tqdm import tqdm

############# SETTING #############

config = configparser.ConfigParser()
config.read('km.ini')

COMMON      = config['COMMON']
ABBRE       = config['ABBREVIATION']
NUM         = config['NUM']
NUM_TY      = config['NUM_TY']
NUM_UNIT    = config['NUM_UNIT']
MONTH       = config['MONTH']
DIGIT       = config['DIGIT']
NUM_COMMON  = config['NUM_COMMON']

############# NUMBER #############

# 0: 6112: 48, ៩: 6121: 57

def en2km(num_en: str):
    if num_en is None:
        return None

    result = ''
    for c in num_en:
        if 48 > ord(c) > 57 and c != '.' and c != ',' and c != '-' and c != '+':
            raise Exception('Invalid en number: ', num_en)
        if c == '.':
            result += ','
        elif c == ',':
            continue
        elif c == '+' or c == '-':
            result += c 
        else:
            try:
                result += chr(ord(c) + 6064)
            except Exception as e:
                print('Error convert num: ', num_en)
                raise e
    return result

def km2en(num_km: str):
    if num_km is None:
        return None
    
    result = ''
    for c in num_km:
        if 6112 > ord(c) > 6121 and c != ',' and c != '.' and c != '-' and c != '+':
            raise Exception('Invalid km number: ', num_km)
        if c == ',':
            result += '.'
        elif c == '.':
            continue
        elif c == '+' or c == '-':
            result += c   
        else:
            try:
                result += chr(ord(c) - 6064)
            except Exception as e:
                print('Error convert num: ', num_km)
                raise e
    return result

def is_float_km(num_km: str):
    return ',' in num_km

def is_float_en(num_km: str):
    return '.' in num_km

def is_integer_num(num_km: str):
    return ',' not in num_km

def digits2word(digits_km: str):
    result = []
    digits_en = km2en(digits_km)
    for num in digits_en:
        result.append(NUM[num])
    return ' '.join(result)

def get_num_units(num_en: str, first_zeros=False):
    if num_en is None or num_en == '':
        return None, None

    num_en = num_en.replace(',', '')
    
    # prepare
    point = num_en.find('.')
    if point != -1:
        num = int(num_en[:point])
        num_point = num_en[point+1:]     # str
    else:
        num = int(num_en)
        num_point = None

    # number part
    if num == 0:
        unit = [0]
    else:
        i = 0
        unit = []
        while num > 0:
            unit.append(num % 10)
            i += 1
            num = num // 10
        
        if first_zeros is True:
            match = re.match('^[0]+', num_en)
            if match is not None:
                zeros = match.group(0)
                for z in zeros:
                    unit = unit + [0]

    # float part
    unit_point = None if num_point is None else []
    if num_point is not None:
        for num in num_point:
            unit_point.append(int(num))
    
    return unit[::-1], unit_point   # number part need to be reversed

def num2word_int(num_km: str, first_zeros=False):
    try:
        num_en = km2en(num_km)
        if num_en is None or num_en == '':
            return ''
        
        if is_float_en(num_en):
            raise Exception('num_km must not be float: ', num_km)
        
        result = []
    
        # sign number
        if num_en[0] == '+' or num_en[0] == '-':
            result.append(NUM_COMMON[num_en[0]])
            
            num_en = num_en[1:]
            num_km = num_km[1:]
        
        skip_unit = 0   # to skip number e.g. 1000000 -> 000000 
        num_units, _ = get_num_units(num_en, first_zeros)
        for idx, value in enumerate(num_units):
            if skip_unit > 0:
                skip_unit -= 1
                continue
    
            nums = num_units[idx:]
            if len(nums) == 1:
                # basic digit
                result.append(NUM[str(value)])
            elif nums == [0] * len(nums):
                # if sub number is 00000 stop as the previous step already converted the number
                break
            elif len(nums) == 2:
                num_str = ''.join([str(n) for n in nums])
                if num_str[0] == '0':
                    # first zero
                    num = NUM.get(str(value))
                    result.append(num)
                    continue
                else:
                    # get number from NUM and NUM_TY
                    num = NUM.get(num_str)
                    if num is None:
                        num = NUM_TY.get(num_str)
                
                    if num is not None:
                        result.append(num)
                        break
                    else:
                        # if not exists split the ty number: 25 -> 20, 5 will be converted next step
                        num_value = NUM_TY[str(value) + '0']
                        result.append(num_value)
            else:
                # get number from NUM_UNIT in form of 10^n
                num_unit = NUM_UNIT.get(str(pow(10, len(num_units) - idx - 1)))
                if num_unit is None:
                    sub_num = [str(value)]
                    for sub_idx, sub_value in enumerate(nums[1:]):
                        sub_num_unit = NUM_UNIT.get(str(pow(10, len(nums) - sub_idx - 1)))
                        if sub_num_unit is not None:
                            num_value = num2word(num_km[:len(sub_num)])
                            result.append('%s %s' % (num_value, sub_num_unit))
    
                            if first_zeros is False:
                                # define number of zero to be skipped. e.g. 100000000 -> 0000000 
                                match = re.match('^[0]+', num_en[sub_idx:])
                                if match is not None:
                                    zeros = match.group(0)
                                    skip_unit = len(zeros) + len(sub_num) - 1
                        
                            break                            
                        else:
                            sub_num.append(str(sub_value))
                else:
                    num_value = NUM[str(value)]
                    result.append('%s_%s' % (num_value, num_unit))
                    
                    if first_zeros is False:
                        # define number of zero to be skipped. e.g. 20012 -> 00
                        sub_value = num_en[idx + 1:]
                        match = re.match('^[0]+', sub_value)
                        if match is not None:
                            zeros = match.group(0)
                            skip_unit = len(zeros)
    
        return ' '.join(result)
    except Exception as e:
        print(e)
        raise e

def num2word(num_km):
    if num_km is None or num_km == '':
        return ''
    
    num_km = num_km.replace('.', '')
    
    if is_float_km(num_km):
        parts = num_km.split(',')
        decimal = num2word_int(parts[0])
        point = num2word_int(parts[1], first_zeros=True)
        
        return '%s %s %s' % (decimal, COMMON['FLOAT_POINT_W'], point)
    else:
        return num2word_int(num_km)

def date2word(date_km: str):
    """" dd/mm/yyyy, dd-mm-yyyy """
    if date_km is None or date_km == '':
        return ''
    
    parts = date_km.split('/')
    if parts is None:
        parts = date_km.split('-')
    
    if len(parts) != 3:
        raise Exception('invalid km date dd/mm/yy or dd-mm-yyyy: ', date_km)
    
    day = num2word(parts[0])
    month = MONTH.get(km2en(parts[1]))
    if month is None:
        raise Exception('invalid month: %s - %s ' % (month, date_km))
    
    month = '%s %s' % (COMMON['MONTH_KW'], month)
    year = num2word(parts[2])
    
    return '%s %s %s' % (day, month, year)

def time2word(time_km: str, show_hour_title=True):
    """" hh:mm:ss """
    if time_km is None or time_km == '':
        return ''

    parts = time_km.split(':')
    if len(parts) > 3:
        raise Exception('invalid km time hh:mm:ss: ', time_km)
    
    # hour
    result = num2word(parts[0])
    if show_hour_title is True:
        result = COMMON['TIME_HH'] + ' ' + result
        
    if len(parts) >= 2:
        mm = num2word(parts[1])
        result += ' %s %s' % (mm, COMMON['TIME_MN'])
    if len(parts) >= 3:
        ss = num2word(parts[2])
        result += ' %s %s' % (ss, COMMON['TIME_SS'])
        
    return result
    
############# TEXT #############

NUM_EN_REGX     = r'(([0-9]+([.,][0-9]+)?)(\s+%)?)'
NUM_KM_REGX     = r'(([០-៩]+([.,][០-៩]+)?)(\s+%)?)'
DATE_KM_REGX    = r'([០-៩]+[-\/][០-៩]+[-\/][០-៩]+)'
TIME_KM_REGX    = r'((%s )?[០-៩]{1,2}:[០-៩]{1,2}(:[០-៩]{1,2})?)' % COMMON['TIME_HH']
LEK_TO_REGX     = r'(([\u1780-\u17e9]+) ?ៗ)'

ESP_CHAR = {
    '«': '',
    '»': '',
    '៖': '',
    '”': '',
    '``': '',
    '"': '',
    "'": '',
    '!': '',
    '+': '',
    '-': '',
    '–': '',
    ' _ ': '',
    ':': '',
    ',': '',
    'ˉ': '',
    '.': '',
    '·': '',
    '(': '',
    ')': '',
    ';': '',
    '/': '',
    '\\': '',
    '[': '',
    ']': '',
    '>>': '',
    '<<': '',
    '<': '',
    '>': '',
    '=': '',
    '&': '',
    '%': '',
    '៚': '',
    '“': '',
    '…': '',
    '↘️': '',
    '✔': '',
    '@': '',
    'ៗ': '',
    '’': '',
    '#': ''
}

def clean_hidden_chars(text=''):
    return ''.join(c for c in text if c.isprintable())

def filter_word_tags(text=''):
    text = text.replace('_', ' ').replace('~', ' ').replace('^', ' ')
    return text

def remove_words_w_bracket(text):
    return re.sub(r'\(.*\)', '', text)

def remove_url(text):
    return re.sub(r'https?:\/\/.*[\r\n]*', '', text)

def normalize(text, esp_char=ESP_CHAR, clean_num=True, clean_lek_to=True):
    # clean
    text = clean_hidden_chars(text)
    
    # abbreviation
    for k, v in ABBRE.items():
        text = text.replace(k, v)
    
    # lek to
    if clean_lek_to is True:
        lek_tos = re.findall(LEK_TO_REGX, text)
        for lek_to, word in lek_tos:
            text = text.replace(lek_to, ' %s %s ' % (word, word), 1)
            
    # km date
    date_kms = re.findall(DATE_KM_REGX, text)
    for date_km in date_kms:
        date = date2word(date_km)
        text = text.replace(date_km, ' %s ' % date, 1)

    # km time
    time_kms = re.findall(TIME_KM_REGX, text)
    for time_km, _, _ in time_kms:
        if time_km.startswith(COMMON['TIME_HH']):
            time = time_km.replace(COMMON['TIME_HH'], '').strip()
            time = time2word(time)
        else:
            time = time2word(time_km)
    
        text = text.replace(time_km, ' %s ' % time, 1)

    # convert en num to km num
    num_ens = re.findall(NUM_EN_REGX, text)
    for num_en, num, _, sign in num_ens:
        for k, v in NUM_COMMON.items():
            sign = sign.replace(k, v)

        num = en2km(num)
        if sign.strip() != '':
            num += ' ' + sign
        
        text = text.replace(num_en, ' %s ' % num, 1)
    
    # km num
    num_kms = re.findall(NUM_KM_REGX, text)
    for num_km, num, _, sign in num_kms:
        # phone number
        pre_text = text[:text.index(num_km)]
        parts = pre_text.split()
        if ' '.join(parts[-2:]) == COMMON['TEL_PRE']:
            num = digits2word(num_km)
        else:
            for k, v in NUM_COMMON.items():
                sign = sign.replace(k, v)
    
            num = num2word(num)
            if clean_num is True:
                num = num.replace('_', ' ')
            if sign.strip() != '':
                num += ' ' + sign

        text = text.replace(num_km, ' %s ' % num, 1)

    # special characters
    if esp_char is not None:
        for k, v in esp_char.items():
            text = text.replace(k, v)
        
    # remove duplicate whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def generate_vocab(corpus_file, vocab_file, vocab_filter=[]):
    vocab_counter = Counter()
    print('Read corpus %s' % corpus_file)
    with open(corpus_file, 'r', encoding='utf-8') as reader:
        for line in tqdm(reader):
            if line == '':
                continue

            # vocab
            word_map = {}
            for word in line.split():
                num = word_map.get(word)
                if num is None:
                    word_map[word] = 1
                else:
                    word_map[word] = num + 1

            vocab_counter.update(word_map)

    # write vocab
    print('Write vocab %s ' % vocab_file)
    with open(vocab_file, 'w') as writer:
        lexicon = sorted(vocab_counter.items(), key=itemgetter(0))
        for word, n in lexicon:
            skip_word = False

            # filters
            for pattern in vocab_filter:
                if re.search(pattern, word):
                    skip_word = True
                    break

            if skip_word is True:
                continue

            writer.write('%s\n' % word)

def merge_corpus(corpus_dir, output_dir, text_filter=None, vocab_filter=[]):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    vocab_counter = Counter()

    sents = []
    for corpus in os.listdir(corpus_dir):
        corpus_file = os.path.join(corpus_dir, corpus)
        if os.path.isdir(corpus_file) or corpus.startswith('.'):
            continue
            
        print('Processing %s...' % corpus_file)

        with open(corpus_file, 'r', encoding='utf-8') as reader:
            for line in tqdm(reader):
                if line == '':
                    continue
                
                if text_filter is not None:
                    line = text_filter(line)
                    
                sents.append(line)

                # vocab
                word_map = {}
                for word in line.split():
                    num = word_map.get(word)
                    if num is None:
                        word_map[word] = 1
                    else:
                        word_map[word] = num + 1

                vocab_counter.update(word_map)

    # write corpus
    final_corpus_file = os.path.join(output_dir, 'corpus.txt')
    print('Write corpus %s ' % final_corpus_file)
    with open(final_corpus_file, 'w', encoding='utf-8') as writer:
        sents = set(sents)
        sents = list(sents)
        sents.sort()

        for line in sents:
            line = line.strip()
            if len(line) == 0:
                continue

            writer.write('%s\n' % line)
    
    # write vocab
    vocab_file = os.path.join(output_dir, 'corpus.vocab')
    print('Write vocab %s ' % vocab_file)
    with open(vocab_file, 'w') as writer:
        lexicon = sorted(vocab_counter.items(), key=itemgetter(0))
        for word, n in lexicon:
            skip_word = False
            
            # filters
            for pattern in vocab_filter:
                if re.search(pattern, word):
                    skip_word = True
                    break
            
            if skip_word is True:
                continue
                
            writer.write('%s\n' % word)

def correct_words(file_in, file_out, word_to_correct_file):
    print('Read %s ....' % word_to_correct_file)
    word_map = {}
    with open(word_to_correct_file, 'r') as reader:
        for line in reader:
            if line.startswith('#'):
                continue

            lines = line.split(',')
            word_map[lines[0]] = lines[1].strip()

    lines = []
    with open(file_in, 'r') as reader:
        for line in reader:
            for k, v in word_map.items():
                line = line.strip()
                line = line.replace(k, v)

            lines.append(line)

    with open(file_out, 'w') as writer:
        for line in lines:
            writer.write('%s\n' % line)

def extract_lek_to(corpus_dir, file_out):
    LEK_TO_TAG = re.compile('([\u1780-\u17e9]+) ([\u1780-\u17e9]+) ៗ')
    
    records = []

    for module_name in os.listdir(corpus_dir):
        if module_name.startswith('.'):
            continue

        module_dir = os.path.join(corpus_dir, module_name)
        if not os.path.isdir(module_dir):
            continue

        print('Processing %s ...' % module_name)

        articles_file = '%s/articles.txt' % module_dir
        with open(articles_file, 'r', encoding='utf-8') as reader:
            for line in reader:
                search = LEK_TO_TAG.search(line)
                if search is not None:
                    data = search.group()
                    records.append(data)

    with open(file_out, 'w', encoding='utf-8') as writer:
        records = set(records)
        records = list(records)
        records.sort()
        for record in records:
            writer.write('%s\n' % record)