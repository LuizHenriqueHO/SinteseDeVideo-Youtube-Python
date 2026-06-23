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
pip install -r requirements.txt
```

### 3. Front-end (CSS)

O CSS é gerado pelo **Tailwind CLI** (não usamos mais o CDN). É necessário **Node.js 18+**.

```bash
npm install        # instala o Tailwind (uma vez)
npm run build:css  # gera static/css/app.css (minificado)
npm run watch:css  # opcional: recompila ao editar os templates
```

> O arquivo compilado fica em `static/css/app.css` e já é referenciado pelo `base.html`.

## Como rodar

```bash
python app.py
```

Acesse **http://127.0.0.1:5000**. Se o comando `python` apontar para a Microsoft Store no Windows, use `py app.py`.
