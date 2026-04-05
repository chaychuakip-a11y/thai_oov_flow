import os
import shutil
import yaml
import sys

def prepare_corpus(config_path="config.yaml"):
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    input_root = cfg['global']['input_root']

    for task_name, task_cfg in cfg['tasks'].items():
        raw_source = task_cfg.get('raw_source_dir')
        
        if not raw_source or not os.path.exists(raw_source):
            print(f"[Skip] Task '{task_name}': raw_source_dir not configured or path does not exist ({raw_source}).")
            continue

        # 自动创建目标目录 (例如: all_corpus_0410/music)
        target_dir = os.path.join(input_root, task_name)
        os.makedirs(target_dir, exist_ok=True)

        copy_count = 0
        
        # 递归遍历原始目录
        for root, _, files in os.walk(raw_source):
            for file in files:
                if file.endswith('.xlsx') and not file.startswith('~'):
                    src_file = os.path.join(root, file)
                    
                    # 将相对路径转换为下划线连接的文件名，防止展平时同名文件被覆盖
                    # 例如: subdir/test.xlsx -> subdir_test.xlsx
                    rel_path = os.path.relpath(src_file, raw_source)
                    flat_name = rel_path.replace(os.sep, '_')
                    dst_file = os.path.join(target_dir, flat_name)
                    
                    shutil.copy2(src_file, dst_file)
                    copy_count += 1
                    
        print(f"[Success] Task '{task_name}': Recursively copied {copy_count} .xlsx files to {target_dir}")

if __name__ == "__main__":
    prepare_corpus()