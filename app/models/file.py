from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .project import Project


class File(SQLModel, table=True):
    __tablename__ = "files"

    project_id: str = Field(foreign_key="projects.id", primary_key=True)
    path: str = Field(primary_key=True)
    hash: Optional[str] = None
    language: Optional[str] = None
    analyzed: Optional[int] = 0
    summary: Optional[str] = None
    last_analyzed_at: Optional[str] = None

    project: "Project" = Relationship(back_populates="files")
