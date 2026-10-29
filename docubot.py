import os
import re
import unicodedata
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


def es_titulo(linea):
    """Una línea corta que no termina como oración ("EVENTOS Y CATERING - Café...", "Menú:")."""
    return 0 < len(linea) <= 80 and not linea.endswith((".", "?", "!"))


def separar_titulo(texto):
    """Devuelve (título del documento, resto del texto). El título es la primera línea,
    si parece título; si no, el documento no tiene título."""
    lineas = texto.strip().splitlines()
    if lineas and es_titulo(lineas[0].strip()):
        return lineas[0].strip(), "\n".join(lineas[1:])
    return "", texto


def dividir_en_fragmentos(texto, max_caracteres=300):
    """Corta por párrafo; si un párrafo es muy largo (pasa en PDFs, que pierden las
    líneas en blanco), lo parte por líneas repitiendo la última línea en el siguiente
    fragmento (traslape), para que una idea cortada a la mitad no pierda contexto.
    Un párrafo que es solo un título no queda solo: se une al párrafo que sigue."""
    fragmentos = []
    titulo_pendiente = []
    for parrafo in texto.split("\n\n"):
        lineas = [linea.strip() for linea in parrafo.splitlines() if linea.strip()]
        if len(lineas) == 1 and es_titulo(lineas[0]):
            titulo_pendiente.append(lineas[0])  # esperar al siguiente párrafo
            continue
        lineas = titulo_pendiente + lineas
        titulo_pendiente = []
        actual = []
        for linea in lineas:
            if actual and len("\n".join(actual + [linea])) > max_caracteres:
                fragmentos.append("\n".join(actual))
                actual = [actual[-1]]  # traslape
            actual.append(linea)
        if actual:
            fragmentos.append("\n".join(actual))
    if titulo_pendiente:  # un título al final, sin texto después: se guarda tal cual
        fragmentos.append("\n".join(titulo_pendiente))
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
    titulo, cuerpo = separar_titulo(leer_documento(ruta))
    # Cada fragmento lleva al inicio de qué documento viene, para no perder el contexto:
    # "Paquete de desayuno..." solo no dice que es de eventos; con el encabezado, sí
    encabezado = f"[{ruta.name} — {titulo}]" if titulo else f"[{ruta.name}]"
    fragmentos = [f"{encabezado}\n{fragmento}" for fragmento in dividir_en_fragmentos(cuerpo)]
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


# Palabras tan comunes que no sirven para buscar por palabra exacta (sin acentos)
PALABRAS_VACIAS = {
    "que", "cual", "cuales", "como", "cuando", "donde", "cuanto", "cuanta", "cuantos", "cuantas",
    "tienen", "tiene", "tienes", "hay", "puedo", "pueden", "puede", "dan", "hacen", "son", "una",
    "uno", "unos", "unas", "los", "las", "del", "con", "sin", "por", "para", "mas", "mis", "sus",
    "cuesta", "cuestan", "algun", "alguna", "esta", "este", "estan", "ustedes",
}


def normalizar(texto):
    """Minúsculas y sin acentos: "Sábado" y "sabado" cuentan como la misma palabra."""
    sin_acentos = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_acentos if unicodedata.category(c) != "Mn")


def palabras_clave(texto):
    return {p for p in re.findall(r"\w+", normalizar(texto)) if len(p) >= 3 and p not in PALABRAS_VACIAS}


def buscar(pregunta, cuantos=5):
    """Búsqueda híbrida: combina búsqueda por significado (embeddings) y por palabra exacta.
    Los embeddings fallan con nombres concretos en listas: "¿cuánto cuesta un latte?"
    dejaba el menú en 6º lugar, aunque es el único fragmento que dice "Latte"."""
    total = coleccion.count()
    if total == 0:
        return []
    # Ranking 1, por significado: los más parecidos según el modelo de embeddings
    semantico = coleccion.query(query_texts=[pregunta], n_results=min(20, total))["ids"][0]
    # Ranking 2, por palabra: cuántas palabras clave de la pregunta aparecen en el fragmento.
    # Se ignora la 1ª línea (el encabezado [archivo — título]), que se repite en todos.
    # Leer todos los fragmentos sirve con pocos documentos; con miles se usaría un índice (BM25)
    todos = coleccion.get()
    claves = palabras_clave(pregunta)
    coincidencias = {
        id_: sum(clave in normalizar(doc.split("\n", 1)[-1]) for clave in claves)
        for id_, doc in zip(todos["ids"], todos["documents"])
    }
    por_palabra = sorted((i for i in coincidencias if coincidencias[i]), key=lambda i: -coincidencias[i])
    # Fusión de rankings recíproca (RRF): cada ranking da 1/(60 + lugar) puntos.
    # Quedar arriba en cualquiera de los dos ayuda; quedar arriba en ambos, más.
    puntos = {}
    for ranking in (semantico, por_palabra):
        for lugar, id_ in enumerate(ranking, start=1):
            puntos[id_] = puntos.get(id_, 0) + 1 / (60 + lugar)
    mejores = sorted(puntos, key=lambda i: -puntos[i])[:cuantos]
    datos = dict(zip(todos["ids"], zip(todos["metadatas"], todos["documents"])))
    return [(datos[i][0]["archivo"], datos[i][1]) for i in mejores]


def responder(pregunta):
    """Devuelve (respuesta de Claude, lista de (archivo, fragmento) usados)."""
    # 1. Recuperar: los 5 fragmentos más relevantes, en todos los documentos.
    # Mandar unos pocos de más es barato y evita que el correcto quede fuera.
    fuentes = buscar(pregunta)
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
