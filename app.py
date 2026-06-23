import os
import re
import uuid
import copy
import threading
from datetime import datetime, date
from io import BytesIO

from flask import (Flask, render_template, request, redirect, url_for, jsonify,
                   session, send_file, abort, flash)
import whisper
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from src.video import (baixar_audio, obter_metadados, transcrever_audio,
                       gerar_resumo, get_summarizer, is_summarizer_cached)
from src.models import (db, User, Summary, Usage, default_settings,
                        get_usage_today, increment_usage)
from src.email_utils import send_email

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-tubify-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "tubify.db"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True  # recarrega templates sem reiniciar o servidor

db.init_app(app)
csrf = CSRFProtect(app)
reset_serializer = URLSafeTimedSerializer(app.secret_key, salt="tubify-password-reset")

# ---------- Constantes / regras de negócio ----------
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "7591rafa@gmail.com")
FREE_DAILY_LIMIT = 3            # resumos por dia no plano gratuito
FREE_MAX_DURATION = 15 * 60     # 15 min (em segundos) no plano gratuito
TASK_TTL_SECONDS = 30 * 60      # tarefas mais antigas que isso são removidas da memória
YOUTUBE_RE = re.compile(
    r"^(https?://)?(www\.)?(m\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w\-]{6,}", re.I)

# Usa todos os núcleos da CPU para acelerar a inferência (sem GPU)
try:
    import torch
    torch.set_num_threads(os.cpu_count() or 1)
except Exception:
    pass

whisper_model = None
_whisper_lock = threading.Lock()
TASKS = {}
MODELS_READY = False  # vira True quando os modelos foram pré-carregados

with app.app_context():
    db.create_all()


# ---------- Modelos de IA ----------

def load_whisper():
    global whisper_model
    if whisper_model is None:
        with _whisper_lock:
            if whisper_model is None:
                print("Carregando Whisper...")
                whisper_model = whisper.load_model("base")
                print("Modelo Whisper carregado.")
    return whisper_model


def warm_up_models(language="pt-BR"):
    """Pré-carrega Whisper + modelo de resumo na inicialização do servidor.

    Na primeira vez isso baixa os modelos (~2GB p/ o multilíngue). Roda em
    background para o servidor já responder enquanto baixa."""
    global MODELS_READY
    try:
        print("Pré-carregando modelos de IA (pode baixar ~2GB na primeira vez)...")
        load_whisper()
        get_summarizer(language)
        MODELS_READY = True
        print("Modelos de IA prontos.")
    except Exception as e:
        print(f"Falha ao pré-carregar modelos: {e}")


# ---------- Helpers ----------

def get_current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


def is_valid_youtube_url(url):
    return bool(url and YOUTUBE_RE.match(url.strip()))


def purge_old_tasks():
    """Remove tarefas antigas da memória para evitar vazamento."""
    now = datetime.utcnow()
    expirados = [tid for tid, t in TASKS.items()
                 if (now - t.get("created_at", now)).total_seconds() > TASK_TTL_SECONDS]
    for tid in expirados:
        TASKS.pop(tid, None)


def can_summarize_today(user):
    """(pode, mensagem_de_erro) — checa o limite diário do plano gratuito."""
    if user is None:
        # Anônimo: limite por sessão
        today = date.today().isoformat()
        anon = session.get("anon_usage", {})
        if anon.get("day") != today:
            anon = {"day": today, "count": 0}
        if anon["count"] >= FREE_DAILY_LIMIT:
            return False, f"Limite gratuito de {FREE_DAILY_LIMIT} resumos por dia atingido. Crie uma conta ou volte amanhã."
        return True, None
    if user.is_pro:
        return True, None
    if get_usage_today(user) >= FREE_DAILY_LIMIT:
        return False, f"Você atingiu o limite de {FREE_DAILY_LIMIT} resumos por dia do plano gratuito. Faça upgrade para o Pro."
    return True, None


def register_usage(user):
    if user is None:
        today = date.today().isoformat()
        anon = session.get("anon_usage", {})
        if anon.get("day") != today:
            anon = {"day": today, "count": 0}
        anon["count"] += 1
        session["anon_usage"] = anon
    else:
        increment_usage(user)


# ---------- Processamento assíncrono ----------

