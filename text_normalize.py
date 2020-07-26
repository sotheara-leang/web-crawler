import re
import configparser

#############

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

#############

# 0: 6112: 48, ៩: 6121: 57

def en2km(num_en: str):
    if num_en is None:
        return None

    result = ''
    for c in num_en:
        if ord(c) < 48 or ord(c) > 57 and c != '.' and c != ',':
            raise Exception('Invalid en number: ', num_en)
        if c == '.':
            result += ','
        elif c == ',':
            # result += ','
            continue
        else:
            result += chr(ord(c) - 6064)
    return result

def km2en(num_km: str):
    if num_km is None:
        return None
    
    result = ''
    for c in num_km:
        if ord(c) < 6112 or ord(c) > 6121 and c != ',' and c != '.':
            raise Exception('Invalid km number: ', num_km)
        if c == ',':
            result += '.'
        elif c == '.':
            # result += ','
            continue
        else:
            result += chr(ord(c) - 6064)
    return result

def is_float_km(num_km: str):
    return ',' in num_km

def is_float_en(num_km: str):
    return '.' in num_km

def is_integer_num(num_km: str):
    return ',' not in num_km

def tel2word(tel: str):
    result = []
    for num in tel:
        result.append(NUM[str(num)])
    return ' '.join(result)

def get_num_units(num_en: str, first_zero=False):
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
        
        if first_zero is True:
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

def num2word_int(num_km: str, first_zero=False):
    num_en = km2en(num_km)
    if num_en is None or num_en == '':
        return ''
    if is_float_en(num_en):
        raise Exception('num_km must not be float: ', num_km)
    
    result = []
    
    skip_unit = 0
    num_units, _ = get_num_units(num_en, first_zero)
    for idx, value in enumerate(num_units):
        if skip_unit > 0:
            skip_unit -= 1
            continue

        nums = num_units[idx:]
        if len(nums) == 1:
            result.append(NUM[str(value)])
        elif nums == [0] * len(nums):
            break
        elif len(nums) == 2:
            num_str = ''.join([str(n) for n in nums])
            if first_zero is False:
                num_str = re.sub(r'^[0]+', '', num_str)     # remove first zero
            else:
                if num_str[0] == '0':
                    result.append(NUM['0'])
                    num_str = num_str[1:]
                    
            if NUM.get(num_str) is not None:
                result.append(NUM[num_str])
                break
            else:
                num_value = NUM_TY[str(value) + '0']
                result.append(num_value)
                # NUM_TY                
                if num_en[1] == '0':
                    break
        else:
            num_unit = NUM_UNIT.get(str(pow(10, len(num_units) - idx - 1)))
            if num_unit is None:
                sub_num = [str(value)]
                for sub_idx, sub_num_value in enumerate(nums[1:]):
                    num_unit = NUM_UNIT.get(str(pow(10, len(num_units) - idx - sub_idx - 1)))
                    if num_unit is not None:
                        num_value = num2word(num_km[:len(sub_num)])
                        result.append('%s %s' % (num_value, num_unit))

                        skip_unit = len(sub_num) - 1
                        break
                    else:
                        sub_num.append(str(sub_num_value))
            else:
                num_value = NUM[str(value)]
                
                # zero part
                sub_num_value = num_en[idx+1:]
                match = re.match('^[0]+', sub_num_value)
                if match is not None:
                    zeros = match.group(0)
                    skip_unit = len(zeros)
                
                result.append('%s_%s' % (num_value, num_unit))

    return ' '.join(result)

def num2word(num_km):
    if num_km is None or num_km == '':
        return ''
    
    num_km = num_km.replace('.', '')
    
    if is_float_km(num_km):
        parts = num_km.split(',')
        decimal = num2word_int(parts[0])
        point = num2word_int(parts[1], first_zero=True)
        
        return '%s %s %s' % (decimal, COMMON['FLOAT_POINT_W'], point)
    else:
        return num2word_int(num_km)
      
def date2word(date_km: str):
    if date_km is None or date_km == '':
        return ''
    
    parts = date_km.split('/')
    if parts is None:
        parts = date_km.split('-')
    
    if len(parts) != 3:
        raise Exception('invalid km date: ', date_km)
    
    day = num2word(parts[0])
    month = MONTH.get(km2en(parts[1]))
    if month is None:
        raise Exception('invalid month: %s - %s ' % (month, date_km))
    
    month = '%s %s' % (COMMON['MONTH_KW'], month)
    year = num2word(parts[2])
    
    return '%s %s %s' % (day, month, year)

#############

NUM_EN_REGX     = r'(([0-9]+([.,][0-9]+)?)(\s+%)?)'
NUM_KM_REGX     = r'(([០-៩]+([.,][០-៩]+)?)(\s+%)?)'
DATE_KM_REGX    = r'([០-៩]+[-\/][០-៩]+[-\/][០-៩]+)'
LEK_TO_REGX     = r'(([\u1780-\u17e9]+) ៗ)'

ESP_CHAR = {
    '«': '',
    '»': '',
    '៖': '',
    '”': '',
    '"': '',
    "'": '',
    '!': '',
    '+': '',
    '-': '',
    ' _ ': '',
    ':': '',
    ',': '',
    'ˉ': '',
    '.': '',
    '(': '',
    ')': '',
}

def normalize(text, esp_char=ESP_CHAR, clean_num=True, clean_lek_to=True):
    # abbreviation
    for k, v in ABBRE.items():
        text = text.replace(k, v)
    
    # lek to
    if clean_lek_to is True:
        lek_tos = re.findall(LEK_TO_REGX, text)
        for lek_to, word in lek_tos:
            text = text.replace(lek_to, '%s %s' % (word, word))

    # en num
    num_ens = re.findall(NUM_EN_REGX, text)
    for num_en, num, _, sign in num_ens:
        for k, v in NUM_COMMON.items():
            sign = sign.replace(k, v)

        num = en2km(num)
        if sign.strip() != '':
            num += ' ' + sign

        text = replace(text, num_en, num)        
    
    # km num
    num_kms = re.findall(NUM_KM_REGX, text)
    for num_km, num, _, sign in num_kms:
        for k, v in NUM_COMMON.items():
            sign = sign.replace(k, v)

        num = num2word(num)
        if clean_num is True:
            num = num.replace('_', ' ')
        if sign.strip() != '':
            num += ' ' + sign
        
        text = replace(text, num_km, num)
    
    # km date
    date_kms = re.findall(DATE_KM_REGX, text)
    for date_km in date_kms:
        date = date2word(date_km)
        text = text.replace(date_km, date)
    
    # special characters
    for k, v in esp_char.items():
        text.replace(k, v)
    
    # remove duplicate whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def replace(string, old_value, new_value):
    return re.sub(r' %s ' % old_value, ' %s ' % new_value, string)


if __name__ == '__main__':
    print(num2word('២០'))
    # print(normalize('ធ្វើ_ឡើង មុន ថ្ងៃ_ទី ១២ សីហា គឺ មុន_ពេល សហ^ភាព អឺរ៉ុប សម្រេច ដក_ហូត ការ~អនុគ្រោះ ពន្ធ EBA ចំនួន ២០ % ពី កម្ពុជា ។'))