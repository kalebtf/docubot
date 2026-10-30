import json
import re
import sys
from docubot import responder, buscar, coleccion, normalizar

sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows no siempre imprime acentos

LIMITE_BUSQUEDA = 5  # buscar() manda 5 fragmentos a Claude: del 6º en adelante, Claude no los ve


def limpiar(texto):
    """Minúsculas, sin acentos y sin comas de miles: "$1,500" y "$1500" son lo mismo."""
    return re.sub(r"(?<=\d),(?=\d)", "", normalizar(texto))


def lugares_de_fragmentos(pregunta, textos):
    """Para cada texto esperado, en qué lugar del ranking de búsqueda aparece un fragmento que lo contiene.
    Devuelve None si no aparece en ningún fragmento."""
    ranking = buscar(pregunta, cuantos=coleccion.count())  # ranking completo, no solo el top 5
    lugares = []
    for texto in textos:
        lugar = next((i for i, (_, frag) in enumerate(ranking, start=1) if limpiar(texto) in limpiar(frag)), None)
        lugares.append(lugar)
    return lugares


with open("preguntas_evaluacion.json", encoding="utf-8") as f:
    preguntas = json.load(f)

filas = []
for item in preguntas:
    pregunta = item["pregunta"]
    respuesta, _ = responder(pregunta)
    limpia = limpiar(respuesta)

    # Respuesta: cada dato esperado es una lista de formas válidas de decirlo; basta con que aparezca una
    faltan = [grupo[0] for grupo in item["debe_incluir"] if not any(limpiar(alt) in limpia for alt in grupo)]
    # Búsqueda: lugar de cada fragmento correcto
    lugares = lugares_de_fragmentos(pregunta, item["fragmentos"])
    peor = None if (not lugares or None in lugares) else max(lugares)
    busqueda_ok = not item["fragmentos"] or (peor is not None and peor <= LIMITE_BUSQUEDA)

    filas.append({"pregunta": pregunta, "ok": not faltan, "faltan": faltan, "lugares": lugares,
                  "busqueda_ok": busqueda_ok, "respuesta": respuesta})

print(f"\n{'#':>2}  {'Pregunta':<55} {'Respuesta':<10} {'Búsqueda':<9} Lugares de los fragmentos")
print("-" * 105)
for n, fila in enumerate(filas, start=1):
    lugares = ", ".join("—" if l is None else str(l) for l in fila["lugares"]) or "(no aplica)"
    print(f"{n:>2}  {fila['pregunta']:<55} {'OK' if fila['ok'] else 'FALLA':<10} "
          f"{'OK' if fila['busqueda_ok'] else 'FALLA':<9} {lugares}")
print("-" * 105)

aciertos = sum(f["ok"] for f in filas)
aciertos_busqueda = sum(f["busqueda_ok"] for f in filas)
print(f"Respuestas correctas: {aciertos}/{len(filas)} ({aciertos / len(filas):.0%})")
print(f"Búsqueda (fragmentos correctos en el top {LIMITE_BUSQUEDA}): {aciertos_busqueda}/{len(filas)} ({aciertos_busqueda / len(filas):.0%})")

for n, fila in enumerate(filas, start=1):
    if not fila["ok"] or not fila["busqueda_ok"]:
        print(f"\n--- Pregunta {n}: {fila['pregunta']}")
        if fila["faltan"]:
            print("Datos que faltan en la respuesta:", ", ".join(fila["faltan"]))
        print("Respuesta de DocuBot:", fila["respuesta"])
