import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any
from urllib.parse import urlparse

import requests
from urllib import error as urllib_error
from urllib import request as urllib_request
from flask import Flask, Response, jsonify, render_template, request, stream_with_context
from flask_cors import CORS

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

DDGS_PROXY = (
    os.getenv("HTTPS_PROXY")
    or os.getenv("https_proxy")
    or os.getenv("HTTP_PROXY")
    or os.getenv("http_proxy")
    or os.getenv("DDGS_PROXY")
    or None
)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_CANDIDATES = [
    os.path.join(_BASE_DIR, "templates"),
    os.path.join(os.path.dirname(_BASE_DIR), "templates"),
]
_TEMPLATE_FOLDER = next((path for path in _TEMPLATE_CANDIDATES if os.path.isdir(path)), _TEMPLATE_CANDIDATES[0])

app = Flask(__name__, template_folder=_TEMPLATE_FOLDER)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

# ------------------ LM Studio 配置 ------------------
LM_STUDIO_BASE = os.getenv("LM_STUDIO_BASE", "http://127.0.0.1:1234")
LM_STUDIO_MODELS_URL = f"{LM_STUDIO_BASE}/v1/models"
LM_STUDIO_CHAT_URL = f"{LM_STUDIO_BASE}/v1/chat/completions"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "local-model")
DEFAULT_SYSTEM_PROMPT = os.getenv("DEFAULT_SYSTEM_PROMPT", "")
# ----------------------------------------------------


@app.route("/")
def index():
    """渲染移动端优先的前端页面。"""
    return render_template("index.html")


@app.errorhandler(404)
def not_found(error):
    """把 API 404 转成可读的 JSON 错误，方便前端展示。"""
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "接口未找到（404）",
            "detail": f"请求路径 {request.path} 不存在，请检查前端请求地址和后端路由是否匹配。",
        }), 404

    return render_template("index.html"), 404


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": "请求内容过大（413）",
        "detail": "上传的代码、图片或聊天上下文超过 12MB，请减少代码量或拆分为多次提问。",
    }), 413


def _normalize_models(payload: Any) -> list[dict]:
    """把 LM Studio 的模型响应规范化为前端可直接渲染的列表。"""
    if isinstance(payload, dict):
        data = payload.get("data", payload)
    else:
        data = payload

    if not isinstance(data, list):
        return []

    models: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id") or item.get("name")
        if model_id:
            models.append({"id": str(model_id)})

    return models


def _extract_context_length(model: Any, default: int = 50000) -> int:
    """从 LM Studio 模型元数据提取上下文上限。"""
    if not isinstance(model, dict):
        return default

    candidates = (
        model.get("context_length"),
        model.get("max_context_length"),
        model.get("max_context_tokens"),
        model.get("context_window"),
        model.get("max_position_embeddings"),
        (model.get("capabilities") or {}).get("context_length")
        if isinstance(model.get("capabilities"), dict) else None,
        (model.get("settings") or {}).get("context_length")
        if isinstance(model.get("settings"), dict) else None,
        (model.get("metadata") or {}).get("context_length")
        if isinstance(model.get("metadata"), dict) else None,
        (model.get("metadata") or {}).get("max_context_length")
        if isinstance(model.get("metadata"), dict) else None,
    )
    for value in candidates:
        try:
            length = int(value)
        except (TypeError, ValueError):
            continue
        if length > 0:
            return length
    return default


def _model_info_from_payload(payload: Any, model_id: str | None = None) -> dict:
    """规范化 LM Studio 模型信息，并为缺失字段提供默认值。"""
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    models = data if isinstance(data, list) else []
    selected = None
    if model_id:
        selected = next(
            (item for item in models if isinstance(item, dict)
             and str(item.get("id") or item.get("name") or item.get("model") or "") == model_id),
            None,
        )
    if selected is None and models:
        selected = next((item for item in models if isinstance(item, dict)), None)

    selected_id = str(
        (selected or {}).get("id")
        or (selected or {}).get("name")
        or (selected or {}).get("model")
        or model_id
        or DEFAULT_MODEL
    )
    context_length = _extract_context_length(selected)
    return {
        "id": selected_id,
        "context_length": context_length,
        "max_context_length": context_length,
    }


