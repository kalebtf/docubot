import os
import chromadb
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Base de datos local que se guarda en la carpeta "chroma_db"
cliente_chroma = chromadb.PersistentClient(path="chroma_db")
coleccion = cliente_chroma.get_or_create_collection(name="cafeteria")

with open("documentos/cafeteria.txt", encoding="utf-8") as archivo:
    texto = archivo.read()

# Dividir el documento en fragmentos (uno por párrafo)
fragmentos = [p.strip() for p in texto.split("\n\n") if p.strip()]
ids = [f"cafeteria-{i}" for i in range(len(fragmentos))]

coleccion.upsert(documents=fragmentos, ids=ids)

pregunta = input("Tu pregunta: ")

# 1. Recuperar: buscar los fragmentos más parecidos a la pregunta
resultados = coleccion.query(query_texts=[pregunta], n_results=2)
contexto = "\n\n".join(resultados["documents"][0])

# 2. Generar: Claude responde usando solo esos fragmentos
respuesta = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=1000,
    output_config={"effort": "low"},  # pensar poco: preguntas simples, menos tokens
    system="Eres el asistente de un negocio. Responde SOLO con la información de los fragmentos. "
           "Si la respuesta no está en los fragmentos, di que no tienes esa información.",
    messages=[{
        "role": "user",
        "content": f"<fragmentos>\n{contexto}\n</fragmentos>\n\nPregunta: {pregunta}",
    }],
)

# La respuesta puede traer bloques de pensamiento antes del texto: imprimir solo el texto
for bloque in respuesta.content:
    if bloque.type == "text":
        print(bloque.text)
