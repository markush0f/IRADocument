import asyncio
import uuid
import random
import time
from fastapi import APIRouter
from app.core.socket_manager import manager
from pydantic import BaseModel
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SimulationRequest(BaseModel):
    project_id: str


@router.post("/simulate/documentation")
async def simulate_documentation(request: SimulationRequest):
    """
    Endpoints to simulate the documentation generation process via WebSockets.
    Useful for frontend testing without running the expensive AI pipeline.
    """
    project_id = request.project_id
    logger.info(f"Starting simulation for project {project_id}")

    asyncio.create_task(_run_simulation(project_id))
    return {"status": "simulation_started", "project_id": project_id}


async def _run_simulation(project_id: str):
    logger.info(f"[Sim] Started pipeline for {project_id}")
    # 1. Pipeline Started
    await manager.broadcast(
        project_id,
        {
            "type": "pipeline_stage",
            "stage": "started",
            "message": "Initializing Simulation...",
        },
    )
    await asyncio.sleep(1)

    # 2. Mining Phase
    logger.info(f"[Sim] Phase: Mining for {project_id}")
    await manager.broadcast(
        project_id,
        {
            "type": "pipeline_stage",
            "stage": "mining",
            "message": "Mining project facts...",
        },
    )

    total_files = 15
    for i in range(total_files):
        await asyncio.sleep(0.2)
        await manager.broadcast(
            project_id,
            {
                "type": "pipeline_progress",
                "stage": "mining_files",
                "current": i + 1,
                "total": total_files,
            },
        )

        # Simulate some agent thoughts
        if random.random() > 0.7:
            await manager.broadcast(
                project_id,
                {
                    "type": "agent_thought",
                    "subtype": "llm_request",
                    "timestamp": int(time.time() * 1000),
                    "id": str(uuid.uuid4()),
                    "data": {
                        "messages": {
                            "role": "user",
                            "content": f"Analyzing file_{i}.py...",
                        }
                    },
                },
            )
            await asyncio.sleep(0.5)
            await manager.broadcast(
                project_id,
                {
                    "type": "agent_thought",
                    "subtype": "llm_response",
                    "timestamp": int(time.time() * 1000),
                    "id": str(uuid.uuid4()),
                    "data": {"content": "Found 3 endpoints and a database model."},
                },
            )

    # 3. Architect Phase
    logger.info(f"[Sim] Phase: Architecting for {project_id}")
    await manager.broadcast(
        project_id,
        {
            "type": "pipeline_stage",
            "stage": "planning",
            "message": "Architect is analyzing structure and designing navigation...",
        },
    )
    await asyncio.sleep(1.5)

    # Send Fake Sidebar Plan
    fake_plan = {
        "project_name": "Simulation Project",
        "tree": [
            {
                "id": "overview",
                "label": "Project Overview",
                "type": "page",
                "children": [],
            },
            {
                "id": "backend",
                "label": "Backend Architecture",
                "type": "category",
                "children": [
                    {
                        "id": "auth-module",
                        "label": "Authentication Service",
                        "type": "page",
                    },
                    {"id": "users-module", "label": "User Management", "type": "page"},
                    {
                        "id": "database-schema",
                        "label": "Database Schema",
                        "type": "page",
                    },
                ],
            },
            {
                "id": "frontend",
                "label": "Frontend App",
                "type": "category",
                "children": [
                    {"id": "components", "label": "UI Components", "type": "page"},
                ],
            },
        ],
    }

    logger.info(f"[Sim] Sending Generated Plan for {project_id}")
    await manager.broadcast(project_id, {"type": "plan_generated", "plan": fake_plan})
    await asyncio.sleep(1)

    # 4. Writing Phase
    logger.info(f"[Sim] Phase: Writing for {project_id}")
    await manager.broadcast(
        project_id,
        {
            "type": "pipeline_stage",
            "stage": "writing",
            "message": "Scribe is generating detailed documentation pages...",
        },
    )

    pages = [
        "Project Overview",
        "Authentication Service",
        "User Management",
        "Database Schema",
        "UI Components",
    ]

    for i, page in enumerate(pages):
        logger.info(f"[Sim] Writing page '{page}' ({i+1}/{len(pages)})")
        # Notify start of page
        await manager.broadcast(
            project_id,
            {
                "type": "pipeline_progress",
                "stage": "writing_page",
                "current": i + 1,
                "total": len(pages),
                "page_label": page,
                "page_id": page.lower().replace(" ", "-"),
                "message": f"Drafting content for '{page}'...",
            },
        )

        # Simulate thinking/writing steps
        await asyncio.sleep(1)
        await manager.broadcast(
            project_id,
            {
                "type": "agent_thought",
                "subtype": "llm_request",
                "timestamp": int(time.time() * 1000),
                "id": str(uuid.uuid4()),
                "data": {
                    "messages": {
                        "role": "user",
                        "content": f"Writing technical documentation for {page}. Focusing on architecture and API contracts.",
                    }
                },
            },
        )

        await asyncio.sleep(1.5)

        # Emit tool call
        await manager.broadcast(
            project_id,
            {
                "type": "agent_thought",
                "subtype": "tool_calls",
                "timestamp": int(time.time() * 1000),
                "id": str(uuid.uuid4()),
                "data": {
                    "calls": [
                        {
                            "function": {
                                "name": "submit_page",
                                "arguments": f"{{'title': '{page}', 'content_length': 4500}}...",
                            }
                        }
                    ]
                },
            },
        )

    # 5. Completed
    logger.info(f"[Sim] Pipeline Completed for {project_id}")
    await manager.broadcast(
        project_id,
        {
            "type": "pipeline_stage",
            "stage": "completed",
            "message": "Documentation successfully generated! Check the sidebar.",
        },
    )
