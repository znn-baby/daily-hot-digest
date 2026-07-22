"""AI 摘要生成模块 - 使用 Silicon Flow API（兼容 OpenAI 格式）"""

import os
import json
import requests

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MAX_RETRIES = 2

PROMPT_TEMPLATE = """你是一位技术资讯编辑。以下是今天从多个网站抓取的热门内容原始数据。

请完成以下任务：
1. 将所有内容归纳为 4-6 个主题分类（如：AI/智能体、开发工具、系统与底层技术、数码产品/效率工具、思考与观点 等）
2. 为每个分类写一段 2-4 句的中文摘要，串联该分类下最重要的几条内容
3. 在摘要中用 [N] 标注引用编号（从 [1] 开始递增）
4. 生成完整的溯源索引列表，每条包含：编号、标题、链接、来源站点

【重要】你必须且只能返回一个 JSON 对象，格式如下：
{{"categories": [{{"name": "分类名", "color": "ai", "summary": "摘要文本 [1][2]"}}], "sources": [{{"num": 1, "title": "标题", "url": "链接", "source": "来源站", "desc": "说明"}}], "stats": {{"total_items": 0, "total_categories": 0, "total_sources": 0}}}

【禁止】不要使用 ```json 或任何 markdown 代码块包裹，不要在 JSON 前后添加任何文字、解释或空行。

---
以下是原始数据：

{raw_data}
"""

SYSTEM_PROMPT = "你是技术资讯编辑。只返回 JSON 对象本身，禁止使用 markdown 代码块，禁止任何前后文字。"


def strip_markdown_fences(text: str) -> str:
    """如果响应被 ```json ... ``` 包裹，剥离代码块标记"""
    text = text.strip()
    if text.startswith("```"):
        # 去掉开头的 ```json 或 ```
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        else:
            text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def parse_json_response(content: str) -> dict | None:
    """解析 JSON 响应：先直接解析，失败则剥离 markdown 代码块后再解析"""
    # 1. 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 2. 剥离 markdown 代码块后解析
    stripped = strip_markdown_fences(content)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3. 兜底：取第一个 { 到最后一个 } 之间的内容
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def call_api(api_key: str, prompt: str, temperature: float = 0.7) -> dict | None:
    """调用 API 并解析响应"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen3.5-9B",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": 4000,
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    result = resp.json()
    content = result["choices"][0]["message"]["content"].strip()

    parsed = parse_json_response(content)
    if parsed:
        print(f"[AI 摘要] 生成成功，{len(parsed.get('categories', []))} 个分类，"
              f"{len(parsed.get('sources', []))} 条来源")
        return parsed

    print(f"[AI 摘要] JSON 解析失败，响应前 300 字符: {content[:300]}")
    return None


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

    for attempt in range(MAX_RETRIES):
        temp = 0.3 if attempt > 0 else 0.7
        try:
            print(f"[AI 摘要] 第 {attempt + 1} 次尝试 (temperature={temp})...")
            result = call_api(api_key, prompt, temperature=temp)
            if result:
                return result
        except requests.RequestException as e:
            print(f"[AI 摘要] API 请求失败: {e}")
            return None
        except KeyError as e:
            print(f"[AI 摘要] 响应格式异常: {e}")
            return None

    print("[AI 摘要] 多次尝试均失败，跳过 AI 摘要")
    return None
