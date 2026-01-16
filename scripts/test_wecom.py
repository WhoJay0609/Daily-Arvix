"""企业微信 Webhook 推送测试脚本"""
from datetime import datetime
import sys
from pathlib import Path

# 将项目根目录加入路径，确保可导入 src
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.emailer import send_wecom_webhook


def main():
    message = (
        f"## 企业微信推送测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "如果你看到这条消息，说明企业微信 Webhook 配置正确。"
    )
    success = send_wecom_webhook(message, max_retries=2)
    if success:
        print("✅ 企业微信测试推送成功")
    else:
        print("❌ 企业微信测试推送失败")


if __name__ == "__main__":
    main()
