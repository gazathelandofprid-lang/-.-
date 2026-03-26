from flask import Flask, request, jsonify, render_template, session, redirect, url_template
from flask_bcrypt import Bcrypt
from models import db, Admin, BotConfig, TelegramUser, SystemStats
import requests
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-production-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)

# --- متغيرات نظام الإذاعة (Broadcast State) ---
broadcast_status = {"status": "idle", "total": 0, "sent": 0, "failed": 0}

# --- حماية المسارات (Decorator) ---
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# --- دوال مساعدة لتيليجرام ---
def tg_api(method, token, payload=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    res = requests.post(url, json=payload)
    return res.json()

# --- إنشاء أول أدمن تلقائياً ---
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        new_admin = Admin(username='admin', password_hash=hashed_pw)
        db.session.add(new_admin)
        db.session.add(SystemStats(messages_sent=0))
        db.session.commit()

# ================= ROUTES =================

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.json
    code = data.get('code')
    if code == '200915':
        session['logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "الكود السري غير صحيح"}), 401

@app.route('/api/bot-login', methods=['POST'])
@login_required
def bot_login():
    token = request.json.get('token')
    res = tg_api("getMe", token)
    
    if res.get('ok'):
        bot_data = res['result']
        bot_db = BotConfig.query.first()
        if not bot_db:
            bot_db = BotConfig(token=token, bot_id=str(bot_data['id']))
            db.session.add(bot_db)
        else:
            bot_db.token = token
            bot_db.bot_id = str(bot_data['id'])
        
        bot_db.first_name = bot_data.get('first_name', '')
        bot_db.username = bot_data.get('username', '')
        db.session.commit()
        return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "التوكن غير صالح"}), 400

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect('/')
    bot = BotConfig.query.first()
    users_count = TelegramUser.query.count()
    stats = SystemStats.query.first()
    return render_template('dashboard.html', bot=bot, users_count=users_count, msgs=stats.messages_sent if stats else 0)

@app.route('/api/update-bot', methods=['POST'])
@login_required
def update_bot():
    data = request.json
    bot = BotConfig.query.first()
    if not bot: return jsonify({"error": "لا يوجد بوت"}), 400
    
    if 'name' in data:
        tg_api("setMyName", bot.token, {"name": data['name']})
    if 'description' in data:
        tg_api("setMyDescription", bot.token, {"description": data['description']})
        
    return jsonify({"success": True})

@app.route('/api/stop-bot', methods=['POST'])
@login_required
def stop_bot():
    BotConfig.query.delete()
    db.session.commit()
    return jsonify({"success": True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- نظام الإذاعة الجماعية (Broadcast) ---
def broadcast_worker(token, text, users):
    global broadcast_status
    broadcast_status = {"status": "running", "total": len(users), "sent": 0, "failed": 0}
    
    with app.app_context():
        stats = SystemStats.query.first()
        for u in users:
            res = tg_api("sendMessage", token, {"chat_id": u.chat_id, "text": text, "parse_mode": "Markdown"})
            if res.get('ok'):
                broadcast_status["sent"] += 1
                stats.messages_sent += 1
            else:
                broadcast_status["failed"] += 1
            db.session.commit()
            time.sleep(0.05) # حماية من حظر تيليجرام (Limits)
            
    broadcast_status["status"] = "finished"

@app.route('/api/broadcast', methods=['POST'])
@login_required
def broadcast():
    global broadcast_status
    if broadcast_status["status"] == "running":
        return jsonify({"error": "هناك إذاعة تعمل حالياً!"}), 400
        
    data = request.json
    text = data.get('text')
    bot = BotConfig.query.first()
    users = TelegramUser.query.all()
    
    if not bot or not text or not users:
        return jsonify({"error": "بيانات غير مكتملة"}), 400
        
    thread = threading.Thread(target=broadcast_worker, args=(bot.token, text, users))
    thread.start()
    return jsonify({"success": True})

@app.route('/api/broadcast/status')
@login_required
def broadcast_progress():
    return jsonify(broadcast_status)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
