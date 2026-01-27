from app.services.analysis_service import AnalysisService
from app.services.project_service import ProjectService
import os


class AnalysisStepError(Exception):
    pass


async def analyze_project_step(context) -> None:
    """
    Step to run the AI analysis on the cloned repository.
    """
    session = getattr(context, "session", None)
    if not session:
        raise AnalysisStepError("No database session found in context")

    project_service = ProjectService(session)
    analysis_service = AnalysisService(session)

    # 1. Register the project if not already registered
    # The context should have repo_path and workspace_id
    project_id = context.workspace_id
    repo_path = str(context.repo_path)

    try:
        await project_service.create_project(
            id=project_id, name=f"Pipeline Analysis {project_id}", root_path=repo_path
        )
    except Exception as e:
        # If it already exists, we continue
        pass

    # 2. Run the analysis
    try:
        result = await analysis_service.generate_analysis_report(project_id)
        context.analysis_result = result

        # We can also fetch the consolidated report fact to keep it in context
        from app.services.fact_service import FactService

        fact_service = FactService(session)
        facts = await fact_service.get_facts_by_project(project_id)
        report = next((f for f in facts if f.type == "discovery_report"), None)
        context.discovery_report = report

    except Exception as e:
        raise AnalysisStepError(f"AI Analysis failed: {str(e)}")
