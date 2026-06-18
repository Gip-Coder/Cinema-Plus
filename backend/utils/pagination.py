from typing import Generic, TypeVar, List
from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

def paginate(query: Query, page: int, size: int) -> Page:
    total = query.count()
    pages = (total + size - 1) // size if size > 0 else 0
    items = query.offset((page - 1) * size).limit(size).all()
    return Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )
