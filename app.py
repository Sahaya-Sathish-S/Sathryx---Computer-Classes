import os, json, secrets, requests
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','false').lower()=='true', MAX_CONTENT_LENGTH=2*1024*1024)

import hmac

ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL",
    "sahayasathish60@gmail.com"
).strip().lower()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Sathryx@2026")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not ADMIN_PASSWORD:
            flash("Admin password is not configured.")
            return render_template("admin_login.html")

        if (
            hmac.compare_digest(email, ADMIN_EMAIL)
            and hmac.compare_digest(password, ADMIN_PASSWORD)
        ):
            session.clear()
            session["admin_logged_in"] = True
            session["admin_email"] = ADMIN_EMAIL

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("admin_login.html")

SUPABASE_URL = os.getenv('SUPABASE_URL','').rstrip('/')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY','')

class StoreError(Exception): pass

def sb_headers():
    if not SUPABASE_URL or not SUPABASE_KEY: raise StoreError('Supabase is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to .env.')
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")    return {'apikey':SUPABASE_KEY,'Authorization':f'Bearer {SUPABASE_KEY}','Content-Type':'application/json','Prefer':'return=representation'}

def sb_request(method, table, *, params=None, payload=None):
    r=requests.request(method, f'{SUPABASE_URL}/rest/v1/{table}', headers=sb_headers(), params=params, json=payload, timeout=20)
    if not r.ok: raise StoreError(f'Database request failed ({r.status_code}): {r.text[:350]}')
    return r.json() if r.text else []

def admin_required(fn):    @wraps(fn)
    def inner(*args, **kwargs):
        if session.get("admin_logged_in") is not True:
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return inner

@app.get('/')
def home(): return render_template('index.html')

@app.post('/api/register')
def register():
    d=request.get_json(silent=True) or request.form
    name=str(d.get('name','')).strip(); email=str(d.get('email','')).strip().lower(); phone=str(d.get('phone','')).strip(); standard=str(d.get('standard','')).strip(); school=str(d.get('school','')).strip()
    if not all([name,email,phone,standard,school]): return jsonify(ok=False,message='Please complete every field.'),400
    if len(name)>100 or len(email)>254 or len(phone)>20 or len(school)>180: return jsonify(ok=False,message='One or more fields are too long.'),400
    if '@' not in email or len(phone)<8: return jsonify(ok=False,message='Please enter a valid email and phone number.'),400
    payload={'name':name,'email':email,'phone':phone,'standard':standard,'school':school,'status':'registered','created_at':datetime.now(timezone.utc).isoformat()}
    try:
        rows=sb_request('POST','students',payload=payload)
        send_email('New SATHRYX class registration', f'<h2>New student registration</h2><p><b>Name:</b> {name}</p><p><b>Email:</b> {email}</p><p><b>Phone:</b> {phone}</p><p><b>Standard:</b> {standard}</p><p><b>School:</b> {school}</p>', ADMIN_EMAIL)
        return jsonify(ok=True,message='Registration received! We will contact you with the next steps.',student=rows[0] if rows else {})
    except StoreError as e: return jsonify(ok=False,message=str(e)),503

