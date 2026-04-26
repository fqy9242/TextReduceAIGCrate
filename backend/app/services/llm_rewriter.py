from __future__ import annotations

import difflib
import random

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import Settings
from app.schemas.system_settings import RuntimeSettingsOut
from app.services.prompt_manager import PromptSpec


class LLMRewriter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._chat_model = None
        self._chat_model_key: tuple[str, str, int, int] | None = None


    async def rewrite(
        self,
        rewrite_prompt: PromptSpec,
        runtime_settings: RuntimeSettingsOut,
        style_instruction: str,
        original_text: str,
        previous_text: str,
        round_index: int,
    ) -> str:
        chat_model = self._get_chat_model(runtime_settings)
        candidate = await self._call_model(
            chat_model=chat_model,
            rewrite_prompt=rewrite_prompt,
            style_instruction=style_instruction,
            original_text=original_text,
            previous_text=previous_text,
            round_index=round_index,
        )

        # If the rewrite is too close to the source, force a second stronger pass.
        source_text = previous_text if round_index > 1 else original_text
        if self._is_too_similar(source_text, candidate):
            stronger_instruction = (
                f"{style_instruction}\n"
                "强制要求：必须明显改写句式和段落节奏；"
                "禁止只替换少量词或只追加结尾句；"
                "在不改变事实的前提下，改写后与输入在表达层面应有显著差异。"
            )
            second_pass = await self._call_model(
                chat_model=chat_model,
                rewrite_prompt=rewrite_prompt,
                style_instruction=stronger_instruction,
                original_text=original_text,
                previous_text=previous_text,
                round_index=round_index,
            )
            if second_pass.strip():
                candidate = second_pass

        content = candidate.strip()
        return content if content else previous_text

    async def _call_model(
        self,
        chat_model: ChatOpenAI,
        rewrite_prompt: PromptSpec,
        style_instruction: str,
        original_text: str,
        previous_text: str,
        round_index: int,
    ) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", rewrite_prompt.system),
                ("human", rewrite_prompt.human),
            ]
        )
        chain = prompt | chat_model
        result = await chain.ainvoke(
            {
                "original_text": original_text,
                "previous_text": previous_text,
                "round_index": round_index,
                "style_instruction": style_instruction,
            }
        )
        return str(result.content)

    def _get_chat_model(self, runtime_settings: RuntimeSettingsOut) -> ChatOpenAI:
        config_key = (
            runtime_settings.openai_model,
            runtime_settings.openai_base_url,
            runtime_settings.openai_timeout_seconds,
            max(0, runtime_settings.openai_max_retries),
        )
        if self._chat_model is not None and self._chat_model_key == config_key:
            return self._chat_model

        self._chat_model = ChatOpenAI(
            model=runtime_settings.openai_model,
            api_key=self.settings.openai_api_key,
            base_url=runtime_settings.openai_base_url,
            temperature=0.85,
            timeout=runtime_settings.openai_timeout_seconds,
            max_retries=max(0, runtime_settings.openai_max_retries),
        )
        self._chat_model_key = config_key
        return self._chat_model

    @staticmethod
    def _is_too_similar(source: str, candidate: str) -> bool:
        clean_source = source.strip()
        clean_candidate = candidate.strip()
        if not clean_candidate:
            return True
        similarity = difflib.SequenceMatcher(None, clean_source, clean_candidate).ratio()
        return similarity > 0.92