def _extract_reply_text(payload: Any) -> str:
    """从 OpenAI 兼容响应中提取 assistant 的回复文本。"""
    if not isinstance(payload, dict):
        return ""

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    response = payload.get("response")
    if isinstance(response, str) and response.strip():
        return response.strip()

    output = payload.get("output")
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, str) and content.strip():
                parts.append(content.strip())
            elif isinstance(content, list):
                for piece in content:
                    if isinstance(piece, dict):
                        text = piece.get("text") or piece.get("content")
                        if text:
                            parts.append(str(text))
                    elif isinstance(piece, str):
                        parts.append(piece)
        if parts:
            return "".join(parts).strip()

    choices = payload.get("choices") or []
    if not choices or not isinstance(choices, list):
        return ""

    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message") if isinstance(first_choice, dict) else None
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()

    # 兼容某些返回把 content 拆成片段数组的情况
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts).strip()

    return str(content).strip() if content is not None else ""


def _request_json(url: str, method: str = "GET", payload: dict | None = None, timeout: int = 60) -> Any:
    """发送 HTTP 请求并解析 JSON。"""
    headers = {"Content-Type": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=timeout) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            return json.loads(response_text)
    except urllib_error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise RuntimeError(f"HTTP {exc.code}：{error_text}") from exc


def _build_responses_input(messages: list[dict], system_prompt: str) -> str:
    """把聊天消息转换为 responses API 可接受的输入文本。"""
    lines = [f"System: {system_prompt}"]
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user").strip() or "user"
        content = message.get("content")
        if isinstance(content, list):
            content = "".join(str(item) for item in content)
        lines.append(f"{role.capitalize()}: {content if content is not None else ''}")
    lines.append("Assistant:")
    return "\n".join(lines)


def _call_lm_studio_chat(payloads: list[tuple[str, dict]]) -> Any:
    """按顺序尝试多个 LM Studio 聊天接口，直到其中一个成功。"""
    last_exc: Exception | None = None
    for url, payload in payloads:
        try:
            print("[chat] 尝试接口:", url)
            return _request_json(url, method="POST", payload=payload, timeout=120)
        except Exception as exc:
            last_exc = exc
            print("[chat] 接口失败:", url, repr(exc))

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("未找到可用的 LM Studio 聊天接口。")


def is_deep_link(url: str) -> bool:
    """判断 URL 是否指向具体文章、论文、视频或新闻详情页。"""
    if not isinstance(url, str) or not url.strip():
        return False

    try:
        parsed_url = urlparse(url.strip())
    except ValueError:
        return False

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return False

    normalized_url = url.strip().lower()
    hostname = (parsed_url.hostname or "").lower()
    path = (parsed_url.path or "").lower()
    path_segments = [segment for segment in path.split("/") if segment]
    path_text = "/".join(path_segments)

    blocked_patterns = (
        r"(?:^|/)search(?:[/?]|$)",
        r"(?:^|[?&])query=",
        r"duckduckgo\.com/l/",
        r"bing\.com/search",
        r"baidu\.com/s(?:[/?]|$)",
        r"/category/",
        r"/tag/",
        r"/topics/",
    )
    if any(re.search(pattern, normalized_url) for pattern in blocked_patterns):
        return False

    if not path_segments:
        return False

    if len(path_segments) == 1 and len(path_segments[0]) <= 8:
        return False

    detail_patterns = (
        r"\.(?:html?|shtml|pdf)(?:$|[?#])",
        r"/(?:article|p|v|video|view|abs)(?:/|$)",
        r"(?:^|/)bv[0-9a-z]+(?:/|$)",
    )
    if any(re.search(pattern, path) for pattern in detail_patterns):
        return True

    has_numeric_id = bool(re.search(r"(?:^|[-_/])\d{3,}(?:$|[-_/])", path))
    has_long_slug = any(len(segment) >= 18 for segment in path_segments)
    if len(path_segments) >= 2 and (has_numeric_id or has_long_slug):
        return True

    return len(path_segments) >= 3 and all(len(segment) > 1 for segment in path_segments)


def _search_web_once(query: str, max_results: int = 3) -> list[dict]:
    """执行一次 ddgs 搜索；异常交由外层统一处理。"""
    results: list[dict] = []
    seen_urls: set[str] = set()
    fetch_limit = max(1, max_results) * 3
    with DDGS(proxy=DDGS_PROXY) as ddgs:
        for item in ddgs.text(query, max_results=fetch_limit):
            if not isinstance(item, dict):
                continue
            url = item.get("href") or item.get("url")
            title = item.get("title") or "未命名网页"
            snippet = item.get("body") or item.get("snippet") or ""
            if not url or not is_deep_link(str(url)):
                continue
            normalized_url = str(url).strip()
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            results.append({
                "id": len(results) + 1,
                "title": str(title),
                "snippet": str(snippet),
                "url": normalized_url,
            })
            if len(results) >= max_results:
                break
    return results


