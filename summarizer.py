"""AI 摘要生成模块 - 使用 Silicon Flow API（兼容 OpenAI 格式）"""

import os
import re
import json
import requests

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MAX_RETRIES = 3

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


def extract_json_from_text(text: str) -> str:
    """从文本中提取 JSON 字符串（处理 markdown 代码块、前后多余文字等）"""
    # 尝试匹配 ```json ... ``` 或 ``` ... ``` （closing backticks 后可能有空格/换行/EOF）
    match = re.search(r'```(?:json)?\s*\n(.*?)\n```\s*$', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 放宽：只要找到 opening ``` 就提取到 closing ```
    match = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 尝试找到第一个 { 和最后一个 } 之间的内容
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]

    return text


def fix_unquoted_keys(text: str) -> str:
    """安全地修复未加引号的 JSON key（字符级解析，不会破坏字符串值）"""
    result = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # 跳过字符串内容
        if c == '"':
            result.append(c)
            i += 1
            while i < n and text[i] != '"':
                if text[i] == '\\' and i + 1 < n:
                    result.append(text[i])
                    result.append(text[i+1])
                    i += 2
                else:
                    result.append(text[i])
                    i += 1
            if i < n:
                result.append('"')
                i += 1
            continue
        # 检测未加引号的 key: 在 { 或 , 之后，字母开头，后跟冒号
        if c in ('{', ','):
            result.append(c)
            i += 1
            # 跳过空白
            j = i
            while j < n and text[j] in ' \t\n\r':
                j += 1
            # 检查是否是未加引号的 key
            if j < n and (text[j].isalpha() or text[j] == '_'):
                k = j
                while k < n and (text[k].isalnum() or text[k] == '_'):
                    k += 1
                key_name = text[j:k]
                # 跳过 key 后的空白
                m = k
                while m < n and text[m] in ' \t\n\r':
                    m += 1
                # 如果后面是冒号，说明是未加引号的 key
                if m < n and text[m] == ':':
                    result.append(f' "{key_name}"')
                    i = m  # 继续处理冒号
                    continue
            continue
        result.append(c)
        i += 1
    return ''.join(result)


def repair_json(text: str) -> str:
    """尝试修复常见的 JSON 格式问题"""
    # 1. 移除尾随逗号（在 } 或 ] 前的逗号）
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # 2. 修复缺少逗号的情况（在 } 或 ] 后跟 " 但中间没有逗号）
    text = re.sub(r'([}\]])\s*\n\s*"', r'\1,\n"', text)
    # 3. 安全地修复未加引号的 key
    text = fix_unquoted_keys(text)
    return text


def parse_json_response(content: str) -> dict | None:
    """尝试多种方式解析 JSON 响应"""
    # 1. 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 2. 提取 JSON 部分
    extracted = extract_json_from_text(content)
    try:
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass

    # 3. 尝试修复 JSON
    repaired = repair_json(extracted)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # 4. 尝试修复原始内容
    repaired = repair_json(content)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    return None


def call_api_with_prompt(api_key: str, prompt: str, system_prompt: str, temperature: float = 0.7) -> dict | None:
    """调用 API 并解析响应"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen3.5-9B",
        "messages": [
            {"role": "system", "content": system_prompt},
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

    # 详细调试信息
    extracted = extract_json_from_text(content)
    print(f"[AI 摘要] JSON 解析失败")
    print(f"[AI 摘要] 原始响应长度: {len(content)} 字符")
    print(f"[AI 摘要] 提取后长度: {len(extracted)} 字符")
    print(f"[AI 摘要] 原始响应前 300 字符: {content[:300]}")
    print(f"[AI 摘要] 提取内容前 300 字符: {extracted[:300]}")
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

    # 尝试多次，降低温度以提高 JSON 格式稳定性
    system_prompts = [
        "你是技术资讯编辑，只返回 JSON，不添加任何其他文字。",
        "你是技术资讯编辑，只返回 JSON，不添加任何其他文字。",
        "你是技术资讯编辑。直接返回 JSON 对象，不要用 ```json 或任何 markdown 格式包裹，不要有任何前后文字。",
    ]
    for attempt in range(MAX_RETRIES):
        temp = 0.3 if attempt > 0 else 0.7
        sys_prompt = system_prompts[attempt] if attempt < len(system_prompts) else system_prompts[-1]
        try:
            print(f"[AI 摘要] 第 {attempt + 1} 次尝试 (temperature={temp})...")
            result = call_api_with_prompt(api_key, prompt, sys_prompt, temperature=temp)
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
