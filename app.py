from flask import Flask, render_template, request, redirect, url_for, jsonify
import time
import os
import whisper
from summarizer import Summarizer
import threading
import uuid

# Import functions from Main.py
from Main import baixar_audio, transcrever_audio, gerar_resumo

app = Flask(__name__)

# Global variables for models
whisper_model = None
summarizer_model = None
TASKS = {}

def load_models():
    global whisper_model, summarizer_model
    if whisper_model is None or summarizer_model is None:
        print("Inicializando modelos de IA sob demanda...")
        try:
            if whisper_model is None:
                print("Carregando Whisper...")
                whisper_model = whisper.load_model("base")
                print("Modelo Whisper carregado.")
            
            if summarizer_model is None:
                print("Carregando Summarizer...")
                summarizer_model = Summarizer()
                print("Modelo Summarizer carregado.")
            
            return True
        except Exception as e:
            print(f"Erro ao carregar modelos: {e}")
            return False
    return True

def process_video_task(task_id, video_url):
    TASKS[task_id] = {'status': 'processing', 'progress': 0, 'step': 'Inicializando...'}
    
    def update_progress(pct, step_name):
        # Map raw percentage to overall progress
        # Download: 0-30%
        # Transcribe: 30-80%
        # Summarize: 80-100%
        
        overall = 0
        if step_name == 'downloading':
            overall = pct * 0.3
        elif step_name == 'transcribing':
            overall = 30 + (pct * 0.5)
        elif step_name == 'summarizing':
            overall = 80 + (pct * 0.2)
            
        TASKS[task_id]['progress'] = int(overall)
        TASKS[task_id]['step'] = step_name

    try:
        # Ensure models are loaded (count this as progress if taking time)
        TASKS[task_id]['step'] = 'Carregando modelos de IA...'
        if not load_models():
             raise Exception("Falha ao carregar modelos de IA")
        
        TASKS[task_id]['step'] = 'Baixando áudio...'
        # Pass update_progress to functions
        audio_path, title, duration_sec, thumbnail, video_id = baixar_audio(video_url, progress_callback=update_progress)
        
        TASKS[task_id]['progress'] = 30
        TASKS[task_id]['step'] = 'Transcrevendo áudio (isso pode demorar)...'
        
        # Whisper transcription
        transcription = transcrever_audio(audio_path, whisper_model)
        TASKS[task_id]['progress'] = 80
        TASKS[task_id]['step'] = 'Gerando resumo...'
        
        summary_text = gerar_resumo(transcription, summarizer_model)
        TASKS[task_id]['progress'] = 95
        TASKS[task_id]['step'] = 'Finalizando...'

        # Cleanup
        try:
            if os.path.exists(audio_path):
                 os.remove(audio_path)
        except Exception as e:
            print(f"Aviso ao deletar arquivo: {e}")
             
        # Format result
        mins, secs = divmod(duration_sec, 60)
        duration_str = f"{mins}:{secs:02d}"
        summary_points = [s.strip() for s in summary_text.split('. ') if s.strip()]
        
        TASKS[task_id]['result'] = {
            'video_url': video_url,
            'video_id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration_str,
            'summary_points': summary_points,
            'full_summary': summary_text
        }
        TASKS[task_id]['status'] = 'completed'
        TASKS[task_id]['progress'] = 100
        
    except Exception as e:
        TASKS[task_id]['status'] = 'error'
        TASKS[task_id]['error'] = str(e)

# Mock data for dashboard (keep this for now)
MOCK_SUMMARIES = [
    {"id": 1, "title": "Introdução ao Machine Learning", "date": "15/01/2026", "duration": "10:05", "thumbnail": "https://img.youtube.com/vi/KNAWp2S3w94/hqdefault.jpg"},
    {"id": 2, "title": "História da Arte Moderna", "date": "14/01/2026", "duration": "45:20", "thumbnail": "https://img.youtube.com/vi/4Wp4a-G3hO8/hqdefault.jpg"},
    {"id": 3, "title": "Como investir em Ações", "date": "10/01/2026", "duration": "12:30", "thumbnail": "https://img.youtube.com/vi/5qap5aO4i9A/hqdefault.jpg"}
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', summaries=MOCK_SUMMARIES)

@app.route('/start_summary', methods=['POST'])
def start_summary():
    print("Recebida requisição de start_summary")
    try:
        video_url = request.form.get('video_url')
        print(f"URL recebida: {video_url}")
        
        if not video_url:
            print("Erro: URL não fornecida")
            return jsonify({'error': 'URL não fornecida'}), 400

        task_id = str(uuid.uuid4())
        print(f"Iniciando tarefa {task_id}")
        
        thread = threading.Thread(target=process_video_task, args=(task_id, video_url))
        thread.start()
        
        return jsonify({'task_id': task_id})
    except Exception as e:
        print(f"Erro no endpoint start_summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    task = TASKS.get(task_id)
    if not task:
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    return jsonify(task)

@app.route('/result/<task_id>')
def get_result(task_id):
    task = TASKS.get(task_id)
    if not task or task['status'] != 'completed':
        return redirect(url_for('dashboard'))
    
    result = task['result']
    # Clean up task from memory after retrieving result (optional, or keep for history)
    # del TASKS[task_id]
    
    return render_template('summary.html', **result)

@app.route('/summary', methods=['POST', 'GET'])
def summary():
    # Legacy synchronous route - redirect to dashboard if accessed directly or handle simple post
    if request.method == 'POST':
        # If someone posts to /summary, redirect to dashboard to use the async flow
        # Or we could just start the task here and render a loading page.
        # Let's keep the old logic for now as fallback or remove it?
        # Better to just use the new async flow.
        return redirect(url_for('dashboard'))
            
    return redirect(url_for('home'))

@app.route('/plans')
def plans():
    return render_template('plans.html')

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    try:
        app.run(debug=True, use_reloader=False)
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        input("Pressione Enter para sair...") 
