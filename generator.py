"""HTML 生成模块 - 生成带溯源索引的静态页面"""

import os
import json
from datetime import datetime

# 分类颜色映射
COLORS = {
    "ai": ("#e8734a", "AI / 智能体"),
    "dev": ("#4a90d9", "开发工具 / 工程实践"),
    "sys": ("#6aab73", "系统与底层技术"),
    "gadget": ("#c77dba", "数码产品 / 效率工具"),
    "opinion": ("#d4a84b", "思考与观点"),
    "security": ("#d9534f", "安全"),
    "web": ("#5bc0de", "Web 开发"),
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日热点汇总 | {date}</title>
<style>
:root {{
  --warm-bg: #faf6f1; --card-bg: #ffffff; --text-primary: #3a3a3a;
  --text-secondary: #777; --border-light: #e8e0d8;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
  background: var(--warm-bg); color: var(--text-primary);
  line-height: 1.8; padding: 40px 20px;
}}
.container {{ max-width: 780px; margin: 0 auto; }}
.header {{
  text-align: center; margin-bottom: 40px;
  padding-bottom: 24px; border-bottom: 2px solid var(--border-light);
}}
.header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: 1px; }}
.header .date {{ font-size: 15px; color: var(--text-secondary); margin-top: 8px; }}
.header .stats {{
  display: flex; justify-content: center; gap: 24px;
  margin-top: 14px; font-size: 13px; color: var(--text-secondary);
}}
.header .stats span {{
  background: var(--card-bg); padding: 4px 14px;
  border-radius: 20px; border: 1px solid var(--border-light);
}}
.nav-link {{
  display: inline-block; margin-top: 12px; font-size: 13px;
  color: var(--text-secondary); text-decoration: none;
  border-bottom: 1px dashed var(--border-light);
}}
.nav-link:hover {{ color: var(--text-primary); }}
.category {{
  background: var(--card-bg); border-radius: 12px;
  padding: 28px 32px; margin-bottom: 20px;
  border: 1px solid var(--border-light);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}}
.category-title {{
  display: flex; align-items: center; gap: 10px;
  font-size: 19px; font-weight: 700; margin-bottom: 16px;
  padding-bottom: 12px; border-bottom: 1px dashed var(--border-light);
}}
.category-badge {{
  display: inline-block; width: 10px; height: 10px;
  border-radius: 50%; flex-shrink: 0;
}}
.category p {{ font-size: 15px; margin-bottom: 12px; text-align: justify; }}
.cite {{
  display: inline; font-size: 12px; font-weight: 600;
  vertical-align: super; line-height: 1; padding: 0 1px;
}}
.cite a {{ text-decoration: none; }}
.cite a:hover {{ text-decoration: underline; }}
.source-index {{
  background: var(--card-bg); border-radius: 12px;
  padding: 28px 32px; margin-top: 32px;
  border: 1px solid var(--border-light);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}}
