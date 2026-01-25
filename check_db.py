import asyncio
from sqlalchemy import inspect
from app.core.database import engine


async def check_db():
    async with engine.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        print("Tablas encontradas en la base de datos:")
        for table in tables:
            print(f"- {table}")

        if not tables:
            print("¡La base de datos está vacía!")
        else:
            print("\nConexión exitosa y esquema verificado.")


if __name__ == "__main__":
    asyncio.run(check_db())
