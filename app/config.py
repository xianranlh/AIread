"""全局配置：从 .env 读取，全部可覆盖。"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- 基础 ----
    db_path: str = "data/radar.db"
    site_title: str = "AI 技术雷达"
    site_url: str = "http://localhost:8000"  # 用于 RSS/推送的绝对链接
    timezone: str = "Asia/Shanghai"
    admin_username: str = "admin"  # 网页管理用户名
    admin_password: str = ""  # 网页设置/统计/问答密码；留空则禁用管理功能

    # ---- LLM 供应商（.env 为默认值，网页 /settings 保存的配置优先）----
    # provider: anthropic | openai_compat | mock
    scorer_provider: str = "anthropic"
    scorer_model: str = "claude-haiku-4-5"
    explainer_provider: str = "anthropic"
    explainer_model: str = "claude-sonnet-4-6"
    fallback_provider: str = "openai_compat"
    fallback_model: str = "deepseek-chat"

    anthropic_api_key: str = ""
    openai_compat_api_key: str = ""
    openai_compat_base_url: str = "https://api.deepseek.com/v1"

    # ---- 采集 ----
    github_token: str = ""           # 可选，提高 API 限额
    collect_languages: str = "python,typescript,rust,go"  # trending 额外按语言抓
    hn_query_keywords: str = "LLM,AI,GPT,Claude,agent,RAG,diffusion,transformer"
    arxiv_categories: str = "cs.AI,cs.CL,cs.LG"
    arxiv_max_results: int = 60
    blog_feeds: str = (
        # —— 官方/前沿（国外）——
        "https://openai.com/news/rss.xml,"            # OpenAI 官方
        "https://deepmind.google/blog/rss.xml,"       # Google DeepMind
        "https://blog.google/technology/ai/rss/,"     # Google AI
        "https://huggingface.co/blog/feed.xml,"       # Hugging Face
        "https://www.microsoft.com/en-us/research/feed/,"  # Microsoft Research
        "https://bair.berkeley.edu/blog/feed.xml,"    # Berkeley BAIR
        "https://www.technologyreview.com/topic/artificial-intelligence/feed,"  # MIT Tech Review AI
        # —— Claude/前沿深度追踪（Anthropic 无官方 RSS，由这些高质量源覆盖）——
        "https://simonwillison.net/atom/everything/," # Simon Willison（逐条解读 Claude/LLM）
        "https://www.latent.space/feed,"              # Latent Space
        "https://importai.substack.com/feed,"         # Import AI（Jack Clark）
        "https://magazine.sebastianraschka.com/feed," # Ahead of AI
        # —— 国内 ——
        "https://www.qbitai.com/feed,"                # 量子位
        "https://www.infoq.cn/feed"                   # InfoQ 中文
    )

    # ---- 处理 ----
    dedup_days: int = 14             # 与近 N 天历史去重
    simhash_max_distance: int = 6
    vector_dup_threshold: float = 0.92
    embedding_enabled: bool = True
    embedding_model: str = "BAAI/bge-m3"
    score_batch_size: int = 20       # 每次 LLM 打分条数
    min_score_keep: float = 5.0      # 低于此分直接丢弃

    # ---- 讲解 / 问答 ----
    explain_limit: int = 12          # 每天精讲条数（成本主开关）
    readme_max_chars: int = 28000
    explain_max_tokens: int = 2500
    ask_max_tokens: int = 1000       # 详情页问答回答上限

    # ---- 每日推送（可选，配了就推；失败不影响管线）----
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass: str = ""
    mail_to: str = ""                # 收件人，多个用逗号分隔
    notify_top_n: int = 8            # 推送摘要条数

    # ---- 调度（cron 表达式，容器时区下）----
    pipeline_cron: str = "0 9,21 * * *"
    weekly_cron: str = "30 21 * * 0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
