"""AI 摘要生成模块 - 使用 Silicon Flow API（兼容 OpenAI 格式）"""

import os
import json
import requests

API_URL = "https://api.siliconflow.cn/v1/chat/completions"

PROMPT_TEMPLATE = """你是一位技术资讯编辑。以下是今天从多个网站抓取的热门内容原始数据。

请完成以下任务：
1. 将所有内容归纳为 4-6 个主题分类（如：AI/智能体、开发工具、系统与底层技术、数码产品/效率工具、思考与观点 等）
2. 为每个分类写一段 2-4 句的中文摘要，串联该分类下最重要的几条内容
3. 在摘要中用 [N] 标注引用编号（从 [1] 开始递增）
4. 生成完整的溯源索引列表，每条包含：编号、标题、链接、来源站点

请严格按以下 JSON 格式返回（不要添加任何其他文字）：
{{
  "categories": [
    {{
      "name": "分类名称",
      "color": "ai|dev|sys|gadget|opinion",
      "summary": "带 [N] 引用编号的中文摘要文本"
    }}
  ],
  "sources": [
    {{
      "num": 1,
      "title": "条目标题",
      "url": "原始链接",
      "source": "GitHub Trending|Lobsters|少数派",
      "desc": "一句话说明"
    }}
  ],
  "stats": {{
    "total_items": 0,
    "total_categories": 0,
    "total_sources": 0
  }}
}}

---
以下是原始数据：

{raw_data}
"""


def summarize_with_ai(raw_data: dict, api_key: str = "") -> dict | None:
    """
    调用 Silicon Flow API 生成分类摘要。
    如果 api_key 为空或调用失败，返回 None。
    """
    if not api_key:
        api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    if not api_key:
        print("[AI 摘要] 未配置 SILICONFLOW_API_KEY，跳过 AI 摘要")
        return None

    # 格式化原始数据
    data_text = ""
    if raw_data.get("github_trending"):
        data_text += "\n【GitHub Trending】\n"
        for item in raw_data["github_trending"]:
            data_text += f"- {item['title']}: {item.get('description', '')} | {item['url']}\n"

    if raw_data.get("lobsters"):
        data_text += "\n【Lobsters】\n"
        for item in raw_data["lobsters"]:
            tags = ", ".join(item.get("tags", []))
            data_text += f"- {item['title']} [{tags}] | {item['url']}\n"

    if raw_data.get("sspai"):
        data_text += "\n【少数派】\n"
        for item in raw_data["sspai"]:
            data_text += f"- {item['title']} ({item.get('author', '')}) | {item['url']}\n"

    prompt = PROMPT_TEMPLATE.format(raw_data=data_text)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": "你是技术资讯编辑，只返回 JSON，不添加任何其他文字。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4000,
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        content = result["choices"][0]["message"]["content"].strip()

        # 清理可能的 markdown 代码块包裹
        if content.startswith("```"):
            lines = content.split("\n")
            # 去掉首尾的 ``` 行
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        parsed = json.loads(content)
        print(f"[AI 摘要] 生成成功，{len(parsed.get('categories', []))} 个分类，"
              f"{len(parsed.get('sources', []))} 条来源")
        return parsed

    except requests.RequestException as e:
        print(f"[AI 摘要] API 请求失败: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[AI 摘要] 解析响应失败: {e}")
        return None
