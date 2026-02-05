from typing import Optional
from sqlmodel import SQLModel, Field


class Endpoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(index=True)
    path: str
    method: str
    file_path: str
    line_number: Optional[int] = None
    description: Optional[str] = None
    framework: Optional[str] = None
