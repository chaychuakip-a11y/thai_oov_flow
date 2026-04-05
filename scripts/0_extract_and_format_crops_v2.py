import os
import sys
import pickle
import re
from openpyxl import load_workbook

ILLEGEAL_CHAR = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]|\'')

def is_En(char):
    return ('a' <= char <= 'z') or ('A' <= char <= 'Z') or char in "<>'"

def remake_line(line):
    line = line.strip()
    new_line = ''
    for p in line:
        if p == ' ':
            if new_line and is_En(new_line[-1]):
                new_line += p
            continue
        if new_line and is_En(p) != is_En(new_line[-1]) and new_line[-1] != ' ':
            new_line += ' '
        new_line += p
    return new_line

def remake_jushi_line(line):
    new_out = []
    for char in line:
        if char == '<':
            new_out.append(char)
        elif char == '>':
            if new_out: new_out[-1] += char
            new_out.append('')
        else:
            if not new_out: new_out.append('')
            new_out[-1] += char
            
    line_out = []
    for part in new_out:
        if not part: continue
        if '<' in part:
            part = part.replace('<', 'cdxa ').replace('>', ' cdxb')
        else:
            part = remake_line(part)
        line_out.append(part)
    return ' '.join(line_out).strip() + ' yjchen'

def load_base_memory(memory_path):
    if os.path.exists(memory_path):
        with open(memory_path, 'rb') as f:
            return pickle.load(f)
    return {'slots': {'new_oov_slots': {}}, 'jushis': {}}

def extract_oov(new_dir, memory):
    slots = memory.get('slots', {})
    jushis = memory.get('jushis', {})
    oov_slot, oov_jushi = set(), set()
    
    for file in os.listdir(new_dir):
        if file.startswith('~') or not file.endswith('.xlsx'):
            continue
        file_path = os.path.join(new_dir, file)
        # 仅读取数值提升性能
        workbook = load_workbook(filename=file_path, read_only=True, data_only=True)
        
        for s_name in workbook.sheetnames:
            sheet = workbook[s_name]
            if s_name == '<>':
                for col in sheet.iter_cols(values_only=True):
                    if not col or not col[0]: continue
                    slot_name = col[0]
                    for slot in col[1:]:
                        if slot and str(slot).strip():
                            cleaned = ILLEGEAL_CHAR.sub('', str(slot)).strip()
                            key = cleaned.replace(' ', '')
                            if slot_name not in slots or key not in slots[slot_name]:
                                oov_slot.add(cleaned)
            else:
                for col in sheet.iter_cols(values_only=True):
                    for jushi in col:
                        if jushi and str(jushi).strip():
                            cleaned = ILLEGEAL_CHAR.sub('', str(jushi)).strip()
                            key = cleaned.replace(' ', '')
                            if key not in jushis:
                                oov_jushi.add(cleaned)
    return list(oov_slot), list(oov_jushi)

if __name__ == "__main__":
    new_dir = sys.argv[1]
    out_crops_dir = sys.argv[2]
    memory_path = sys.argv[3]
    
    os.makedirs(out_crops_dir, exist_ok=True)
    memory = load_base_memory(memory_path)
    oov_slots_list, oov_jushis_list = extract_oov(new_dir, memory)
    
    if oov_slots_list:
        with open(os.path.join(out_crops_dir, 'oov_slot.txt.desplit'), 'w', encoding='utf-8') as f:
            f.writelines(remake_line(slot) + '\n' for slot in oov_slots_list)
            
    if oov_jushis_list:
        with open(os.path.join(out_crops_dir, 'oov_jushi.txt.desplit'), 'w', encoding='utf-8') as f:
            f.writelines(remake_jushi_line(jushi) + '\n' for jushi in oov_jushis_list)