.source-index h2 {{
  font-size: 18px; font-weight: 700; margin-bottom: 20px;
  padding-bottom: 12px; border-bottom: 2px solid var(--border-light);
}}
.source-group {{ margin-bottom: 18px; }}
.source-group-title {{
  font-size: 13px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
}}
.source-list {{ list-style: none; padding: 0; }}
.source-list li {{
  font-size: 14px; padding: 5px 0;
  display: flex; align-items: baseline; gap: 8px; line-height: 1.6;
}}
.source-list li .num {{
  flex-shrink: 0; display: inline-block; width: 22px; height: 22px;
  line-height: 22px; text-align: center; border-radius: 50%;
  font-size: 11px; font-weight: 700; color: #fff;
}}
.source-list li a {{
  color: var(--text-primary); text-decoration: none;
  border-bottom: 1px dashed var(--border-light);
}}
.source-list li a:hover {{ border-bottom-color: #4a90d9; color: #4a90d9; }}
.source-list li .desc {{ color: var(--text-secondary); font-size: 13px; }}
.footer {{
  text-align: center; margin-top: 32px;
  font-size: 12px; color: var(--text-secondary);
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>每日热点汇总</h1>
    <div class="date">{date_display}</div>
    <div class="stats">
      <span>{source_count} 个信息源</span>
      <span>{category_count} 个分类</span>
      <span>{item_count} 条内容</span>
    </div>
    <a class="nav-link" href="index.html">&larr; 查看所有日期</a>
  </div>

{categories_html}

  <div class="source-index">
    <h2>溯源索引</h2>
{sources_by_group_html}
  </div>

  <div class="footer">
    自动生成 · 数据截至 {date} · 
    <a href="index.html" style="color:var(--text-secondary)">查看所有日期</a>
  </div>
</div>
</body>
</html>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日热点汇总 - 归档</title>
<style>
:root {{ --warm-bg: #faf6f1; --card-bg: #ffffff; --text-primary: #3a3a3a;
  --text-secondary: #777; --border-light: #e8e0d8; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
  background: var(--warm-bg); color: var(--text-primary);
  line-height: 1.8; padding: 40px 20px;
}}
.container {{ max-width: 600px; margin: 0 auto; }}
.header {{
  text-align: center; margin-bottom: 40px;
  padding-bottom: 24px; border-bottom: 2px solid var(--border-light);
}}
.header h1 {{ font-size: 28px; font-weight: 700; }}
.header p {{ font-size: 15px; color: var(--text-secondary); margin-top: 8px; }}
.date-list {{ list-style: none; }}
.date-list li {{
  background: var(--card-bg); border: 1px solid var(--border-light);
  border-radius: 8px; padding: 14px 20px; margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}}
.date-list li a {{
  color: var(--text-primary); text-decoration: none;
  font-size: 16px; font-weight: 600;
}}
.date-list li a:hover {{ color: #4a90d9; }}
.date-list li .meta {{
  font-size: 13px; color: var(--text-secondary); margin-top: 4px;
}}
.empty {{
  text-align: center; padding: 60px 20px;
  color: var(--text-secondary); font-size: 15px;
}}
.footer {{
  text-align: center; margin-top: 40px;
  font-size: 12px; color: var(--text-secondary);
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>每日热点汇总</h1>
    <p>自动抓取 GitHub Trending / Lobsters / 少数派 + AI 摘要</p>
  </div>
  {date_list_html}
  <div class="footer">
    Powered by GitHub Actions · 每日 UTC 01:00 自动更新
  </div>
</div>
</body>
</html>"""


def _get_color(color_key: str) -> str:
    """获取分类颜色值"""
    return COLORS.get(color_key, ("#888", color_key))[0]


def _get_color_name(color_key: str) -> str:
    """获取分类中文名"""
    return COLORS.get(color_key, ("#888", color_key))[1]


def generate_daily_page(data: dict, ai_summary: dict | None, date_str: str) -> str:
    """
    生成单日汇总 HTML 页面。
    data: 原始抓取数据
    ai_summary: AI 生成的摘要（可能为 None）
    date_str: 日期字符串 YYYY-MM-DD
    """
    if ai_summary:
        return _generate_from_ai_summary(ai_summary, date_str, data)
    else:
        return _generate_from_raw_data(data, date_str)


def _generate_from_ai_summary(ai_summary: dict, date_str: str, raw_data: dict) -> str:
    """使用 AI 摘要生成页面"""
    categories = ai_summary.get("categories", [])
    sources = ai_summary.get("sources", [])
    stats = ai_summary.get("stats", {})

    # 生成分类 HTML
    categories_html = ""
    for cat in categories:
        color_key = cat.get("color", "ai")
        color = _get_color(color_key)
        name = cat.get("name", "未分类")
        summary = cat.get("summary", "")

        # 将 [N] 转换为带链接的上标
        import re
        def replace_cite(match):
            num = match.group(1)
            return (f'<span class="cite" style="color:{color}">'
                    f'<a href="#src{num}">[{num}]</a></span>')

        summary_html = re.sub(r'\[(\d+)\]', replace_cite, summary)

        categories_html += f"""
  <div class="category">
    <div class="category-title">
      <span class="category-badge" style="background:{color}"></span>
      {name}
    </div>
    <p>{summary_html}</p>
  </div>
"""

    # 按来源分组生成溯源索引
    sources_by_source = {}
    for src in sources:
        source_name = src.get("source", "其他")
        if source_name not in sources_by_source:
            sources_by_source[source_name] = []
        sources_by_source[source_name].append(src)

    sources_html = ""
    for source_name, items in sources_by_source.items():
        sources_html += f"""
    <div class="source-group">
      <div class="source-group-title">{source_name}</div>
      <ul class="source-list">
"""
        for item in items:
            num = item.get("num", 0)
            title = item.get("title", "")
            url = item.get("url", "#")
            desc = item.get("desc", "")
            # 根据来源确定颜色
            color = "#888"
            for s_name, s_items in sources_by_source.items():
                if "GitHub" in s_name:
                    for si in s_items:
                        if si.get("num") == num:
                            color = _get_color("dev")
                elif "Lobsters" in s_name:
                    for si in s_items:
                        if si.get("num") == num:
                            color = _get_color("sys")
                elif "少数派" in s_name:
                    for si in s_items:
                        if si.get("num") == num:
                            color = _get_color("gadget")

            sources_html += (
                f'        <li id="src{num}">'
                f'<span class="num" style="background:{color}">{num}</span>'
                f'<a href="{url}" target="_blank">{title}</a> '
                f'<span class="desc">— {desc}</span></li>\n'
            )
        sources_html += "      </ul>\n    </div>\n"

    # 统计
    source_count = len(sources_by_source)
    category_count = len(categories)
    item_count = stats.get("total_items", len(sources))

    # 日期显示
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        date_display = f"{dt.year} 年 {dt.month} 月 {dt.day} 日 · {weekdays[dt.weekday()]}"
    except ValueError:
        date_display = date_str

    return HTML_TEMPLATE.format(
        date=date_str,
        date_display=date_display,
        source_count=source_count,
        category_count=category_count,
        item_count=item_count,
        categories_html=categories_html,
        sources_by_group_html=sources_html,
    )


def _generate_from_raw_data(data: dict, date_str: str) -> str:
    """无 AI 摘要时，直接用原始数据生成简洁页面"""
    categories_html = ""
    source_num = 0
    all_sources = []

    # GitHub Trending
    gh_items = data.get("github_trending", [])
    if gh_items:
        items_html = ""
        for item in gh_items:
            source_num += 1
            stars = f" ({item['stars']} stars)" if item.get("stars") else ""
            items_html += f'<li><a href="{item["url"]}" target="_blank">{item["title"]}</a>{stars} — {item.get("description", "")}</li>'
            all_sources.append({"num": source_num, "title": item["title"], "url": item["url"],
                                "source": "GitHub Trending", "desc": item.get("description", "")})
        categories_html += f"""
  <div class="category">
    <div class="category-title">
      <span class="category-badge" style="background:{_get_color('dev')}"></span>
      GitHub Trending
    </div>
    <ul style="padding-left:20px;font-size:14px;">{items_html}</ul>
  </div>
"""

    # Lobsters
    lob_items = data.get("lobsters", [])
    if lob_items:
        items_html = ""
        for item in lob_items:
            source_num += 1
            tags = ", ".join(item.get("tags", []))
            tag_str = f' <span style="color:#999">[{tags}]</span>' if tags else ""
            items_html += f'<li><a href="{item["url"]}" target="_blank">{item["title"]}</a>{tag_str}</li>'
            all_sources.append({"num": source_num, "title": item["title"], "url": item["url"],
                                "source": "Lobsters", "desc": tags})
        categories_html += f"""
  <div class="category">
    <div class="category-title">
      <span class="category-badge" style="background:{_get_color('sys')}"></span>
      Lobsters 热帖
    </div>
    <ul style="padding-left:20px;font-size:14px;">{items_html}</ul>
  </div>
"""

    # 少数派
    sspai_items = data.get("sspai", [])
    if sspai_items:
        items_html = ""
        for item in sspai_items:
            source_num += 1
            author = f' ({item.get("author", "")})' if item.get("author") else ""
            items_html += f'<li><a href="{item["url"]}" target="_blank">{item["title"]}</a>{author}</li>'
            all_sources.append({"num": source_num, "title": item["title"], "url": item["url"],
                                "source": "少数派", "desc": item.get("author", "")})
        categories_html += f"""
  <div class="category">
    <div class="category-title">
      <span class="category-badge" style="background:{_get_color('gadget')}"></span>
      少数派精选
    </div>
    <ul style="padding-left:20px;font-size:14px;">{items_html}</ul>
  </div>
"""

    # 溯源索引（按来源分组）
    sources_by_source = {}
    for src in all_sources:
        sn = src["source"]
        if sn not in sources_by_source:
            sources_by_source[sn] = []
        sources_by_source[sn].append(src)

    sources_html = ""
    for sn, items in sources_by_source.items():
        sources_html += f"""
    <div class="source-group">
      <div class="source-group-title">{sn}</div>
      <ul class="source-list">
"""
        for item in items:
            color = {"GitHub Trending": "#4a90d9", "Lobsters": "#6aab73", "少数派": "#c77dba"}.get(sn, "#888")
            sources_html += (
                f'        <li id="src{item["num"]}">'
                f'<span class="num" style="background:{color}">{item["num"]}</span>'
                f'<a href="{item["url"]}" target="_blank">{item["title"]}</a> '
                f'<span class="desc">— {item["desc"]}</span></li>\n'
            )
        sources_html += "      </ul>\n    </div>\n"

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        date_display = f"{dt.year} 年 {dt.month} 月 {dt.day} 日 · {weekdays[dt.weekday()]}"
    except ValueError:
        date_display = date_str

    return HTML_TEMPLATE.format(
        date=date_str,
        date_display=date_display,
        source_count=len(sources_by_source),
        category_count=3 if categories_html else 0,
        item_count=len(all_sources),
        categories_html=categories_html,
        sources_by_group_html=sources_html,
    )


def generate_index_page(site_dir: str) -> str:
    """
    扫描 site_dir 下所有日期命名的 HTML 文件，生成归档首页。
    """
    dates = []
    if os.path.isdir(site_dir):
        for fname in os.listdir(site_dir):
            if fname.endswith(".html") and fname != "index.html" and len(fname) == 15:
                # 格式: YYYY-MM-DD.html
                date_str = fname[:-5]
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    dates.append(date_str)
                except ValueError:
                    pass

    dates.sort(reverse=True)

    if not dates:
        list_html = '<div class="empty">暂无内容，等待首次自动生成...</div>'
    else:
        list_html = '<ul class="date-list">'
        for d in dates:
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
                weekdays = ["一", "二", "三", "四", "五", "六", "日"]
                display = f"{dt.year}-{dt.month:02d}-{dt.day:02d} 周{weekdays[dt.weekday()]}"
            except ValueError:
                display = d
            list_html += f'<li><a href="{d}.html">{display}</a></li>'
        list_html += '</ul>'

    return INDEX_TEMPLATE.format(date_list_html=list_html)
