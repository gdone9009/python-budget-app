import sys
import time
from functools import wraps
from typing import Callable, Any

class BudgetError(Exception):
    def __init__(self, message: str, hint: str):
        super().__init__(message)
        self.hint = hint

def handle_exceptions(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except BudgetError as e:
            print(f"\n[오류] {e}")
            print(f"[힌트] {e.hint}")
            sys.exit(1)
        except Exception as e:
            print(f"\n[오류] 알 수 없는 시스템 오류가 발생했습니다: {e}")
            sys.exit(1)
    return wrapper