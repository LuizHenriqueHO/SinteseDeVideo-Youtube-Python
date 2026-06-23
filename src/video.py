import whisper
from pytubefix import YouTube
from pytubefix.cli import on_progress
from transformers import pipeline
import os
import threading

# Modelo de resumo por idioma. distilbart é só inglês; para PT/ES usamos um
# modelo multilíngue (mT5 XLSum) para que o resumo saia no idioma do conteúdo.
SUMMARIZER_MODELS = {
    "en": "sshleifer/distilbart-cnn-12-6",
    "pt-BR": "csebuetnlp/mT5_multilingual_XLSum",
    "es": "csebuetnlp/mT5_multilingual_XLSum",
}
DEFAULT_SUMMARIZER_MODEL = "csebuetnlp/mT5_multilingual_XLSum"

# Mapeia o tamanho escolhido pelo usuário em limites de comprimento do resumo.
SIZE_LENGTHS = {
    "curto": {"max_length": 90, "min_length": 30},
    "medio": {"max_length": 180, "min_length": 60},
    "longo": {"max_length": 320, "min_length": 130},
}

# Cache de pipelines de resumo já carregados (evita recarregar o modelo).
_SUMMARIZERS = {}
_SUMMARIZER_LOCK = threading.Lock()


def is_summarizer_cached(language="pt-BR"):
    """Indica se o modelo do idioma já está em memória (sem disparar download)."""
    model_name = SUMMARIZER_MODELS.get(language, DEFAULT_SUMMARIZER_MODEL)
    return model_name in _SUMMARIZERS


def get_summarizer(language="pt-BR"):
    """Carrega (sob demanda, com cache + lock) o pipeline de resumo para o idioma."""
    model_name = SUMMARIZER_MODELS.get(language, DEFAULT_SUMMARIZER_MODEL)
    # Double-checked locking: evita dois threads baixando o mesmo modelo.
    if model_name not in _SUMMARIZERS:
        with _SUMMARIZER_LOCK:
            if model_name not in _SUMMARIZERS:
                _SUMMARIZERS[model_name] = pipeline("summarization", model=model_name)
    return _SUMMARIZERS[model_name]


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


def obter_metadados(url):
    """Retorna (titulo, duracao_segundos, video_id) sem baixar o áudio.

    Usado para validar limites de plano (ex.: duração) antes do download."""
    yt = YouTube(url)
    return yt.title, yt.length, yt.video_id


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
        atual = atual[corte + 1:]
    if atual.strip():
        partes.append(atual)
    return partes


def gerar_resumo(texto, modelo_resumo=None, size="medio", language="pt-BR"):
    """Gera um resumo respeitando o tamanho e o idioma escolhidos.

    - size: 'curto' | 'medio' | 'longo' (controla o comprimento)
    - language: define o modelo (en -> distilbart; pt-BR/es -> multilíngue)
    """
    texto = texto.strip().replace("\n", " ")
    texto = " ".join(texto.split())

    if modelo_resumo is None:
        modelo_resumo = get_summarizer(language)

    lengths = SIZE_LENGTHS.get(size, SIZE_LENGTHS["medio"])
    max_len = lengths["max_length"]
    min_len = lengths["min_length"]

    partes = _chunk_text(texto, max_chars=3000)
    resumos_parciais = []
    for parte in partes:
        saida = modelo_resumo(parte, max_length=max_len, min_length=min_len, do_sample=False)
        resumos_parciais.append(saida[0]["summary_text"].strip())
    combinado = " ".join(resumos_parciais)

    # Se houve vários pedaços, faz uma passada final para condensar.
    if len(partes) > 1:
        final_saida = modelo_resumo(combinado, max_length=max_len + 40, min_length=min_len + 20, do_sample=False)
        resumo = final_saida[0]["summary_text"]
    else:
        resumo = combinado

    resumo = resumo.strip().replace("\n", " ")
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
    resumo = gerar_resumo(transcricao, language="pt-BR")

    print("\n RESUMO: \n")
    print(resumo)
