#!/bin/bash

# 开启严格模式：任何命令失败或管道故障即刻终止 Pipeline
set -e
set -o pipefail

TASK_NAME=$1
FORCE_INIT=$2

if [ -z "$TASK_NAME" ]; then
    echo "Usage: bash run_pipeline.sh <task_name> [--force-init]"
    exit 1
fi

# 获取当前项目的绝对根目录
ROOT_DIR=$(pwd)

# 1. 解析 YAML 配置并注入环境变量
# 得到 NEW_XLSX_DIR, OUT_DIR, BASE_DICT, MASTER_MEMORY, TTS_TOOL_PATH 等
eval $(python scripts/parse_config.py $TASK_NAME)

# 2. 基础环境加载
source /home3/asrdictt/yjchen221/.bashrc_1
conda activate cdx

# 3. 处理 Force Init 逻辑 (备份 Master Memory)
if [ "$FORCE_INIT" == "--force-init" ] && [ -f "$MASTER_MEMORY" ]; then
    BAK="${MASTER_MEMORY}.bak_$(date +%Y%m%d%H%M%S)"
    mv "$MASTER_MEMORY" "$BAK"
    echo "[Notice] Force init triggered. Old memory backed up to: $BAK"
fi

# 创建必要的输出和日志目录
mkdir -p ${OUT_DIR}/logs ${OUT_DIR}/crops_res ${OUT_DIR}/temp_pkl ${OUT_DIR}/xlsx

# --- Pipeline 开始 ---

# [Step 1] 提取增量 OOV 词条
echo "[Step 1] Extracting OOVs for ${TASK_NAME}..."
python ${SCRIPT_DIR}/0_extract_and_format_crops_v2.py \
    ${NEW_XLSX_DIR} \
    ${OUT_DIR}/crops_res \
    ${MASTER_MEMORY} > ${OUT_DIR}/logs/step1_extract.log

# [Step 2] Serial TTS prediction (Stable version)
echo "[Step 2] Serial TTS prediction for ${TASK_NAME}..."
(
    source /work2/asrdictt/wwyang9/asr_training/11_txt_fuzhu_whisper_hulk/hulk.bashrc 2>/dev/null || true
    
    export TTSKNL_DOMAIN=. 
    export OMP_NUM_THREADS=1 
    export LD_LIBRARY_PATH=.
    
    BIN_DIR="${ROOT_DIR}/${TTS_TOOL_PATH}"
    cd "${BIN_DIR}"
    
    shopt -s nullglob
    for txt_in in "${ROOT_DIR}/${OUT_DIR}/crops_res/"*.desplit; do
        if [ -f "$txt_in" ] && [ ! -f "${txt_in}.tts_out" ]; then
            
            # 清理上一次可能残留的文件，防止干扰
            rm -f frontinfo.txt run.log
            
            # 直接在原始目录下串行执行
            ./ttsSample -l libttsknl.so -x 1 -i "$txt_in" -m 1 -f 1 -g 1 -z 1 -o wav -v 69400 > run.log 2>&1
            
            # 及时转移结果
            if [ -f "frontinfo.txt" ]; then
                mv frontinfo.txt "${txt_in}.tts_out"
            else
                echo "[Error] Execution failed for $txt_in" >&2
                cat run.log > "${txt_in}.error_log"
            fi
        fi
    done
    echo "[Log] Step 2 finished."
) > "${OUT_DIR}/logs/step2_tts.log" 2>&1

# [Step 3] 词典后处理与校验
echo "[Step 3] Processing dicts for ${TASK_NAME}..."
python ${SCRIPT_DIR}/unified_dict_processor.py \
    --crops_dir ${OUT_DIR}/crops_res \
    --base_dict ${BASE_DICT} > ${OUT_DIR}/logs/step3_postprocess.log

# [Step 4] 1:1 重构 Excel 并合入 Memory
echo "[Step 4] Remaking Excel and updating memory for ${TASK_NAME}..."
python ${SCRIPT_DIR}/8_remake_xlsx_v2.py \
    ${OUT_DIR}/temp_pkl \
    ${OUT_DIR}/crops_res \
    ${NEW_XLSX_DIR} \
    ${OUT_DIR}/xlsx \
    ${MASTER_MEMORY} > ${OUT_DIR}/logs/step4_remake.log

echo "Pipeline finished for ${TASK_NAME}. Results: ${OUT_DIR}/xlsx/"