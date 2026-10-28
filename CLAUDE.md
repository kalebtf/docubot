# DocuBot — contexto para Claude

## Quién soy
- Kaleb, Java developer en México (remoto). Estoy dejando Java para convertirme en Applied AI Engineer / AI Solutions Engineer.
- No soy bueno en algoritmos ni code challenges. Aprendo haciendo, no con teoría ni clases de sintaxis.
- Windows, Python 3.12.10, VS Code. Siempre usar `python -m pip`. Activar entorno con `.venv\Scripts\activate`.

## Cómo quiero trabajar
- Aprender haciendo: construimos cosas reales, en pasos pequeños, uno a la vez.
- Cada vez que instalemos, creemos o corramos algo, explícame en 1–3 frases QUÉ es y PARA QUÉ sirve, comparándolo con Java cuando ayude.
- Desde 2026-10-27: Claude implementa y corre los pasos directamente; al terminar me dice qué implementó (qué comandos corrió y qué hizo) y qué tengo que probar yo. Quiero entender el código, así que la explicación breve se mantiene.
- En cada respuesta explícame con palabras simples: 1) qué hicimos, 2) para qué sirve en el proyecto y en el trabajo real de un AI Engineer, 3) los conceptos nuevos, y 4) el siguiente paso según el plan.
- Nunca muestres, imprimas ni subas el contenido de `.env` (tiene mi API key).

## El plan (12 meses)
- Meses 1–3: PORTAFOLIO PRIMERO. 3 proyectos funcionales, desplegados gratis, con demo en video y código público en GitHub, antes de aplicar a clientes o empleos:
  1. DocuBot (este proyecto): asistente que responde preguntas sobre documentos de un negocio (RAG).
  2. Agente con herramientas: lee correos/formularios, extrae datos y los guarda.
  3. Automatización con n8n + IA.
- Después: freelance de IA en Upwork (nicho: asistentes de IA sobre documentos y automatizaciones para pequeñas empresas), y aplicar a empleos de Applied AI.
- Regla de gasto: herramientas y hosting gratuitos; máximo ~$15 USD en total (solo crédito de API).

## Decisiones técnicas de DocuBot
- LLM: Claude vía API de Anthropic (modelo `claude-sonnet-5-5`), key en `.env`.
- Búsqueda en documentos: ChromaDB con embeddings locales gratuitos (no se necesita otra API key). Modelo de embeddings: `paraphrase-multilingual-MiniLM-L12-v2` vía `sentence-transformers` (`normalize_embeddings=True`; colección `documentos` en DocuBot, `cafeteria`/`cafeteria_multilingue` solo en `probar_chroma.py`). Se descarga solo la primera vez (~460 MB en `~/.cache/huggingface`).
- Interfaz: Gradio 6.30 en `app.py` (`gr.Blocks`: columna de subida de archivos + `gr.ChatInterface`); muestra la respuesta + los fragmentos usados. Endpoints de API: `/chatear` y `/subir` (útiles para probar con `gradio_client`). Si el 7860 está ocupado (p. ej. Kaleb ya tiene la app abierta), Gradio arranca en 7861: revisar el puerto antes de probar.
- Despliegue (plan): Hugging Face Spaces gratis (CPU con 16 GB de RAM, aguanta PyTorch + el modelo de embeddings); la key va como "secret" del Space, nunca en el repo.
- Sonnet 5.5 piensa por defecto: la respuesta puede traer bloques `thinking` antes del texto. Nunca usar `respuesta.content[0].text`; recorrer `respuesta.content` y tomar los bloques con `type == "text"`. Usamos `output_config={"effort": "low"}` y `max_tokens=1000` (el pensamiento también gasta tokens).

