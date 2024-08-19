# app/blueprints/auth.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token
from extensions import db
from models import User, Customer
from schemas import UserSchema, LoginSchema

blp = Blueprint("auth", __name__, description="Authentication operations")

@blp.route("/register")
class RegisterResource(MethodView):
    @blp.arguments(UserSchema)
    @blp.response(201, UserSchema)
    def post(self, user_data):
        if User.query.filter((User.username == user_data["username"]) | (User.email == user_data["email"])).first():
            abort(409, message="A user with that username or email already exists.")
        
        customer = Customer.query.filter_by(name=user_data["customer_name"]).first()
        if not customer:
            customer = Customer(name=user_data["customer_name"])
            db.session.add(customer)
        
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            customer=customer
        )
        user.set_password(user_data["password"])
        
        db.session.add(user)
        db.session.commit()
        
        return user

@blp.route("/login")
class LoginResource(MethodView):
    @blp.arguments(LoginSchema)
    def post(self, login_data):
        user = User.query.filter_by(username=login_data["username"]).first()
        if user and user.check_password(login_data["password"]):
            access_token = create_access_token(identity=user.id)
            return {"access_token": access_token}, 200
        abort(401, message="Invalid credentials.")