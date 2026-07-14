"""
챕터 3 — LangGraph 3패턴(직렬/조건분기/병렬) 기능 모듈.

  service.py : 그래프 빌더 + 토폴로지 3-1~3-3 등록

자체 REST 컨트롤러는 없다. 제네릭 그래프 뷰어 엔진(api/graphs.py + common/registry·
topology·streaming)이 토폴로지/실행 SSE로 대신 서빙한다.
"""
