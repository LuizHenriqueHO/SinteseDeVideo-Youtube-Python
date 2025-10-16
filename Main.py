
import whisper
from pytubefix import YouTube
from pytubefix.cli import on_progress
from summarizer import Summarizer

url = input("Escreva a url do video do youtube: ")

yt = YouTube(url, on_progress_callback=on_progress)
print(yt.title)

ys = yt.streams.get_audio_only()
arquivo = ys.download()

modelo = whisper.load_model("base")

dicionario = modelo.transcribe(arquivo)
transcricao = dicionario['text']


texto_completo = transcricao
modelo = Summarizer()
resumo = modelo(texto_completo, min_length=30, max_length=1000)

print(resumo)
