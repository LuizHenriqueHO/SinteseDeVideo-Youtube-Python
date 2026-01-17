import whisper
from pytubefix import YouTube
from pytubefix.cli import on_progress
from summarizer import Summarizer
from transformers import pipeline
import os

def baixar_audio(url, progress_callback=None):
    def internal_progress(stream, chunk, bytes_remaining):
        # Call the original pytubefix callback for CLI output
        on_progress(stream, chunk, bytes_remaining)
        
        # Calculate percentage for our custom callback
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        
        if progress_callback:
            progress_callback(percentage_of_completion, "downloading")

    yt = YouTube(url, on_progress_callback=internal_progress)
    print(f"Baixando: {yt.title}")
    audio = yt.streams.get_audio_only().download()
    # Return more info for the UI
    return audio, yt.title, yt.length, yt.thumbnail_url, yt.video_id

def transcrever_audio(arquivo, modelo):
    dicionario = modelo.transcribe(arquivo)
    return dicionario["text"]

def _chunk_text(texto, max_chars=3000):
    partes = []
    atual = texto
    while len(atual) > max_chars:
        corte = atual.rfind(".", 0, max_chars)
        if corte == -1:
            corte = max_chars
        partes.append(atual[:corte + 1])
        atual = atual[corte + 1 :]
    if atual.strip():
        partes.append(atual)
    return partes

def gerar_resumo(texto, modelo_resumo=None):
    texto = texto.strip()
    texto = texto.replace("\n", " ")
    texto = " ".join(texto.split())

    if modelo_resumo is None:
        try:
            modelo_resumo = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        except Exception:
            modelo_resumo = Summarizer()

    if hasattr(modelo_resumo, "task") and modelo_resumo.task == "summarization":
        partes = _chunk_text(texto, max_chars=3000)
        resumos_parciais = []
        for parte in partes:
            saida = modelo_resumo(parte, max_length=180, min_length=60, do_sample=False)
            resumos_parciais.append(saida[0]["summary_text"].strip())
        combinado = " ".join(resumos_parciais)
        if len(partes) > 1:
            final_saida = modelo_resumo(combinado, max_length=200, min_length=80, do_sample=False)
            resumo = final_saida[0]["summary_text"]
        else:
            resumo = combinado
    else:
        resumo = modelo_resumo(texto, min_length=60, max_length=500)

    resumo = resumo.strip()
    resumo = resumo.replace("\n", " ")
    resumo = " ".join(resumo.split())
    return resumo

if __name__ == "__main__":
    url = input("Escreva a url do video do youtube: ")
    
    arquivo, title, length, thumb, video_id = baixar_audio(url)
    
    print("Carregando modelo Whisper...")
    modelo = whisper.load_model("base")
    
    print("Transcrevendo...")
    transcricao = transcrever_audio(arquivo, modelo)
    
    print("Gerando resumo...")
    resumo = gerar_resumo(transcricao)
    
    print("\n RESUMO: \n")
    print(resumo)
