#!/usr/bin/env bash

set -u

# 每日 ArXiv 日报 Cron 安装脚本，将在每天早上 6:00 运行。

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_DIR/cron.log"

if [ ! -f "$PROJECT_DIR/main.py" ]; then
    echo "错误: main.py 不存在: $PROJECT_DIR/main.py" >&2
    exit 1
fi

resolve_python_path() {
    local candidate="$1"
    case "$candidate" in
        /*) ;;
        *) candidate="$PROJECT_DIR/${candidate#./}" ;;
    esac
    if [ ! -x "$candidate" ]; then
        echo "错误: Python 不可执行: $candidate" >&2
        return 1
    fi
    local candidate_dir
    candidate_dir="$(cd -- "$(dirname -- "$candidate")" && pwd)" || return 1
    printf '%s/%s' "$candidate_dir" "$(basename -- "$candidate")"
}

if [ -n "${PYTHON_BIN:-}" ]; then
    PYTHON_BIN="$(resolve_python_path "$PYTHON_BIN")" || exit 1
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(resolve_python_path "$(command -v python3)")" || exit 1
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(resolve_python_path "$(command -v python)")" || exit 1
else
    echo "错误: 找不到 python3 或 python，请先安装 Python" >&2
    exit 1
fi

# '%' 在 crontab 命令中会被解释为换行；明确拒绝含它的路径，避免生成错误任务。
case "$PROJECT_DIR$PYTHON_BIN$LOG_FILE" in
    *%*)
        echo "错误: 项目、Python 或日志路径包含 cron 特殊字符 '%'，请换到不含 '%' 的路径" >&2
        exit 1
        ;;
esac

shell_quote() {
    printf "'%s'" "${1//\'/\'\\\'\'}"
}

QUOTED_PROJECT_DIR="$(shell_quote "$PROJECT_DIR")"
QUOTED_PYTHON_BIN="$(shell_quote "$PYTHON_BIN")"
QUOTED_LOG_FILE="$(shell_quote "$LOG_FILE")"
CRON_JOB="0 6 * * * cd $QUOTED_PROJECT_DIR && $QUOTED_PYTHON_BIN main.py >> $QUOTED_LOG_FILE 2>&1"

CRONTAB_ERROR_FILE="$(mktemp)" || {
    echo "错误: 无法创建临时文件以读取 crontab" >&2
    exit 1
}
trap 'rm -f "$CRONTAB_ERROR_FILE"' EXIT
CURRENT_CRONTAB=""
if CURRENT_CRONTAB="$(LC_ALL=C crontab -l 2>"$CRONTAB_ERROR_FILE")"; then
    :
else
    CRONTAB_STATUS=$?
    CRONTAB_ERROR="$(<"$CRONTAB_ERROR_FILE")"
    if [ "$CRONTAB_STATUS" -ne 1 ] || [[ "$CRONTAB_ERROR" != *"no crontab"* ]]; then
        echo "错误: 无法读取当前 crontab (退出码 $CRONTAB_STATUS): ${CRONTAB_ERROR:-未知错误}" >&2
        exit 1
    fi
fi

# 删除本脚本生成的重复行，保留其他任务和注释。使用 shell 字符串比较，避免路径中的反斜杠被 awk 解释。
UPDATED_CRONTAB=""
if [ -n "$CURRENT_CRONTAB" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        [ "$line" = "$CRON_JOB" ] && continue
        if [ -n "$UPDATED_CRONTAB" ]; then
            UPDATED_CRONTAB+=$'\n'
        fi
        UPDATED_CRONTAB+="$line"
    done <<< "$CURRENT_CRONTAB"
fi
if [ -n "$UPDATED_CRONTAB" ]; then
    UPDATED_CRONTAB+=$'\n'
fi
UPDATED_CRONTAB+="$CRON_JOB"

if ! printf '%s\n' "$UPDATED_CRONTAB" | crontab -; then
    echo "错误: 写入 crontab 失败" >&2
    exit 1
fi

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
echo "  cd $PROJECT_DIR && $PYTHON_BIN main.py"
