# Documentação 

Rafael Henriques Aquino Correa e Luiz Henrique Horta Oliveira

__Objetivo: Criar projeto de Phyton para resumir vídeos do youtube.__

## Desenvolvimento
O projeto será feito em 3 etapas:

1)Baixar o vídeo ✅

2)Extrair o aúdio e converter para texto ✅

3)Criar resumo de texto ✅

## Pré-requisitos de Instalação

Para rodar este projeto, você precisa garantir que os seguintes componentes estejam instalados em seu sistema.

### 1. Software de Sistema

* **Python 3.8+**
* **FFmpeg** (Necessário para o Whisper processar áudio)
    * **Windows (via Chocolatey):** `choco install ffmpeg`
    * **macOS (via Homebrew):** `brew install ffmpeg`
    * **Linux (Ubuntu/Debian):** `sudo apt install ffmpeg`

> **Importante:** Após instalar o FFmpeg, **reinicie seu terminal ou VS Code.**

### 2. Bibliotecas Python

Você pode instalar todas as bibliotecas Python necessárias com um único comando:

```bash
pip install openai-whisper pytubefix bert-extractive-summarizer torch
