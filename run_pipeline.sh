#!/bin/bash
set -e
set -o pipefail

task_name=$1
force_init=$2

if [ -z "$task_name" ]; then
    echo "error: task_name is required."
    exit 1
fi

source /home3/asrdictt/yjchen221/.bashrc_1
conda activate cdx

new_xlsx_dir="all_corpus_0327/${task_name}"
out_dir="update_0330/${task_name}"
base_dict="./dicts/${task_name}_base_dict.checked"
master_memory="./dicts/${task_name}_master_memory.pkl"
script_dir=$(cd "$(dirname "$0")" && pwd)

# 处理强制初始化逻辑
if [ "$force_init" == "--force-init" ]; then
    echo "[Notice] Force init triggered. Clearing old memory for ${task_name}..."
    if [ -f "$master_memory" ]; then
        backup_name="${master_memory}.bak_$(date +%Y%m%d%H%M%S)"
        mv "$master_memory" "$backup_name"
        echo "[Notice] Old memory backed up to: $backup_name"
    fi
fi

mkdir -p ${out_dir}/logs ${out_dir}/crops_res ${out_dir}/temp_pkl ${out_dir}/xlsx

echo "[step 1] extract oovs for ${task_name}..."
python scripts/0_extract_and_format_crops_v2.py ${new_xlsx_dir} ${out_dir}/crops_res ${master_memory} > ${out_dir}/logs/step1_extract.log

echo "[step 2] parallel tts prediction for ${task_name}..."
(
    source /work2/asrdictt/wwyang9/asr_training/11_txt_fuzhu_whisper_hulk/hulk.bashrc
    export TTSKNL_DOMAIN=. OMP_NUM_THREADS=1 LD_LIBRARY_PATH=.
    cd pred_tool_gongban/bin_predict
    
    max_jobs=8
    jobs_count=0
    
    for txt_in in ${script_dir}/${out_dir}/crops_res/*.desplit; do
        if [ -f "$txt_in" ] && [ ! -f "${txt_in}.tts_out" ]; then
            (
                ./ttsSample -l libttsknl.so -x 1 -i "$txt_in" -m 1 -f 1 -g 1 -z 1 -o wav -v 69400 > "${txt_in}.run.log" 2>&1
                [ -f "frontinfo.txt" ] && mv frontinfo.txt "${txt_in}.tts_out"
            ) &
            ((jobs_count++))
            if ((jobs_count >= max_jobs)); then
                wait -n
                ((jobs_count--))
            fi
        fi
    done
    wait
) > ${out_dir}/logs/step2_tts.log

echo "[step 3] process dicts for ${task_name}..."
python scripts/unified_dict_processor.py --crops_dir ${out_dir}/crops_res --base_dict ${base_dict} > ${out_dir}/logs/step3_postprocess.log

echo "[step 4] remake excel and update memory for ${task_name}..."
python scripts/8_remake_xlsx_v2.py ${out_dir}/temp_pkl ${out_dir}/crops_res ${new_xlsx_dir} ${out_dir}/xlsx ${master_memory} > ${out_dir}/logs/step4_remake.log