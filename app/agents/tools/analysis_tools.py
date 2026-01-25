from typing import Dict, Any
from .registry import registry
from app.core.database import AsyncSessionLocal


@registry.tool
async def run_project_analysis(project_id: str) -> Dict[str, Any]:
    """
    Triggers an AI-driven analysis of the project to discover its technology stack
    and generate a discovery report. All findings will be saved to the database.
    """
    from app.services.analysis_service import AnalysisService

    async with AsyncSessionLocal() as session:
        service = AnalysisService(session)
        result = await service.generate_analysis_report(project_id)
        return result
