from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_session
from src.api.models.bookdb import Book
import shutil
import uuid
import os

router = APIRouter(prefix="/books", tags=["Books"])

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/{book_id}/upload-pdf")
async def upload_pdf(
        book_id: uuid.UUID,
        pdf: UploadFile = File(...),
        session: AsyncSession = Depends(get_async_session)
):
    if not pdf.filename.endswith(".pdf"):
        raise HTTPException(400, "Файл має бути PDF")

    file_name = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    book = await session.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Книга не знайдена")

    book.pdf_path = file_path
    await session.commit()

    return {"status": "ok", "pdf_path": file_path}


