from flask import Flask
from routes import init_routes
from database import init_db
from auth import init_auth

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Replace with a secure key

# Initialize components
init_db(app)
init_auth(app)
init_routes(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
