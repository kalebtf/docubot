# DocuBot — contexto para Claude

## Quién soy
- Kaleb, Java developer en México (remoto). Estoy dejando Java para convertirme en Applied AI Engineer / AI Solutions Engineer.
- No soy bueno en algoritmos ni code challenges. Aprendo haciendo, no con teoría ni clases de sintaxis.
- Windows, Python 3.12.10, VS Code. Siempre usar `python -m pip`. Activar entorno con `.venv\Scripts\activate`.

## Cómo quiero trabajar
- Aprender haciendo: construimos cosas reales, en pasos pequeños, uno a la vez.
- Cada vez que instalemos, creemos o corramos algo, explícame en 1–3 frases QUÉ es y PARA QUÉ sirve, comparándolo con Java cuando ayude.
- Desde 2026-10-27: Claude implementa y corre los pasos directamente; al terminar me dice qué implementó (qué comandos corrió y qué hizo) y qué tengo que probar yo. Quiero entender el código, así que la explicación breve se mantiene.
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
- Búsqueda en documentos: ChromaDB con embeddings locales gratuitos (no se necesita otra API key).
- Interfaz y despliegue: opciones gratuitas (por definir cuando lleguemos).
- Sonnet 5.5 piensa por defecto: la respuesta puede traer bloques `thinking` antes del texto. Nunca usar `respuesta.content[0].text`; recorrer `respuesta.content` y tomar los bloques con `type == "text"`. Usamos `output_config={"effort": "low"}` y `max_tokens=1000` (el pensamiento también gasta tokens).

## Estado actual
- Hecho: carpeta del proyecto, `.venv`, `anthropic` y `python-dotenv` instalados, `.env` con la key, `.gitignore` (`.env`, `.venv/`, `__pycache__/`), `hola_claude.py` creado, Git instalado y configurado, `CLAUDE.md` creado, `hola_claude.py` corrido con éxito (la API responde), repo público en https://github.com/kalebtf/docubot (rama `main`, `.env` verificado fuera).
- `preguntar_documento.py` responde preguntas sobre `documentos/cafeteria.txt` (documento completo en el prompt, sin ChromaDB todavía). Probado: responde lo que está y dice "no tengo esa información" cuando no está.
- `chromadb` 1.5.9 instalado. `probar_chroma.py` hace búsqueda semántica (sin Claude): fragmentos por párrafo, `PersistentClient` en `chroma_db/` (en `.gitignore`), modelo por defecto `all-MiniLM-L6-v2`. Resultado: encuentra el párrafo correcto en 3 de 4 preguntas, pero con distancias altas (~1.0–1.3), y para "¿cuánto cuesta un latte?" pone el título del documento antes que el menú → el modelo es débil en español.
- `docubot.py`: RAG completo. Chroma recupera los 2 fragmentos más parecidos y Claude responde solo con ellos. Probado: "¿tienes tacos?" → dice que no aparecen en el menú; latte → $55; transferencia → no se acepta.
- Siguiente:
  1. Cambiar a un modelo de embeddings multilingüe y comparar distancias.
  2. Commit y push de `.gitignore`, `CLAUDE.md`, `probar_chroma.py`, `docubot.py`.

## Bitácora
Al terminar cada avance importante, actualizar "Estado actual" y agregar una línea aquí con fecha y lo que hicimos.

- 2026-10-27: Creado `CLAUDE.md` con el contexto del proyecto.
- 2026-10-27: Primera llamada exitosa a la API de Claude con `hola_claude.py`.
- 2026-10-27: Repo público `kalebtf/docubot` creado con `gh`, primer commit y push.
- 2026-10-27: DocuBot lee su primer documento (`preguntar_documento.py` + `documentos/cafeteria.txt`) y no inventa respuestas. Commit y push.
- 2026-10-27: Instalado ChromaDB; primera búsqueda semántica con `probar_chroma.py`. Detectado que el modelo de embeddings por defecto es flojo en español.
- 2026-10-27: Primer RAG completo (`docubot.py`): Chroma recupera y Claude genera la respuesta.
- 2026-10-27: Arreglado `AttributeError: 'ThinkingBlock'` en los 3 scripts (leer solo bloques de texto, effort low, max_tokens 1000).
