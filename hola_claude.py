import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()  # carga la API key desde .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

respuesta = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=300,
    messages=[{"role": "user", "content": "Explícame en 2 frases qué es un sistema RAG."}],
)

print(respuesta.content[0].text)