def process_video_task(task_id, video_url, user_id, summary_prefs, notify_email):
    TASKS[task_id] = {"status": "processing", "progress": 0, "step": "Inicializando...",
                      "created_at": datetime.utcnow()}

    def update_progress(pct, step_name):
        overall = 0
        if step_name == "downloading":
            overall = pct * 0.3
        elif step_name == "transcribing":
            overall = 30 + (pct * 0.5)
        elif step_name == "summarizing":
            overall = 80 + (pct * 0.2)
        TASKS[task_id]["progress"] = int(overall)
        TASKS[task_id]["step"] = step_name

    try:
        size = summary_prefs.get("size", "medio")
        summary_format = summary_prefs.get("format", "topicos")
        language = summary_prefs.get("language", "pt-BR")

        # 1) Metadados + validação de limite de duração (antes de baixar)
        TASKS[task_id]["step"] = "Lendo informações do vídeo..."
        _title, duration_sec, _vid = obter_metadados(video_url)
        is_pro = False
        if user_id:
            with app.app_context():
                u = db.session.get(User, user_id)
                is_pro = bool(u and u.is_pro)
        if not is_pro and duration_sec > FREE_MAX_DURATION:
            raise Exception(
                f"No plano gratuito o vídeo pode ter no máximo {FREE_MAX_DURATION // 60} minutos. "
                f"Este tem {duration_sec // 60} min. Faça upgrade para o Pro para vídeos longos.")

        # 2) Carrega modelos (avisa se for o download inicial)
        if MODELS_READY or is_summarizer_cached(language):
            TASKS[task_id]["step"] = "Carregando modelos de IA..."
        else:
            TASKS[task_id]["step"] = ("Baixando modelo de IA pela primeira vez "
                                      "(~2GB, pode levar alguns minutos)...")
        load_whisper()
        modelo_resumo = get_summarizer(language)

        # 3) Baixar áudio
        TASKS[task_id]["step"] = "Baixando áudio..."
        audio_path, title, duration_sec, thumbnail, video_id = baixar_audio(
            video_url, progress_callback=update_progress)

        # 4) Transcrever
        TASKS[task_id]["progress"] = 30
        TASKS[task_id]["step"] = "Transcrevendo áudio (isso pode demorar)..."
        transcription = transcrever_audio(audio_path, whisper_model)

        # 5) Resumir (respeitando tamanho e idioma das preferências)
        TASKS[task_id]["progress"] = 80
        TASKS[task_id]["step"] = "Gerando resumo..."
        summary_text = gerar_resumo(transcription, modelo_resumo, size=size, language=language)

        TASKS[task_id]["progress"] = 95
        TASKS[task_id]["step"] = "Finalizando..."

        # Limpeza do arquivo de áudio
        try:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            print(f"Aviso ao deletar arquivo: {e}")

        mins, secs = divmod(duration_sec, 60)
        duration_str = f"{mins}:{secs:02d}"

        # Formato: tópicos -> divide em pontos; texto corrido -> sem pontos
        if summary_format == "topicos":
            summary_points = [s.strip() for s in summary_text.split(". ") if s.strip()]
        else:
            summary_points = []

        summary_id = None
        # Persiste no histórico do usuário + uso + notificação
        if user_id:
            with app.app_context():
                u = db.session.get(User, user_id)
                if u:
                    s = Summary(user_id=u.id, title=title, video_id=video_id,
                                video_url=video_url, duration=duration_str,
                                full_summary=summary_text, points=summary_points)
                    db.session.add(s)
                    db.session.commit()
                    summary_id = s.id
                    if notify_email and u.settings.get("notifications", {}).get("email_ready"):
                        send_email(u.email, "Seu resumo do Tubify está pronto!",
                                   f"O resumo de \"{title}\" foi gerado e já está disponível no seu painel.")

        TASKS[task_id]["result"] = {
            "video_url": video_url, "video_id": video_id, "title": title,
            "thumbnail": thumbnail, "duration": duration_str,
            "summary_points": summary_points, "full_summary": summary_text,
            "summary_id": summary_id,
        }
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["progress"] = 100

    except Exception as e:
        TASKS[task_id]["status"] = "error"
        TASKS[task_id]["error"] = str(e)


