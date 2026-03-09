"""
storage/db.py
=============
SQLAlchemy engine + session factory ve DB başlatma.

Neden var?
----------
AGENT GUIDE kural #4: "Training data (files) ≠ product state (DB)"
LendingClub verisi CSV/Parquet'ta kalır; ürün state (customer snapshots,
plan history, model runs, audit trail) SQLite'ta saklanır.

MVP'de SQLite → tez bittikten sonra kolayca PostgreSQL'e taşınır
(sadece DB_URL değişir, sqlalchemy kodu değişmez).

Kullanım
--------
    from credit_coach.storage.db import get_session, init_db
    init_db()
    with get_session() as session:
        session.add(some_orm_object)
        session.commit()
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# SQLAlchemy Base — tüm ORM modelleri buradan miras alır
# ------------------------------------------------------------------ #
class Base(DeclarativeBase):
    """Tüm ORM tablolarının ortak base sınıfı."""
    pass


# ------------------------------------------------------------------ #
# Engine kurulumu
# ------------------------------------------------------------------ #
def _get_db_url() -> str:
    """
    DB bağlantı URL'ini ortam değişkeninden veya varsayılandan alır.

    Öncelik: DB_URL env var > varsayılan SQLite
    """
    return os.getenv("DB_URL", "sqlite:///./credit_coach_state.db")


def create_db_engine(db_url: str | None = None, echo: bool = False):
    """
    SQLAlchemy engine oluşturur.

    Parameters
    ----------
    db_url : str | None
        Bağlantı URL'i. None ise ortam değişkeni /  varsayılan kullanılır.
    echo : bool
        True ise SQL sorgular stdout'a yazdırılır (debug amaçlı).

    Returns
    -------
    sqlalchemy.Engine
    """
    url = db_url or _get_db_url()
    engine = create_engine(url, echo=echo, future=True)

    # SQLite için WAL modu — eş zamanlı okuma/yazma performansı
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("DB engine created: %s", url.split("@")[-1])  # şifreyi gizleme
    return engine


# ------------------------------------------------------------------ #
# Uygulama geneli singleton engine + SessionFactory
# ------------------------------------------------------------------ #
_engine = None
_SessionFactory: sessionmaker | None = None


def get_engine(db_url: str | None = None):
    """Singleton engine döndürür; ilk çağrıda oluşturur."""
    global _engine
    if _engine is None:
        _engine = create_db_engine(db_url)
    return _engine


def get_session_factory() -> sessionmaker:
    """Singleton SessionFactory döndürür."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(
            bind=get_engine(), autocommit=False, autoflush=False
        )
    return _SessionFactory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager olarak SQLAlchemy session verir.

    Kullanım:
        with get_session() as session:
            session.add(obj)
            session.commit()

    Hata durumunda otomatik rollback + session kapatma garantilenir.
    """
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ------------------------------------------------------------------ #
# DB Başlatma
# ------------------------------------------------------------------ #
def init_db(db_url: str | None = None) -> None:
    """
    Tüm tabloları oluşturur (eğer yoksa).

    Bu fonksiyonu uygulama ilk başladığında bir kez çağırın.
    Mevcut tablolara dokunmaz (CREATE TABLE IF NOT EXISTS semantiği).
    """
    # ORM modelleri import edilmeli ki Base.metadata'ya kayıt olsunlar
    from credit_coach.storage import models  # noqa: F401  (side-effect import)

    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    logger.info("Database initialized — all tables created/verified.")
