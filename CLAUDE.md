# DocuBot — contexto para Claude

## Quién soy
- Kaleb, Java developer en México (remoto). Estoy dejando Java para convertirme en Applied AI Engineer / AI Solutions Engineer.
- No soy bueno en algoritmos ni code challenges. Aprendo haciendo, no con teoría ni clases de sintaxis.
- Windows, Python 3.12.10, VS Code. Siempre usar `python -m pip`. Activar entorno con `.venv\Scripts\activate`.

## Cómo quiero trabajar
- Aprender haciendo: construimos cosas reales, en pasos pequeños, uno a la vez.
- Cada vez que instalemos, creemos o corramos algo, explícame en 1–3 frases QUÉ es y PARA QUÉ sirve, comparándolo con Java cuando ayude.
- Quiero escribir y entender el código yo: propón el código, explícalo brevemente y déjame correrlo. No hagas cambios grandes sin explicarme antes.
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

## Estado actual
- Hecho: carpeta del proyecto, `.venv`, `anthropic` y `python-dotenv` instalados, `.env` con la key, `.gitignore` (`.env`, `.venv/`, `__pycache__/`), `hola_claude.py` creado, Git instalado y configurado, `CLAUDE.md` creado, `hola_claude.py` corrido con éxito (la API responde).
- Siguiente:
  1. Crear repo público "docubot" en GitHub y hacer el primer commit y push, verificando que `.env` NO se suba.
  2. Que DocuBot lea su primer documento.

## Bitácora
Al terminar cada avance importante, actualizar "Estado actual" y agregar una línea aquí con fecha y lo que hicimos.

- 2026-10-27: Creado `CLAUDE.md` con el contexto del proyecto.
- 2026-10-27: Primera llamada exitosa a la API de Claude con `hola_claude.py`.
