# Daily ArXiv Digest

智能论文日报生成器，每日从 ArXiv 拉取论文，用 OpenAI-compatible LLM 生成中文摘要，并把结果保存为 Markdown。需要 Python 3.10+、ArXiv 网络访问和一个可用的 LLM API；推送渠道是可选的。

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

### 1. 准备环境

```bash
git clone https://github.com/WhoJay0609/Daily-Arvix.git
cd Daily-Arvix
python3 --version  # 需要 3.10 或更高版本
python3 -m pip install -r requirements.txt
```

### 2. 配置 LLM 和兴趣方向

复制示例配置。示例默认 `PUSH_CHANNEL=none`，只写本地文件，不会向示例收件人发送消息：

```bash
cp env.example .env
```

至少填写 `OPENAI_API_KEY`。`OPENAI_BASE_URL` 和 `OPENAI_MODEL` 指向所选的 OpenAI-compatible 服务；服务的模型名称、计费和速率限制由服务商决定。不要把真实密钥提交到 Git。

关键配置项：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | LLM API 密钥 | `sk-...` |
| `OPENAI_BASE_URL` | API 地址 | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | 模型名称 | `deepseek/deepseek-chat` |
| `ARXIV_CATEGORIES` | ArXiv 分类 | `cs.LG,cs.DC` |
| `ARXIV_MAX_RESULTS` | 每个 ArXiv 分类最多拉取数量 | `50` |
| `PREFILTER_KEYWORDS` | 标题/摘要/分类至少命中一个的关键词（逗号分隔） | `diffusion,graph` |
| `PREFILTER_NEGATIVE_KEYWORDS` | 标题/摘要/分类命中任一项即排除 | `survey,benchmark` |
| `TOP_N_DETAILED` | Top 详细摘要数量 | `5` |
| `LLM_CACHE_ENABLED` | 是否启用 LLM 缓存 | `true` |
| `LLM_CACHE_FILE` | LLM 缓存文件路径 | `.llm_cache.json` |
| `OUTPUT_DIR` | 日报输出目录 | `output` |
| `HISTORY_FILE` | 已处理 ArXiv ID 文件 | `.paper_history.txt` |
| `SMTP_HOST` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` 或 `587` |
| `SMTP_USER` | 发件邮箱 | `your@qq.com` |
| `SMTP_PASS` | SMTP 授权码 | `授权码` |
| `MAIL_FROM` | 发件人 | `your@qq.com` |
| `MAIL_TO` | 收件人（逗号分隔） | `a@example.com,b@example.com` |
| `WECOM_WEBHOOK_URL` | 企业微信机器人 Webhook | `https://qyapi.weixin.qq.com/...` |
| `PUSH_CHANNEL` | 推送方式；`none` 只保存本地文件 | `none` / `email` / `wecom` / `both` |

**兴趣提示词**：编辑 `prompts/interest.txt`，描述你的研究兴趣（一行即可）

### 3. 手动运行

```bash
python3 main.py
```

首次运行会检查 `OPENAI_API_KEY`，缺少时只打印错误并退出。完整首次运行需要先安装上面的依赖，并会访问 ArXiv 和所选 LLM；本地检查不会替你调用这些外部服务。配置完整且网络可用时生成：

- `output/daily_digest_YYYY-MM-DD.md`：按日期归档的 Markdown；
- `output/daily_digest.md`：同内容的最新版本**副本**，不是软链接；
- `.paper_history.txt`：本次候选记录的 ArXiv ID 及日期（不等于每篇摘要都生成成功）；
- `.llm_cache.json`：启用缓存时保存评分和摘要结果。

如果当天归档已经存在，程序会读取该文件并跳过拉取、筛选和 LLM 生成，只尝试再次推送。

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

添加以下行（每天 6:00 运行；将路径替换为实际克隆目录）：

```cron
0 6 * * * cd /path/to/Daily-Arvix && /usr/bin/python3 main.py >> cron.log 2>&1
```

`scripts/setup_cron.sh` 会从自身位置推导项目目录并选择 `python3`（其次是 `python`），因此可直接在克隆目录运行。项目、解释器或日志路径含 `%` 时脚本会拒绝安装，因为 `%` 是 cron 的特殊字符。

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