## Estado actual
- Hecho: carpeta del proyecto, `.venv`, `anthropic` y `python-dotenv` instalados, `.env` con la key, `.gitignore` (`.env`, `.venv/`, `__pycache__/`), `hola_claude.py` creado, Git instalado y configurado, `CLAUDE.md` creado, `hola_claude.py` corrido con éxito (la API responde), repo público en https://github.com/kalebtf/docubot (rama `main`, `.env` verificado fuera).
- `preguntar_documento.py` responde preguntas sobre `documentos/cafeteria.txt` (documento completo en el prompt, sin ChromaDB todavía). Probado: responde lo que está y dice "no tengo esa información" cuando no está.
- `chromadb` 1.5.9 instalado. `probar_chroma.py` hace búsqueda semántica (sin Claude): fragmentos por párrafo, `PersistentClient` en `chroma_db/` (en `.gitignore`), modelo por defecto `all-MiniLM-L6-v2`. Resultado: encuentra el párrafo correcto en 3 de 4 preguntas, pero con distancias altas (~1.0–1.3), y para "¿cuánto cuesta un latte?" pone el título del documento antes que el menú → el modelo es débil en español.
- `docubot.py`: RAG completo. Chroma recupera los 2 fragmentos más parecidos y Claude responde solo con ellos. Probado: "¿tienes tacos?" → dice que no aparecen en el menú; latte → $55; transferencia → no se acepta.
- `sentence-transformers` instalado. `probar_chroma.py` ahora compara los dos modelos con 4 preguntas fijas (una colección por modelo). Resultado: multilingüe acierta 4/4 con distancias 0.50–0.65; el modelo por defecto acierta 2/4 con distancias 0.85–1.17 (falla "¿a qué hora abren?" y "¿cuánto cuesta un latte?"). `docubot.py` ya usa el modelo multilingüe; probado: "¿a qué hora abren el sábado?" → 8:00 a 14:00.
- Respaldo del contexto en Google Drive: documento "DocuBot - Contexto del proyecto".
- `gradio` instalado. `docubot.py` refactorizado: la lógica vive en `responder(pregunta)` → (texto, fragmentos); el `input()` quedó bajo `if __name__ == "__main__"`. `app.py` = interfaz web de chat en http://127.0.0.1:7860 con preguntas de ejemplo. Probado vía `gradio_client` (endpoint `/chatear`): latte → $55 con fragmentos citados.
- Varios documentos: `pypdf` instalado. `docubot.py` lee todos los `.txt` y `.pdf` de `documentos/` (`cafeteria.txt`, `promociones.txt`, `preguntas_frecuentes.pdf`), los guarda en la colección `documentos` con metadato `archivo`, y la reconstruye en cada arranque (borrar y crear) para no dejar fragmentos viejos. Divisor: por párrafo y, si pasa de 300 caracteres, por líneas con traslape de 1 línea (el PDF pierde las líneas en blanco). `n_results=5` porque con 3 el menú quedaba fuera para "¿cuánto cuesta un latte?" (quedaba 4º). `app.py` muestra 📄 archivo + fragmento. Probado con Claude: latte, perro, promoción en la tarde, factura del mes pasado y tacos → todas correctas; combina info de varios archivos.
- Arreglado (2026-10-28): los títulos quedaban como fragmentos sueltos y ocupaban el top 5 (con `eventos_y_catering.txt` subido, "¿hacen catering para eventos?" traía 4 títulos de 5 y Claude respondía "no tengo esa información"). Ahora `separar_titulo()` saca el título del documento (primera línea si `es_titulo()`: ≤80 caracteres y no termina en `.?!`), `dividir_en_fragmentos()` une cualquier párrafo-título al párrafo siguiente, e `indexar_documento()` antepone a cada fragmento `[archivo — título]`. Resultado: catering → 3 de los primeros 4 son de eventos, ningún título solo; Claude responde paquete de desayuno, renta y anticipo. Perro, factura y promoción en la tarde siguen correctas. 15 fragmentos (antes 18).
- Problema abierto: "¿cuánto cuesta un latte?" NO trae el menú (queda 6º, distancia 0.68; ya fallaba antes del arreglo de títulos) y Claude dice que no tiene el precio. "Capuchino" y "molletes" sí lo traen 1º. Causa: el menú es una lista de 5 productos en un solo fragmento y el modelo de embeddings no liga "latte" con esa lista. Ideas: búsqueda híbrida (palabra exacta + semántica) o un fragmento por producto. Es una de las preguntas de ejemplo de la página.
- La sección "Fragmentos usados" en la página es larga (5 citas) y ahora cada cita repite el encabezado `[archivo — título]`.
- Subir documentos desde la página: `docubot.py` expone `indexar_documento(ruta)` (borra los fragmentos viejos de ese archivo y agrega los nuevos) y `listar_documentos()`. En `app.py`, `subir()` copia el archivo de la carpeta temporal de Gradio a `documentos/`, lo indexa sin reiniciar y muestra ✅/⚠️ + la lista de documentos. Si no hay texto (PDF escaneado) o falla la lectura (txt no UTF-8), borra el archivo y avisa. Archivo de prueba en `ejemplos_para_subir/eventos_y_catering.txt`. Simulado vía API: antes de subir, "¿cuánto cuesta rentar el salón 3 horas?" → no tengo info; después → $4,500 citando el archivo nuevo; un txt latin-1 → ⚠️ UnicodeDecodeError.
- Limitación: el traslape del PDF a veces pega una línea suelta ("con un día de anticipación", que es de reservaciones) a otro tema y confunde a Claude (habló de "48 horas vs un día" para eventos). En Hugging Face Spaces gratis lo subido se pierde al reiniciar el Space.
- Preparado para desplegar (aún NO publicado): `requirements.txt` con versiones fijas. `app.py` protege el crédito: máx. 500 caracteres por pregunta (no gasta cupo), `LIMITE_PREGUNTAS_DIA` (variable de entorno, por defecto 50, contador en memoria que se reinicia cada día y al reiniciar el Space), `max_file_size="2mb"`. `publicar_space.py` crea el Space público `<usuario>/docubot`, pone `ANTHROPIC_API_KEY` como secret (desde `.env`, sin imprimirla), sube solo `app.py`, `docubot.py`, `requirements.txt` y `documentos/*` (lista blanca), y un README propio del Space con la cabecera YAML (sdk gradio 6.30.0, Python 3.12). Probado: límite y largo de pregunta; la lista blanca no incluye `.env`.
- Bloqueado en: Kaleb no tiene sesión de Hugging Face (`LocalTokenNotFoundError`). Necesita cuenta, token "Write" y `hf auth login`; después Claude corre `python publicar_space.py`.
- Limitación del demo público: lo que suba un visitante lo ven todos los demás (una sola colección compartida).
- Siguiente (camino a la versión final):
  0. Arreglar "latte" (ver problema abierto) antes de publicar, porque es una pregunta de ejemplo.
  1. Publicar en Hugging Face Spaces (`python publicar_space.py`) y probar la URL.
  2. README con GIF/captura, video demo de 1–2 min.