@app.post('/api/chat')
def chat():
    d=request.get_json(silent=True) or {}; msg=str(d.get('message','')).strip()[:1200]; lang=d.get('language','English')
    if not msg: return jsonify(reply='Please type your question.')
    system=f'''You are the friendly SATHRYX Computer Classes assistant. Reply in {lang}. Be concise, warm, and accurate. Course facts: Christmas Holiday Special, 1-31 December 2026, daily 6:00 PM-8:00 PM, ₹250, students 1st to 12th standard, practical/activity-based. Venue: 12/592, Sangu Nagar, Vadakkankulam, Tirunelveli. Modules: Computer Fundamentals days 1-4; Python days 5-13; HTML & CSS days 14-20; JavaScript days 21-26; Creative Project Development days 27-29; Final Assessment & Achievement day 30. Includes 11 mini projects plus a final project, practical challenges and course completion certificate. Registration asks name, email, phone, standard and school. SATHRYX motto: Learn, Create, Grow; help people learn technology and create useful digital experiences. Do not invent fees, guarantees, or policies. If asked something outside this course, say you can help with course-related questions.'''
    key=os.getenv('OPENROUTER_API_KEY' , ''); gem=os.getenv('GEMINI_API_KEY')
    try:
        if key:
            r=requests.post('https://openrouter.ai/api/v1/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json','HTTP-Referer':os.getenv('SITE_URL','http://localhost:5000'),'X-Title':'SATHRYX Classes Assistant'},json={'model':os.getenv('OPENROUTER_MODEL','openai/gpt-4o-mini'),'messages':[{'role':'system','content':system},{'role':'user','content':msg}]},timeout=30)
            r.raise_for_status(); answer=r.json()['choices'][0]['message']['content']
        elif gem:
            r=requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gem}',json={'systemInstruction':{'parts':[{'text':system}]},'contents':[{'parts':[{'text':msg}]}]},timeout=30)
            r.raise_for_status(); answer=r.json()['candidates'][0]['content']['parts'][0]['text']
        else: answer=f"I can help with SATHRYX classes! The course runs 1–31 December, 6–8 PM, costs ₹250 and is open to 1st–12th standard students. Ask me about the syllabus, registration or venue."
        return jsonify(reply=answer)
    except Exception: return jsonify(reply='I am having trouble connecting right now. Please try again in a moment or contact the SATHRYX team.')

def send_email(subject, html, to):
    key=os.getenv('RESEND_API_KEY', '')
    if not key: return False
    try:
        r=requests.post('https://api.resend.com/emails',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'from':os.getenv('EMAIL_FROM','SATHRYX Classes <onboarding@resend.dev>'),'to':[to],'subject':subject,'html':html},timeout=15)
        r.raise_for_status(); return True
    except Exception as e:
        app.logger.warning('Email send failed: %s',e); return False

@app.post('/admin/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.get("/admin")
@admin_required
def dashboard():
    try:
        students = sb_request(
            "GET",
            "students",
            params={
                "select": "*",
                "order": "created_at.desc"
            }
        )

        return render_template(
            "dashboard.html",
            students=students,
            error=None
        )

    except StoreError as e:
        return render_template(
            "dashboard.html",
            students=[],
            error=str(e)
        )
@app.get('/admin/student/<int:student_id>')
@admin_required
def student_detail(student_id):
    try:
        student=sb_request('GET','students',params={'id':f'eq.{student_id}','select':'*'})
        if not student: return 'Student not found',404
        logs=sb_request('GET','student_records',params={'student_id':f'eq.{student_id}','select':'*','order':'record_date.desc,created_at.desc'})
        return render_template('student.html',student=student[0],logs=logs,error=None)
    except StoreError as e: return render_template('student.html',student={'id':student_id,'name':'Student'},logs=[],error=str(e))

@app.post('/admin/student/<int:student_id>/record')
@admin_required
def add_record(student_id):
    d=request.form
    payload={'student_id':student_id,'record_date':d.get('record_date') or datetime.now().date().isoformat(),'record_type':d.get('record_type','progress'),'attendance':d.get('attendance') or None,'topic':d.get('topic','').strip(),'activities':d.get('activities','').strip(),'attempts':d.get('attempts','').strip(),'learning_interest':d.get('learning_interest','').strip(),'assessment_score':int(d['assessment_score']) if d.get('assessment_score','').isdigit() else None,'trainer_remarks':d.get('trainer_remarks','').strip(),'next_steps':d.get('next_steps','').strip()}
    try: sb_request('POST','student_records',payload=payload); flash('Student record saved.','success')
    except StoreError as e: flash(str(e),'error')
    return redirect(url_for('student_detail',student_id=student_id))

@app.post('/admin/student/<int:student_id>/status')
@admin_required
def update_status(student_id):
    try: sb_request('PATCH','students',params={'id':f'eq.{student_id}'},payload={'status':request.form.get('status','registered')}); flash('Status updated.','success')
    except StoreError as e: flash(str(e),'error')
    return redirect(url_for('student_detail',student_id=student_id))

@app.get('/health')
def health(): return jsonify(status='ok',supabase_configured=bool(SUPABASE_URL and SUPABASE_KEY),ai_configured=bool(os.getenv('OPENROUTER_API_KEY') or os.getenv('GEMINI_API_KEY')))

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=os.getenv('FLASK_DEBUG','false').lower()=='true')
