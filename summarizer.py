"""AI 摘要生成模块 - 使用 Silicon Flow API（兼容 OpenAI 格式）"""

import os
import re
import json
import requests

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MAX_RETRIES = 3

PROMPT_TEMPLATE = """你是一位技术资讯编辑，正在给读者写今天的科技简报。以下是今天从多个网站抓取的热门内容原始数据。

请完成以下任务：
1. 将所有内容归纳为 4-6 个主题分类（如：AI/智能体、开发工具、系统与底层技术、数码产品/效率工具、思考与观点 等）
2. 为每个分类写摘要，要求：
   - GitHub Trending 项目写一段，逐个介绍重要项目，带上具体数据（star 数等），语气自然
   - 社区热议（Lobsters 讨论、少数派文章）另起一段，用聊天的口吻介绍，像你在跟朋友分享今天看到的有趣内容
   - 适当加入你的看法和点评（"这个挺有意思""值得关注""搞安全的朋友必看"等），但不要太刻意
3. 在提到每个项目时用 [N] 标注引用编号（从 [1] 开始递增，按出现顺序编号）
4. 生成完整的溯源索引列表，每条包含：编号、标题、链接、来源站点

【覆盖要求】必须覆盖所有三个来源的内容：GitHub Trending 项目、Lobsters 讨论帖、少数派文章。不要只写 GitHub 项目而忽略 Lobsters 和少数派的内容。

【写作风格】像一个真实的技术博主在写每日简报，不要像机器生成的。可以用"今天""有意思的是""值得一提的是"等口语化表达。GitHub 项目和社区讨论要分成不同的段落。

【重要】你必须且只能返回一个 JSON 对象，格式示例如下（注意所有字段名和结构必须严格一致）：
{{
  "categories": [{{"name": "分类名", "color": "ai", "summary": "今天 GitHub 上 AI Agent 相关项目又炸了。worldmonitor[1] 用 AI 做实时全球情报监控与地缘政治追踪，已经拿了 66,000+ star，搞国际关系研究的朋友可以看看。ai-agent-book[2] 是李博杰写的智能体设计开源书，配套完整代码，想系统入门的话这本不错。

Lobsters 今天最火的一条挺吓人的：OpenAI 某模型在测试中突破安全沙箱，自己跑去 Hugging Face 抓数据来通过测试[3]。这事在圈里吵翻了，AI 安全边界到底在哪？"}}],
  "sources": [{{"num": 1, "title": "标题", "url": "链接", "source": "来源站", "desc": "说明"}}],
  "stats": {{"total_items": 0, "total_categories": 0, "total_sources": 0}}
}}

【禁止】不要使用 ```json 或任何 markdown 代码块包裹，不要在 JSON 前后添加任何文字、解释或空行。

---
以下是原始数据：

{raw_data}
"""

SYSTEM_PROMPT = "你是技术资讯编辑，像真人博主一样写每日科技简报。语气自然口语化，GitHub 项目和社区讨论分段写。必须覆盖 GitHub、Lobsters、少数派三个来源。只返回 JSON 对象本身，禁止使用 markdown 代码块，禁止任何前后文字。"


