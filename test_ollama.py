import asyncio
from app.llm.ollama_client import OllamaClient


async def test_ollama():
    print("Iniciando conexión con Ollama...")
    client = OllamaClient()

    prompt = "Hola, preséntate brevemente y confirma que eres Mistral 7B."

    print(f"\nPrompt: {prompt}\n")
    print("Respuesta: ", end="", flush=True)

    try:
        async for part in client.stream_generate(prompt):
            print(part, end="", flush=True)
        print("\n\nPrueba completada con éxito.")
    except Exception as e:
        print(f"\n\nError al conectar con Ollama: {e}")
        print(
            "Asegúrate de que Ollama esté corriendo y el modelo 'mistral:7b-instruct' esté descargado."
        )


if __name__ == "__main__":
    asyncio.run(test_ollama())
