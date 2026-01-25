from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .project import Project


class Fact(SQLModel, table=True):
    __tablename__ = "facts"

    id: str = Field(primary_key=True)
    project_id: str = Field(foreign_key="projects.id")
    type: Optional[str] = None
    source: Optional[str] = None
    payload: Optional[str] = None
    confidence: Optional[float] = None
    created_at: Optional[str] = None

    project: "Project" = Relationship(back_populates="facts")
