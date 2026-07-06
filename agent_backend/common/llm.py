"""
공유 LLM 객체. 챕터별 체인/그래프가 전부 이걸 가져다 쓴다.
"""
from functools import lru_cache

from langchain_openai import ChatOpenAI


@lru_cache
def get_llm() -> ChatOpenAI:
    """LLM 객체는 한 번만 만들어 재사용한다. (노트북 2-1과 동일: gpt-4o-mini, temperature=0)"""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)
