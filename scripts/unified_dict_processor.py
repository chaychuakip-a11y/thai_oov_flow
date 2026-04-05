import os
import argparse

error_marks = set(list(r'0123456789+-*.,?<>\|;:[]{}()&^%$#@!~`。，《》？“”‘’；：、'))
no_alone_set = set(['ๆ','ร์','น์','ต์','ค์','ซ์'])
conti_set = set(['cdxa','cdxb','yjchen'])

def finetune_no_alone_word(words, phones):
    if len(words) == 0:
        return words, phones
    assert len(words) == len(phones)
    new_words, new_phones = [], []
    for i in range(len(words)):
        word, phone = words[i], phones[i]
        if i == 0:
            new_words.append(word)
            new_phones.append(phone)
            continue
        if word in no_alone_set:
            new_words[-1] = new_words[-1] + word
            new_phones[-1] = new_phones[-1] + ' ' + phone
        else:
            new_words.append(word)
            new_phones.append(phone)
    return new_words, new_phones

def parse_phones(ss: str):
    contents = ss.strip().replace('#', '').split(']')
    words, phones = [], []
    num_set = set('0 1 2 3 4 5 6 7 8 9'.split(' '))
    res_word = None
    for content in contents:
        if len(content.strip()) == 0:
            continue
        word, temp_phone = content.split('[')
        word = word.replace('*', '').replace(' ', '').strip()
        temp_phone = temp_phone.replace('=', ' ').replace('(', ' ').replace(')', ' ')
        phone = []
        for p in temp_phone.split(' '):
            if len(p) == 0 or p in num_set:
                continue
            phone.append(p)
        phone = ' '.join(phone)
        if len(phone) == 0:
            if len(words) > 0:
                words[-1] += word
            else:
                res_word = word if res_word is None else res_word + word
            continue
        phones.append(phone)
        if res_word is not None:
            words.append(res_word + word)
            res_word = None
        else:
            words.append(word)
    return finetune_no_alone_word(words, phones)

def remake_jushi_line(line):
    jushi_line_out = ''
    slot_Tag = False
    for word in line.strip().split(' '):
        if word == 'yjchen': continue
        if word == 'cdxa':
            slot_Tag = True
            jushi_line_out += '<'
        elif word == 'cdxb':
            slot_Tag = False
            jushi_line_out = jushi_line_out[:-1] + '> '
        else:
            if slot_Tag:
                jushi_line_out += word + '_'
            else:
                jushi_line_out += word + ' '
    return jushi_line_out.strip() + '\n'

def is_valid_word(word):
    if len(word.encode('utf-8')) > 63:
        return False
    if word != '<s>' and word != '</s>':
        for p in word:
            if p in error_marks:
                return False
    return True

def process_pipeline(crops_dir, base_dict_path):
    global_dict = {}
    if os.path.exists(base_dict_path):
        with open(base_dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                parts = line.strip().split('\t')
                word = parts[0]
                phones = parts[1] if len(parts) > 1 else '<UNK>'
                if word not in global_dict:
                    global_dict[word] = set()
                global_dict[word].add(phones)

    for file in os.listdir(crops_dir):
        if not file.endswith('.tts_out'): continue
        in_file = os.path.join(crops_dir, file)
        checked_split_file = os.path.join(crops_dir, file + '.split.checked')
        is_jushi = ('jushi' in file or 'shuofa' in file)

        lines_sent_out = []
        with open(in_file, mode='r', encoding='utf-8') as fi:
            for line in fi:
                line = line.strip()
                if not line: continue
                
                words, phones = parse_phones(line)
                accept_line = True
                valid_line_words = []
                
                for w, p in zip(words, phones):
                    if w in conti_set:
                        valid_line_words.append(w)
                        continue
                    
                    if not is_valid_word(w):
                        accept_line = False
                        break
                        
                    if p:
                        if w not in global_dict:
                            global_dict[w] = set()
                        if p not in global_dict[w] and p != '<UNK>':
                            global_dict[w].add(p)
                            
                    valid_line_words.append(w)
                
                if accept_line:
                    line_str = ' '.join(valid_line_words) + '\n'
                    if is_jushi:
                        lines_sent_out.append(remake_jushi_line(line_str))
                    else:
                        lines_sent_out.append(line_str)
        
        with open(checked_split_file, 'w', encoding='utf-8') as fw:
            fw.writelines(lines_sent_out)

    with open(base_dict_path, 'w', encoding='utf-8') as f:
        f.write('<s>\t<s>\n')
        f.write('</s>\t</s>\n')
        for word in sorted(global_dict.keys()):
            if word in ['<s>', '</s>']: continue
            for phone in sorted(global_dict[word]):
                f.write(f'{word}\t{phone}\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--crops_dir', required=True)
    parser.add_argument('--base_dict', required=True)
    args = parser.parse_args()
    process_pipeline(args.crops_dir, args.base_dict)