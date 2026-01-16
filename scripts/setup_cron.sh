#!/bin/bash

# 每日 ArXiv 日报 Cron 安装脚本
# 将在每天早上 6:00 自动运行

PROJECT_DIR="/home/hujie/paper/tools/daily_arvix"
PYTHON_BIN="/home/hujie/anaconda3/bin/python"
LOG_FILE="$PROJECT_DIR/cron.log"

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "错误: 项目目录不存在 $PROJECT_DIR"
    exit 1
fi

# 检查 main.py
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    echo "错误: main.py 不存在"
    exit 1
fi

# 生成 cron 任务
CRON_JOB="0 6 * * * cd $PROJECT_DIR && $PYTHON_BIN main.py >> $LOG_FILE 2>&1"

# 检查是否已存在相同任务
if crontab -l 2>/dev/null | grep -F "$PROJECT_DIR/main.py" > /dev/null; then
    echo "检测到已存在的 cron 任务，先移除..."
    crontab -l 2>/dev/null | grep -v "$PROJECT_DIR/main.py" | crontab -
fi

# 添加新任务
echo "添加 cron 任务: 每天 06:00 运行日报生成器"
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron 任务安装成功！"
echo ""
echo "任务详情:"
echo "  时间: 每天早上 6:00"
echo "  脚本: $PROJECT_DIR/main.py"
echo "  日志: $LOG_FILE"
echo ""
echo "查看当前 cron 任务:"
echo "  crontab -l"
echo ""
echo "手动测试运行:"
echo "  cd $PROJECT_DIR && python3 main.py"
