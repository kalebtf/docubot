import os
from pathlib import Path
import chromadb
from chromadb.errors import NotFoundError
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from anthropic import Anthropic
from pypdf import PdfReader

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CARPETA_DOCUMENTOS = Path("documentos")


def leer_documento(ruta):
    """Devuelve el texto de un .txt o de un .pdf."""
    if ruta.suffix.lower() == ".pdf":
        return "\n\n".join(pagina.extract_text() for pagina in PdfReader(ruta).pages)
    return ruta.read_text(encoding="utf-8")


def dividir_en_fragmentos(texto, max_caracteres=300):
    """Corta por párrafo; si un párrafo es muy largo (pasa en PDFs, que pierden las
    líneas en blanco), lo parte por líneas repitiendo la última línea en el siguiente
    fragmento (traslape), para que una idea cortada a la mitad no pierda contexto."""
    fragmentos = []
    for parrafo in texto.split("\n\n"):
        lineas = [linea.strip() for linea in parrafo.splitlines() if linea.strip()]
        actual = []
        for linea in lineas:
            if actual and len("\n".join(actual + [linea])) > max_caracteres:
                fragmentos.append("\n".join(actual))
                actual = [actual[-1]]  # traslape
            actual.append(linea)
        if actual:
            fragmentos.append("\n".join(actual))
    return fragmentos


# Base de datos local que se guarda en la carpeta "chroma_db"
cliente_chroma = chromadb.PersistentClient(path="chroma_db")
# Modelo de embeddings multilingüe: entiende español mucho mejor que el de por defecto
modelo_embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2",
    normalize_embeddings=True,
)

# Reconstruir el índice en cada arranque: así un documento borrado o editado
# no deja fragmentos viejos en la base
try:
    cliente_chroma.delete_collection("documentos")
except NotFoundError:
    pass
coleccion = cliente_chroma.create_collection(name="documentos", embedding_function=modelo_embeddings)

EXTENSIONES = (".txt", ".pdf")


def indexar_documento(ruta):
    """Lee, divide y guarda un documento en Chroma. Devuelve cuántos fragmentos guardó."""
    # Si el archivo ya estaba (lo están reemplazando), quitar sus fragmentos viejos
    coleccion.delete(where={"archivo": ruta.name})
    fragmentos = dividir_en_fragmentos(leer_documento(ruta))
    if fragmentos:  # un PDF escaneado (solo imagen) no trae texto
        coleccion.add(
            documents=fragmentos,
            ids=[f"{ruta.name}-{i}" for i in range(len(fragmentos))],
            metadatas=[{"archivo": ruta.name}] * len(fragmentos),  # para saber de dónde salió cada fragmento
        )
    return len(fragmentos)


def listar_documentos():
    return sorted(r.name for r in CARPETA_DOCUMENTOS.iterdir() if r.suffix.lower() in EXTENSIONES)


for nombre in listar_documentos():
    indexar_documento(CARPETA_DOCUMENTOS / nombre)


def responder(pregunta):
    """Devuelve (respuesta de Claude, lista de (archivo, fragmento) usados)."""
    # 1. Recuperar: buscar los fragmentos más parecidos a la pregunta, en todos los documentos
    # 5 y no menos: con varios documentos el fragmento correcto a veces queda en 4º lugar
    # (p. ej. "¿cuánto cuesta un latte?" → el menú). Mandar unos pocos de más es barato.
    resultados = coleccion.query(query_texts=[pregunta], n_results=5)
    fuentes = [
        (metadatos["archivo"], fragmento)
        for fragmento, metadatos in zip(resultados["documents"][0], resultados["metadatas"][0])
    ]
    contexto = "\n\n".join(
        f'<fragmento archivo="{archivo}">\n{fragmento}\n</fragmento>' for archivo, fragmento in fuentes
    )

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

    # La respuesta puede traer bloques de pensamiento antes del texto: tomar solo el texto
    texto_respuesta = "".join(b.text for b in respuesta.content if b.type == "text")
    return texto_respuesta, fuentes


# Solo corre cuando ejecutas "python docubot.py" (como el main de Java), no cuando otro archivo lo importa
if __name__ == "__main__":
    pregunta = input("Tu pregunta: ")
    texto_respuesta, fuentes = responder(pregunta)
    print(texto_respuesta)
    print("\nFuentes:", ", ".join(sorted({archivo for archivo, _ in fuentes})))
