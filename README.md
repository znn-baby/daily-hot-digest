<div align="center">

# Daily Hot Digest

**每天自动抓取技术社区热点 · AI 生成中文摘要 · 零成本部署到你的 GitHub Pages**

[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/znn-baby/daily-hot-digest/daily.yml?label=Daily%20Build&logo=github)](https://github.com/znn-baby/daily-hot-digest/actions)
[![GitHub Pages](https://img.shields.io/badge/Live-Demo-blue?logo=githubpages)](https://znn-baby.github.io/daily-hot-digest/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[快速开始](#-快速开始) · [在线示例](#-在线示例) · [添加数据源](#-自定义扩展) · [常见问题](#-常见问题)

</div>

---

## 这是什么？

一个**零成本、全自动**的技术资讯聚合工具。每天早晨自动运行，帮你生成一份带溯源链接的技术热点汇总：

```
GitHub Trending + Lobsters + 少数派
            ↓
     Python 抓取原始数据
            ↓
   Silicon Flow AI 生成中文摘要
            ↓
   生成带 [N] 溯源编号的静态 HTML
            ↓
    GitHub Pages 自动部署上线
```

**你不需要做任何事情**——Fork 这个仓库，配置一个免费的 API Key，剩下的交给 GitHub Actions。

## 在线示例

部署后你会得到这样的站点：

- **首页**：按日期归档的汇总列表，随时回看历史内容
- **每日页面**：分类摘要 + 底部溯源索引，每条信息都能追溯到原始来源

> Demo: [https://znn-baby.github.io/daily-hot-digest/](https://znn-baby.github.io/daily-hot-digest/)

## 特性

- **零成本运行** — GitHub Actions 免费额度 + Silicon Flow 免费 API，个人使用完全够用
- **全自动部署** — 每天定时抓取、摘要、生成、部署，无需人工干预
- **溯源可追踪** — 每条摘要内容都标注了引用编号，底部索引可一键跳转原文
- **按日期归档** — 首页自动聚合所有历史日期，随时回看
- **易于扩展** — 模块化设计，添加新数据源只需写一个 Python 文件
- **纯静态输出** — 生成的 HTML 无外部依赖，加载快、可离线查看

## 当前数据源

| 来源 | 内容类型 | 抓取状态 |
|------|----------|----------|
| [GitHub Trending](https://github.com/trending) | 每日热门开源仓库 | 稳定 |
| [Lobsters](https://lobste.rs/) | 深度技术讨论（类 Hacker News） | 稳定 |
| [少数派](https://sspai.com/) | 数码产品、效率工具、科技资讯 | 稳定 |

> 计划添加更多数据源？欢迎 PR！参考 [自定义扩展](#-自定义扩展)。

## 快速开始

### 1. Fork 并克隆

```bash
git clone git@github.com:znn-baby/daily-hot-digest.git
cd daily-hot-digest
```

### 2. 获取 Silicon Flow API Key（免费）

1. 访问 [Silicon Flow](https://cloud.siliconflow.cn) 注册账号
2. 进入 **控制台 → API 密钥 → 创建密钥**
3. 免费额度覆盖 Qwen2.5-7B-Instruct 模型，日常使用绑绰有余

### 3. 配置 GitHub

1. 进入仓库 **Settings → Secrets and variables → Actions**
2. 点击 **New repository secret**
3. Name 填 `SILICONFLOW_API_KEY`，Value 填你的 API Key
4. 进入 **Settings → Pages**，Source 选择 **GitHub Actions**

### 4. 本地测试（可选）

```bash
pip install -r requirements.txt

# 无 AI 摘要（纯原始数据展示）
python main.py

# 带 AI 摘要
export SILICONFLOW_API_KEY=your-key    # Linux/Mac
set SILICONFLOW_API_KEY=your-key       # Windows CMD
python main.py
```

生成的页面在 `site/` 目录下，双击 `index.html` 即可预览。

### 5. 推送并等待自动部署

```bash
git add -A
git commit -m "init: daily hot digest"
git push
```

推送后可以去 **Actions** 页面手动触发一次，不用等到第二天。部署完成后访问：

```
https://znn-baby.github.io/daily-hot-digest/
```

## 自定义扩展

### 添加新数据源

在 `scrapers/` 目录下新建一个 Python 文件，实现一个返回 `list[dict]` 的函数即可：

```python
# scrapers/my_source.py
import requests
from bs4 import BeautifulSoup

def scrape_my_source(limit: int = 10) -> list[dict]:
    """抓取你的数据源"""
    resp = requests.get("https://example.com/hot", timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for idx, article in enumerate(soup.select(".article"), 1):
        if idx > limit:
            break
        items.append({
            "rank": idx,
            "title": article.select_one("h2").get_text(strip=True),
            "url": article.select_one("a")["href"],
            "description": article.select_one("p").get_text(strip=True),
        })
    return items
```

然后在 `main.py` 中引入并调用，在 `generator.py` 中添加对应的渲染逻辑。

### 修改定时任务

编辑 `.github/workflows/daily.yml` 中的 cron 表达式：

```yaml
schedule:
  # 每天 UTC 01:00（北京时间 09:00）
  - cron: '0 1 * * *'
```

> 提示：GitHub Actions 的 schedule 使用 UTC 时间，北京时间 = UTC + 8。

### 更换 AI 模型

编辑 `summarizer.py` 中的 model 字段：

```python
payload = {
    "model": "Qwen/Qwen3.5-9B",  # 换成其他免费模型
    ...
}
```

Silicon Flow 支持的免费模型列表见 [官方文档](https://docs.siliconflow.cn/cn/userguide/models)。

## 项目结构

```
daily-hot-digest/
├── main.py                  # 主入口：抓取 → 摘要 → 生成
├── scrapers/                # 数据抓取模块（每个源一个文件）
│   ├── github_trending.py
│   ├── lobsters.py
│   └── sspai.py
├── summarizer.py            # AI 摘要（Silicon Flow API）
├── generator.py             # HTML 生成（含溯源编号格式）
├── .github/workflows/
│   └── daily.yml            # GitHub Actions 定时任务 + 部署
├── site/                    # 生成的静态网站（自动部署）
├── data/                    # 原始数据 JSON 备份
└── requirements.txt         # Python 依赖
```

## 常见问题

**Q: 真的完全免费吗？**
A: GitHub Actions 公开仓库每月有 2000 分钟免费额度，Silicon Flow 的 Qwen2.5-7B-Instruct 模型也有免费额度。每天运行一次，每次约 2-3 分钟，个人使用完全免费。

**Q: 不配置 AI API Key 能用吗？**
A: 可以。不配置时会直接展示抓取的原始标题和链接，跳过 AI 摘要步骤。页面仍然正常生成。

**Q: 为什么选 Silicon Flow 而不是其他 AI API？**
A: Silicon Flow 是国内平台，无需代理，注册即送免费额度，API 格式兼容 OpenAI，接入成本最低。如果你有偏好的其他 API，修改 `summarizer.py` 中的 URL 和 model 即可。

**Q: 部署后页面没有更新？**
A: 检查 Actions 页面是否运行成功。常见原因：Secret 名称拼写错误（必须是 `SILICONFLOW_API_KEY`）、Pages 的 Source 未选择 GitHub Actions。

**Q: 如何添加更多数据源？**
A: 参考 [自定义扩展](#-自定义扩展) 章节。欢迎提交 PR 贡献新的抓取模块！

## 致谢

灵感来源于每天刷 GitHub Trending、Lobsters、少数派的习惯。与其逐个翻网站，不如让机器代劳。

## License

[MIT](LICENSE)

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star 支持！**

每天一杯咖啡的时间，让技术资讯自动送到你面前。

</div>
