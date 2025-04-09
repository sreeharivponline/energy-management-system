from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from database import db, Admin, User, Officer
import bcrypt

login_manager = LoginManager()

class AuthUser(UserMixin):
    def __init__(self, id, role, is_officer=False):
        self.id = id  # Keep full ID format (e.g., 'user:1')
        self.role = role
        self.is_officer = is_officer

    def get_id(self):
        return str(self.id)

def init_auth(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        print(f"Loading user with ID: {user_id}")
        
        try:
            role, actual_id = user_id.split(":")  # Extract role and ID
            actual_id = int(actual_id)  # Convert to integer
        except ValueError:
            print("Invalid user_id format")
            return None
        
        if role == 'admin':
            admin = Admin.query.get(actual_id)
            if admin:
                print(f"Loaded admin: {admin.username}")
                return AuthUser(f"admin:{admin.id}", 'admin', is_officer=False)
        elif role == 'user':
            user = User.query.get(actual_id)
            if user:
                print(f"Loaded user: {user.username}")
                return AuthUser(f"user:{user.id}", user.role, is_officer=False)
        elif role == 'officer':
            officer = Officer.query.get(actual_id)
            if officer:
                print(f"Loaded officer: {officer.username}")
                return AuthUser(f"officer:{officer.id}", 'kseb', is_officer=True)
        
        print("User not found in user_loader")
        return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    except Exception as e:
        print(f"Error in check_password: {str(e)}")
        return False