"""
챕터 4 — 로컬 우선 Multi-Agent System(MAS) 기능 모듈.

  service.py    : 그래프(라우팅+병렬+합류) 빌더 + 토폴로지 4-1 등록
  repository.py : 로컬 데이터 접근 (disease.db / disease_info.csv / 내부 RAG 문서)

자체 REST 컨트롤러는 없다. 제네릭 그래프 뷰어 엔진이 토폴로지/실행 SSE로 서빙한다.
"""
