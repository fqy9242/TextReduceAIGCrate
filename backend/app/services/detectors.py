from __future__ import annotations

from dataclasses import dataclass

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import Settings
from app.schemas.system_settings import RuntimeSettingsOut
from app.services.prompt_manager import PromptManager


@dataclass
class DetectorResult:
    score: float
    label: str
    raw: dict


def normalize_label(label: str) -> str:
    normalized = label.strip().lower()
    if normalized in {"ai_like", "ai", "machine", "high_ai"}:
        return "ai_like"
    if normalized in {"human_like", "human", "low_ai"}:
        return "human_like"
    return "uncertain"


class BaseDetector:
    async def detect(self, text: str, runtime_settings: RuntimeSettingsOut | None = None) -> DetectorResult:
        raise NotImplementedError


class LLMDetector(BaseDetector):
    def __init__(self, settings: Settings, prompt_manager: PromptManager):
        self.settings = settings
        self.prompt_manager = prompt_manager

    async def detect(self, text: str, runtime_settings: RuntimeSettingsOut | None = None) -> DetectorResult:
        model = self.settings.openai_model
        api_key = self.settings.openai_api_key
        base_url = self.settings.openai_base_url

        try:
            prompt_spec = self.prompt_manager.get_prompt("detector", "default")
            system_prompt = prompt_spec.system
        except KeyError:
            system_prompt = "你是一个专业的AI文本痕迹检测器。请评估给定文本由AI生成的概率(0-100)。\n请仔细分析文本的结构、重复性、生硬的转折、过于规律的句式等AI常见痕迹。\n返回JSON格式数据，必须包含两个字段：\n1. 'score' (0-100的浮点数，数值越高代表越像AI生成)\n2. 'label' (字符串，可选值为 'ai_like', 'human_like', 'uncertain'。score>45为ai_like，score<25为human_like，其余为uncertain)\n3. 'reason' (字符串，简要说明判断理由)"

        if runtime_settings:
            model = runtime_settings.detector_model or model
            base_url = runtime_settings.openai_base_url or base_url

        chat_model = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,
            timeout=self.settings.openai_timeout_seconds,
            max_retries=max(0, self.settings.openai_max_retries),
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}")
        ])
        chain = prompt | chat_model
        try:
            result = await chain.ainvoke({"text": text})
            payload = json.loads(str(result.content))
            score = float(payload.get("score", 100.0))
            label = normalize_label(str(payload.get("label", "uncertain")))
            return DetectorResult(score=score, label=label, raw=payload)
        except Exception as e:
            return DetectorResult(
                score=100.0,
                label="ai_like",
                raw={"error": str(e), "provider": "llm"}
            )


def build_detector(settings: Settings, prompt_manager: PromptManager, runtime_settings: RuntimeSettingsOut | None = None) -> BaseDetector:
    return LLMDetector(settings, prompt_manager)

