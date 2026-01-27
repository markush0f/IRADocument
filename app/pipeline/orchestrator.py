from typing import List, Callable, Any, Optional
from dataclasses import dataclass, field
import asyncio
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineContext:
    """Shared state between pipeline steps."""

    repo_url: Optional[str] = None
    branch: Optional[str] = None
    workspace_id: Optional[str] = None
    workspace_path: Any = None
    repo_path: Any = None
    repo: Any = None
    latest_commit: Optional[str] = None
    session: Any = None
    analysis_result: dict = field(default_factory=dict)
    discovery_report: Any = None
    errors: List[str] = field(default_factory=list)


class AnalysisPipeline:
    def __init__(self, steps: List[Callable]):
        self.steps = steps

    async def run(self, context: PipelineContext):
        """Execute all steps in the pipeline sequence."""
        for step in self.steps:
            step_name = step.__name__
            logger.info(f"Executing pipeline step: {step_name}")
            try:
                if asyncio.iscoroutinefunction(step):
                    await step(context)
                else:
                    step(context)
            except Exception as e:
                logger.error(f"Error in step {step_name}: {str(e)}")
                context.errors.append(f"{step_name}: {str(e)}")
                break
        return context


# Factory to create the standard analysis pipeline
def create_standard_pipeline():
    from .steps.prepare_workspace import prepare_workspace
    from .steps.clone_repo import clone_repo
    from .steps.analyze_project import analyze_project_step

    return AnalysisPipeline([prepare_workspace, clone_repo, analyze_project_step])
