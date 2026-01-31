from pydantic import BaseModel, Field
from typing import List, Literal


class MinerConclusion(BaseModel):
    topic: str = Field(description="The domain of the fact (e.g., Auth, UI, Data)")
    impact: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Criticality of the fact"
    )
    statement: str = Field(
        description="A comprehensive, objective statement of the fact (aim for 30-60 words)"
    )


class MinerOutput(BaseModel):
    file: str = Field(description="The path of the file being analyzed")
    conclusions: List[MinerConclusion] = Field(description="List of extracted facts")


class MinerBatchOutput(BaseModel):
    results: List[MinerOutput] = Field(
        description="List of analysis results for each file in the batch"
    )
