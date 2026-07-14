"""
date_planner — 데이트 코스 AI Agent (미니 프로젝트).

학습용 챕터(chapters/ch2~4)와 달리, 이건 실제 사용자용 미니 제품이다.
한 패키지 안에 그래프·API·데이터·스키마를 자기완결적으로 모아 둔다.

  graph.py     : LangGraph MAS (planner → 병렬 검색 → curator) + 토폴로지 5-1 등록
  router.py    : REST 라우터 (/api/date/config, /api/date/plan)
  places.py    : 큐레이션 장소 데이터셋 + 통합 검색 (라이브 실패 시 폴백)
  providers.py : 외부 라이브 검색 provider (Kakao Local)
  schemas.py   : 이 프로젝트 전용 pydantic 모델

프론트엔드는 agent_frontend/src/date/ (별도 페이지 date.html).
"""
