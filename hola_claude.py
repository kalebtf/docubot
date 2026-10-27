import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()  # carga la API key desde .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

respuesta = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=1000,
    output_config={"effort": "low"},  # pensar poco: preguntas simples, menos tokens
    messages=[{"role": "user", "content": "Explícame en 2 frases qué es un sistema RAG."}],
)

# La respuesta puede traer bloques de pensamiento antes del texto: imprimir solo el texto
for bloque in respuesta.content:
    if bloque.type == "text":
        print(bloque.text)