#!/bin/bash

check_log_errors() {
    local log_file=$1  # 将第一个参数赋值给变量log_file，表示日志文件的路径

    # 检查日志文件是否存在
    if [[ ! -f "$log_file" ]]; then
        echo "指定的日志文件不存在: $log_file"
        return 1
    fi

    # 使用grep命令检查"core dumped"或"Error"的存在
    # -C 5表示打印匹配行的前后各5行
    local pattern="core dumped|Error|error"
    if grep -E -C 5 "$pattern" "$log_file"; then
        echo "检测到错误信息，请查看上面的输出。"
        exit 1
    else
        echo "$log_file 中未检测到明确的错误信息。请手动排查 $log_file 以获取更多信息。"
    fi
}

start_time=$(date +%s)  # 记录开始时间

DIR="/workspace/QAnything/logs/debug_logs"

# 检查目录是否存在
if [ ! -d "$DIR" ]; then
  # 如果目录不存在，则创建目录
  mkdir -p "$DIR"
  echo "Directory $DIR created."
else
  echo "Directory $DIR already exists."
fi

# 创建软连接
if [ ! -L "/workspace/QAnything/qanything_kernel/dependent_server/embedding_server/embedding_model_configs_v0.0.1" ]; then  # 如果不存在软连接
  cd /workspace/QAnything/qanything_kernel/dependent_server/embedding_server && ln -s /root/models/linux_onnx/embedding_model_configs_v0.0.1 .
fi

if [ ! -L "/workspace/QAnything/qanything_kernel/dependent_server/rerank_server/rerank_model_configs_v0.0.1" ]; then  # 如果不存在软连接
  cd /workspace/QAnything/qanything_kernel/dependent_server/rerank_server && ln -s /root/models/linux_onnx/rerank_model_configs_v0.0.1 .
fi

if [ ! -L "/workspace/QAnything/qanything_kernel/dependent_server/ocr_server/ocr_models" ]; then  # 如果不存在软连接
  cd /workspace/QAnything/qanything_kernel/dependent_server/ocr_server && ln -s /root/models/ocr_models .  # 创建软连接
fi

if [ ! -L "/workspace/QAnything/qanything_kernel/dependent_server/pdf_parser_server/pdf_to_markdown/checkpoints" ]; then  # 如果不存在软连接
  cd /workspace/QAnything/qanything_kernel/dependent_server/pdf_parser_server/pdf_to_markdown/ && ln -s /root/models/pdf_models checkpoints  # 创建软连接
fi

if [ ! -L "/workspace/QAnything/nltk_data" ]; then  # 如果不存在软连接
  cd /workspace/QAnything/ && ln -s /root/nltk_data .  # 创建软连接
fi

cd /workspace/QAnything || exit

nohup python3 -u qanything_kernel/dependent_server/rerank_server/rerank_server.py --use_gpu --workers 1 > /workspace/QAnything/logs/debug_logs/rerank_server.log 2>&1 &
PID1=$!
nohup python3 -u qanything_kernel/dependent_server/embedding_server/embedding_server.py --use_gpu --workers 10 > /workspace/QAnything/logs/debug_logs/embedding_server.log 2>&1 &
PID2=$!
nohup python3 -u qanything_kernel/dependent_server/pdf_parser_server/pdf_parser_server.py --use_gpu --workers 1 > /workspace/QAnything/logs/debug_logs/pdf_parser_server.log 2>&1 &
PID3=$!
nohup python3 -u qanything_kernel/dependent_server/ocr_server/ocr_server.py --use_gpu --workers 1> /workspace/QAnything/logs/debug_logs/ocr_server.log 2>&1 &
PID4=$!
nohup python3 -u qanything_kernel/dependent_server/insert_files_serve/insert_files_server.py --port 8110 --workers 1 > /workspace/QAnything/logs/debug_logs/insert_files_server.log 2>&1 &
PID5=$!
nohup python3 -u qanything_kernel/qanything_server/sanic_api.py --host $USER_IP --port 8777 --workers 1 > /workspace/QAnything/logs/debug_logs/main_server.log 2>&1 &
PID6=$!

# Keep the container running
while true; do
    sleep 5
done