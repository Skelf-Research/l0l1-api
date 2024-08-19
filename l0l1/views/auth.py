from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User

jwt = JWTManager()

def setup_auth(app):
    jwt.init_app(app)

    @app.route('/login', methods=['POST'])
    def login():
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        return jsonify({"msg": "Bad username or password"}), 401

    @app.route('/register', methods=['POST'])
    def register():
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        if User.query.filter_by(username=username).first():
            return jsonify({"msg": "Username already exists"}), 400
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User created successfully"}), 201
