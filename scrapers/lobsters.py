"""Lobsters 抓取模块"""

import requests
from bs4 import BeautifulSoup

URL = "https://lobste.rs/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


def scrape_lobsters(limit: int = 15) -> list[dict]:
    """
    抓取 Lobsters 首页热帖。
    返回列表，每项包含: rank, title, url, source_url, tags, score, comments
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[Lobsters] 请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    stories = soup.select("li.story")
    for idx, story in enumerate(stories, 1):
        if idx > limit:
            break

        # 标题 & 链接
        title_tag = story.select_one("span.link a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        source_url = title_tag.get("href", "")
        if source_url.startswith("/"):
            source_url = f"https://lobste.rs{source_url}"

        # Lobsters 评论页
        comment_tag = story.select_one("a.comments_label a")
        comments_url = ""
        if comment_tag:
            href = comment_tag.get("href", "")
            comments_url = f"https://lobste.rs{href}" if href.startswith("/") else href

        # 标签
        tags = []
        for tag in story.select("a.tag"):
            tags.append(tag.get_text(strip=True))

        # 分数
        score_tag = story.select_one(".score")
        score = score_tag.get_text(strip=True) if score_tag else ""

        # 评论数
        comments_text = ""
        if comment_tag:
            comments_text = comment_tag.get_text(strip=True)

        # 作者
        author_tag = story.select_one("a.u-author")
        author = author_tag.get_text(strip=True) if author_tag else ""

        items.append({
            "rank": idx,
            "title": title,
            "url": comments_url or source_url,
            "source_url": source_url,
            "tags": tags,
            "score": score,
            "comments": comments_text,
            "author": author,
        })

    print(f"[Lobsters] 成功抓取 {len(items)} 条")
    return items
