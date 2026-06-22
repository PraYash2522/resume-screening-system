from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_required, current_user
from flask_mail import Mail
import os, json
from ai_matcher import ResumeJobMatcher
from database import db, User, ScanHistory
from auth import auth_bp, mail

app = Flask(__name__)

# ── Core config ───────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ── Gmail config ──────────────────────────────────────────────────────────────
# Set these as environment variables — never hardcode credentials!
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')   # your Gmail
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')   # your App Password
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

# ── Init extensions ───────────────────────────────────────────────────────────
db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(auth_bp)
os.makedirs('uploads', exist_ok=True)
matcher = ResumeJobMatcher()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    recent_scans = ScanHistory.query.filter_by(user_id=current_user.id).order_by(ScanHistory.scan_date.desc()).limit(5).all()
    total_scans  = ScanHistory.query.filter_by(user_id=current_user.id).count()
    scans        = ScanHistory.query.filter_by(user_id=current_user.id).all()
    avg_score    = sum([s.match_score for s in scans]) / len(scans) if scans else 0
    return render_template('dashboard.html',
                           recent_scans=recent_scans,
                           total_scans=total_scans,
                           avg_score=round(avg_score, 2))

@app.route('/analysis/<int:scan_id>')
@login_required
def analysis_by_id(scan_id):
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        flash('Scan not found.', 'error')
        return redirect(url_for('dashboard'))
    analysis_data = {
        'overall_score': scan.match_score, 'skills_score': scan.match_score,
        'experience_score': 70.0, 'education_score': 60.0, 'keyword_density': 65.0,
        'matched_skills': ['Python', 'Django', 'Flask', 'JavaScript', 'SQL'],
        'missing_skills': ['React', 'AWS', 'Docker'],
        'strengths': ['Good technical skills', 'Relevant experience', 'Strong educational background'],
        'suggestions': ['Add more quantifiable achievements', 'Update certifications', 'Include project links']
    }
    return render_template('analysis.html', analysis_json=json.dumps(analysis_data))

@app.route('/screening')
@login_required
def screening():
    return render_template('index.html')

@app.route('/analysis')
@login_required
def analysis():
    if 'last_analysis' not in session:
        flash('No analysis data found. Please scan a resume first.', 'error')
        return redirect(url_for('screening'))
    return render_template('analysis.html', analysis_json=session['last_analysis'])

@app.route('/upload', methods=['POST'])
@login_required
def upload_files():
    try:
        resume_file     = request.files.get('resume')
        job_description = request.form.get('job_description', '')

        if not resume_file or not job_description:
            return jsonify({'success': False, 'message': 'Please provide both resume and job description'})

        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
        resume_file.save(resume_path)
        resume_text = matcher.extract_text_from_pdf(resume_path)

        if not resume_text or len(resume_text) < 50:
            return jsonify({'success': False, 'message': 'Could not extract text from PDF. Please use a text-based PDF.'})

        analysis = matcher.detailed_analysis(resume_text, job_description)
        score    = analysis['overall_score']
        quality  = "Excellent Match" if score >= 70 else "Good Match" if score >= 50 else "Moderate Match" if score >= 30 else "Low Match"

        job_title = job_description.split('\n')[0][:200] if job_description else "Job Analysis"
        new_scan  = ScanHistory(user_id=current_user.id, resume_name=resume_file.filename,
                                job_title=job_title, match_score=score)
        db.session.add(new_scan)
        db.session.commit()

        session['last_analysis'] = json.dumps(analysis)

        return jsonify({'success': True, 'score': score, 'quality': quality,
                        'message': f'Match Score: {score}%', 'redirect': '/analysis'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("\n🚀 Starting AI Resume Pro...")
    print("📍 Open: http://localhost:5000\n")
    app.run(debug=True, port=5000)  