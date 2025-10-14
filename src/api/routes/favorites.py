from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Dict, Set, Optional
from uuid import UUID
from threading import RLock

router = APIRouter()



try:
    
    from src.core.database import BOOKS, DB_LOCK  
except Exception:
    BOOKS: Dict[UUID, Dict] = {}
    DB_LOCK = RLock()


FAVORITES: Dict[str, Set[UUID]] = {}
FAVORITES_LOCK = RLock()



class FavoriteItem(BaseModel):
    book_id: UUID


class FavoriteCreate(BaseModel):
    book_id: UUID


class FavoriteList(BaseModel):
    user: str
    count: int
    items: List[FavoriteItem]


class BookOut(BaseModel):
    id: UUID
    isbn: str
    title: str
    author: str
    total_copies: int
    reserved_count: int = 0
    genres: List[str] = []


class FavoriteListExpanded(BaseModel):
    user: str
    count: int
    items: List[BookOut]



def get_current_user_email(x_user_email: str = Header(..., alias="X-User-Email")) -> str:
    email = x_user_email.strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email")
    return email


@router.get(
    "/me",
    response_model=FavoriteList,  
)
def get_my_favorites(
    expand: bool = Query(False, description="Повернути розгорнуті дані книги"),
    user_email: str = Depends(get_current_user_email),
):
    with FAVORITES_LOCK:
        ids = list(FAVORITES.get(user_email, set()))

    if not expand:
        return FavoriteList(
            user=user_email,
            count=len(ids),
            items=[FavoriteItem(book_id=b_id) for b_id in ids],
        )

    
    books: List[BookOut] = []
    with DB_LOCK:
        for b_id in ids:
            data = BOOKS.get(b_id)
            if data:
                # мапуємо словник книги у модель BookOut, ігноруючи зайві поля
                books.append(
                    BookOut(
                        id=data["id"],
                        isbn=str(data.get("isbn", "")),
                        title=str(data.get("title", "")),
                        author=str(data.get("author", "")),
                        total_copies=int(data.get("total_copies", 0)),
                        reserved_count=int(data.get("reserved_count", 0)),
                        genres=list(data.get("genres", []) or []),
                    )
                )
            else:
                # якщо книги вже немає в каталозі то просто пропускаємо
                continue

    
    return FavoriteListExpanded(user=user_email, count=len(books), items=books)



@router.post(
    "/me",
    status_code=status.HTTP_201_CREATED,
    response_model=FavoriteItem,
)
def add_to_favorites(
    payload: FavoriteCreate,
    user_email: str = Depends(get_current_user_email),
):
    # Перевірка існування книги (якщо доступний BOOKS)
    with DB_LOCK:
        if BOOKS and payload.book_id not in BOOKS:
            raise HTTPException(status_code=404, detail="Book not found")

    with FAVORITES_LOCK:
        favs = FAVORITES.setdefault(user_email, set())
        favs.add(payload.book_id)

    return FavoriteItem(book_id=payload.book_id)



# DELETE /favorites/me/{book_id} — видалити книгу зі списку бажань
@router.delete(
    "/me/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_from_favorites(
    book_id: UUID,
    user_email: str = Depends(get_current_user_email),
):
    with FAVORITES_LOCK:
        favs = FAVORITES.get(user_email)
        if not favs or book_id not in favs:
            # видалення ідемпотентне — повертаємо 204 навіть якщо не було
            return
        favs.remove(book_id)



# DELETE /favorites/me — очистити увесь список бажань
@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def clear_favorites(user_email: str = Depends(get_current_user_email)):
    with FAVORITES_LOCK:
        if user_email in FAVORITES:
            FAVORITES[user_email].clear()



# GET /favorites/me/count — коротка метрика розміру списку
class FavoriteCount(BaseModel):
    user: str
    count: int


@router.get("/me/count", response_model=FavoriteCount)
def favorites_count(user_email: str = Depends(get_current_user_email)):
    with FAVORITES_LOCK:
        cnt = len(FAVORITES.get(user_email, set()))
    return FavoriteCount(user=user_email, count=cnt)
