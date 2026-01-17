from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file
import time
import os
from io import BytesIO
import whisper
from summarizer import Summarizer
from transformers import pipeline
import threading
import uuid
import copy
from werkzeug.security import generate_password_hash, check_password_hash

# Import functions from Main.py
from Main import baixar_audio, transcrever_audio, gerar_resumo

app = Flask(__name__)
app.secret_key = "tubify-secret"

# Global variables for models
whisper_model = None
summarizer_model = None
TASKS = {}
USERS = {}
ADMIN_EMAIL = "7591rafa@gmail.com"

DEFAULT_SETTINGS = {
    "account": {
        "name": "",
        "email": ""
    },
    "summary": {
        "size": "medio",
        "format": "topicos",
        "language": "pt-BR"
    },
    "appearance": {
        "theme": "claro",
        "font_size": "media",
        "high_contrast": False,
        "reduce_animations": False
    },
    "notifications": {
        "email_ready": True,
        "daily_limit_alerts": True,
        "news": False
    },
    "plan": {
        "current": "gratuito"
    }
}

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
                print("Carregando modelo de resumo...")
                summarizer_model = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
                print("Modelo de resumo carregado.")
            
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


def get_current_user():
    email = session.get('user_email')
    if not email:
        return None
    return USERS.get(email)


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}

# Mock data for dashboard (atualizado para lista vazia)
MOCK_SUMMARIES = []


@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    settings = session.get('settings')
    if not settings:
        settings = copy.deepcopy(DEFAULT_SETTINGS)
    user = get_current_user()
    if user and user.get("plan") == "pro":
        settings["plan"]["current"] = "pro"
    active_tab = request.args.get('tab', 'conta')
    success_message = None
    if request.method == 'POST':
        section = request.form.get('section')
        if not section:
            section = 'conta'
        active_tab = section
        if section == 'conta':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            settings["account"]["name"] = name
            settings["account"]["email"] = email
            success_message = "Suas informações de conta foram atualizadas com sucesso."
        elif section == 'resumo':
            size = request.form.get('summary_size', 'medio')
            summary_format = request.form.get('summary_format', 'topicos')
            language = request.form.get('summary_language', 'pt-BR')
            settings["summary"]["size"] = size
            settings["summary"]["format"] = summary_format
            settings["summary"]["language"] = language
            success_message = "Suas preferências de resumo foram salvas com sucesso."
        elif section == 'aparencia':
            theme = request.form.get('theme', 'claro')
            font_size = request.form.get('font_size', 'media')
            high_contrast = bool(request.form.get('high_contrast'))
            reduce_animations = bool(request.form.get('reduce_animations'))
            settings["appearance"]["theme"] = theme
            settings["appearance"]["font_size"] = font_size
            settings["appearance"]["high_contrast"] = high_contrast
            settings["appearance"]["reduce_animations"] = reduce_animations
            success_message = "Suas preferências de aparência foram atualizadas."
        elif section == 'notificacoes':
            email_ready = bool(request.form.get('email_ready'))
            daily_limit_alerts = bool(request.form.get('daily_limit_alerts'))
            news = bool(request.form.get('news'))
            settings["notifications"]["email_ready"] = email_ready
            settings["notifications"]["daily_limit_alerts"] = daily_limit_alerts
            settings["notifications"]["news"] = news
            success_message = "Suas preferências de notificações foram salvas."
        elif section == 'plano':
            success_message = "Seu plano foi atualizado com sucesso."
        elif section == 'privacidade':
            action = request.form.get('action')
            if action == 'apagar_historico':
                success_message = "Seu histórico de resumos foi apagado."
            elif action == 'excluir_conta':
                success_message = "Sua conta foi excluída com sucesso."
        session['settings'] = settings
    return render_template(
        'configuracoes.html',
        account=settings["account"],
        summary=settings["summary"],
        appearance=settings["appearance"],
        notifications=settings["notifications"],
        plan=settings["plan"],
        active_tab=active_tab,
        success_message=success_message
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = USERS.get(email)
        if not user or not check_password_hash(user['password_hash'], password):
            error = "Email ou senha inválidos."
        else:
            if email == ADMIN_EMAIL:
                user['plan'] = 'pro'
                user['is_admin'] = True
            session['user_email'] = email
            return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not name or not email or not password or not confirm:
            error = "Preencha todos os campos."
        elif password != confirm:
            error = "As senhas não coincidem."
        elif email in USERS:
            error = "Já existe uma conta com esse email."
        else:
            plan = "pro" if email == ADMIN_EMAIL else "gratuito"
            is_admin = email == ADMIN_EMAIL
            USERS[email] = {
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password),
                "plan": plan,
                "is_admin": is_admin
            }
            session['user_email'] = email
            return redirect(url_for('dashboard'))
    return render_template('cadastro.html', error=error)


@app.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    message = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if email:
            message = "Se existir uma conta com esse email, enviaremos instruções para redefinir sua senha."
        else:
            message = "Informe um email válido."
    return render_template('recuperar_senha.html', message=message)


@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template('dashboard.html', summaries=MOCK_SUMMARIES, active_section='resumos', user=user)


@app.route('/favoritos')
def favoritos():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template('dashboard.html', summaries=MOCK_SUMMARIES, active_section='favoritos', user=user)

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


@app.route('/save_summary', methods=['POST'])
def save_summary():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    summaries = session.get('summaries', [])
    summaries.append({
        "title": request.form.get('title', ''),
        "video_id": request.form.get('video_id', ''),
        "duration": request.form.get('duration', ''),
        "full_summary": request.form.get('full_summary', '')
    })
    session['summaries'] = summaries
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return "Biblioteca de PDF não está instalada. Execute 'pip install reportlab' para habilitar exportação em PDF.", 500

    title = request.form.get('title', 'Resumo Tubify')
    duration = request.form.get('duration', '')
    full_summary = request.form.get('full_summary', '')

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, title)
    y -= 25

    if duration:
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Duração original: {duration}")
        y -= 20

    pdf.setFont("Helvetica", 11)
    text = pdf.beginText(50, y)
    for line in full_summary.splitlines():
        text.textLine(line)
    pdf.drawText(text)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="resumo_tubify.pdf",
        mimetype="application/pdf"
    )

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
    app.run(debug=True, use_reloader=False)