def search_web(query: str, max_results: int = 3, timeout: float = 12.0) -> list[dict]:
    """使用 ddgs 搜索并规范化结果；失败后自动重试一次。"""
    if not query or DDGS is None:
        print("[WARN] 联网搜索失败/超时，跳过搜索")
        return []

    for attempt in range(2):
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_search_web_once, query, max_results)
            return future.result(timeout=timeout)
        except (FuturesTimeoutError, Exception) as exc:
            if attempt == 0:
                print("[WARN] 联网搜索失败/超时，准备重试一次：", repr(exc))
            else:
                print("[WARN] 联网搜索失败/超时，跳过搜索：", repr(exc))
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    return []


def _message_content_text(message: Any) -> str:
    """提取消息中的纯文本内容。"""
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            str(item.get("text") or item.get("content") or "")
            if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content or "").strip()


def _clean_messages_for_api(messages: list[dict]) -> list[dict]:
    """清理历史消息开头残留的联网状态提示，避免污染模型上下文。"""
    status_prefix_pattern = re.compile(
        r"^\s*(?:"
        r"🔍\s*正在联网搜索最新资料\.\.\."
        r"|"
        r"⚠️\s*联网搜索超时/无响应，已切换至本地模型回答\.\.\."
        r")\s*"
    )

    cleaned_messages: list[dict] = []
    for message in messages:
        if not isinstance(message, dict):
            continue

        cleaned_message = dict(message)
        content = cleaned_message.get("content")
        if isinstance(content, str):
            cleaned_message["content"] = status_prefix_pattern.sub("", content, count=1)
        cleaned_messages.append(cleaned_message)

    return cleaned_messages


def _extract_search_query(messages: list[dict]) -> str:
    """提取最新问题；过短问题会拼接上一条用户背景。"""
    user_messages = [
        _message_content_text(message)
        for message in messages
        if isinstance(message, dict) and message.get("role") == "user"
    ]
    user_messages = [message for message in user_messages if message]
    if not user_messages:
        return ""

    latest = user_messages[-1]
    if len(latest) >= 4 or len(user_messages) < 2:
        return latest

    background = user_messages[-2]
    return f"{background} {latest}".strip()


def _build_multimodal_messages(messages: list[dict], image_base64: str | None) -> list[dict]:
    """将最后一条用户消息转换为 OpenAI 兼容的文本+图片消息。"""
    if not image_base64:
        return messages

    multimodal_messages = [dict(message) for message in messages]
    user_index = next(
        (index for index in range(len(multimodal_messages) - 1, -1, -1)
         if isinstance(multimodal_messages[index], dict)
         and multimodal_messages[index].get("role") == "user"),
        -1,
    )
    if user_index < 0:
        return messages

    user_message = dict(multimodal_messages[user_index])
    text_content = _message_content_text(user_message)
    user_message["content"] = [
        {"type": "text", "text": text_content},
        {"type": "image_url", "image_url": {"url": image_base64}},
    ]
    multimodal_messages[user_index] = user_message
    return multimodal_messages


def _extract_visual_search_query(image_base64: str, user_query: str, model: str) -> str:
    """调用视觉模型识别图片并提炼一个适合搜索的关键词。"""
    prompt = (
        f"请识别这张图片中的核心物体/文字/错误信息，并结合用户问题‘{user_query}’，"
        "生成一个适合搜索引擎查询的 1 个精准关键词。"
        "只返回关键词，不要解释，不要 Markdown。"
    )
    control_payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}},
            ],
        }],
        "temperature": 0.1,
        "max_tokens": 40,
        "stream": False,
    }
    try:
        response = requests.post(LM_STUDIO_CHAT_URL, json=control_payload, timeout=20)
        response.raise_for_status()
        query = _extract_reply_text(response.json()).strip()
        return re.sub(r"\s+", " ", query).strip(" \"'`\n")[:200]
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        print("[chat] 图片视觉识别失败，回退到用户文本搜索词")
        return ""


