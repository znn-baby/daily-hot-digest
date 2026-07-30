#!/usr/bin/env python3
"""
每日热点汇总 - 主入口
抓取 → AI 摘要 → 生成静态 HTML → 部署
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass  # GitHub Actions 通过 secrets 注入环境变量

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(ROOT_DIR, "site")
DATA_DIR = os.path.join(ROOT_DIR, "data")

sys.path.insert(0, ROOT_DIR)

from scrapers import (
    scrape_github_trending, scrape_lobsters, scrape_sspai,
    scrape_weibo, scrape_zhihu, scrape_hackernews,
)
from summarizer import summarize_with_ai
from generator import (
    generate_daily_page, generate_index_page, generate_monthly_page,
    write_shared_assets, migrate_old_pages,
)


def get_today_str() -> str:
    """获取今天的日期字符串 (UTC+8)"""
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def get_output_dir(date_str: str) -> str:
    """
    根据日期决定输出目录：
    - 当月 → site/（平铺在根目录）
    - 往月/往年 → site/YYYY/MM/（按月归档）
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    now = datetime.now()

    if dt.year == now.year and dt.month == now.month:
        return SITE_DIR
    else:
        month_dir = os.path.join(SITE_DIR, f"{dt.year}", f"{dt.month:02d}")
        os.makedirs(month_dir, exist_ok=True)
        return month_dir


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


def save_raw_data(data: dict, date_str: str):
    """保存原始数据到 data/ 目录"""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{date_str}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[数据] 原始数据已保存: {path}")


def generate_html(data: dict, ai_summary: dict | None, date_str: str):
    """生成 HTML 页面"""
    os.makedirs(SITE_DIR, exist_ok=True)

    # 1. 写入共享资源
    write_shared_assets(SITE_DIR)

    # 2. 迁移旧页面到归档目录
    migrate_old_pages(SITE_DIR)

    # 3. 生成当日页面
    output_dir = get_output_dir(date_str)
    page_html = generate_daily_page(data, ai_summary, date_str, output_dir, SITE_DIR)
    page_path = os.path.join(output_dir, f"{date_str}.html")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"[生成] 当日页面: {page_path}")

    # 4. 更新月度归档页（如果当月有旧页面被迁移）
    _update_monthly_indexes()

    # 5. 重新生成首页
    index_html = generate_index_page(SITE_DIR)
    index_path = os.path.join(SITE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"[生成] 首页: {index_path}")


def _update_monthly_indexes():
    """扫描所有月度目录，重新生成月度归档页"""
    for year_entry in os.listdir(SITE_DIR):
        year_dir = os.path.join(SITE_DIR, year_entry)
        if not os.path.isdir(year_dir) or not year_entry.isdigit() or len(year_entry) != 4:
            continue
        year = int(year_entry)

        for month_entry in os.listdir(year_dir):
            month_dir = os.path.join(year_dir, month_entry)
            if not os.path.isdir(month_dir) or not month_entry.isdigit() or len(month_entry) != 2:
                continue
            month = int(month_entry)

            # 收集该月所有日期页面
            dates = []
            for fname in os.listdir(month_dir):
                if fname.endswith(".html") and fname != "index.html" and len(fname) == 15:
                    date_str = fname[:-5]
                    try:
                        datetime.strptime(date_str, "%Y-%m-%d")
                        dates.append(date_str)
                    except ValueError:
                        pass

            if dates:
                monthly_html = generate_monthly_page(dates, year, month, month_dir, SITE_DIR)
                monthly_path = os.path.join(month_dir, "index.html")
                with open(monthly_path, "w", encoding="utf-8") as f:
                    f.write(monthly_html)
                print(f"[生成] 月度归档: {year}/{month:02d}/index.html ({len(dates)} 期)")


def main():
    date_str = get_today_str()
    print(f"\n{'='*50}")
    print(f"  每日热点汇总 - {date_str}")
    print(f"{'='*50}\n")

    # 1. 抓取数据
    data = run_scrapers()

    # 检查是否有数据
    total = sum(len(v) for v in data.values())
    if total == 0:
        print("\n[警告] 所有抓取器均返回空数据，跳过生成")
        sys.exit(1)

    # 2. 保存原始数据
    save_raw_data(data, date_str)

    # 3. AI 摘要（可选）
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    ai_summary = None
    if api_key:
        print("\n" + "=" * 50)
        print("调用 AI 生成摘要...")
        print("=" * 50)
        ai_summary = summarize_with_ai(data, api_key)
    else:
        print("\n[提示] 未设置 SILICONFLOW_API_KEY，将使用原始数据直接生成页面")
        print("[提示] 配置方法: export SILICONFLOW_API_KEY=your-key")

    # 4. 生成 HTML
    print("\n" + "=" * 50)
    print("生成 HTML 页面...")
    print("=" * 50)
    generate_html(data, ai_summary, date_str)

    print(f"\n{'='*50}")
    print(f"  完成！输出目录: {SITE_DIR}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
