"""
Gemini AI client helpers for AI skills.
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import AI_CONFIG


class AIClientMixin:
    """Provide Gemini client setup, retry logic and response parsing."""

    def _init_ai_client(self, api_key: str = "", api_base: str = "", model: str = ""):
        # Gemini 配置
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "") or AI_CONFIG.get("gemini_api_key", "")
        self.gemini_model = os.environ.get("GEMINI_MODEL", "") or AI_CONFIG.get("gemini_model", "gemini-2.0-flash")
        
        self._gemini_model = None
        self._build_client()

    def _build_client(self):
        # 读取代理配置
        proxy_url = os.environ.get("PROXY_URL", "") or os.environ.get("HTTP_PROXY", "")
        if proxy_url:
            os.environ.setdefault("HTTP_PROXY", proxy_url)
            os.environ.setdefault("HTTPS_PROXY", proxy_url)
            print(f"[AI Client] 代理配置: {proxy_url}")

        masked_api_key = ""
        if self.gemini_api_key:
            if len(self.gemini_api_key) > 12:
                masked_api_key = f"{self.gemini_api_key[:8]}...{self.gemini_api_key[-4:]}"
            else:
                masked_api_key = self.gemini_api_key
            print(f"[AI Client] API Key: {masked_api_key}")

        # 初始化 Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self._gemini_model = genai.GenerativeModel(self.gemini_model)
                print(f"[AI Client] ✅ Gemini 客户端已初始化: {self.gemini_model}")
            except Exception as e:
                print(f"[AI Client] ⚠️ Gemini 初始化失败: {e}")
                self._gemini_model = None
        else:
            if not GEMINI_AVAILABLE:
                print("[AI Client] ⚠️ google-generativeai 未安装")
            if not self.gemini_api_key:
                print("[AI Client] ⚠️ GEMINI_API_KEY 未配置")

    def is_available(self) -> bool:
        """检查 Gemini 是否可用"""
        return GEMINI_AVAILABLE and bool(self.gemini_api_key) and self._gemini_model is not None

    def update_config(self, api_key: str, api_base: str = "", model: str = ""):
        """更新配置（保持接口兼容）"""
        # api_key 参数用于 Gemini API Key
        if api_key:
            self.gemini_api_key = api_key
        if model:
            self.gemini_model = model
        self._build_client()

    def _call_api_with_retry(
        self,
        messages: List[Dict[str, Any]],
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> Optional[Any]:
        """调用 Gemini API 带重试"""
        return self._call_gemini_with_retry(messages, max_retries, **kwargs)

    def _call_gemini_with_retry(
        self,
        messages: List[Dict[str, Any]],
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> Optional[Any]:
        """调用 Gemini API 带重试"""
        if not self._gemini_model:
            return None

        retries = max_retries or AI_CONFIG["max_retries"]
        last_error = None

        # 转换 messages 为 Gemini 格式
        prompt = self._messages_to_gemini_prompt(messages)
        max_tokens = kwargs.get('max_tokens', AI_CONFIG['max_tokens'])
        timestamp = datetime.now().strftime("%H:%M:%S")
        start_time = time.time()
        print(f"[AI Client] [{timestamp}] 开始 Gemini API 调用 | 模型: {self.gemini_model} | Prompt长度: {len(prompt)}字符 | max_tokens: {max_tokens}")

        # 获取生成配置
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', AI_CONFIG['temperature']),
                max_output_tokens=max_tokens,
                thinking_config=genai.types.ThinkingConfig(
                    thinking_budget=1024  # 限制思考token为1024，避免占用太多输出配额
                ),
            )
        except (AttributeError, TypeError):
            # 旧版 SDK 不支持 thinking_config
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', AI_CONFIG['temperature']),
                max_output_tokens=max_tokens,
            )

        for attempt in range(retries):
            try:
                if attempt > 0:
                    wait_time = self._get_retry_wait_seconds(attempt, last_error)
                    retry_timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[AI Client] [{retry_timestamp}] Gemini Retry {attempt + 1}/{retries} in {wait_time}s")
                    time.sleep(wait_time)

                response = self._gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )

                if response.text:
                    elapsed = time.time() - start_time
                    response_text = response.text if hasattr(response, 'text') else ''
                    success_timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[AI Client] [{success_timestamp}] 响应成功 | 耗时: {elapsed:.1f}s | 响应长度: {len(response_text)}字符")
                    return response
                else:
                    print(f"[AI Client] Gemini returned empty response")
                    return None

            except Exception as exc:
                last_error = exc
                error_timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[AI Client] [{error_timestamp}] Gemini Attempt {attempt + 1} failed: {exc}")

                if not self._is_retryable_error(exc) or attempt >= retries - 1:
                    break

        failed_timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[AI Client] [{failed_timestamp}] Gemini API call failed: {last_error}")
        return None

    def _messages_to_gemini_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """将 OpenAI 格式的 messages 转换为 Gemini 的 prompt"""
        parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if isinstance(content, list):
                # 处理 content blocks
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        text_parts.append(item)
                content = "\n".join(text_parts)
            
            if not content:
                continue
                
            if role == "system":
                parts.append(f"[System Instruction]\n{content}")
            elif role == "assistant":
                parts.append(f"[Assistant Context]\n{content}")
            else:
                parts.append(str(content))
        
        return "\n\n".join(parts)

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

    # finish_reason 映射表（数字 -> 可读名称）
    FINISH_REASON_MAP = {0: "UNSPECIFIED", 1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY", 4: "RECITATION", 5: "OTHER"}

    def _extract_response_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        
        # 处理 Gemini 响应
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, 'finish_reason', 'unknown')
            # 将数字映射为可读名称
            finish_reason_name = self.FINISH_REASON_MAP.get(finish_reason, f"UNKNOWN({finish_reason})")
            print(f"[AI Client] 响应详情 | candidates: {len(response.candidates)} | finish_reason: {finish_reason_name}")
            # 如果是 MAX_TOKENS，打印警告
            if finish_reason == 2:
                print(f"[AI Client] ⚠️ 警告: 输出被截断 (MAX_TOKENS)，建议增大 max_tokens 配置")

        if hasattr(response, 'text'):
            return response.text
        
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
