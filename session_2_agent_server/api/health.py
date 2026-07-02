"""시스템 상태 확인용 라우터. (LLM 키 없이도 동작)"""
from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    """서버가 살아있는지 확인."""
    return {"status": "ok"}
