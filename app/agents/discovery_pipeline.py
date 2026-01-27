from typing import List, Optional, Dict, Any, Callable
from .core.pipeline import BasePipeline
from .core.prompt_loader import PromptLoader
from .core.types import AnalysisStage
from app.scanners.technology_scanner import TechnologyScanner


class ProjectDiscoveryPipeline(BasePipeline):

    def __init__(
        self,
        agent,
        project_id: str,
        repo_path: str,
        enabled_stages: Optional[List[AnalysisStage]] = None,
    ):
        super().__init__(agent)
        self.project_id = project_id
        self.repo_path = repo_path
        # The list of stages to execute, in the correct order
        self.active_stages = enabled_stages or ["exploration", "tech_stack"]

    async def _prepare_tech_stack_context(self) -> Dict[str, Any]:
        """
        Runs automated scanners to provide context for the tech_stack stage.
        """
        scanner = TechnologyScanner(self.repo_path)
        tech_results = scanner.scan()
        return {"tech_data": scanner.format_for_llm(tech_results)}

    def _get_tools_for_stage(self, stage_name: str) -> List[str]:
        """
        Defines which tools are allowed for each stage.
        """
        tools_map = {
            "exploration": ["browse_repository"],
            "tech_stack": [],  # Reasoning only based on pre-scanned data
        }
        return tools_map.get(stage_name, [])

    def _get_prompt_for_stage(self, stage_name: str, context: Dict[str, Any]) -> str:
        """
        Selects the appropriate prompt file based on the current stage.
        """
        # Mapping stage names to specific prompt files
        prompt_map = {
            "exploration": "exploration",
            "tech_stack": "tech_stack",
        }
        prompt_file = prompt_map.get(stage_name, stage_name)
        return PromptLoader.load_prompt(prompt_file, **context)

    async def execute(self) -> Dict[str, Any]:
        """
        Executes the requested stages dynamically.
        """
        # Set the agent identity for this specific pipeline
        self.agent.set_system_prompt(PromptLoader.load_prompt("system_analyst"))

        # Mapping of stages to their respective data preparation methods
        preprocessors: Dict[str, Callable] = {
            "tech_stack": self._prepare_tech_stack_context
        }

        for stage_name in self.active_stages:
            # 1. Initialize context variables
            context_vars = {"project_id": self.project_id}

            # 2. Run pre-processor if the stage requires it
            if stage_name in preprocessors:
                prep_result = await preprocessors[stage_name]()
                context_vars.update(prep_result)

            # 3. Select prompt and Run the analysis stage
            stage_prompt = self._get_prompt_for_stage(stage_name, context_vars)

            await self.run_stage(
                name=stage_name,
                prompt=stage_prompt,
                tools=self._get_tools_for_stage(stage_name),
            )

        return {
            "project_id": self.project_id,
            "stages_executed": list(self.stages_results.keys()),
            "results": self.stages_results,
        }