def extract_json_from_text(text: str) -> str:
    """从文本中提取 JSON 字符串（处理 markdown 代码块、前后多余文字等）"""
    # 匹配 ```json ... ``` 或 ``` ... ```（closing backticks 后可能有空格/换行/EOF）
    match = re.search(r'```(?:json)?\s*\n(.*?)\n```\s*$', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 放宽：只要找到 opening ``` 就提取到 closing ```
    match = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 兜底：取第一个 { 到最后一个 } 之间的内容
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text


def parse_json_response(content: str) -> dict | None:
    """尝试多种方式解析 JSON 响应"""
    # 1. 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # 2. 从 markdown 代码块中提取后解析
    extracted = extract_json_from_text(content)
    try:
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass
    # 3. 修复常见 JSON 问题
    repaired = _repair_json(extracted)
    if repaired:
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass
    return None


def _repair_json(text: str) -> str:
    """修复 LLM 生成的常见 JSON 问题"""
    s = text
    # 去除尾随逗号: ,} 或 ,]
    s = re.sub(r',\s*([}\]])', r'\1', s)
    # 对象/数组之间缺少逗号: }\n" 或 ]\n"
    s = re.sub(r'([}\]])\s*\n\s*"', r'\1,\n"', s)
    # 修复字符串值中未转义的双引号（LLM 常在中文里写 "xxx" 而不转义）
    s = _fix_unescaped_quotes(s)
    # 修复字符串中未转义的控制字符
    s = _fix_unescaped_control_chars(s)
    return s


def _fix_unescaped_quotes(text: str) -> str:
    """修复 JSON 字符串值中未转义的双引号。
    逐字符扫描，跟踪是否在字符串内及当前是 key 还是 value。
    将字符串内未转义的 " 替换为 \\"
    """
    result = []
    in_string = False
    expect_key = True  # True=期待 key, False=期待 value
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '\\' and in_string and i + 1 < len(text):
            result.append(ch)
            result.append(text[i + 1])
            i += 2
            continue
        if ch == '"':
            if not in_string:
                in_string = True
                result.append(ch)
            else:
                # 在字符串内遇到引号 — 判断是否是真正的字符串结束
                j = i + 1
                while j < len(text) and text[j] in ' \t\r\n':
                    j += 1
                next_ch = text[j] if j < len(text) else ''
                # 合法的字符串结束符：, } ] : （key 后跟冒号，value 后跟逗号/括号）
                if next_ch in ',}]' or (next_ch == ':' and expect_key):
                    in_string = False
                    expect_key = not expect_key  # key→value 或 value→key
                    result.append(ch)
                else:
                    # 这是字符串内的引号，需要转义
                    result.append('\\')
                    result.append(ch)
        elif ch == ':' and not in_string:
            expect_key = False  # 冒号后期待 value
            result.append(ch)
        elif ch in '{[' and not in_string:
            expect_key = True  # 新对象/数组开始，期待 key
            result.append(ch)
        elif ch in ',]' and not in_string:
            expect_key = True  # 逗号/数组结束后，下一个是 key（或数组元素）
            result.append(ch)
        else:
            result.append(ch)
        i += 1
    return ''.join(result)


def _fix_unescaped_control_chars(text: str) -> str:
    """修复 JSON 字符串值中未转义的控制字符（换行、制表符等）"""
    result = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '\\' and in_string and i + 1 < len(text):
            result.append(ch)
            result.append(text[i + 1])
            i += 2
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ch in '\n\r\t':
            result.append('\\' + {'\n': 'n', '\r': 'r', '\t': 't'}[ch])
        else:
            result.append(ch)
        i += 1
    return ''.join(result)


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
        "max_tokens": 8000,
    }
    # 尝试禁用 Qwen3 thinking 模式（Silicon Flow 支持）
    # 如果 API 不支持该参数会被忽略，不影响正常请求
    payload["enable_thinking"] = False

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    result = resp.json()
    choice = result["choices"][0]
    message = choice.get("message", {})
    content = (message.get("content") or "").strip()
    finish_reason = choice.get("finish_reason", "unknown")

    # 如果 content 为空但存在 reasoning_content，说明 thinking 模式未正确关闭
    if not content and message.get("reasoning_content"):
        print(f"[AI 摘要] content 为空但存在 reasoning_content，"
              f"finish_reason={finish_reason}，尝试从 reasoning 中提取...")
        content = message["reasoning_content"].strip()

    print(f"[AI 摘要] finish_reason={finish_reason}, content长度={len(content)}")

    if not content:
        print(f"[AI 摘要] API 返回空内容，message keys: {list(message.keys())}")
        return None

    parsed = parse_json_response(content)
    if parsed:
        print(f"[AI 摘要] 生成成功，{len(parsed.get('categories', []))} 个分类，"
              f"{len(parsed.get('sources', []))} 条来源")
        return parsed

    print(f"[AI 摘要] JSON 解析失败，响应前 500 字符: {content[:500]}")
    # 保存原始响应用于调试
    try:
        debug_path = os.path.join(os.path.dirname(__file__), "data", "ai-debug-response.txt")
        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[AI 摘要] 原始响应已保存: {debug_path}")
    except Exception:
        pass
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
