# AI 技术雷达（ai-tech-radar）

全自动 AI 学习平台：每天定时拉取 **GitHub 热门项目 + AI 前沿技术**，由 AI 去重、打分、筛选，并对最值得关注的条目生成**结构化中文深度讲解**（是什么 / 解决什么问题 / 原理 / 上手路径 / 前置知识 / 学习路径），每周日自动生成趋势综述。

数据源：GitHub Trending（爬虫）· GitHub 新晋高星（官方 API）· Hacker News（Algolia API）· arXiv（cs.AI/CL/LG）· Hugging Face（趋势模型 + Daily Papers）· 各大实验室官方博客 RSS。

技术栈：Python 3.12 + FastAPI + SQLite（零外部依赖）· LLM 可配置（Claude / DeepSeek / 任意 OpenAI 兼容端点，主模型故障自动降级）· BGE-M3 本地语义去重（可关）· Docker Compose 部署。

## VPS 快速部署（5 分钟）

前提：VPS 已装 Docker（`curl -fsSL https://get.docker.com | sh`）。

```bash
# 1. 上传/克隆项目到 VPS
scp -r ai-tech-radar user@your-vps:~/ && ssh user@your-vps && cd ai-tech-radar

# 2. 配置
cp .env.example .env
vim .env        # 填 ANTHROPIC_API_KEY / OPENAI_COMPAT_API_KEY / GITHUB_TOKEN

# 3. 启动（web 站点 + 定时调度两个容器）
docker compose up -d --build

# 4. 立即手动跑一次管线（不等定时），看着日志出内容
docker compose run --rm scheduler python -m app.pipeline

# 5. 浏览器打开 http://VPS_IP:8000
```

之后每天 9:00 / 21:00（Asia/Shanghai）自动更新，每周日 21:30 自动生成周报。

## 域名 + HTTPS（可选）

```nginx
# /etc/nginx/sites-available/radar
server {
    server_name radar.example.com;
    location / { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/radar /etc/nginx/sites-enabled/
sudo nginx -s reload
sudo certbot --nginx -d radar.example.com   # 自动 HTTPS
```

然后把 `.env` 里 `SITE_URL` 改为 `https://radar.example.com`（影响 RSS 链接），`docker compose restart`。

## 常用操作

```bash
docker compose logs -f scheduler          # 看管线日志
docker compose run --rm scheduler python -m app.pipeline   # 手动跑管线
docker compose run --rm scheduler python -m app.weekly     # 手动生成周报
cp data/radar.db backup/                  # 备份（整库就一个文件）
```

## 网页设置：在线切换模型（/settings）

`.env` 里设置 `ADMIN_PASSWORD=你的密码` 后，访问 `http://站点/settings`（用户名 `admin`）即可在网页上为**粗筛 / 精讲 / 兜底**三个角色分别配置 provider、model、base_url、API Key——三个角色可以指向**不同厂商**（比如粗筛 DeepSeek + 精讲 Claude）。保存即生效（存在数据库里，优先于 .env，下次管线运行自动使用），无需重启；页面带「测试连接」按钮。建议配合 HTTPS 使用。

## 每日推送（Telegram / 邮件）

`.env` 配好 `TELEGRAM_BOT_TOKEN`+`TELEGRAM_CHAT_ID`（找 @BotFather 建 bot、@userinfobot 查 chat_id）或 SMTP 四项+`MAIL_TO`，每次管线跑完自动推送当日 Top 8 摘要（带讲解链接）。测试：

```bash
docker compose run --rm scheduler python -m app.notify --test
```

## 详情页 AI 问答

每个条目页底部有「继续提问」：基于该条目讲解时存档的 README/材料由 AI 回答（不会重新抓网页，响应快且省 token）。需输入管理密码（防止公网游客烧你的 API 额度），回答上限由 `ASK_MAX_TOKENS` 控制。

## 浮动 AI 笔记助手（✨ 按钮）

每个页面右下角有可拖动的 ✨ 悬浮按钮（位置自动记忆）：

