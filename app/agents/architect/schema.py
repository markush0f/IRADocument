from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WikiPage(BaseModel):
    id: str = Field(
        ..., description="Unique slug for the page (e.g., 'services-overview')."
    )
    title: str = Field(..., description="Human-readable title.")
    category: str = Field(
        ...,
        description="Category: 'Overview', 'Guide', 'Architecture', 'API', 'Module'.",
    )
    content_markdown: str = Field(
        ...,
        description="The rich markdown content of the page. Should be extensive and technical.",
    )
    related_files: List[str] = Field(
        default_factory=list, description="List of source files related to this page."
    )
    diagram_mermaid: Optional[str] = Field(
        None, description="Optional Mermaid diagram definition for this page."
    )


class NavigationItem(BaseModel):
    label: str
    page_id: Optional[str] = None
    children: List["NavigationItem"] = Field(default_factory=list)


class WikiStructure(BaseModel):
    project_name: str
    landing_page_summary: str = Field(
        ..., description="Short summary for the home page hero section."
    )
    navigation: List[NavigationItem] = Field(
        ..., description="The hierarchical navigation tree."
    )
    pages: List[WikiPage] = Field(
        ..., description="All the generated documentation pages."
    )


# Recursive model reference update
NavigationItem.model_rebuild()
