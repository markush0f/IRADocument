import asyncio
from app.main import lifespan
from fastapi import FastAPI
import os


async def test_startup_export():
    app = FastAPI()
    print("Simulando arranque de la aplicación...")
    async with lifespan(app):
        print("Evento lifespan (startup) ejecutado.")

    file_path = "app/agents/tools/definitions.json"
    if os.path.exists(file_path):
        print(f"\n¡Éxito! El archivo {file_path} ha sido creado.")
        with open(file_path, "r") as f:
            content = f.read()
            print(f"Contenido (primeros 200 caracteres): {content[:200]}...")
    else:
        print(f"\nError: El archivo {file_path} no se encontró.")


if __name__ == "__main__":
    asyncio.run(test_startup_export())
