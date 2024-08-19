# cli.py
import click
from flask.cli import FlaskGroup
from app import create_app
from app.models import db, User, Customer
from werkzeug.security import generate_password_hash

cli = FlaskGroup(create_app=create_app)

@cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    click.echo("Initialized the database.")

@cli.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.password_option()
def create_admin(username, email, password):
    """Create an admin user."""
    user = User(username=username, email=email, password=generate_password_hash(password), is_admin=True)
    customer = Customer(name="Admin", email=email)
    db.session.add(user)
    db.session.add(customer)
    db.session.commit()
    click.echo(f"Created admin user {username}")

if __name__ == "__main__":
    cli()