# ---------- Rotas ----------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            error = "Email ou senha inválidos."
        else:
            if email == ADMIN_EMAIL and not user.is_pro:
                user.plan = "pro"
                user.is_admin = True
                db.session.commit()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
    return render_template("login.html", error=error)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or not email or not password or not confirm:
            error = "Preencha todos os campos."
        elif password != confirm:
            error = "As senhas não coincidem."
        elif User.query.filter_by(email=email).first():
            error = "Já existe uma conta com esse email."
        else:
            settings = default_settings()
            settings["account"]["name"] = name
            settings["account"]["email"] = email
            user = User(name=name, email=email,
                        plan="pro" if email == ADMIN_EMAIL else "gratuito",
                        is_admin=(email == ADMIN_EMAIL),
                        settings=settings)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
    return render_template("cadastro.html", error=error)


@app.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar_senha():
    message = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first() if email else None
        if user:
            token = reset_serializer.dumps(user.email)
            link = url_for("redefinir_senha", token=token, _external=True)
            send_email(user.email, "Redefinição de senha - Tubify",
                       f"Para redefinir sua senha, acesse o link abaixo (válido por 1 hora):\n\n{link}")
        # Mensagem genérica (não revela se o email existe)
        message = "Se existir uma conta com esse email, enviaremos instruções para redefinir sua senha."
    return render_template("recuperar_senha.html", message=message)


@app.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    try:
        email = reset_serializer.loads(token, max_age=3600)
    except SignatureExpired:
        return render_template("redefinir_senha.html", invalid="O link expirou. Solicite um novo.")
    except BadSignature:
        return render_template("redefinir_senha.html", invalid="Link inválido.")

    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not password or password != confirm:
            error = "As senhas não coincidem."
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(password)
                db.session.commit()
                return redirect(url_for("login"))
            error = "Conta não encontrada."
    return render_template("redefinir_senha.html", token=token, error=error)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    summaries = user.summaries.order_by(Summary.created_at.desc()).all()
    return render_template("dashboard.html", summaries=summaries, active_section="resumos",
                           user=user, usage_today=get_usage_today(user),
                           daily_limit=FREE_DAILY_LIMIT)


@app.route("/favoritos")
def favoritos():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    summaries = user.summaries.filter_by(is_favorite=True).order_by(Summary.created_at.desc()).all()
    return render_template("dashboard.html", summaries=summaries, active_section="favoritos", user=user)


@app.route("/start_summary", methods=["POST"])
def start_summary():
    purge_old_tasks()
    video_url = request.form.get("video_url")
    if not video_url:
        return jsonify({"error": "URL não fornecida"}), 400
    if not is_valid_youtube_url(video_url):
        return jsonify({"error": "Informe um link válido do YouTube."}), 400

    user = get_current_user()
    pode, msg = can_summarize_today(user)
    if not pode:
        return jsonify({"error": msg}), 429

    # Preferências de resumo (do usuário logado ou padrão)
    if user:
        prefs = user.settings.get("summary", default_settings()["summary"])
        notify = True
        user_id = user.id
    else:
        prefs = session.get("settings", {}).get("summary", default_settings()["summary"])
        notify = False
        user_id = None

    register_usage(user)
    task_id = str(uuid.uuid4())
    thread = threading.Thread(target=process_video_task,
                              args=(task_id, video_url, user_id, prefs, notify))
    thread.start()
    return jsonify({"task_id": task_id})


@app.route("/progress/<task_id>")
def get_progress(task_id):
    task = TASKS.get(task_id)
    if not task:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    # Não serializa o datetime interno
    return jsonify({k: v for k, v in task.items() if k != "created_at"})


@app.route("/result/<task_id>")
def get_result(task_id):
    task = TASKS.get(task_id)
    if not task or task["status"] != "completed":
        return redirect(url_for("dashboard"))
    return render_template("summary.html", **task["result"])


