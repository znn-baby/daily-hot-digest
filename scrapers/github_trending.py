"""GitHub Trending 抓取模块"""

import requests
from bs4 import BeautifulSoup

URL = "https://github.com/trending"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_github_trending(limit: int = 15) -> list[dict]:
    """
    抓取 GitHub Trending 页面。
    返回列表，每项包含: rank, title, url, description, stars, language
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[GitHub Trending] 请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for idx, article in enumerate(soup.select("article.Box-row"), 1):
        if idx > limit:
            break

        # 仓库名 & 链接
        h2 = article.select_one("h2")
        if not h2:
            continue
        a_tag = h2.select_one("a")
        if not a_tag:
            continue
        repo_path = a_tag.get("href", "").strip("/")
        title = repo_path.replace("/", " / ")
        url = f"https://github.com/{repo_path}"

        # 描述
        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # 语言
        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else ""

        # star 数（今日）
        stars_today = ""
        star_spans = article.select("span.d-inline-block")
        for span in star_spans:
            text = span.get_text(strip=True)
            if "stars today" in text or "star" in text.lower():
                stars_today = text
                break

        # 总 star 数
        total_stars = ""
        links = article.select("a.Link--muted")
        for link in links:
            svg = link.select_one("svg.octicon-star")
            if svg:
                total_stars = link.get_text(strip=True).replace(",", "")
                break

        items.append({
            "rank": idx,
            "title": title,
            "url": url,
            "description": description,
            "stars": total_stars,
            "stars_today": stars_today,
            "language": language,
        })

    print(f"[GitHub Trending] 成功抓取 {len(items)} 条")
    return items
