import pytest
import uuid
import os
from app.services.project_service import ProjectService
from app.services.analysis_service import AnalysisService
from app.core.database import AsyncSessionLocal, engine
from app.core.logger import get_logger
from sqlmodel import SQLModel

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_project_report_generation_flow():
    """
    Test the complete flow of project report generation using the Agent.
    """
    logger.info("Starting test_project_report_generation_flow")

    # Initialize DB for testing
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        project_service = ProjectService(session)
        analysis_service = AnalysisService(session)

        # 1. Setup test project
        project_id = f"test-report-{uuid.uuid4().hex[:6]}"
        current_dir = os.getcwd()

        logger.info(f"Creating test project {project_id}")
        await project_service.create_project(
            id=project_id, name="IRADocument Test Analysis", root_path=current_dir
        )

        # 2. Run analysis
        logger.info("Requesting AI Project Analysis")
        # Note: We are using the default model from settings, but could be overridden if AnalysisService allowed it.
        result = await analysis_service.generate_analysis_report(project_id)

        # 3. Assertions
        logger.info(f"Analysis finished with status: {result.get('status')}")
        logger.info(f"Agent Conclusion: {result.get('agent_conclusion')}")
        logger.info(f"Discoveries found: {result.get('discoveries_count')}")

        if result.get("status") == "failed":
            pytest.fail(f"Analysis failed: {result.get('error')}")

        assert result["status"] == "completed"
        assert result["discoveries_count"] > 0