def _is_obviously_non_search_query(query: str) -> bool:
    """快速拦截代码、数学表达式和常见短问候，避免不必要的联网裁决。"""
    text = str(query or "").strip()
    if not text:
        return True

    if re.fullmatch(r"\s*```[\s\S]*```\s*", text):
        return True

    code_patterns = (
        r"^\s*(?:def|class|import|from|return|async|await|function|const|let|var)\b",
        r"^\s*#include\s*[<\"]",
        r"^\s*(?:public|private|protected|static)\s+(?:class|void|int|string)\b",
        r"(?:=>|:=|\{\s*[\w$]+\s*:|;\s*(?:if|for|while)\b)",
    )
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in code_patterns):
        return True

    greetings = (
        r"^(?:hi|hello|hey|yo|你好|您好|嗨|哈喽|こんにちは|こんばんは|안녕|bonjour|hola|ciao)"
        r"[!！。.？?～~\s]*$"
    )
    if re.fullmatch(greetings, text, re.IGNORECASE):
        return True

    compact = re.sub(r"\s+", "", text)
    if len(compact) <= 40 and re.fullmatch(r"[\d\s()+\-*/%^.=<>≤≥πe]+", compact, re.IGNORECASE):
        return True

    return False


@app.route("/api/models", methods=["GET"])
def get_models():
    """获取 LM Studio 当前可用模型；失败时返回默认占位模型。"""
    try:
        print("[models] 收到请求：/api/models")
        models = _normalize_models(_request_json(LM_STUDIO_MODELS_URL, timeout=10))
        return jsonify(models or [{"id": "local-model"}])
    except Exception as exc:
        print("[models] 获取模型失败:", repr(exc))
        return jsonify([{"id": "local-model"}])


@app.route("/api/model-info", methods=["GET"])
def get_model_info():
    """返回当前/指定 LM Studio 模型的上下文上限。"""
    requested_model = str(request.args.get("model") or "").strip() or None
    try:
        payload = _request_json(LM_STUDIO_MODELS_URL, timeout=10)
        return jsonify(_model_info_from_payload(payload, requested_model))
    except Exception as exc:
        print("[models] 获取模型上下文上限失败:", repr(exc))
        return jsonify({
            "id": requested_model or DEFAULT_MODEL,
            "context_length": 8192,
            "fallback": True,
        })


