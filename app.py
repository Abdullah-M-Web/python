import os
import sqlite3
import requests
from flask import Flask, render_template, request, url_for, redirect, session, flash

app = Flask(__name__)
app.secret_key = 'smart_aid_platform_2026_final'

# إعداد مسارات قاعدة البيانات
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'aid_requests.db')

# --- وظائف قاعدة البيانات ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # جدول طلبات المساعدة
    conn.execute('''CREATE TABLE IF NOT EXISTS requests 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   full_name TEXT NOT NULL, 
                   phone TEXT NOT NULL, 
                   aid_type TEXT, 
                   status TEXT DEFAULT 'قيد الانتظار', 
                   date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # جدول إحصائيات الزيارات
    conn.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, views INTEGER)''')
    conn.execute('INSERT OR IGNORE INTO stats (id, views) VALUES (1, 0)')
    conn.commit()
    conn.close()

init_db()

# --- المسارات (Routes) ---

@app.route('/')
def home():
    conn = get_db_connection()
    conn.execute('UPDATE stats SET views = views + 1 WHERE id = 1')
    conn.commit()
    conn.close()
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('full_name')
        phone = request.form.get('phone')
        aid_type = request.form.get('aid_type')
        if name and phone:
            conn = get_db_connection()
            conn.execute('INSERT INTO requests (full_name, phone, aid_type) VALUES (?, ?, ?)', 
                         (name, phone, aid_type))
            conn.commit()
            conn.close()
            return render_template('registration.html', success=True)
    return render_template('registration.html')

@app.route('/economy')
def economy():
    try:
        # جلب أسعار عملات حقيقية
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        data = response.json()
        rates = {
            'EUR': round(data['rates'].get('EUR', 0.92), 2),
            'JOD': round(data['rates'].get('JOD', 0.71), 2),
            'TRY': round(data['rates'].get('TRY', 32.50), 2),
            'EGP': round(data['rates'].get('EGP', 47.00), 2)
        }
    except:
        rates = {'EUR': 0.92, 'JOD': 0.71, 'TRY': 32.50, 'EGP': 47.00}
    return render_template('economy.html', rates=rates)

@app.route('/weather')
def weather():
    # بيانات الطقس (يمكنك لاحقاً ربطها بـ API مفتاح حقيقي)
    # مدينة الافتراضية: غزة
    weather_data = {
        'city': "فلسطين - غزة",
        'temp': 24,
        'desc': "سماء صافية",
        'icon': "01d",
        'humidity': 60,
        'wind': 10
    }
    return render_template('weather.html', weather=weather_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == 'admin2026': 
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        flash('كلمة المرور غير صحيحة')
    return render_template('login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    conn = get_db_connection()
    reqs = conn.execute('SELECT * FROM requests ORDER BY id DESC').fetchall()
    views = conn.execute('SELECT views FROM stats WHERE id = 1').fetchone()[0]
    conn.close()
    return render_template('admin.html', requests=reqs, views=views)

@app.route('/delete/<int:id>')
def delete_request(id):
    if session.get('logged_in'):
        conn = get_db_connection()
        conn.execute('DELETE FROM requests WHERE id = ?', (id,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

# --- صفحات إضافية ثابتة ---
@app.route('/jobs')
def jobs(): return render_template('jobs.html')

@app.route('/education')
def education(): return render_template('education.html')

@app.route('/article')
def article(): return render_template('article.html')

@app.route('/privacy')
def privacy(): return render_template('privacy.html')

if __name__ == '__main__':
    app.run(debug=True)