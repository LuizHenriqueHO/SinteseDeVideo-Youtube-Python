"""Modelos de banco de dados (SQLAlchemy) e helpers de persistência do Tubify."""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def default_settings():
    """Configurações iniciais de um usuário."""
    return {
        "account": {"name": "", "email": ""},
        "summary": {"size": "medio", "format": "topicos", "language": "pt-BR"},
        "appearance": {"theme": "claro", "font_size": "media", "high_contrast": False, "reduce_animations": False},
        "notifications": {"email_ready": True, "daily_limit_alerts": True, "news": False},
        "plan": {"current": "gratuito"},
    }


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(20), nullable=False, default="gratuito")
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    settings = db.Column(db.JSON, nullable=False, default=default_settings)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    summaries = db.relationship("Summary", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    usages = db.relationship("Usage", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_pro(self):
        return self.plan == "pro"


class Summary(db.Model):
    __tablename__ = "summaries"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(500), default="")
    video_id = db.Column(db.String(50), default="")
    video_url = db.Column(db.String(500), default="")
    duration = db.Column(db.String(20), default="")
    full_summary = db.Column(db.Text, default="")
    points = db.Column(db.JSON, default=list)
    is_favorite = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Usage(db.Model):
    """Contador diário de resumos gerados por usuário (para limites de plano)."""
    __tablename__ = "usage"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    day = db.Column(db.String(10), nullable=False)  # 'YYYY-MM-DD'
    count = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (db.UniqueConstraint("user_id", "day", name="uq_user_day"),)


# ---------- Helpers ----------

def get_usage_today(user):
    today = date.today().isoformat()
    usage = Usage.query.filter_by(user_id=user.id, day=today).first()
    return usage.count if usage else 0


def increment_usage(user):
    today = date.today().isoformat()
    usage = Usage.query.filter_by(user_id=user.id, day=today).first()
    if usage is None:
        usage = Usage(user_id=user.id, day=today, count=0)
        db.session.add(usage)
    usage.count += 1
    db.session.commit()
    return usage.count
