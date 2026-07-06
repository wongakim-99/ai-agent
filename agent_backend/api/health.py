"""헬스체크 라우터: 서버가 살아있는지 확인용."""
from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}
