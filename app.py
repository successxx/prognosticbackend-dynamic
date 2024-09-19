import logging
import os
import re
import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID

logging.basicConfig(level=logging.INFO)
flask_cors_logger = logging.getLogger('flask_cors')
flask_cors_logger.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
cors = CORS(app)

database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql+pg8000://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://postgres:postgres@localhost/prognostic'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

db = SQLAlchemy(app)

class Prognostic(db.Model):
    __tablename__ = 'prognostic'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid.uuid4)
    user_email = db.Column(db.String, unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)

def create_table_if_not_exists():
    with app.app_context():
        inspector = inspect(db.engine)
        if 'prognostic' not in inspector.get_table_names():
            db.create_all()
            logger.info("Table 'prognostic' created.")
        else:
            logger.info("Table 'prognostic' already exists.")

create_table_if_not_exists()

def markdown_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'### (.*)', r'<h3 class="text-xl font-bold mb-2">\1</h3>', text)
    text = re.sub(r'## (.*)', r'<h2 class="text-2xl font-bold mb-4">\1</h2>', text)
    text = text.replace('\n', '<br>')
    return text

@app.before_request
def log_request():
    logger.info(f"Incoming request: {request.method} {request.url} - Body: {request.get_data()}")

@app.after_request
def log_response(response):
    logger.info(f"Outgoing response: Status {response.status_code} - Body: {response.get_data(as_text=True)}")
    return response

import uuid
import urllib.parse  # Import for decoding URL-encoded strings

@cross_origin()
@app.route('/insert_user', methods=['POST'])
def insert_user():
    data = request.json
    user_email = data.get('user_email')
    text_content = data.get('text')

    if not user_email:
        return jsonify({'error': 'user_email is required'}), 400

    # Decode the URL-encoded text content
    decoded_text = urllib.parse.unquote(text_content)

    user_uuid = uuid.uuid4()
    transformed_text = markdown_to_html(decoded_text)  # Now process the decoded content

    try:
        existing_user = Prognostic.query.filter_by(user_email=user_email).first()
        if existing_user:
            existing_user.text = transformed_text
            db.session.commit()
            return jsonify({'message': 'User updated successfully!', 'user_id': str(existing_user.user_id)}), 200
        else:
            new_user = Prognostic(user_id=user_uuid, user_email=user_email, text=transformed_text)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': 'User added successfully!', 'user_id': str(new_user.user_id)}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while inserting user: {e}")
        return jsonify({'error': str(e)}), 400



@app.route('/get_user', methods=['POST'])
def get_user():
    data = request.get_json()
    user_email = data.get('user_email')
    if not user_email:
        return jsonify({"error": "Email parameter is required"}), 400

    try:
        user = Prognostic.query.filter_by(user_email=user_email).first()

        if user:
            response_data = {
                "success": True,
                "text": user.text,
                "user_email": user.user_email,
                "length": len(user.text)
            }
            return jsonify(response_data), 200
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error while fetching user: {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
