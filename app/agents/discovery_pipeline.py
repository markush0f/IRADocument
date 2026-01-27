from typing import List, Optional, Dict, Any
from .core.pipeline import BasePipeline
from .core.prompt_loader import PromptLoader


class ProjectDiscoveryPipeline(BasePipeline):
    """
    Concrete implementation of the project discovery ladder.
    Stages are modular and use externalized prompts.
    """

    def _get_stage_definitions(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Returns the definitions of all available stages using loaded prompts.
        """
        return {
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

    async def execute(
        self, project_id: str, enabled_stages: Optional[List[str]] = None
    ):
        """
        Executes selected stages for project discovery in the correct order.
        If enabled_stages is None, it runs the full sequence by default.
        """
        definitions = self._get_stage_definitions(project_id)

        # The 'ladder' order is defined here
        sequence = ["exploration", "tech_stack", "summary"]

        # Filter and maintain order
        stages_to_run = [
            s for s in sequence if enabled_stages is None or s in enabled_stages
        ]

        for stage_name in stages_to_run:
            stage_def = definitions.get(stage_name)
            if stage_def:
                await self.run_stage(
                    name=stage_name,
                    prompt=stage_def["prompt"],
                    tools=stage_def["tools"],
                )

        return {
            "project_id": project_id,
            "stages_executed": list(self.stages_results.keys()),
            "stages_detail": self.stages_results,
            "summary": self.stages_results.get("summary"),
        }
