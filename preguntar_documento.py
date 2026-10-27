import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Leer el documento completo
with open("documentos/cafeteria.txt", encoding="utf-8") as archivo:
    documento = archivo.read()

pregunta = input("Tu pregunta: ")

respuesta = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=300,
    system="Eres el asistente de un negocio. Responde SOLO con la información del documento. "
           "Si la respuesta no está en el documento, di que no tienes esa información.",
    messages=[{
        "role": "user",
        "content": f"<documento>\n{documento}\n</documento>\n\nPregunta: {pregunta}",
    }],
)

print(respuesta.content[0].text)
