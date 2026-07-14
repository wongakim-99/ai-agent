"""
챕터 4 데이터 접근 계층 (repository) — 로컬 disease.db(SQLite) + disease_info.csv + 내부 RAG 문서.

서버 기동 시 샘플 데이터를 자동 생성(idempotent)하고, 그래프 노드(service.py)가 호출할
조회 함수를 제공한다. 실행 디렉터리에 의존하지 않도록 __file__ 로 repo 루트를 앵커한다.
"""
from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

# api/chapter4/repository.py → parents[0]=chapter4, [1]=api, [2]=agent_backend, [3]=repo 루트
REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = REPO_ROOT / "disease.db"
CSV_PATH = REPO_ROOT / "disease_info.csv"

# 아는 병명(라우터가 로컬 데이터 유무를 판단하는 기준) — DB/CSV 에 실제 존재하는 키
KNOWN_DISEASES = ["고혈압", "당뇨", "비만"]

# 내부 RAG 문서 (in-memory 코퍼스)
INTERNAL_DOCS = [
    {
        "title": "고혈압 생활관리 사내 교육자료",
        "content": "혈압이 높은 사람은 저염식, 채소와 생선 위주의 식단, 칼륨이 풍부한 식품을 고려한다. 빠르게 걷기와 수영처럼 지속 가능한 유산소 운동이 좋다.",
    },
    {
        "title": "당뇨 생활관리 사내 교육자료",
        "content": "당뇨 관리는 정제 탄수화물 제한, 통곡물과 잎채소, 식후 가벼운 걷기, 근력운동이 핵심이다.",
    },
    {
        "title": "비만 생활관리 사내 교육자료",
        "content": "비만 관리는 고단백 저칼로리 식단, 가공식품 줄이기, 유산소와 근력 운동 병행이 중요하다.",
    },
]


def ensure_demo_data() -> None:
    """Git에는 DB/CSV를 올리지 않고, 실행 시 로컬 샘플 데이터를 자동 생성한다(idempotent)."""
    if not DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "CREATE TABLE disease (name TEXT PRIMARY KEY, diet TEXT, exercise TEXT)"
            )
            conn.executemany(
                "INSERT INTO disease VALUES (?, ?, ?)",
                [
                    ("고혈압", "저염식, 채소·생선 위주, 칼륨 풍부한 바나나·시금치", "빠르게 걷기 하루 30분, 수영"),
                    ("당뇨", "정제 탄수화물 제한, 통곡물·잎채소, 저혈당지수 음식", "식후 가벼운 걷기, 근력운동 주 3회"),
                    ("비만", "고단백 저칼로리, 채소·닭가슴살, 가공식품 줄이기", "유산소+근력 병행, 주 5회 이상"),
                ],
            )

    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "symptom", "caution"])
            writer.writeheader()
            writer.writerows([
                {"name": "고혈압", "symptom": "두통, 뒷목 뻣뻣함, 어지럼증", "caution": "나트륨 과다 섭취 주의, 정기 혈압 측정"},
                {"name": "당뇨", "symptom": "잦은 갈증, 빈뇨, 피로, 체중감소", "caution": "혈당 급변 주의, 공복 운동 자제"},
                {"name": "비만", "symptom": "피로, 관절 부담, 호흡 곤란", "caution": "급격한 단식 금지, 무리한 운동 주의"},
            ])


ensure_demo_data()  # 모듈 import(서버 기동) 시 1회 — 파일 있으면 no-op


def fetch_disease_db(disease: str) -> tuple[str, str] | None:
    """disease.db 에서 (diet, exercise) 행을 조회한다. 없으면 None."""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT diet, exercise FROM disease WHERE name = ?", (disease,)
        ).fetchone()


def fetch_disease_csv(disease: str) -> dict | None:
    """disease_info.csv 에서 해당 병명 행(dict)을 조회한다. 없으면 None."""
    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return next((r for r in rows if r["name"] == disease), None)


def retrieve_internal_docs(query: str, k: int = 2) -> list[dict]:
    """작은 데모용 RAG 검색기: 토큰 겹침 점수 + 약한 도메인 힌트."""
    tokens = set(re.findall(r"[가-힣A-Za-z0-9]+", query))
    scored = []
    for doc in INTERNAL_DOCS:
        doc_text = doc["title"] + " " + doc["content"]
        doc_tokens = set(re.findall(r"[가-힣A-Za-z0-9]+", doc_text))
        score = len(tokens & doc_tokens)
        if "혈압" in query and "고혈압" in doc["title"]:
            score += 3
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored[:k] if score > 0]
