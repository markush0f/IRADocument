import asyncio
from app.core.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Project, File
from app.storage import ProjectRepository, FileRepository


async def test_repository_pattern():
    async with AsyncSession(engine) as session:
        # Initialize Repositories
        project_repo = ProjectRepository(session)
        file_repo = FileRepository(session)

        # 1. Create a Project
        project_id = "test_repo_1"
        print(f"Creando proyecto {project_id}...")
        new_project = Project(
            id=project_id, name="Repo Pattern Test", root_path="/path/to/test"
        )
        await project_repo.create(new_project)

        # 2. Create a File for that project
        print("Creando archivo asociado...")
        new_file = File(project_id=project_id, path="repo_test.py", language="python")
        await file_repo.create(new_file)

        # 3. Read Data
        print("\nLeyendo datos...")
        project = await project_repo.get_by_id(project_id)
        if project:
            print(f"Proyecto encontrado: {project.name}")
            # Acceso a relaciones (SQLModel)
            files = await file_repo.get_by_project(project_id)
            for f in files:
                print(f" - Archivo: {f.path} ({f.language})")

        # 4. Cleanup (Opcional, pero para mantener limpia la prueba)
        # await project_repo.delete(project_id)
        # print("\nProyecto de prueba eliminado.")


if __name__ == "__main__":
    asyncio.run(test_repository_pattern())
