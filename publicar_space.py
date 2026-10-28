"""Publica DocuBot en Hugging Face Spaces (como un "mvn deploy").

Requiere haber iniciado sesión una vez con:  hf auth login
"""
import os
from dotenv import load_dotenv
from huggingface_hub import HfApi

# El README del Space lleva una cabecera (YAML) que le dice a Hugging Face cómo correr la app.
# Es distinto del README de GitHub, por eso se sube desde aquí.
README_SPACE = """---
title: DocuBot
emoji: ☕
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Responde preguntas sobre los documentos de un negocio
---

# DocuBot

Asistente que responde preguntas sobre los documentos de un negocio (RAG con ChromaDB + Claude).
Código: https://github.com/kalebtf/docubot
"""

load_dotenv()
api = HfApi()
repo_id = f"{api.whoami()['name']}/docubot"

api.create_repo(repo_id, repo_type="space", space_sdk="gradio", private=False, exist_ok=True)

# La key viaja como "secret" del Space: no queda en ningún archivo ni se imprime
api.add_space_secret(repo_id, "ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))

# Subir SOLO lo necesario (lista blanca): .env, .venv y chroma_db nunca salen de tu compu
api.upload_folder(
    repo_id=repo_id,
    repo_type="space",
    folder_path=".",
    allow_patterns=["app.py", "docubot.py", "requirements.txt", "documentos/*"],
    commit_message="Publicar DocuBot",
)
api.upload_file(
    path_or_fileobj=README_SPACE.encode("utf-8"),
    path_in_repo="README.md",
    repo_id=repo_id,
    repo_type="space",
    commit_message="README del Space",
)

print(f"Listo: https://huggingface.co/spaces/{repo_id}")
print("La primera vez tarda ~5-10 min en construir (instala PyTorch y descarga el modelo).")
