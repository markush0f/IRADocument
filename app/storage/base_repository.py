from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, obj_data: T) -> T:
        """Create a new record."""
        self.session.add(obj_data)
        await self.session.commit()
        await self.session.refresh(obj_data)
        return obj_data

    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get a record by its primary key."""
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination."""
        statement = select(self.model).offset(offset).limit(limit)
        results = await self.session.exec(statement)
        return results.all()

    async def update(self, id: Any, data: dict) -> Optional[T]:
        """Update a record by id."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None

        for key, value in data.items():
            setattr(db_obj, key, value)

        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> bool:
        """Delete a record by id."""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False

        await self.session.delete(db_obj)
        await self.session.commit()
        return True
