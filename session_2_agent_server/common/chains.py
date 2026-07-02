"""
섹션 2에서 배운 LCEL 체인들을 그대로 옮겨온 파일.
노트북 셀 = 여기의 함수 하나. 서버(main.py)가 이 체인들을 가져다 쓴다.
"""
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableParallel


@lru_cache
def get_llm() -> ChatOpenAI:
    """LLM 객체는 한 번만 만들어 재사용한다. (노트북 2-1과 동일)"""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


# --- 2-2. LCEL 기본형: Prompt | LLM | Parser ---
@lru_cache
def explain_chain():
    prompt = PromptTemplate.from_template(
        "{topic}를 처음 배우는 사람에게 한국어로 3문장 이내로 설명해줘."
    )
    return prompt | get_llm() | StrOutputParser()


# --- 2-3. ChatPromptTemplate: system/human 역할 분리 ---
@lru_cache
def chat_chain():
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "너는 사내 교육을 돕는 AI Agent 강사다. 짧고 명확하게 설명한다."),
        ("human", "{question}"),
    ])
    return chat_prompt | get_llm() | StrOutputParser()


# --- 2-4. JsonOutputParser: 출력을 dict로 구조화 ---
@lru_cache
def sentiment_chain():
    parser = JsonOutputParser()
    prompt = PromptTemplate.from_template(
        "다음 문장을 감정 분석해줘. 반드시 JSON으로만 답해.\n"
        "sentiment(긍정/부정/중립)와 reason 키를 포함해.\n"
        "문장: {review}\n출력 형식 안내: {format_instructions}"
    )
    # format_instructions 를 미리 채워 넣어 부분 완성(partial)한다.
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    return prompt | get_llm() | parser


# --- 2-5. RunnableParallel: 한 입력을 여러 관점으로 동시에 ---
@lru_cache
def analyze_chain():
    summary_chain = PromptTemplate.from_template(
        "다음 내용을 한 문장으로 요약해줘: {text}"
    ) | get_llm() | StrOutputParser()

    keyword_chain = PromptTemplate.from_template(
        "다음 내용의 핵심 키워드 3개만 쉼표로 출력해줘: {text}"
    ) | get_llm() | StrOutputParser()

    return RunnableParallel({"summary": summary_chain, "keywords": keyword_chain})
