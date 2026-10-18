"""HTTP Target for REST and OpenAI/vLLM/Ollama compatible endpoints."""

import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional
from evalguard.targets.base import BaseTarget
from evalguard.models import TestCase, TargetResponse


class HttpTarget(BaseTarget):
    """Executes test cases against remote HTTP/REST LLM endpoints with zero external dependencies."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.url = self.config.get("url", "http://localhost:8000/v1/chat/completions")
        self.headers = self.config.get("headers", {"Content-Type": "application/json"})
        self.model = self.config.get("model", "default")
        self.temperature = float(self.config.get("temperature", 0.0))
        self.timeout = float(self.config.get("timeout_seconds", 30.0))
        self.payload_format = self.config.get("format", "openai")  # 'openai' or 'custom'
        self.cost_per_1k_tokens = float(self.config.get("cost_per_1k_tokens", 0.002))

    def invoke(self, test_case: TestCase) -> TargetResponse:
        start_time = time.perf_counter()

        # Build payload
        if self.payload_format == "openai":
            messages = []
            if test_case.system_prompt:
                messages.append({"role": "system", "content": test_case.system_prompt})
            
            user_content = test_case.prompt
            if test_case.context:
                context_str = "\n".join(f"Document: {doc}" for doc in test_case.context)
                user_content = f"Context:\n{context_str}\n\nQuestion: {user_content}"

            messages.append({"role": "user", "content": user_content})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
            }
        else:
            payload = {
                "prompt": test_case.prompt,
                "context": test_case.context or [],
                "variables": test_case.variables,
            }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data_bytes, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                body = json.loads(resp.read().decode("utf-8"))

                if self.payload_format == "openai":
                    choices = body.get("choices", [])
                    content = choices[0]["message"]["content"] if choices else ""
                    usage = body.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", len(test_case.prompt.split()) * 4 // 3)
                    comp_tokens = usage.get("completion_tokens", len(content.split()) * 4 // 3)
                    total_tokens = usage.get("total_tokens", prompt_tokens + comp_tokens)
                else:
                    content = body.get("response") or body.get("content") or body.get("output", "")
                    prompt_tokens = len(test_case.prompt.split()) * 4 // 3
                    comp_tokens = len(content.split()) * 4 // 3
                    total_tokens = prompt_tokens + comp_tokens

                cost = (total_tokens / 1000.0) * self.cost_per_1k_tokens

                return TargetResponse(
                    content=content,
                    latency_ms=round(elapsed_ms, 2),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=comp_tokens,
                    total_tokens=total_tokens,
                    cost_usd=round(cost, 6),
                    raw_metadata=body
                )

        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_body = e.read().decode("utf-8", errors="replace")
            return TargetResponse(
                content="",
                latency_ms=round(elapsed_ms, 2),
                error=f"HTTP {e.code}: {e.reason} - {error_body}"
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TargetResponse(
                content="",
                latency_ms=round(elapsed_ms, 2),
                error=f"Network error calling {self.url}: {str(e)}"
            )
