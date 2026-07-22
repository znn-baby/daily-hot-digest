"""少数派 (sspai.com) 抓取模块"""

import requests
from bs4 import BeautifulSoup

URL = "https://sspai.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


def scrape_sspai(limit: int = 12) -> list[dict]:
    """
    抓取少数派首页文章。
    返回列表，每项包含: rank, title, url, author, summary
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[少数派] 请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    # 少数派首页文章卡片 - 尝试多种选择器
    articles = soup.select("article")
    if not articles:
        articles = soup.select("[class*='ArticleItem'], [class*='article-card'], [class*='recommend']")
    if not articles:
        articles = soup.select("[class*='card'], [class*='item']")

    seen_titles = set()
    idx = 0

    for article in articles:
        if idx >= limit:
            break

        # 标题
        title_tag = article.select_one("a[class*='title'], h2 a, h3 a, .title a, a.title")
        if not title_tag:
            title_tag = article.select_one("a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        if not title or len(title) < 4 or title in seen_titles:
            continue
        seen_titles.add(title)

        href = title_tag.get("href", "")
        if href.startswith("/"):
            href = f"https://sspai.com{href}"
        elif not href.startswith("http"):
            continue

        # 作者
        author_tag = article.select_one("[class*='author'], .nickname, a[class*='author']")
        author = author_tag.get_text(strip=True) if author_tag else ""

        # 摘要
        summary_tag = article.select_one("[class*='summary'], [class*='desc'], p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""

        idx += 1
        items.append({
            "rank": idx,
            "title": title,
            "url": href,
            "author": author,
            "summary": summary,
        })

    print(f"[少数派] 成功抓取 {len(items)} 条")
    return items
