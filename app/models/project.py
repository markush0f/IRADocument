from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .file import File
    from .fact import Fact
    from .relation import Relation


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: str = Field(primary_key=True)
    name: Optional[str] = None
    root_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Relationships
    files: List["File"] = Relationship(back_populates="project")
    facts: List["Fact"] = Relationship(back_populates="project")
    relations: List["Relation"] = Relationship(back_populates="project")
