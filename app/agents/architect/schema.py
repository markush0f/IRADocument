from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- NAVIGATION STRUCTURE (Sidebar) ---
class NavigationNode(BaseModel):
    id: str = Field(
        ..., description="Unique slug for the page/section (e.g., 'services-module')."
    )
    label: str = Field(..., description="Display label for the sidebar.")
    type: str = Field(
        ..., description="'category' (grouping only) or 'page' (has content)."
    )
    children: List["NavigationNode"] = Field(
        default_factory=list, description="Sub-items."
    )


class WikiNavigation(BaseModel):
    project_name: str
    tree: List[NavigationNode]


# Recursive reference
NavigationNode.model_rebuild()


# --- PAGE DETAIL (Content) ---
class WikiPageDetail(BaseModel):
    id: str = Field(..., description="Must match the ID in the navigation tree.")
    title: str
    description: str = Field(..., description="Brief meta-description.")
    content_markdown: str = Field(
        ..., description="Extremely detailed, technical markdown content."
    )
    diagram_mermaid: Optional[str] = Field(
        None, description="Mermaid chart definition."
    )
    related_files: List[str] = Field(default_factory=list)