@app.route("/toggle_favorite/<int:summary_id>", methods=["POST"])
def toggle_favorite(summary_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    s = db.session.get(Summary, summary_id)
    if not s or s.user_id != user.id:
        abort(404)
    s.is_favorite = not s.is_favorite
    db.session.commit()
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/delete_summary/<int:summary_id>", methods=["POST"])
def delete_summary(summary_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    s = db.session.get(Summary, summary_id)
    if not s or s.user_id != user.id:
        abort(404)
    db.session.delete(s)
    db.session.commit()
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return "Biblioteca de PDF não está instalada. Execute 'pip install reportlab'.", 500

    title = request.form.get("title", "Resumo Tubify")
    duration = request.form.get("duration", "")
    full_summary = request.form.get("full_summary", "")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, title[:90])
    y -= 25
    if duration:
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Duração original: {duration}")
        y -= 20
    pdf.setFont("Helvetica", 11)
    text = pdf.beginText(50, y)
    # Quebra simples de linhas longas
    for raw in full_summary.splitlines() or [full_summary]:
        while len(raw) > 95:
            text.textLine(raw[:95])
            raw = raw[95:]
        text.textLine(raw)
    pdf.drawText(text)
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="resumo_tubify.pdf",
                     mimetype="application/pdf")


@app.route("/summary", methods=["POST", "GET"])
def summary():
    # Fallback sem-JS: o fluxo real é assíncrono via /start_summary
    return redirect(url_for("home"))


@app.route("/plans")
def plans():
    return render_template("plans.html")


@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    user = get_current_user()
    # Base de configurações: do usuário (se logado) ou da sessão/padrão
    if user:
        settings = copy.deepcopy(user.settings)
    else:
        settings = session.get("settings") or default_settings()
    settings["plan"]["current"] = "pro" if (user and user.is_pro) else "gratuito"

    active_tab = request.args.get("tab", "conta")
    success_message = None

    if request.method == "POST":
        section = request.form.get("section", "conta")
        active_tab = section

        if section == "conta":
            settings["account"]["name"] = request.form.get("name", "").strip()
            settings["account"]["email"] = request.form.get("email", "").strip()
            success_message = "Suas informações de conta foram atualizadas com sucesso."
        elif section == "resumo":
            settings["summary"]["size"] = request.form.get("summary_size", "medio")
            settings["summary"]["format"] = request.form.get("summary_format", "topicos")
            settings["summary"]["language"] = request.form.get("summary_language", "pt-BR")
            success_message = "Suas preferências de resumo foram salvas com sucesso."
        elif section == "aparencia":
            settings["appearance"]["theme"] = request.form.get("theme", "claro")
            settings["appearance"]["font_size"] = request.form.get("font_size", "media")
            settings["appearance"]["high_contrast"] = bool(request.form.get("high_contrast"))
            settings["appearance"]["reduce_animations"] = bool(request.form.get("reduce_animations"))
            success_message = "Suas preferências de aparência foram atualizadas."
        elif section == "notificacoes":
            settings["notifications"]["email_ready"] = bool(request.form.get("email_ready"))
            settings["notifications"]["daily_limit_alerts"] = bool(request.form.get("daily_limit_alerts"))
            settings["notifications"]["news"] = bool(request.form.get("news"))
            success_message = "Suas preferências de notificações foram salvas."
        elif section == "plano":
            if not user:
                return redirect(url_for("login"))
            user.plan = "pro"
            db.session.commit()
            settings["plan"]["current"] = "pro"
            success_message = "Plano Pro ativado! Agora você tem resumos ilimitados."
        elif section == "privacidade":
            if not user:
                return redirect(url_for("login"))
            action = request.form.get("action")
            if action == "apagar_historico":
                user.summaries.delete()
                db.session.commit()
                success_message = "Seu histórico de resumos foi apagado."
            elif action == "excluir_conta":
                db.session.delete(user)
                db.session.commit()
                session.clear()
                return redirect(url_for("home"))

        # Persiste
        if user and section in ("conta", "resumo", "aparencia", "notificacoes"):
            user.settings = settings
            db.session.commit()
        elif not user:
            session["settings"] = settings

    return render_template("configuracoes.html",
                           account=settings["account"], summary=settings["summary"],
                           appearance=settings["appearance"], notifications=settings["notifications"],
                           plan=settings["plan"], active_tab=active_tab,
                           success_message=success_message)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    # Pré-carrega os modelos em background (a não ser que TUBIFY_SKIP_WARMUP=1)
    if os.environ.get("TUBIFY_SKIP_WARMUP", "0") != "1":
        threading.Thread(target=warm_up_models, daemon=True).start()
    print(f"Iniciando servidor Flask (debug={debug})...")
    app.run(debug=debug, use_reloader=False)
