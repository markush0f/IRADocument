from typing import List, Optional, Dict, Any
from .core.pipeline import BasePipeline
from .core.prompt_loader import PromptLoader


class ProjectDiscoveryPipeline(BasePipeline):
    """
    Project Discovery Ladder configured via constructor.
    The execution flow is determined at instantiation time.
    """

    def __init__(
        self, agent, project_id: str, enabled_stages: Optional[List[str]] = None
    ):
        super().__init__(agent)
        self.project_id = project_id

        # 1. Define the full logical sequence (the order of the ladder)
        self.full_ladder = ["exploration", "tech_stack", "summary"]

        # 2. Filter stages based on variables passed to the constructor
        self.active_stages = [
            s for s in self.full_ladder if enabled_stages is None or s in enabled_stages
        ]

        # 3. Pre-map definitions for the active stages
        self.definitions = {
            "exploration": {
                "prompt": PromptLoader.load_prompt(
                    "exploration", project_id=project_id
                ),
                "tools": ["browse_repository"],
            },
            "tech_stack": {
                "prompt": PromptLoader.load_prompt("tech_stack", project_id=project_id),
                "tools": ["analyze_tech_stack"],
            },
            "summary": {
                "prompt": PromptLoader.load_prompt("summary", project_id=project_id),
                "tools": ["list_project_facts"],
            },
        }

    async def execute(self):
        """
        Executes the pre-configured sequence of stages.
        """
        for stage_name in self.active_stages:
            stage_def = self.definitions.get(stage_name)
            if stage_def:
                await self.run_stage(
                    name=stage_name,
                    prompt=stage_def["prompt"],
                    tools=stage_def["tools"],
                )

        return {
            "project_id": self.project_id,
            "stages_executed": list(self.stages_results.keys()),
            "stages_detail": self.stages_results,
            "summary": self.stages_results.get("summary"),
        }
