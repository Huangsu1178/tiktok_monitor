"""
Shared OpenAI-compatible client helpers for AI skills.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import AI_CONFIG


class AIClientMixin:
    """Provide shared client setup, retry logic and response parsing."""

    def _init_ai_client(self, api_key: str = "", api_base: str = "", model: str = ""):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "") or AI_CONFIG.get("api_base", "")
        self.model = model or AI_CONFIG["default_model"]
        self._client = None
        self._build_client()

    def _build_client(self):
        if not (OPENAI_AVAILABLE and self.api_key):
            self._client = None
            return

        client_kwargs: Dict[str, Any] = {
            "api_key": self.api_key,
            "http_client": httpx.Client(
                event_hooks={
                    "request": [self._log_request],
                    "response": [self._log_response],
                },
                timeout=httpx.Timeout(
                    connect=AI_CONFIG["timeout_connect"],
                    read=AI_CONFIG["timeout_read"],
                    write=AI_CONFIG["timeout_write"],
                    pool=AI_CONFIG["timeout_pool"],
                ),
            ),
        }
        if self.api_base:
            client_kwargs["base_url"] = self.api_base
        self._client = OpenAI(**client_kwargs)

    def is_available(self) -> bool:
        return OPENAI_AVAILABLE and bool(self.api_key) and self._client is not None

    def update_config(self, api_key: str, api_base: str = "", model: str = ""):
        self.api_key = api_key
        if api_base or api_base == "":
            self.api_base = api_base
        if model:
            self.model = model
        self._build_client()

    def _log_request(self, request: httpx.Request):
        if not AI_CONFIG.get("debug_api_logging", False):
            return
        print("\n[AI Client] ===== Request =====")
        print(f"[AI Client] Method: {request.method}")
        print(f"[AI Client] URL: {request.url}")
        print(f"[AI Client] Headers: {dict(request.headers)}")
        try:
            body = json.loads(request.content.decode("utf-8"))
            print(f"[AI Client] Body: {json.dumps(body, ensure_ascii=False, indent=2)}")
        except Exception:
            print(f"[AI Client] Body: {request.content[:500]}")
        print("[AI Client] ====================\n")

    def _log_response(self, response: httpx.Response):
        if not AI_CONFIG.get("debug_api_logging", False):
            return
        print("\n[AI Client] ===== Response =====")
        print(f"[AI Client] Status Code: {response.status_code}")
        print(f"[AI Client] Headers: {dict(response.headers)}")
        try:
            body = response.json()
            print(f"[AI Client] Body: {json.dumps(body, ensure_ascii=False, indent=2)}")
        except Exception:
            print(f"[AI Client] Body: {response.text[:500]}")
        print("[AI Client] =====================\n")

    def _call_api_with_retry(
        self,
        messages: List[Dict[str, Any]],
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> Optional[Any]:
        if not self._client:
            return None

        retries = max_retries or AI_CONFIG["max_retries"]
        last_error = None

        for attempt in range(retries):
            try:
                if attempt > 0:
                    wait_time = self._get_retry_wait_seconds(attempt, last_error)
                    print(f"[AI Client] Retry {attempt + 1}/{retries} in {wait_time}s")
                    time.sleep(wait_time)

                return self._client.chat.completions.create(
                    model=self.model,
                    messages=self._normalize_messages(messages, content_mode="text"),
                    **kwargs,
                )
            except Exception as exc:
                last_error = exc
                print(f"[AI Client] Attempt {attempt + 1} failed: {exc}")

                # Some OpenAI-compatible providers require content blocks instead of plain strings.
                if self._should_retry_with_content_blocks(exc):
                    try:
                        print("[AI Client] Retrying with content blocks format")
                        return self._client.chat.completions.create(
                            model=self.model,
                            messages=self._normalize_messages(messages, content_mode="blocks"),
                            **kwargs,
                        )
                    except Exception as block_exc:
                        last_error = block_exc
                        print(f"[AI Client] Content blocks retry failed: {block_exc}")

                if self._should_retry_with_raw_request(exc):
                    raw_response = self._call_raw_chat_completion(messages, **kwargs)
                    if raw_response is not None:
                        return raw_response

                if not self._is_retryable_error(exc) or attempt >= retries - 1:
                    break

        print(f"[AI Client] API call failed: {last_error}")
        return None

    def _get_retry_wait_seconds(self, attempt: int, error: Optional[Exception]) -> int:
        error_text = str(error or "").lower()
        if "429" in error_text or "rate limit" in error_text or "too many" in error_text:
            return 5 * (AI_CONFIG["retry_backoff_base"] ** attempt)
        return AI_CONFIG["retry_backoff_base"] ** attempt

    def _is_retryable_error(self, error: Exception) -> bool:
        error_text = str(error).lower()
        if any(token in error_text for token in ("400", "badrequest", "401", "403", "authentication")):
            return False
        return any(
            token in error_text
            for token in ("429", "rate limit", "too many", "500", "502", "503", "504", "connection", "timeout", "network")
        )

    def _should_retry_with_content_blocks(self, error: Exception) -> bool:
        error_text = str(error).lower()
        return "unsupported content type" in error_text or "content type" in error_text

    def _should_retry_with_raw_request(self, error: Exception) -> bool:
        error_text = str(error).lower()
        return any(
            token in error_text
            for token in (
                "unsupported content type",
                "content type",
                "invalid_request_error",
                "400",
                "badrequest",
            )
        )

    def _call_raw_chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None

        url = self._get_chat_completions_url()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        timeout = httpx.Timeout(
            connect=AI_CONFIG["timeout_connect"],
            read=AI_CONFIG["timeout_read"],
            write=AI_CONFIG["timeout_write"],
            pool=AI_CONFIG["timeout_pool"],
        )
        variants = [
            self._normalize_messages(messages, content_mode="text"),
            self._merge_messages_to_single_user(messages),
        ]

        for index, variant in enumerate(variants, start=1):
            payload = self._build_raw_payload(variant, **kwargs)
            try:
                print(f"[AI Client] Retrying with raw HTTP payload (variant {index})")
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    return response.json()
            except Exception as raw_exc:
                print(f"[AI Client] Raw HTTP retry failed (variant {index}): {raw_exc}")

        return None

    def _get_chat_completions_url(self) -> str:
        base_url = (self.api_base or "https://api.openai.com/v1").rstrip("/") + "/"
        return urljoin(base_url, "chat/completions")

    def _build_raw_payload(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if kwargs.get("temperature") is not None:
            payload["temperature"] = kwargs["temperature"]
        if kwargs.get("max_tokens") is not None:
            payload["max_tokens"] = kwargs["max_tokens"]
        return payload

    def _merge_messages_to_single_user(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        normalized = self._normalize_messages(messages, content_mode="text")
        parts: List[str] = []
        for message in normalized:
            role = message.get("role", "user")
            content = message.get("content", "")
            if not content:
                continue
            if role == "system":
                parts.append(f"[System Instruction]\n{content}")
            elif role == "assistant":
                parts.append(f"[Assistant Context]\n{content}")
            else:
                parts.append(str(content))
        return [{"role": "user", "content": "\n\n".join(parts)}]

    def _normalize_messages(self, messages: List[Dict[str, Any]], content_mode: str = "text") -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for message in messages:
            normalized_message = dict(message)
            content = normalized_message.get("content", "")

            if content_mode == "blocks":
                if isinstance(content, str):
                    normalized_message["content"] = [{"type": "text", "text": content}]
                elif isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(item)
                        elif isinstance(item, str):
                            parts.append({"type": "text", "text": item})
                    normalized_message["content"] = parts
            else:
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    normalized_message["content"] = "\n".join(part for part in text_parts if part)
                elif content is None:
                    normalized_message["content"] = ""

            normalized.append(normalized_message)
        return normalized

    def _extract_response_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        if hasattr(response, "choices"):
            choice = response.choices[0]
            message = getattr(choice, "message", None)
            if message is not None:
                content = getattr(message, "content", "")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if hasattr(item, "text"):
                            parts.append(item.text)
                        elif isinstance(item, dict) and item.get("type") == "text":
                            parts.append(item.get("text", ""))
                    return "".join(parts)
        if isinstance(response, dict) and "choices" in response:
            return response["choices"][0]["message"]["content"]
        print(f"[AI Client] Unknown response format: {type(response)}")
        return ""

    def _parse_json_response(self, raw: str) -> Optional[dict]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        import re

        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if fenced:
            try:
                return json.loads(fenced.group(1))
            except json.JSONDecodeError:
                pass

        inline = re.search(r"\{.*\}", raw, re.DOTALL)
        if inline:
            try:
                return json.loads(inline.group(0))
            except json.JSONDecodeError:
                pass

        return None
