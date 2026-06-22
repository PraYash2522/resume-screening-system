from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from database import db, User
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os

auth_bp = Blueprint('auth', __name__)
mail = Mail()

def get_serializer():
    return URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production'))

# ─── Forgot Password ──────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email', '').strip()
    user = User.query.filter_by(email=email).first()

    # Always show success (security: don't reveal if email exists)
    if user:
        s = get_serializer()
        token = s.dumps(email, salt='password-reset')
        reset_url = url_for('auth.reset_password', token=token, _external=True)

        try:
            msg = Message(
                subject='🔑 Reset Your AI Resume Pro Password',
                sender=os.environ.get('MAIL_USERNAME'),
                recipients=[email]
            )
            msg.html = f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:30px;background:#f9f9f9;border-radius:15px;">
                <h2 style="color:#667eea;text-align:center;">🤖 AI Resume Pro</h2>
                <h3 style="color:#333;">Password Reset Request</h3>
                <p style="color:#555;">Hello! We received a request to reset your password.</p>
                <p style="color:#555;">Click the button below to reset it. This link expires in <strong>15 minutes</strong>.</p>
                <div style="text-align:center;margin:30px 0;">
                    <a href="{reset_url}" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:14px 35px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:16px;">
                        Reset My Password
                    </a>
                </div>
                <p style="color:#999;font-size:0.85em;">If you didn't request this, ignore this email. Your password won't change.</p>
                <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
                <p style="color:#bbb;font-size:0.8em;text-align:center;">AI Resume Pro &copy; 2025</p>
            </div>
            """
            mail.send(msg)
        except Exception as e:
            print(f"Mail error: {e}")

    return {'success': True, 'message': 'If this email is registered, a reset link has been sent.'}


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = get_serializer()
    try:
        email = s.loads(token, salt='password-reset', max_age=900)  # 15 min
    except SignatureExpired:
        flash('Reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.login'))
    except BadSignature:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm  = request.form.get('confirm_password')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html', token=token)

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)

        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Password reset successful! Please login.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)


# ─── Normal Auth ──────────────────────────────────────────────────────────────

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username         = request.form.get('username')
        email            = request.form.get('email')
        password         = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('signup.html')
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('signup.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'error')
            return render_template('signup.html')

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        user     = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('home'))   