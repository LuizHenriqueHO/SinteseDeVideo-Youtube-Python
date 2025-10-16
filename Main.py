
import whisper
from pytubefix import YouTube
from pytubefix.cli import on_progress

url = "https://www.youtube.com/watch?v=puymQ31SgG0"

yt = YouTube(url, on_progress_callback=on_progress)
print(yt.title)

ys = yt.streams.get_audio_only()
arquivo = ys.download()

modelo = whisper.load_model("base")

transcricao = modelo.transcribe(arquivo)

print(transcricao)
