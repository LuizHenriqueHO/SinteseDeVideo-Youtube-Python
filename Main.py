import whisper
from pytubefix import YouTube
from pytubefix.cli import on_progress
from summarizer import Summarizer
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

def gerar_resumo(texto, modelo_resumo=None):
    if modelo_resumo is None:
        modelo_resumo = Summarizer()
        
    resumo = modelo_resumo(texto, min_length=30, max_length=1000)

    #Parte de formatacao correta do nosso resumo
    resumo = resumo.strip() 
    resumo = resumo.replace("\n", " ")
    resumo = resumo.replace("  ", " ") 

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
