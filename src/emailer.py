"""SMTP 邮件发送模块与 HTTP 推送"""
import smtplib
import time
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests

from .config import Config


def send_email(subject: str, body: str, to_addr: Optional[str] = None, max_retries: int = 3) -> bool:
    """
    发送邮件（带重试机制）
    
    Args:
        subject: 邮件标题
        body: 邮件正文
        to_addr: 收件地址（可选）
        max_retries: 最大重试次数
        
    Returns:
        bool: 是否发送成功
    """
    if not Config.MAIL_FROM or not Config.MAIL_TO:
        print("未配置 MAIL_FROM/MAIL_TO，跳过邮件发送")
        return False

    to_addr = to_addr or Config.MAIL_TO

    msg = MIMEMultipart()
    msg["From"] = Config.MAIL_FROM
    msg["To"] = to_addr
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    def _try_send(port: int, use_ssl: bool) -> None:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(Config.SMTP_HOST, port, timeout=30, context=context) as server:
                server.ehlo()
                if Config.SMTP_USER and Config.SMTP_PASS:
                    server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg)
        else:
            with smtplib.SMTP(Config.SMTP_HOST, port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if Config.SMTP_USER and Config.SMTP_PASS:
                    server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg)

    # 构建尝试序列（优先当前配置，其次常用端口兜底）
    attempts = []
    if Config.SMTP_SSL or Config.SMTP_PORT == 465:
        attempts.append((Config.SMTP_PORT, True))
        if Config.SMTP_PORT != 587:
            attempts.append((587, False))
    else:
        attempts.append((Config.SMTP_PORT, False))
        if Config.SMTP_PORT != 465:
            attempts.append((465, True))

    for attempt in range(max_retries):
        try:
            port, use_ssl = attempts[min(attempt, len(attempts) - 1)]
            mode = "SSL" if use_ssl else "STARTTLS"
            print(f"尝试发送邮件: {Config.SMTP_HOST}:{port} ({mode})")
            _try_send(port, use_ssl)

            print("邮件发送成功")
            return True

        except Exception as e:
            print(f"邮件发送失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print("邮件发送最终失败")
                return False


def send_wecom_webhook(message: str, max_retries: int = 3) -> bool:
    """
    通过企业微信机器人 Webhook 发送消息（Markdown）
    """
    if not Config.WECOM_WEBHOOK_URL:
        print("未配置 WECOM_WEBHOOK_URL，跳过企业微信推送")
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": message
        }
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(Config.WECOM_WEBHOOK_URL, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("errcode") == 0:
                    print("企业微信推送成功")
                    return True
                print(f"企业微信推送失败: {data}")
            else:
                print(f"企业微信推送失败: HTTP {resp.status_code}")
        except Exception as e:
            print(f"企业微信推送失败 (尝试 {attempt + 1}/{max_retries}): {e}")

        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            print(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)

    print("企业微信推送最终失败")
    return False


def _split_other_papers_section(section: str) -> list:
    """按单篇论文切分“其他相关论文”部分"""
    lines = section.splitlines(keepends=True)
    blocks = []
    start_indices = []
    for idx, line in enumerate(lines):
        if line.startswith("**") and ". " in line:
            prefix = line.split(". ", 1)[0]
            if prefix[2:].isdigit():
                start_indices.append(idx)
    if not start_indices:
        return [section] if section.strip() else []
    header = "".join(lines[:start_indices[0]])
    for i, start in enumerate(start_indices):
        end = start_indices[i + 1] if i + 1 < len(start_indices) else len(lines)
        blocks.append("".join(lines[start:end]))
    if header.strip():
        blocks[0] = header + blocks[0]
    return blocks


def _split_digest_blocks(digest_content: str) -> list:
    """按单篇论文切分日报内容"""
    if not digest_content.strip():
        return []
    parts = digest_content.split("\n---\n\n")
    if len(parts) == 1:
        return [digest_content]
    blocks = []
    for i, part in enumerate(parts[:-1]):
        blocks.append(part + "\n---\n\n")
    tail = parts[-1]
    if "## 📝 其他相关论文" in tail:
        tail_blocks = _split_other_papers_section(tail)
        blocks.extend(tail_blocks)
    else:
        blocks.append(tail)
    return [b for b in blocks if b.strip()]


def send_wecom_webhook_split(
    subject: str,
    digest_content: str,
    max_retries: int = 3,
    max_len: int = 4096
) -> bool:
    """
    拆分日报并分段推送，确保不把单篇论文拆开
    """
    blocks = _split_digest_blocks(digest_content)
    if not blocks:
        return send_wecom_webhook(f"## {subject}\n\n{digest_content}", max_retries=max_retries)

    def _byte_len(text: str) -> int:
        return len(text.encode("utf-8"))

    def _trim_to_bytes(text: str, max_bytes: int) -> str:
        if _byte_len(text) <= max_bytes:
            return text
        return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")

    safe_prefix = f"## {subject}（第99/99部分）\n\n"
    max_content_len = max_len - _byte_len(safe_prefix)
    if max_content_len <= 0:
        return False

    def _truncate_block(block: str) -> str:
        suffix = "\n\n（内容过长已截断）\n"
        if _byte_len(block) <= max_content_len:
            return block
        keep_len = max_content_len - _byte_len(suffix)
        if keep_len <= 0:
            return _trim_to_bytes(suffix, max_content_len)
        return _trim_to_bytes(block, keep_len) + suffix

    chunks = []
    current = ""
    for block in blocks:
        block = _truncate_block(block)
        if not current:
            current = block
            continue
        if _byte_len(current) + _byte_len(block) <= max_content_len:
            current += block
        else:
            chunks.append(current)
            current = block
    if current:
        chunks.append(current)

    total = len(chunks)
    success_all = True
    for idx, chunk in enumerate(chunks, 1):
        prefix = f"## {subject}（第{idx}/{total}部分）\n\n"
        message = prefix + chunk
        if _byte_len(message) > max_len:
            message = _trim_to_bytes(message, max_len)
        ok = send_wecom_webhook(message, max_retries=max_retries)
        success_all = success_all and ok
    return success_all
