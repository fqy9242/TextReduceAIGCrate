from __future__ import annotations

import difflib
import random

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import Settings
from app.services.prompt_manager import PromptSpec


class LLMRewriter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._chat_model = None
        if not settings.use_mock_llm_flag:
            self._chat_model = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                temperature=0.85,
            )

    @property
    def llm_mode(self) -> str:
        return "mock" if self._chat_model is None else "real"

    async def rewrite(
        self,
        rewrite_prompt: PromptSpec,
        style_instruction: str,
        original_text: str,
        previous_text: str,
        round_index: int,
    ) -> str:
        if self._chat_model is None:
            return self._mock_rewrite(original_text, previous_text, round_index)

        candidate = await self._call_model(
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
        chain = prompt | self._chat_model
        result = await chain.ainvoke(
            {
                "original_text": original_text,
                "previous_text": previous_text,
                "round_index": round_index,
                "style_instruction": style_instruction,
            }
        )
        return str(result.content)

    @staticmethod
    def _is_too_similar(source: str, candidate: str) -> bool:
        clean_source = source.strip()
        clean_candidate = candidate.strip()
        if not clean_candidate:
            return True
        similarity = difflib.SequenceMatcher(None, clean_source, clean_candidate).ratio()
        return similarity > 0.92

    def _mock_rewrite(self, original_text: str, previous_text: str, round_index: int) -> str:
        source = previous_text if round_index > 1 else original_text
        replacements = [
            ("首先", "先说"),
            ("因此", "所以"),
            ("此外", "另外"),
            ("总之", "整体来看"),
            ("非常", "相当"),
            ("可以看出", "能够看到"),
        ]
        rewritten = source
        random.shuffle(replacements)
        for old, new in replacements[:3]:
            rewritten = rewritten.replace(old, new)

        # Make fallback rewrite visibly different instead of just appending one sentence.
        rewritten = rewritten.replace("，", "，并且")
        rewritten = rewritten.replace("。", "。同时，")
        rewritten = rewritten.replace("此外", "另外")
        rewritten = rewritten.replace("有效改善", "明显改善")
        rewritten = rewritten.replace("提升了", "进一步提升了")
        return rewritten.rstrip("，并且").rstrip("同时，")
