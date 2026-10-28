import chromadb
from chromadb.utils import embedding_functions

# Base de datos local que se guarda en la carpeta "chroma_db"
cliente = chromadb.PersistentClient(path="chroma_db")

# Dos modelos de embeddings para comparar. Cada uno necesita su propia colección,
# porque los vectores de un modelo no se pueden comparar con los de otro.
modelos = {
    # Modelo por defecto de Chroma (all-MiniLM-L6-v2): entrenado casi solo en inglés
    "cafeteria": embedding_functions.DefaultEmbeddingFunction(),
    # Modelo multilingüe (50+ idiomas, incluido español)
    "cafeteria_multilingue": embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2",
        normalize_embeddings=True,  # igual que el modelo por defecto, para que las distancias sean comparables
    ),
}

with open("documentos/cafeteria.txt", encoding="utf-8") as archivo:
    texto = archivo.read()

# Dividir el documento en fragmentos (uno por párrafo)
fragmentos = [p.strip() for p in texto.split("\n\n") if p.strip()]
ids = [f"cafeteria-{i}" for i in range(len(fragmentos))]

colecciones = {}
for nombre, funcion in modelos.items():
    colecciones[nombre] = cliente.get_or_create_collection(name=nombre, embedding_function=funcion)
    colecciones[nombre].upsert(documents=fragmentos, ids=ids)

preguntas = [
    "¿A qué hora abren?",
    "¿Cuánto cuesta un latte?",
    "¿Puedo pagar con transferencia?",
    "¿Hacen envíos a domicilio?",
]

# Distancia más baja = más parecido. Mostramos el fragmento #1 de cada modelo.
for pregunta in preguntas:
    print(f"\n=== {pregunta}")
    for nombre, coleccion in colecciones.items():
        resultados = coleccion.query(query_texts=[pregunta], n_results=1)
        fragmento = resultados["documents"][0][0].splitlines()[0]  # solo la primera línea, para que quepa
        distancia = resultados["distances"][0][0]
        print(f"  {nombre:<22} distancia {distancia:.3f} -> {fragmento}")
