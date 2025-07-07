from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from config import load_config

auth = Blueprint('auth', __name__)
login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    config = load_config()
    
    # 使用配置文件中的用户名和密码进行验证
    if username == config.get('admin_username', 'admin') and password == config.get('admin_password', 'admin'):
        user = User(1)
        login_user(user)
        return redirect(url_for('index'))
    
    flash('用户名或密码不正确')
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))