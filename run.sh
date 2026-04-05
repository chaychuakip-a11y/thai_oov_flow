# 同时并行启动四个任务，且每个任务拥有独立的 TTS 执行空间
nohup bash run_pipeline.sh gongban > logs_gongban.txt 2>&1 &
nohup bash run_pipeline.sh music > logs_music.txt 2>&1 &
nohup bash run_pipeline.sh poi > logs_poi.txt 2>&1 &
nohup bash run_pipeline.sh weather > logs_weather.txt 2>&1 &