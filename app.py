import os
import shutil
from datetime import date
from pathlib import Path
import gradio as gr
from docubot import CARPETA_DOCUMENTOS, EXTENSIONES, indexar_documento, listar_documentos, responder

# Protección del crédito de la API: en el demo público cualquiera puede preguntar
LIMITE_PREGUNTAS_DIA = int(os.getenv("LIMITE_PREGUNTAS_DIA", "50"))
MAX_CARACTERES_PREGUNTA = 500
contador = {"fecha": None, "preguntas": 0}


def chatear(mensaje, historial):
    if len(mensaje) > MAX_CARACTERES_PREGUNTA:  # antes del contador: no gasta cupo
        return f"Tu pregunta es muy larga (máximo {MAX_CARACTERES_PREGUNTA} caracteres)."
    if contador["fecha"] != date.today():  # día nuevo: reiniciar el contador
        contador.update(fecha=date.today(), preguntas=0)
    if contador["preguntas"] >= LIMITE_PREGUNTAS_DIA:
        return "Este demo ya llegó a su límite de preguntas por hoy. Vuelve mañana 🙂"
    contador["preguntas"] += 1

    # Cada pregunta es independiente: por ahora no usamos el historial
    texto_respuesta, fuentes = responder(mensaje)

    # Mostrar de qué documento y qué parte salió la respuesta (así se ve que no inventa)
    citas = "\n\n".join(
        f"📄 **{archivo}**\n> {fragmento.replace(chr(10), '  ' + chr(10) + '> ')}"
        for archivo, fragmento in fuentes
    )
    return f"{texto_respuesta}\n\n---\n**Fragmentos usados:**\n\n{citas}"


def mostrar_documentos():
    return "**Documentos cargados:**\n\n" + "\n".join(f"- 📄 {nombre}" for nombre in listar_documentos())


def subir(rutas_temporales):
    """Gradio guarda lo que sube el usuario en una carpeta temporal: lo copiamos a
    documentos/ y lo indexamos en Chroma, sin reiniciar la app."""
    mensajes = []
    for ruta_temporal in rutas_temporales or []:
        destino = CARPETA_DOCUMENTOS / Path(ruta_temporal).name
        shutil.copy(ruta_temporal, destino)
        try:
            cantidad = indexar_documento(destino)
        except Exception as error:  # p. ej. un .txt que no está en UTF-8 o un PDF dañado
            cantidad, motivo = 0, f"no se pudo leer ({error.__class__.__name__})"
        else:
            motivo = "no se encontró texto (¿es un PDF escaneado?)"
        if cantidad:
            mensajes.append(f"✅ **{destino.name}**: {cantidad} fragmentos listos")
        else:
            destino.unlink()
            mensajes.append(f"⚠️ **{destino.name}**: {motivo}")
    # Devolver None al componente de archivos lo limpia para la siguiente subida
    return "\n\n".join(mensajes + [mostrar_documentos()]), None


with gr.Blocks(title="DocuBot") as demo:
    gr.Markdown("# ☕ DocuBot — Café La Esquina\n"
                "Respondo solo con lo que dicen los documentos del negocio.")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Para el dueño del negocio")
            archivos = gr.File(
                label="Sube tus documentos (.txt o .pdf)",
                file_count="multiple",
                file_types=list(EXTENSIONES),
            )
            estado = gr.Markdown(mostrar_documentos())
        with gr.Column(scale=3):
            gr.ChatInterface(
                fn=chatear,
                examples=[
                    "¿A qué hora abren el sábado?",
                    "¿Cuánto cuesta un latte?",
                    "¿Puedo llevar a mi perro?",
                    "¿Tienen alguna promoción en la tarde?",
                    "¿Me dan factura de una compra del mes pasado?",
                    "¿Tienen tacos?",
                ],
            )
    archivos.upload(subir, inputs=archivos, outputs=[estado, archivos], api_name="subir")

if __name__ == "__main__":
    demo.launch(max_file_size="2mb")  # documentos de negocio pequeños; evita que suban archivos enormes
