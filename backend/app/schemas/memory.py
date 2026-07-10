from datetime import datetime

from pydantic import BaseModel


class MemoryResponse(BaseModel):
    id: str
    memory_type: str
    content: str
    importance_score: float
    access_count: int
    created_at: datetime

    class Config:
        from_attributes = True