### 测试 ArXiv 时间戳（会访问 ArXiv）

```bash
python3 scripts/test_arxiv_time.py
```

### 测试邮件（会真实发送）

```bash
python3 scripts/test_email.py
```

### 测试企业微信（会真实发送）

```bash
python3 scripts/test_wecom.py
```

只有在 `.env` 中填入真实 SMTP 或企业微信凭据后才运行对应推送测试；没有凭据时它们会跳过或失败，不会生成本地日报。

## 🎯 工作流程

1. **拉取论文**：按 `ARXIV_CATEGORIES` 分别请求 ArXiv，每个分类最多 `ARXIV_MAX_RESULTS` 篇；使用 `updated` 时间筛选最近 24 小时的记录，若没有记录则回退到接口返回的前几篇。
2. **历史过滤**：从论文链接提取 ArXiv ID，跳过 `.paper_history.txt` 中已经记录的 ID。
3. **预筛过滤**：可选地在标题、摘要和分类上应用包含/排除关键词。
4. **相关性判断**：LLM 根据 `prompts/interest.txt` 为每篇候选返回 `is_relevant`、0–10 分数和理由。
5. **过滤排序**：只保留 `is_relevant=true` 的结果，并按分数降序排列。
6. **生成摘要**：
   - TopN：生成结构化摘要（TL;DR/贡献/局限/适用场景）
   - 其他：生成简短摘要（1-2 句）
7. **保存归档**：写入日期归档和最新版本副本，并在流程结束时记录本次候选的 ArXiv ID。
8. **可选推送**：当 `PUSH_CHANNEL` 为 `email`、`wecom` 或 `both` 时，通过 SMTP 或企业微信 Webhook 发送；否则只保留本地文件。

## 🔧 高级配置

### 支持的 LLM 服务

项目使用 OpenAI Python 客户端的 `chat.completions.create` 接口；可配置提供该接口的服务，例如 OpenRouter、OpenAI、GLM、DeepSeek 或本地 Ollama。具体模型名写入 `OPENAI_MODEL`，实际兼容性由服务商接口和模型决定。

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

## 边界与限制

- 程序没有离线或 dry-run 模式：一次完整运行需要访问 ArXiv 和 LLM 服务。相关性评分最终失败的论文不会进入相关结果；摘要生成失败的已入选论文可能保留回退内容或空摘要字段。
- ArXiv 的时间窗口依据 `updated`（缺失时用 `published`），每个分类独立受 `ARXIV_MAX_RESULTS` 限制；接口异常的分类会返回空结果。
- 摘要由所选 LLM 根据 ArXiv 元数据生成，项目不做事实核验或引用核验；请把它当作筛选和阅读入口。
- 邮件和企业微信推送失败不会删除已经生成的本地文件。默认示例使用 `PUSH_CHANNEL=none`，避免占位邮箱或 Webhook 被误用。

## 兼容性、排错与本地检查

- Python 3.10+；cron 安装脚本适用于提供 `crontab` 的 Unix-like 环境。Windows 定时任务未在项目中提供。
- `ModuleNotFoundError: feedparser`：当前环境尚未安装项目依赖，先运行 `python3 -m pip install -r requirements.txt`。
- `错误: 未配置 OPENAI_API_KEY`：在 `.env` 中填写密钥后再运行；完整运行仍需要 ArXiv 和 LLM 网络访问。

仓库提供的 cron 回归检查和语法检查已在 2026-09-12 本地运行：

```console
python3 -m unittest tests.test_setup_cron -v  # 1 passed
python3 -m compileall -q main.py src tests   # exit 0
```

`python3 main.py` 的成功输出依赖外部服务和真实凭据，因此没有把联网运行结果当作仓库内的兼容性证据。

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

欢迎提交 Issue 和 Pull Request。兴趣方向请修改 `prompts/interest.txt`；配置示例只保留占位值，不要提交 `.env`、缓存、历史记录或输出文件。若修改筛选、缓存或推送行为，请同时更新 README 中的流程和边界说明。

## 📄 许可

MIT License
