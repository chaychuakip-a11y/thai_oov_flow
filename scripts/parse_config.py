import yaml
import sys
import os

def parse_config(task_name, config_path="config.yaml"):
    if not os.path.exists(config_path):
        print(f"echo 'Error: {config_path} not found'; exit 1")
        return

    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    
    if task_name not in cfg['tasks']:
        print(f"echo 'Error: Task {task_name} not defined in yaml'; exit 1")
        return

    g = cfg['global']
    t = cfg['tasks'][task_name]

    # 导出路径变量
    paths = {
        "NEW_XLSX_DIR": os.path.join(g['input_root'], task_name),
        "OUT_DIR": os.path.join(g['output_root'], task_name),
        "BASE_DICT": os.path.join(g['dict_root'], t['base_dict']),
        "MASTER_MEMORY": os.path.join(g['dict_root'], t['master_memory']),
        "SCRIPT_DIR": g['script_dir'],
        # 任务特定的 TTS 工具路径
        "TTS_TOOL_PATH": t['tts_tool_path']
    }

    for k, v in paths.items():
        print(f"export {k}='{v}'")

if __name__ == "__main__":
    parse_config(sys.argv[1])