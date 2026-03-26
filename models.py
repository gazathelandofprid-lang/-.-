from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class BotConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    bot_id = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100))
    username = db.Column(db.String(100))

class TelegramUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(100), unique=True, nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    messages_sent = db.Column(db.Integer, default=0)
