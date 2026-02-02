from typing import List, Optional
from pydantic import BaseModel, Field


class ArchitecturalComponent(BaseModel):
    name: str = Field(
        ..., description="Name of the component (e.g., 'Auth Service', 'User Model')"
    )
    type: str = Field(
        ..., description="Type of component (Service, Model, API, Utility, etc.)"
    )
    description: str = Field(
        ..., description="High-level summary of what this component does."
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of other components this one interacts with.",
    )


class TechnologicalStack(BaseModel):
    language: str = Field(..., description="Primary programming language.")
    frameworks: List[str] = Field(
        default_factory=list,
        description="List of frameworks used (e.g., FastAPI, React).",
    )
    databases: List[str] = Field(
        default_factory=list, description="List of databases and storages."
    )
    libraries: List[str] = Field(
        default_factory=list, description="Key functionality libraries."
    )


class ArchitectureReport(BaseModel):
    project_name: str = Field(..., description="Inferred name of the project.")
    summary: str = Field(
        ...,
        description="Executive summary of the project architecture (2-3 paragraphs).",
    )
    tech_stack: TechnologicalStack = Field(
        ..., description="Detected technology stack."
    )
    key_components: List[ArchitecturalComponent] = Field(
        ..., description="Major architectural blocks identified."
    )
    data_flow: str = Field(
        ..., description="Description of how data moves through the system."
    )
    deployment_inference: str = Field(
        ..., description="Inferred deployment strategy (Docker, Cloud, etc.)."
    )
    markdown_content: str = Field(
        ...,
        description="The full, formatted Markdown report ready for saving as ARCHITECTURE.md",
    )
