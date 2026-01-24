# Daily ArXiv Digest

智能论文日报生成器，每日自动拉取 ArXiv 最新论文并通过 LLM 生成中文摘要。

## ✨ 特性

- 📰 **智能筛选**：自动判断论文相关性，跳过无关论文
- 🔎 **关键词预筛**：在 LLM 之前做轻量关键词过滤，降低噪声与成本
- 🏆 **TopN 详细摘要**：对评分最高的 N 篇论文生成结构化分析（TL;DR、贡献、局限等）
- 📝 **简洁概述**：其他相关论文生成简短摘要
- 📅 **每日归档**：自动保存每天的日报历史
- 🔄 **自动重试**：LLM 调用和邮件发送失败时自动重试
- 📧 **邮件推送**：支持 SMTP 邮件发送（QQ/Gmail/企业邮箱等）
- ⏰ **定时运行**：支持 cron 定时任务，每天自动生成
- 📚 **去重机制**：自动记录已读论文，避免重复处理
- 💾 **断点续跑**：LLM 调用缓存，支持失败后重跑

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

将 `env.example` 复制为 `.env`，并填写真实值：

```bash
cp env.example .env
```

关键配置项：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | LLM API 密钥 | `sk-...` |
| `OPENAI_BASE_URL` | API 地址 | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | 模型名称 | `deepseek/deepseek-chat` |
| `ARXIV_CATEGORIES` | ArXiv 分类 | `cs.LG,cs.DC` |
| `ARXIV_MAX_RESULTS` | 每次拉取数量 | `50` |
| `PREFILTER_KEYWORDS` | 预筛关键词（逗号分隔） | `diffusion,graph` |
| `PREFILTER_NEGATIVE_KEYWORDS` | 预筛排除关键词（逗号分隔） | `survey,benchmark` |
| `TOP_N_DETAILED` | Top 详细摘要数量 | `5` |
| `LLM_CACHE_ENABLED` | 是否启用 LLM 缓存 | `true` |
| `LLM_CACHE_FILE` | LLM 缓存文件路径 | `.llm_cache.json` |
| `SMTP_HOST` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` 或 `587` |
| `SMTP_USER` | 发件邮箱 | `your@qq.com` |
| `SMTP_PASS` | SMTP 授权码 | `授权码` |
| `MAIL_FROM` | 发件人 | `your@qq.com` |
| `MAIL_TO` | 收件人（逗号分隔） | `a@example.com,b@example.com` |
| `WECOM_WEBHOOK_URL` | 企业微信机器人 Webhook | `https://qyapi.weixin.qq.com/...` |
| `PUSH_CHANNEL` | 推送方式 | `email` / `wecom` / `both` |

**兴趣提示词**：编辑 `prompts/interest.txt`，描述你的研究兴趣（一行即可）

### 3. 手动运行

```bash
python main.py
```

生成文件：
- `output/daily_digest_YYYY-MM-DD.md`：归档版本
- `output/daily_digest.md`：最新版本（软链接）

## ⏰ 定时任务

### 自动安装（推荐）

运行脚本自动配置每天早上 6:00 运行：

```bash
bash scripts/setup_cron.sh
```

### 手动配置

编辑 crontab：

```bash
crontab -e
```

添加以下行（每天 6:00 运行）：

```cron
0 6 * * * cd /home/hujie/paper/tools/daily_arvix && /usr/bin/python3 main.py >> cron.log 2>&1
```

查看日志：

```bash
tail -f cron.log
```

## 📧 邮箱配置示例

### QQ 邮箱（推荐）

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_qq@qq.com
SMTP_PASS=你的SMTP授权码
MAIL_FROM=your_qq@qq.com
MAIL_TO=recipient@example.com
```

**获取授权码**：
1. 登录 QQ 邮箱网页版
2. 设置 → 账户 → POP3/SMTP 服务
3. 开启服务并生成授权码

### Gmail

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=应用专用密码
MAIL_FROM=your@gmail.com
MAIL_TO=recipient@example.com
```

## 🧪 推送测试

### 测试邮件

```bash
python scripts/test_email.py
```

### 测试企业微信

```bash
python scripts/test_wecom.py
```

## 🎯 工作流程

1. **拉取论文**：从 ArXiv API 获取最新论文
2. **去重过滤**：检查历史记录，过滤已处理的论文（基于 ArXiv ID）
3. **预筛过滤**：基于关键词做快速过滤（可选）
4. **相关性判断**：LLM 评估每篇论文与兴趣方向的相关性并打分
5. **过滤排序**：保留相关论文并按评分排序
6. **生成摘要**：
   - TopN：生成结构化摘要（TL;DR/贡献/局限/适用场景）
   - 其他：生成简短摘要（1-2 句）
7. **保存归档**：生成 Markdown 日报并归档
8. **历史记录**：保存已处理论文 ID，下次运行时跳过
9. **邮件发送/企业微信推送**：通过 SMTP 或企业微信 Webhook 发送

## 🔧 高级配置

### 支持的 LLM 提供商

- **OpenRouter**（推荐）：支持多种免费模型
- **OpenAI**：GPT-3.5/GPT-4
- **GLM**（智谱清言）：glm-4 系列
- **DeepSeek**：deepseek-chat
- **本地 Ollama**：需配置本地地址

### 重试机制

- LLM 调用失败：自动重试 3 次，指数退避（2^n 秒）
- 邮件发送失败：自动重试 3 次，指数退避

### 预筛选配置

- `PREFILTER_KEYWORDS`：只保留包含关键词的论文（标题/摘要/分类）
- `PREFILTER_NEGATIVE_KEYWORDS`：包含关键词则直接剔除
- 关键词为空则自动跳过预筛选

### LLM 缓存

- 默认启用，缓存文件为 `.llm_cache.json`
- 可用于失败重跑与降低重复调用成本

### 历史记录与去重

- 历史文件：`.paper_history.txt`（自动创建）
- 格式：`arxiv_id|处理日期`
- 每次运行前自动过滤已处理论文
- 查看统计：运行时会显示"历史记录: 共 X 篇，今日已处理 Y 篇"
- 手动清理：删除 `.paper_history.txt` 重新开始

## 📝 日报格式示例

```markdown
# 每日论文日报 (2026-01-16)

## 📌 重点推荐（Top 5）

### 1. Paper Title Here

**评分**: 9.5/10  
**作者**: Author1, Author2 等  
**日期**: 2026-01-15  
**链接**: https://arxiv.org/abs/...  

**背景**: ...  
**动机**: ...  
**方法**: ...  
**总结**: ...  
**推荐理由**: ...  

---

## 📝 其他相关论文

**1. Another Paper Title**  
评分: 7.8/10 | 作者: Author 等 | [链接](https://...)  
简短摘要内容...
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

MIT License
