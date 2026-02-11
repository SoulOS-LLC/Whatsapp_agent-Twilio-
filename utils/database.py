"""
Database utility functions
Handles database connections, session management, and initialization
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
from config.config import settings
from utils.models import Base
from loguru import logger


                        
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

                        
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.success("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def drop_db():
    """Drop all database tables - USE WITH CAUTION"""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get database session context manager.
    
    Usage:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get database session for FastAPI dependency injection.
    
    Usage in FastAPI:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db_session)):
            ...
    """
    db = SessionLocal()
    try:
        return db
    finally:
        pass                                           


                       
def check_db_health() -> bool:
    """Check if database connection is healthy"""
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False