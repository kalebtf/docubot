import chromadb

# Base de datos local que se guarda en la carpeta "chroma_db"
cliente = chromadb.PersistentClient(path="chroma_db")
coleccion = cliente.get_or_create_collection(name="cafeteria")

with open("documentos/cafeteria.txt", encoding="utf-8") as archivo:
    texto = archivo.read()

# Dividir el documento en fragmentos (uno por párrafo)
fragmentos = [p.strip() for p in texto.split("\n\n") if p.strip()]
ids = [f"cafeteria-{i}" for i in range(len(fragmentos))]

coleccion.upsert(documents=fragmentos, ids=ids)

pregunta = input("Tu pregunta: ")
resultados = coleccion.query(query_texts=[pregunta], n_results=2)

for fragmento, distancia in zip(resultados["documents"][0], resultados["distances"][0]):
    print(f"--- distancia {distancia:.3f}")
    print(fragmento)
