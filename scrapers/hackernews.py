"""Hacker News 抓取模块"""

import requests

API_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
HEADERS = {
    "User-Agent": "DailyHotDigest/1.0",
}


def scrape_hackernews(limit: int = 15) -> list[dict]:
    """
    抓取 Hacker News 热榜。
    返回列表，每项包含: rank, title, url, score, author, descendants
    """
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        story_ids = resp.json()[:limit]
    except (requests.RequestException, ValueError) as e:
        print(f"[Hacker News] 请求失败: {e}")
        return []

    items = []
    for idx, story_id in enumerate(story_ids, 1):
        try:
            item_resp = requests.get(ITEM_URL.format(story_id), headers=HEADERS, timeout=15)
            item_resp.raise_for_status()
            story = item_resp.json()
        except (requests.RequestException, ValueError):
            continue

        title = story.get("title", "")
        if not title:
            continue

        # 链接优先用 url 字段（外部链接），否则用 HN 讨论页
        url = story.get("url", "") or f"https://news.ycombinator.com/item?id={story_id}"

        items.append({
            "rank": idx,
            "title": title,
            "url": url,
            "score": story.get("score", 0),
            "author": story.get("by", ""),
            "comments": story.get("descendants", 0),
            "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
        })

    print(f"[Hacker News] 成功抓取 {len(items)} 条")
    return items
