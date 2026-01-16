"""配置管理模块"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    """项目配置类"""
    
    # OpenAI Compatible API 配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'glm-4.7')
    
    # ArXiv 配置
    ARXIV_CATEGORIES = os.getenv('ARXIV_CATEGORIES', 'cs.LG,cs.DC').split(',')
    ARXIV_MAX_RESULTS = int(os.getenv('ARXIV_MAX_RESULTS', '50'))
    
    # 兴趣提示词
    INTEREST_PROMPT_FILE = os.getenv('INTEREST_PROMPT_FILE', 'prompts/interest.txt')
    
    # 邮件配置
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_SSL = os.getenv('SMTP_SSL', 'false').lower() in ('1', 'true', 'yes')
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    MAIL_FROM = os.getenv('MAIL_FROM', '')
    MAIL_TO = os.getenv('MAIL_TO', '')

    # 企业微信机器人 Webhook
    WECOM_WEBHOOK_URL = os.getenv('WECOM_WEBHOOK_URL', '')

    # 推送方式: email / wecom / both
    PUSH_CHANNEL = os.getenv('PUSH_CHANNEL', 'both').lower()
    
    # 输出配置
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    
    # 历史记录配置
    HISTORY_FILE = os.getenv('HISTORY_FILE', '.paper_history.txt')
    
    @classmethod
    def get_interest_prompt(cls) -> str:
        """读取兴趣提示词"""
        try:
            with open(cls.INTEREST_PROMPT_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "Machine Learning, Deep Learning, Distributed Systems"
    
    @classmethod
    def validate(cls) -> bool:
        """验证必要的配置是否存在"""
        if not cls.OPENAI_API_KEY:
            print("错误: 未配置 OPENAI_API_KEY")
            return False
        if cls.PUSH_CHANNEL in ("email", "both"):
            if not cls.MAIL_FROM or not cls.MAIL_TO:
                print("警告: 未配置邮件信息，将只生成本地文件")
        if cls.PUSH_CHANNEL in ("wecom", "both"):
            if not cls.WECOM_WEBHOOK_URL:
                print("警告: 未配置企业微信 Webhook，将只生成本地文件")
        return True
    
    @classmethod
    def ensure_output_dir(cls):
        """确保输出目录存在"""
        Path(cls.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
