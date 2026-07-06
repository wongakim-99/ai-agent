"""
공유 LLM 객체. 챕터 2 LCEL 체인들이 이걸 가져다 쓴다.
session_2 의 get_llm() 과 같은 역할이지만, 교차 패키지 import 를 피하려고
session_3 안에 다시 정의한다. (계획서 §레지스트리 참고)
"""
from functools import lru_cache

from langchain_openai import ChatOpenAI


@lru_cache
def get_llm() -> ChatOpenAI:
    """LLM 객체는 한 번만 만들어 재사용한다. (노트북 2-1과 동일: gpt-4o-mini, temperature=0)"""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)
