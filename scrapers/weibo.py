"""微博热搜抓取模块（通过 tophub.today 聚合）"""

import requests
from bs4 import BeautifulSoup

URL = "https://tophub.today/n/KqndgxeLl9"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


def scrape_weibo(limit: int = 15) -> list[dict]:
    """
    通过 tophub.today 抓取微博热搜榜。
    返回列表，每项包含: rank, title, url, hot_value
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[微博热搜] 请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for row in soup.select("table tr")[1:]:  # 跳过表头
        if len(items) >= limit:
            break

        cells = row.select("td")
        if len(cells) < 2:
            continue

        # 标题和链接
        a_tag = cells[1].select_one("a")
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        href = a_tag.get("href", "")
        if not title:
            continue

        # 热度
        hot_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
        # 解析热度数字（如 "167万" → 1670000）
        hot_value = 0
        if hot_text:
            hot_text = hot_text.replace(",", "")
            if "万" in hot_text:
                try:
                    hot_value = int(float(hot_text.replace("万", "")) * 10000)
                except ValueError:
                    pass
            elif "亿" in hot_text:
                try:
                    hot_value = int(float(hot_text.replace("亿", "")) * 100000000)
                except ValueError:
                    pass
            else:
                try:
                    hot_value = int(hot_text)
                except ValueError:
                    pass

        items.append({
            "rank": len(items) + 1,
            "title": title,
            "url": href if href.startswith("http") else f"https://s.weibo.com/weibo?q={title}",
            "hot_value": hot_value,
        })

    print(f"[微博热搜] 成功抓取 {len(items)} 条")
    return items