@app.route("/api/chat", methods=["POST"])
def chat():
    """把前端对话转发给 LM Studio，并返回 AI 回复。"""
    try:
        data = request.get_json(silent=True) or {}
        messages = data.get("messages", [])
        system_prompt = str(data.get("system_prompt") or DEFAULT_SYSTEM_PROMPT).strip() or DEFAULT_SYSTEM_PROMPT
        temperature = data.get("temperature", 0.7)
        model = str(data.get("model") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
        web_search = data.get("web_search", False) is True
        image_base64 = data.get("image_base64")
        if not isinstance(image_base64, str) or not image_base64.startswith("data:image/"):
            image_base64 = None

        if not isinstance(messages, list):
            return jsonify({"error": "messages 必须是数组。"}), 400

        message_chars = sum(
            len(str(message.get("content") or ""))
            for message in messages
            if isinstance(message, dict)
        )
        if message_chars > 600000:
            return jsonify({
                "error": "上下文内容过长",
                "detail": f"当前消息文本约 {message_chars} 个字符，已超过 60000 字符限制；请拆分代码后再发送。",
            }), 413

        messages = _clean_messages_for_api(messages)

        print("[chat] 收到请求：/api/chat")
        print(
            "[chat] 请求摘要:",
            {
                "message_count": len(messages),
                "model": model,
                "web_search": web_search,
                "has_image": bool(image_base64),
                "image_size": len(image_base64) if image_base64 else 0,
            },
        )

        try:
            temperature_value = float(temperature)
        except (TypeError, ValueError):
            temperature_value = 0.7

        temperature_value = max(0.0, min(1.0, temperature_value))

        api_messages = _build_multimodal_messages(messages, image_base64)
        final_messages = [{"role": "system", "content": system_prompt}] + api_messages
        payload = {
            "model": model,
            "messages": final_messages,
            "temperature": temperature_value,
            "stream": True,
        }

        print("[chat] 模型:", model)
        print("[chat] 温度:", temperature_value)
        print("[chat] 消息数:", len(final_messages))

        def generate():
            try:
                request_payload = payload
                if web_search:
                    user_query = _extract_search_query(messages)
                    # 不要在最终回答前强制再调用一次视觉模型。文本模型可能不支持图片，
                    # 这次额外调用会让请求长时间无首字节；有用户问题时直接用它搜索，
                    # 图片仍会随最终多模态请求交给模型处理。
                    search_query = user_query
                    if not search_query or _is_obviously_non_search_query(search_query):
                        should_search, search_query = False, ""
                    else:
                        should_search = True

                    if not should_search:
                        search_query = ""
                    else:
                        status_chunk = {
                            "choices": [{"delta": {"content": "🔍 正在联网搜索最新资料...\n\n"}}]
                        }
                        yield f"data: {json.dumps(status_chunk, ensure_ascii=False)}\n\n"

                    search_results = search_web(search_query) if should_search else []
                    if search_results:
                        citations_chunk = {"citations": search_results}
                        yield f"data: {json.dumps(citations_chunk, ensure_ascii=False)}\n\n"

                        reference_lines = ["【网络搜索实时参考资料】："]
                        for result in search_results:
                            reference_lines.append(
                                f"[{result['id']}] 标题: {result['title']} | 摘要: {result['snippet']}"
                            )
                        reference_lines.append(
                            "\n【回答与引用规范】：\n"
                            "1. 请结合上述【网络搜索实时参考资料】以及你自身的通用知识库，全面地回答用户问题。\n"
                            "2. 凡是取材自上述参考资料的具体事实/数据，必须在该句末尾标注对应的角标（如 [1] 或 [2]）。\n"
                            "3. 允许基于你的知识对背景、行业影响、相关概念进行扩充阐述，确保回答条理清晰、内容充实，避免过于简短。"
                        )
                        search_system_prompt = "\n\n".join([
                            system_prompt,
                            "\n".join(reference_lines),
                        ])
                        request_payload = {
                            **payload,
                            "messages": [{"role": "system", "content": search_system_prompt}] + api_messages,
                        }
                    elif should_search:
                        warning_chunk = {
                            "choices": [{"delta": {"content": "⚠️ 联网搜索超时/无响应，已切换至本地模型回答...\n\n"}}]
                        }
                        yield f"data: {json.dumps(warning_chunk, ensure_ascii=False)}\n\n"

                with requests.post(
                    LM_STUDIO_CHAT_URL,
                    json=request_payload,
                    stream=True,
                    timeout=(10, 120),
                ) as lm_response:
                    if lm_response.status_code >= 400:
                        error_text = lm_response.text[:2000]
                        print("[chat] LM Studio 返回 HTTP 错误:", lm_response.status_code, error_text)
                        detail = f"HTTP {lm_response.status_code}：{error_text}"
                        if image_base64:
                            detail += "。请确认当前 LM Studio 模型支持视觉输入（image_url）。"
                        yield f"data: {json.dumps({'error': 'LM Studio 返回错误', 'detail': detail}, ensure_ascii=False)}\n\n"
                        return

                    for line in lm_response.iter_lines(decode_unicode=False):
                        if not line:
                            continue
                        if isinstance(line, bytes):
                            line = line.decode("utf-8", errors="replace")
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("data:"):
                            data = line[5:].lstrip()
                            yield f"data: {data}\n\n"
                        else:
                            yield f"data: {line}\n\n"
            except requests.RequestException as exc:
                print("[chat] 请求 LM Studio 失败:", repr(exc))
                yield f"data: {json.dumps({'error': '无法连接到 LM Studio，请确认本地服务已启动并监听 1234 端口。'}, ensure_ascii=False)}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        return Response(stream_with_context(generate()), content_type="text/event-stream; charset=utf-8")

    except TimeoutError:
        return jsonify({"error": "LM Studio 请求超时，请检查本地模型是否仍在生成中。"}), 504
    except urllib_error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        print("[chat] LM Studio 返回 HTTP 错误:", exc.code, error_text)

        if exc.code == 404:
            return jsonify({
                "error": "LM Studio 接口未找到（404）",
                "detail": "请确认 LM Studio 本地服务已启动，并检查当前接口地址是否为 /v1/models 和 /v1/chat/completions。",
            }), 502

        return jsonify({
            "error": "LM Studio 返回错误",
            "detail": f"HTTP {exc.code}：{error_text}",
        }), 502
    except urllib_error.URLError as exc:
        if "timed out" in str(exc).lower():
            return jsonify({"error": "LM Studio 请求超时，请检查本地模型是否仍在生成中。"}), 504
        print("[chat] 请求 LM Studio 失败:", repr(exc))
        return jsonify({"error": "无法连接到 LM Studio，请确认本地服务已启动并监听 1234 端口。"}), 502
    except Exception as exc:
        print("[chat] 处理异常:", repr(exc))
        return jsonify({"error": f"后端处理失败：{exc}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