## Bitácora
Al terminar cada avance importante, actualizar "Estado actual" y agregar una línea aquí con fecha y lo que hicimos.

- 2026-10-27: Creado `CLAUDE.md` con el contexto del proyecto.
- 2026-10-27: Primera llamada exitosa a la API de Claude con `hola_claude.py`.
- 2026-10-27: Repo público `kalebtf/docubot` creado con `gh`, primer commit y push.
- 2026-10-27: DocuBot lee su primer documento (`preguntar_documento.py` + `documentos/cafeteria.txt`) y no inventa respuestas. Commit y push.
- 2026-10-27: Instalado ChromaDB; primera búsqueda semántica con `probar_chroma.py`. Detectado que el modelo de embeddings por defecto es flojo en español.
- 2026-10-27: Primer RAG completo (`docubot.py`): Chroma recupera y Claude genera la respuesta.
- 2026-10-27: Arreglado `AttributeError: 'ThinkingBlock'` en los 3 scripts (leer solo bloques de texto, effort low, max_tokens 1000).
- 2026-10-27: Commit y push del RAG completo (`14f3614`). Respaldo del contexto en Google Drive.
- 2026-10-27: Cambio a embeddings multilingües (`paraphrase-multilingual-MiniLM-L12-v2`): 4/4 aciertos contra 2/4, distancias ~2x más bajas. `docubot.py` ya lo usa.
- 2026-10-27: Primera interfaz web con Gradio (`app.py`): chat con ejemplos y fragmentos citados. `docubot.py` ahora expone `responder()`.
- 2026-10-27: Varios documentos (txt + PDF con `pypdf`), fragmentos con archivo de origen, divisor con traslape, `n_results=5`.
- 2026-10-27: Subir documentos desde la página (`indexar_documento`, `/subir`); simulado con `ejemplos_para_subir/eventos_y_catering.txt`.
- 2026-10-27: Preparado el despliegue: `requirements.txt`, límites de gasto en `app.py`, `publicar_space.py`. Falta login de Hugging Face.
- 2026-10-28: Arreglado: títulos ya no son fragmentos sueltos; cada fragmento lleva `[archivo — título]`. Catering ahora responde bien. Detectado que "latte" no trae el menú (6º lugar).
