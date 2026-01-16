"""SMTP 邮件发送测试脚本"""
from datetime import datetime
import sys
from pathlib import Path

# 将项目根目录加入路径，确保可导入 src
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.emailer import send_email


def main():
    subject = f"邮件测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    body = (
        "这是一封测试邮件。\n\n"
        "如果你收到此邮件，说明 SMTP 配置正确。\n"
        "如果未收到，请检查 .env 中的 SMTP_* 配置。"
    )
    success = send_email(subject, body, max_retries=2)
    if success:
        print("✅ 测试邮件发送成功")
    else:
        print("❌ 测试邮件发送失败")


if __name__ == "__main__":
    main()
