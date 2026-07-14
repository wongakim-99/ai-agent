"""
date_planner — 데이트 코스 AI Agent (미니 프로젝트).

학습용 챕터(chapter2~4)와 달리, 이건 실제 사용자용 미니 제품이다.
한 기능 모듈 안에 controller/service/dto/repository 계층을 자기완결적으로 모아 둔다.

  controller.py : REST 라우터 (/api/date/config, /api/date/plan)
  service.py    : LangGraph MAS (planner → 병렬 검색 → curator) + 토폴로지 5-1 등록
  repository.py : 장소 데이터 접근 (큐레이션 데이터셋 + Kakao 라이브 provider)
  dto.py        : 이 기능 모듈 전용 pydantic 모델

프론트엔드는 agent_frontend/src/date/ (별도 페이지 date.html).
"""
