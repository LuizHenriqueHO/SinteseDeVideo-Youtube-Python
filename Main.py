import whisper
from pytubefix import YouTube
from pytubefix.cli import on_progress
from summarizer import Summarizer

def baixar_audio(url):
    yt = YouTube(url, on_progress_callback=on_progress)
    print(yt.title)
    audio = yt.streams.get_audio_only().download()
    return audio

def transcrever_audio(arquivo, modelo):
    dicionario = modelo.transcribe(arquivo)
    return dicionario["text"]

def gerar_resumo(texto):
    modelo_resumo = Summarizer()
    return modelo_resumo(texto, min_length=30, max_length=1000)

url = input("Escreva a url do video do youtube: ")

arquivo = baixar_audio(url)

modelo = whisper.load_model("base")

transcricao = transcrever_audio(arquivo, modelo)

resumo = gerar_resumo(transcricao)

print("\n RESUMO: \n")
print(resumo)
