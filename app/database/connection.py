import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

logger = logging.getLogger("voice_agent.database.connection")

class DatabaseManager:
    """
    Manages SQLAlchemy asynchronous database engine and connection pool lifecycles.
    """
    def __init__(self):
        self.engine = None
        self.session_maker = None

    async def initialize(self):
        """
        Creates the database engine and establishes connection pool.
        """
        logger.info(f"Initializing async database engine with URL: {settings.DATABASE_URL.split('@')[-1]}")
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600
        )
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def close(self):
        """
        Disposes of the connection pool on application shutdown.
        """
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection pool disposed.")

# Global Singleton Database Manager
db_manager = DatabaseManager()
