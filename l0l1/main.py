from app import create_app
from flask import render_template, send_from_directory
from extensions import db

app = create_app()

@app.route('/')
def serve_frontend():
    return send_from_directory('templates', 'index.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)