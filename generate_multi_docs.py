import asyncio
import json
import os
import uuid
from sqlmodel import SQLModel
from app.core.database import engine, AsyncSessionLocal
from app.services.project_service import ProjectService
from app.services.analysis_service import AnalysisService
from app.services.fact_service import FactService

PROMPTS = [
    {
        "name": "security_focus",
        "system": "You are a Cyber Security Architect Bot. Task: Audit project '{project_id}'. Focus on vulnerabilities and security. Conclude with a 'discovery_report'. MANDATORY: NO PROSE. ONLY TOOL CALLS. START with 'list_directory_content'.",
        "user": "Full security audit for '{project_id}' now.",
    },
    {
        "name": "performance_focus",
        "system": "You are a Performance Engineer Bot. Analyze project '{project_id}'. Focus on bottlenecks and scalability. Conclude with a 'discovery_report'. MANDATORY: NO PROSE. ONLY TOOL CALLS. START with 'list_directory_content'.",
        "user": "Full performance audit for '{project_id}' now.",
    },
    {
        "name": "clean_code_focus",
        "system": "You are a Software Quality Expert Bot. Review project '{project_id}'. Focus on SOLID, patterns, and quality. Conclude with a 'discovery_report'. MANDATORY: NO PROSE. ONLY TOOL CALLS. START with 'list_directory_content'.",
        "user": "Full code quality review for '{project_id}' now.",
    },
    {
        "name": "infrastructure_focus",
        "system": "You are a DevOps Architect Bot. Analyze project '{project_id}'. Focus on deployment and CI/CD. Conclude with a 'discovery_report'. MANDATORY: NO PROSE. ONLY TOOL CALLS. START with 'list_directory_content'.",
        "user": "Full infra audit for '{project_id}' now.",
    },
    {
        "name": "product_focus",
        "system": "You are a Product Architect Bot. Analyze project '{project_id}'. Focus on logic and features. Conclude with a 'discovery_report'. MANDATORY: NO PROSE. ONLY TOOL CALLS. START with 'list_directory_content'.",
        "user": "Full product analysis for '{project_id}' now.",
    },
]


async def run_documentation_generation():
    os.makedirs("audit_reports", exist_ok=True)

    # Initialize DB
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    for i, p in enumerate(PROMPTS):
        project_id = f"audit-{p['name']}-{uuid.uuid4().hex[:4]}"
        print(f"\n[{i+1}/5] Running analysis for: {p['name']} (ID: {project_id})")

        async with AsyncSessionLocal() as session:
            project_service = ProjectService(session)
            analysis_service = AnalysisService(session)
            fact_service = FactService(session)

            # Setup project
            await project_service.create_project(
                id=project_id, name=f"Audit {p['name']}", root_path=os.getcwd()
            )

            # Run analysis
            sys_prompt = p["system"].format(project_id=project_id)
            usr_prompt = p["user"].format(project_id=project_id)

            result = await analysis_service.generate_analysis_report(
                project_id, system_prompt=sys_prompt, user_prompt=usr_prompt
            )

            # Get findings
            facts = await fact_service.get_facts_by_project(project_id)
            report = next((f for f in facts if f.type == "discovery_report"), None)

            output_data = {
                "audit_type": p["name"],
                "project_id": project_id,
                "system_prompt": sys_prompt,
                "user_prompt": usr_prompt,
                "ai_documentation_response": result.get("agent_conclusion"),
                "consolidated_report": (
                    report.payload if report else "No consolidated report fact found"
                ),
                "discoveries": [
                    {
                        "type": f.type,
                        "source": f.source,
                        "payload": (
                            json.loads(f.payload)
                            if isinstance(f.payload, str)
                            else f.payload
                        ),
                    }
                    for f in facts
                    if f.type != "discovery_report"
                ],
                "all_facts_count": len(facts),
            }

            filename = f"audit_reports/report_{p['name']}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"Generated: {filename}")


if __name__ == "__main__":
    asyncio.run(run_documentation_generation())
