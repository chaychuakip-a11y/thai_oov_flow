Gemini 说
LexiMemory: Automotive ASR Lexicon & Corpus Sync Tool
LexiMemory 是专为车载语音识别（Automotive ASR）场景设计的语料处理与词典同步工具。它通过 Master Memory 机制实现增量更新，在保证 Excel 行数绝对对齐（Row Alignment）的同时，自动化完成 OOV 提取、TTS 发音预测及词典融合。

核心特性
增量式 OOV 挖掘：基于 master_memory.pkl 记录已处理词条，仅对新增语料执行 TTS 预测，极大节省计算资源。

严格行对齐 (Row-Aligned)：采用 1-to-1 Mapping 逻辑重写 Excel，确保原始语料的行结构不因映射失败或空值而坍塌。

多任务并行化：支持 gongban, music, poi, weather 四类任务并发运行。通过 YAML 配置独立的 TTS_TOOL_PATH 彻底消除文件 I/O 冲突。

配置驱动：所有路径与任务参数均收敛于 config.yaml，实现逻辑与数据的完全解耦。

项目结构
Plaintext
LexiMemory/
├── config.yaml             # 全局任务配置文件
├── scripts/                # 核心 Python 逻辑
│   ├── parse_config.py     # YAML 配置解析器
│   ├── 0_extract..._v2.py  # 增量 OOV 提取
│   ├── unified_dict_...    # 词典校验与合并
│   └── 8_remake_xlsx_v2.py # Excel 重构与状态持久化
├── dicts/                  # 存储 .pkl 记忆文件与基准词典 (.checked)
├── all_corpus_0327/        # 输入：各任务原始 .xlsx 语料
├── update_0330/            # 输出：自动生成的中间产物与结果 Excel
├── pred_tool_*/            # 外部 TTS 引擎 (不同任务独立副本)
├── run_pipeline.sh         # 通用流水线引擎
└── run_${task}.sh          # 任务触发器 (gongban, music, poi, weather)
快速开始
1. 环境准备
确保 Python 环境已安装 PyYAML, pandas, openpyxl 及 tqdm。

Bash
pip install pyyaml pandas openpyxl tqdm
chmod +x scripts/*.py *.sh
2. 配置任务
在 config.yaml 中定义你的路径映射。如果需要并行跑多个任务，请确保每个任务的 tts_tool_path 指向不同的目录。

3. 执行更新
常规增量更新：直接运行对应任务脚本。

Bash
bash run_music.sh
强制重置并初始化：当原始语料库发生重大变更，需要彻底清理旧记忆并重新全量扫描时。

Bash
bash run_music.sh --force-init
核心配置逻辑说明
Master Memory 机制
项目不再依赖反复对比 old_xlsx 目录，而是将所有已知的映射关系（Slot & Jushi）存储在 master_memory.pkl 中。

优势：处理 100 万行级别的语料更新，OOV 提取阶段可从分钟级缩短至秒级。

持久化：每次 step 4 完成后，新的 OOV 映射会自动并入该文件。

词典校验规则
在 unified_dict_processor.py 中预设了严格的过滤机制：

长度限制：单词编码长度不得超过 63 bytes。

非法字符：自动剔除包含 0-9, +-*, 标点符号等异常字符的词条。

特殊处理：自动处理泰语等语种的特殊组合字符（如 ๆ, ร์）以免断词错误。

注意事项
[!WARNING]
TTS 并发冲突：ttsSample 工具会在当前路径下读写 frontinfo.txt。禁止在 config.yaml 中让两个并行任务指向同一个 tts_tool_path，否则会导致发音数据互相覆盖。

[!TIP]
Row Alignment：如果发现输出的 Excel 行数减少，请检查 0_extract... 阶段是否有大量词条命中了 ILLEGEAL_CHAR 过滤逻辑。