from typing import Any, Dict

def standard_response(data: Any = None, message: str = "Operation successful", success: bool = True) -> Dict[str, Any]:
    return {
        "success": success,
        "message": message,
        "data": data
    }
