"""
챕터 2 — LCEL 조각들 (invoke / prompt|llm|parser / chat / json / parallel).
노트북 2-1 ~ 2-5 를 그대로 옮겨 러너블 빌더로 만들고 레지스트리에 등록한다.

LCEL 러너블도 .get_graph() 로 토폴로지가 나오지만 노드 id가 매 빌드마다 UUID라
불안정하다. 그래서 여기서는 '모양(lcel_shape)'만 선언하고, 안정적인 토폴로지/실행
매핑은 common/topology.py, common/streaming.py 가 그 모양을 보고 생성한다.
"""
from __future__ import annotations

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableParallel

from agent_backend.common.llm import get_llm
from agent_backend.common.registry import GraphSpec, register


# --- 2-1. LLM 직접 호출 (단일 노드) ---
def build_invoke():
    return get_llm()


# --- 2-2. LCEL 기본형: Prompt | LLM | StrOutputParser ---
def build_explain():
    prompt = PromptTemplate.from_template(
        "{topic}를 처음 배우는 사람에게 한국어로 3문장 이내로 설명해줘."
    )
    return prompt | get_llm() | StrOutputParser()


# --- 2-3. ChatPromptTemplate: system/human 역할 분리 ---
def build_chat():
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "너는 사내 교육을 돕는 AI Agent 강사다. 짧고 명확하게 설명한다."),
        ("human", "{question}"),
    ])
    return chat_prompt | get_llm() | StrOutputParser()


# --- 2-4. JsonOutputParser: 출력을 dict로 구조화 ---
def build_sentiment():
    parser = JsonOutputParser()
    prompt = PromptTemplate.from_template(
        "다음 문장을 감정 분석해줘. 반드시 JSON으로만 답해.\n"
        "sentiment(긍정/부정/중립)와 reason 키를 포함해.\n"
        "문장: {review}\n출력 형식 안내: {format_instructions}"
    ).partial(format_instructions=parser.get_format_instructions())
    return prompt | get_llm() | parser


# --- 2-5. RunnableParallel: 한 입력을 여러 관점으로 동시에 ---
def build_analyze():
    summary_chain = PromptTemplate.from_template(
        "다음 내용을 한 문장으로 요약해줘: {text}"
    ) | get_llm() | StrOutputParser()
    keyword_chain = PromptTemplate.from_template(
        "다음 내용의 핵심 키워드 3개만 쉼표로 출력해줘: {text}"
    ) | get_llm() | StrOutputParser()
    return RunnableParallel({"summary": summary_chain, "keywords": keyword_chain})


# =========================================================
# 레지스트리 등록
# =========================================================
register(GraphSpec(
    id="2-1", chapter=2, kind="lcel", lcel_shape="single",
    title="2-1 LLM 직접 호출: invoke()",
    concept="가장 기본. LLM 노드 하나에 질문을 던지고 답을 받는다. (입력→출력, 단방향)",
    build=build_invoke,
    input_example={"question": "AI Agent를 한 문장으로 설명해줘"},
))

register(GraphSpec(
    id="2-2", chapter=2, kind="lcel", lcel_shape="linear", parser_kind="str",
    title="2-2 LCEL 기본형: Prompt | LLM | Parser",
    concept="| 파이프로 prompt → llm → parser 를 잇는다. LangGraph의 add_edge 직렬과 같은 감각.",
    build=build_explain,
    input_example={"topic": "LangGraph"},
))

register(GraphSpec(
    id="2-3", chapter=2, kind="lcel", lcel_shape="linear", parser_kind="str",
    title="2-3 ChatPromptTemplate: system/human 분리",
    concept="system 에 역할, human 에 질문. 같은 prompt→llm→parser 지만 프롬프트가 대화형이다.",
    build=build_chat,
    input_example={"question": "Tool과 Agent의 차이를 알려줘"},
))

register(GraphSpec(
    id="2-4", chapter=2, kind="lcel", lcel_shape="linear", parser_kind="json",
    title="2-4 JsonOutputParser: 출력을 dict로",
    concept="파서만 JsonOutputParser 로 바꾸면 결과가 문자열이 아니라 dict가 된다. (분기 판단에 유용)",
    build=build_sentiment,
    input_example={"review": "배송도 빠르고 품질도 좋아서 만족합니다."},
))

register(GraphSpec(
    id="2-5", chapter=2, kind="lcel", lcel_shape="parallel",
    branches=("summary", "keywords"),
    title="2-5 RunnableParallel: 여러 관점 동시에",
    concept="한 입력을 요약/키워드 체인에 동시에 흘린다. LangGraph 3-3 병렬 fan-out의 축소판.",
    build=build_analyze,
    input_example={"text": "LangGraph는 State를 중심으로 노드와 엣지를 연결해 에이전트 워크플로우를 구성한다."},
))
