from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .project import Project


class TreeNode(SQLModel, table=True):
    __tablename__ = "tree_nodes"

    project_id: str = Field(foreign_key="projects.id", primary_key=True)
    path: str = Field(primary_key=True)

    priority: str = Field(default="medium")  # high, medium, low, skip
    status: str = Field(default="pending")  # pending, analyzing, done, error

    # Context for why this node is in the tree
    reason: Optional[str] = None  # e.g. "Imported by main.py"
    depth: int = Field(default=0)

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    project: "Project" = Relationship(back_populates="tree_nodes")
