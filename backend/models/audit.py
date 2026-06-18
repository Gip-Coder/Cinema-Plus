from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from backend.database import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    entity_type = Column(String(50), index=True)
    entity_id = Column(Integer, index=True)
    action = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)
