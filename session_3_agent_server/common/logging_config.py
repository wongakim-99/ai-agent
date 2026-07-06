"""
앱 전역 로깅 설정. main.py 에서 앱을 만들기 전에 setup_logging() 을 한 번 호출한다.
다른 모듈에서는 get_logger(__name__) 로 로거를 받아 쓴다. (session_2 와 동일)
"""
import logging
import sys

# 예: 14:23:05 | INFO    | app.api.graphs | POST /graphs/3-2/run
_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """루트 로거와 uvicorn 로거 포맷을 통일한다. (중복 호출해도 안전)"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True

    access = logging.getLogger("uvicorn.access")
    access.handlers.clear()
    access.disabled = True


def get_logger(name: str) -> logging.Logger:
    """모듈용 로거를 반환한다. name 은 보통 __name__ 을 넘긴다."""
    return logging.getLogger(name)
