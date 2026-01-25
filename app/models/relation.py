from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .project import Project


class Relation(SQLModel, table=True):
    __tablename__ = "relations"

    project_id: str = Field(foreign_key="projects.id", primary_key=True)
    from_node: str = Field(primary_key=True)
    to_node: str = Field(primary_key=True)
    relation: str = Field(primary_key=True)
    source: Optional[str] = None

    project: "Project" = Relationship(back_populates="relations")