- **点击**打开笔记面板；**先选中页面文字再右键按钮**，可带选中内容打开
- 面板内可**切换模型**（精讲/粗筛/兜底三个角色，对应 /settings 里的配置）
- 自动抓取上下文：页面标题 + URL + 选中内容；在条目页还会自动附带讲解与 README 材料
- 生成**结构化 Markdown 笔记**（TL;DR/核心要点/详细笔记/延伸问题），自动保存
- 可**复制 Markdown / 下载 .md**；「/notes」页可查看、下载、删除全部笔记，或一键导出合并文件 `/notes/export.md`
- 生成与笔记管理需管理密码（同 ADMIN_PASSWORD）

## 八股复习系统（/quiz）

内置 **50 道成体系八股题**（Java / Python / AI 基础 / Agent / 场景设计，各 10 道，含参考答案），并实现了**对齐 ts-fsrs 的 FSRS-5 间隔重复算法**（完整卡片状态机 新题→学习中→复习→重学 + 19 参数遗忘曲线，按目标保留率 90% 动态推算下次复习时间）：

- **复习模式**：到期题 + 新题自动排队；显示答案后**右下角浮条提醒评估掌握程度**（忘了/困难/记得/简单，按钮上直接标注各自的下次间隔），评完自动进入下一题
- 每道题展示**遗忘曲线**（当前记忆保持率 R(t)、稳定度 S）
- **概览页**（/quiz）：今日复习进度条、各领域状态分布、今日复习时间轴
- **右侧会话时间轴**：复习页右侧实时记录每个节点（评分/追问）带预览摘要，**点击跳转定位**回该题
- **一键生成结构化复盘笔记**：基于今日复习数据（薄弱题、评分分布）生成，自动存入 /notes
- **AI 能力**：每题可「AI 详解」扩展答案、针对题目追问、**重要回答星标收藏**进笔记；「AI 出题」按领域扩充题库
- 评分/出题/复盘需管理密码；纯浏览公开

## 运行统计（/stats）

页脚「统计」入口（需管理密码）：累计 token 用量与成本估算、近 14 天收录趋势、各数据源 7 天健康度（某源持续为 0 = 该源挂了）、最近 30 次运行明细。

## 成本调节（.env）

| 开关 | 效果 |
|---|---|
| `EXPLAIN_LIMIT=12` | 每天深讲条数，**成本主开关**。12 条 ≈ $12/月；6 条 ≈ $6/月 |
| `MIN_SCORE_KEEP=5.0` | 调高可减少入库噪音 |
| 全换 DeepSeek | `.env` 中四行注释打开即可，月成本 < $2，质量略降 |
| `EMBEDDING_ENABLED=false` | 关闭语义去重（小内存 VPS 用），改纯 simhash |

## 本地开发 / 测试

```bash
pip install -r requirements.txt
python scripts/smoke_test.py     # 离线冒烟测试（Mock LLM，不花钱不出网）
SCORER_PROVIDER=mock EXPLAINER_PROVIDER=mock FALLBACK_PROVIDER=mock \
  python -m app.pipeline         # Mock 模式跑真实采集
uvicorn app.web.main:app --reload  # 本地起站点
```

## 项目结构

```
app/
├── collectors/   # 数据源（每源一文件，加新源只需注册到 __init__.py）
├── processors/   # 清洗 → simhash/向量去重 → AI 打分分类
├── explainer/    # 取证(README/HN评论) → 结构化讲解 → 相关推荐
├── llm/          # 多供应商客户端 + 自动降级路由
├── web/          # FastAPI + Jinja2 站点（含 RSS、搜索、归档、周报）
├── pipeline.py   # 主管线编排
├── weekly.py     # 周报生成
└── scheduler.py  # cron 调度服务
```

## 常见问题

- **首次运行很慢**：在下载 BGE-M3 模型（~2GB，缓存在 `data/hf-cache`，只下一次）。不想要就 `EMBEDDING_ENABLED=false`。
- **GitHub API 403**：没填 `GITHUB_TOKEN`，匿名限额 60 次/小时。到 github.com → Settings → Developer settings → Tokens 生成一个（无需任何权限勾选）。
- **讲解质量校验失败自动重试一次**，仍失败则该条跳过，不影响整体管线。
- **Claude API 不可用**：自动降级到 `FALLBACK_PROVIDER`（默认 DeepSeek），日志可见切换记录。
- 升级路径：数据量大了迁 PostgreSQL（`pgloader` 一条命令）；想要交互问答，在 `web/` 加路由 + 把 README 塞进上下文即可，架构不用动。
