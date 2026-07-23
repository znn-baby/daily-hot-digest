"""知乎热榜抓取模块（通过 tophub.today 聚合）"""

import re
import requests
from bs4 import BeautifulSoup

URL = "https://tophub.today/n/mproPpoq6O"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


def scrape_zhihu(limit: int = 15) -> list[dict]:
    """
    通过 tophub.today 抓取知乎热榜。
    返回列表，每项包含: rank, title, url, hot_value
    """
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[知乎热榜] 请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for row in soup.select("table tr")[1:]:  # 跳过表头
        if len(items) >= limit:
            break

        cells = row.select("td")
        if len(cells) < 3:
            continue

        # 标题在 cell[2]，链接在 cell[2] 或 cell[3] 的 a 标签中
        title_cell = cells[2]
        title_text = title_cell.get_text(strip=True)

        # 提取链接
        a_tag = title_cell.select_one("a")
        if not a_tag:
            a_tag = row.select_one("a[href*='zhihu']")
        if not a_tag:
            continue

        href = a_tag.get("href", "")
        if not href.startswith("http"):
            href = f"https://www.zhihu.com{href}" if href.startswith("/") else f"https://www.zhihu.com/question/{href}"

        # 解析热度和清理标题
        hot_value = 0
        hot_match = re.search(r'(\d+\.?\d*)\s*(万)?\s*热度?$', title_text)
        if hot_match:
            num_str = hot_match.group(1).strip()
            is_wan = hot_match.group(2) is not None
            title = title_text[:hot_match.start()].strip().rstrip('？?')
            try:
                num = float(num_str)
                hot_value = int(num * 10000) if is_wan else int(num)
            except ValueError:
                pass
        else:
            title = title_text

        if not title:
            continue

        items.append({
            "rank": len(items) + 1,
            "title": title,
            "url": href,
            "hot_value": hot_value,
        })

    print(f"[知乎热榜] 成功抓取 {len(items)} 条")
    return items
