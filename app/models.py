from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Integer, DECIMAL, DateTime, ForeignKey, Table, Column, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


audiobook_author = Table(
    "audiobook_author",
    Base.metadata,
    Column("audiobook_id", Integer, ForeignKey("audiobooks.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
)

audiobook_genre = Table(
    "audiobook_genre",
    Base.metadata,
    Column("audiobook_id", Integer, ForeignKey("audiobooks.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

audiobook_textbook = Table(
    "audiobook_textbook",
    Base.metadata,
    Column("audiobook_id", Integer, ForeignKey("audiobooks.id", ondelete="CASCADE"), primary_key=True),
    Column("textbook_id", Integer, ForeignKey("text_books.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    audiobooks: Mapped[List["Audiobook"]] = relationship(
        "Audiobook",
        secondary=audiobook_author,
        back_populates="authors"
    )


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("genres.id", ondelete="SET NULL"), nullable=True)

    parent: Mapped["Genre"] = relationship("Genre", remote_side=[id], back_populates="children")
    children: Mapped[List["Genre"]] = relationship("Genre", back_populates="parent")

    audiobooks: Mapped[List["Audiobook"]] = relationship(
        "Audiobook",
        secondary=audiobook_genre,
        back_populates="genres"
    )


class Audiobook(Base):
    __tablename__ = "audiobooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    litres_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=True)

    formats: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fragment_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    authors: Mapped[List["Author"]] = relationship(
        "Author",
        secondary=audiobook_author,
        back_populates="audiobooks"
    )

    genres: Mapped[List["Genre"]] = relationship(
        "Genre",
        secondary=audiobook_genre,
        back_populates="audiobooks"
    )

    text_versions: Mapped[List["TextBook"]] = relationship(
        "TextBook",
        secondary=audiobook_textbook,
        back_populates="audiobooks",
        order_by="desc(TextBook.year), TextBook.price"
    )

    __table_args__ = (
        Index("idx_audiobook_name_search", "name"),
        Index("idx_audiobook_price", "price"),
        Index("idx_audiobook_created", "created_at"),
    )


class TextBook(Base):
    """Текстовые книги (бумажные/электронные издания)."""
    __tablename__ = "text_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    litres_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Форматы (FB2, EPUB, PDF и т.д.)
    formats: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Мета-информация для группировки
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Нормализованные поля для быстрого связывания
    normalized_key: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    author_normalized: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связь с аудиокнигами
    audiobooks: Mapped[List["Audiobook"]] = relationship(
        "Audiobook",
        secondary=audiobook_textbook,
        back_populates="text_versions"
    )

    __table_args__ = (
        Index("idx_textbook_lookup", "normalized_key", "author_normalized"),
        Index("idx_textbook_year", "year"),
        Index("idx_textbook_price", "price"),
    )
