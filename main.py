#!/usr/bin/env python3
"""
每日热点汇总 - 主入口（JSON-only 架构）
抓取 → AI 摘要 → 保存 JSON → 前端渲染
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(ROOT_DIR, "site")
DATA_DIR = os.path.join(ROOT_DIR, "data")

sys.path.insert(0, ROOT_DIR)

from scrapers import (
    scrape_github_trending, scrape_lobsters, scrape_sspai,
    scrape_weibo, scrape_zhihu, scrape_hackernews,
)
from summarizer import summarize_with_ai


# ============================================================
# 工具函数
# ============================================================

def get_today_str() -> str:
    """获取今天的日期字符串 (UTC+8)"""
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def save_data(data: dict, date_str: str, ai_summary: dict | None = None):
    """保存数据到 data/ 目录（含 AI 摘要）"""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{date_str}.json")
    payload = dict(data)
    if ai_summary:
        payload["ai_summary"] = ai_summary
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[数据] 已保存: {path}")


def generate_index_json():
    """生成 data/index.json — 所有可用日期的列表（降序）"""
    os.makedirs(DATA_DIR, exist_ok=True)
    dates = []
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".json") and len(fname) == 15 and "-complete" not in fname:
            date_str = fname[:-5]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_str)
            except ValueError:
                pass
    dates.sort(reverse=True)

    path = os.path.join(DATA_DIR, "index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"dates": dates, "updated": datetime.now().isoformat()}, f)
    print(f"[索引] data/index.json: {len(dates)} 期")


def load_data(date_str: str) -> tuple:
    """加载数据文件，返回 (data, ai_summary)"""
    path = os.path.join(DATA_DIR, f"{date_str}.json")
    if not os.path.exists(path):
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    ai_summary = payload.pop("ai_summary", None)
    return payload, ai_summary


# ============================================================
# 旧页面迁移：将 YYYY-MM-DD.html 转为重定向页
# ============================================================

REDIRECT_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Redirecting...</title>
<link rel="canonical" href="{base_url}#/{date}">
<script>location.replace('{base_url}#/{date}');</script>
</head><body><p>Redirecting to <a href="{base_url}#/{date}">{date}</a>...</p></body></html>"""


def migrate_to_redirects():
    """将 site/ 下所有旧日期 HTML 转为重定向页"""
    if not os.path.isdir(SITE_DIR):
        return

    count = 0
    # 根目录下的 YYYY-MM-DD.html
    for fname in os.listdir(SITE_DIR):
        if fname.endswith(".html") and len(fname) == 15 and fname != "index.html":
            date_str = fname[:-5]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            path = os.path.join(SITE_DIR, fname)
            _write_redirect(path, date_str, "")
            count += 1

    # 子目录下的 YYYY/MM/YYYY-MM-DD.html
    for year_entry in os.listdir(SITE_DIR):
        year_dir = os.path.join(SITE_DIR, year_entry)
        if not os.path.isdir(year_dir) or not year_entry.isdigit() or len(year_entry) != 4:
            continue
        for month_entry in os.listdir(year_dir):
            month_dir = os.path.join(year_dir, month_entry)
            if not os.path.isdir(month_dir) or not month_entry.isdigit():
                continue
            for fname in os.listdir(month_dir):
                if fname.endswith(".html") and len(fname) == 15 and fname != "index.html":
                    date_str = fname[:-5]
                    path = os.path.join(month_dir, fname)
                    _write_redirect(path, date_str, "../../")
                    count += 1

    if count:
        print(f"[迁移] {count} 个旧页面已转为重定向")


def _write_redirect(path: str, date_str: str, base_url: str):
    """写入重定向页面（仅在内容不同时）"""
    content = REDIRECT_TEMPLATE.format(base_url=base_url, date=date_str)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            if f.read().strip() == content.strip():
                return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# 回填模式
# ============================================================

def backfill_all():
    """为所有历史数据生成 AI 摘要（如果缺失）"""
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        print("[回填] 未设置 SILICONFLOW_API_KEY，无法生成 AI 摘要")
        return

    dates = sorted(
        f[:-5] for f in os.listdir(DATA_DIR)
        if f.endswith(".json") and len(f) == 15 and "-complete" not in f
    )
    if not dates:
        print("[回填] 没有找到数据文件")
        return

    for date_str in dates:
        data, ai_summary = load_data(date_str)
        if data is None:
            continue
        if ai_summary is None:
            print(f"[回填] {date_str}: 生成 AI 摘要...")
            ai_summary = summarize_with_ai(data, api_key)
            save_data(data, date_str, ai_summary)
        else:
            print(f"[回填] {date_str}: 已有 AI 摘要，跳过")

    generate_index_json()
    print("[回填] 完成")


# ============================================================
# 抓取 & 主流程
# ============================================================

def run_scrapers() -> dict:
    """运行所有抓取器"""
    print("=" * 50)
    print("开始抓取数据...")
    print("=" * 50)

    data = {
        "github_trending": scrape_github_trending(),
        "lobsters": scrape_lobsters(),
        "sspai": scrape_sspai(),
        "weibo": scrape_weibo(),
        "zhihu": scrape_zhihu(),
        "hackernews": scrape_hackernews(),
    }

    total = sum(len(v) for v in data.values())
    print(f"\n抓取完成，共 {total} 条数据")
    return data


def main():
    # --backfill 模式
    if "--backfill" in sys.argv:
        print(f"\n{'='*50}")
        print(f"  回填模式：为历史数据生成 AI 摘要")
        print(f"{'='*50}\n")
        backfill_all()
        return

    date_str = get_today_str()
    print(f"\n{'='*50}")
    print(f"  每日热点汇总 - {date_str}")
    print(f"{'='*50}\n")

    # 1. 抓取数据
    data = run_scrapers()
    total = sum(len(v) for v in data.values())
    if total == 0:
        print("\n[警告] 所有抓取器均返回空数据，跳过生成")
        sys.exit(1)

    # 2. AI 摘要
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    ai_summary = None
    if api_key:
        print("\n" + "=" * 50)
        print("调用 AI 生成摘要...")
        print("=" * 50)
        ai_summary = summarize_with_ai(data, api_key)
    else:
        print("\n[提示] 未设置 SILICONFLOW_API_KEY，跳过 AI 摘要")

    # 3. 保存数据（含 AI 摘要）
    save_data(data, date_str, ai_summary)

    # 4. 更新索引
    generate_index_json()

    # 5. 迁移旧页面为重定向
    os.makedirs(SITE_DIR, exist_ok=True)
    migrate_to_redirects()

    print(f"\n{'='*50}")
    print(f"  完成！")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
