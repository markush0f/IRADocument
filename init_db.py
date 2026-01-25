import asyncio
from app.core.database import engine
from sqlmodel import SQLModel

# Import all models to ensure they are registered in SQLModel.metadata
from app.models import Project, File, Fact, Relation


async def init_db():
    async with engine.begin() as conn:
        # SQLModel uses the same metadata as SQLAlchemy
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database initialized successfully with SQLModel and async support!")


if __name__ == "__main__":
    asyncio.run(init_db())
