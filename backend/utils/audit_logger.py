from sqlalchemy.orm import Session
from backend.models.models import AuditLog
import json
from datetime import datetime, timezone
from typing import Any

def log_action(
    db: Session,
    user_id: int,
    entity_type: str, # 'theatre', 'screen', 'pricing', 'media', 'rule'
    entity_id: int,
    action: str, # 'create', 'update', 'delete', 'toggle'
    old_value: Any = None,
    new_value: Any = None,
    ip_address: str = None
):
    """
    Creates an audit log entry for changes made by admins.
    Safely serializes dictionaries or objects to string formats.
    """
    def serialize(val):
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            try:
                return json.dumps(val)
            except Exception:
                return str(val)
        return str(val)

    old_str = serialize(old_value)
    new_str = serialize(new_value)

    log_entry = AuditLog(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=old_str,
        new_value=new_str,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc)
    )
    
    db.add(log_entry)
    db.commit()
