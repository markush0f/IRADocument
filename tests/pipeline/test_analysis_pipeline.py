import pytest
import os
from app.pipeline.orchestrator import create_standard_pipeline, PipelineContext
from app.core.database import AsyncSessionLocal, engine
from sqlmodel import SQLModel


@pytest.mark.asyncio
async def test_full_analysis_pipeline():
    """
    Test the complete parent pipeline: Prepare -> Clone -> Analyze
    """
    # Initialize DB
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Use a real public small repo for testing if possible, or just this one
        repo_url = os.getcwd()  # Test on self

        context = PipelineContext(repo_url=repo_url, session=session)

        pipeline = create_standard_pipeline()

        # Run
        await pipeline.run(context)

        # Assertions
        assert not context.errors, f"Pipeline had errors: {context.errors}"
        assert context.workspace_id is not None
        assert context.repo_path is not None
        assert context.analysis_result["status"] == "completed"
        assert context.discovery_report is not None

        print(f"\nPipeline finished for workspace: {context.workspace_id}")
        if context.discovery_report:
            print(f"Report Summary: {context.discovery_report.payload[:200]}...")
