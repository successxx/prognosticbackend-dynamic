import logging
import os
import re
import time  # Import for tracking execution time
import urllib
import uuid
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from pythonjsonlogger import jsonlogger  # JSON formatter for logs
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

# Set up logging with JSON formatter
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')

logHandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Suppress Flask's default logging
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)  # Suppress INFO logs from Werkzeug

app = Flask(__name__)
cors = CORS(app)
dyno = os.getenv('DYNO', 'unknown-dyno')

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Auto-generated on insert
    booking_button_name = db.Column(db.Text, nullable=True)  # Can be NULL
    booking_button_redirection = db.Column(db.Text, nullable=True)  # Can be NULL


def create_table_and_index_if_not_exists():
    with app.app_context():
        inspector = inspect(db.engine)

        # Check if the 'prognostic' table exists
        if 'prognostic' not in inspector.get_table_names():
            db.create_all()
            logger.info("Table 'prognostic' created.")
        else:
            logger.info("Table 'prognostic' already exists.")

        with db.engine.connect() as connection:
            # Check for 'created_at' column and add it if necessary
            created_at_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'prognostic' AND column_name = 'created_at';
            """)).fetchone()

            if not created_at_exists:
                connection.execute(text("""
                    ALTER TABLE prognostic 
                    ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
                """))
                logger.info("'created_at' column added.")
                connection.commit()
            else:
                logger.info("'created_at' column already exists.")

            # Check for 'booking_button_name' column and add it if necessary
            booking_button_name_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'prognostic' AND column_name = 'booking_button_name';
            """)).fetchone()

            if not booking_button_name_exists:
                connection.execute(text("""
                    ALTER TABLE prognostic 
                    ADD COLUMN booking_button_name TEXT;
                """))
                connection.commit()
                logger.info("'booking_button_name' column added.")
            else:
                logger.info("'booking_button_name' column already exists.")

            # Check for 'booking_button_redirection' column and add it if necessary
            booking_button_redirection_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'prognostic' AND column_name = 'booking_button_redirection';
            """)).fetchone()

            if not booking_button_redirection_exists:
                connection.execute(text("""
                    ALTER TABLE prognostic 
                    ADD COLUMN booking_button_redirection TEXT;
                """))
                connection.commit()
                logger.info("'booking_button_redirection' column added.")
            else:
                logger.info("'booking_button_redirection' column already exists.")

            # Check if index on 'user_email' exists and create it if necessary
            index_check_query = text("""
                SELECT indexname FROM pg_indexes WHERE tablename = 'prognostic' AND indexname = 'idx_user_email';
            """)

            index_exists = connection.execute(index_check_query).fetchone()

            if not index_exists:
                create_index_query = text("""
                    CREATE INDEX idx_user_email ON prognostic (user_email);
                """)
                try:
                    connection.execute(create_index_query)
                    connection.commit()  # Explicitly commit the transaction
                    logger.info("Index 'idx_user_email' created.")
                except Exception as e:
                    logger.error(f"Failed to create index: {e}")
            else:
                logger.info("Index 'idx_user_email' already exists.")


# Call the function to create the table and index if not present
create_table_and_index_if_not_exists()


def markdown_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'### (.*)', r'<h3 class="text-xl font-bold mb-2">\1</h3>', text)
    text = re.sub(r'## (.*)', r'<h2 class="text-2xl font-bold mb-4">\1</h2>', text)
    text = text.replace('\n', '<br>')
    return text


# Custom log function with additional attributes
def log_custom_message(message, extra_data):
    extra_data['dyno'] = dyno
    logger.info(message, extra=extra_data)


@cross_origin()
@app.route('/insert_user', methods=['POST'])
def insert_user():
    start_time = time.time()  # Start tracking time
    data = request.json
    user_email = data.get('user_email')
    text_content = data.get('text')
    booking_button_name = data.get('booking_button_name')
    booking_button_redirection = data.get('booking_button_redirection')

    if not user_email:
        response = jsonify({'error': 'user_email is required'})
        response.status_code = 400
        # Log the request and response (without text content)
        extra_data = {
            "event_time": time.time(),  # Custom event time
            "method": request.method,
            "url": request.url,
            "remote_addr": request.remote_addr,
            "headers": dict(request.headers),
            "response_status": response.status_code,
            "elapsed_time": f"{time.time() - start_time:.4f} seconds",
        }
        log_custom_message("Insert user failed", extra_data)
        return response

    decoded_text = urllib.parse.unquote(text_content)
    user_uuid = uuid.uuid4()
    transformed_text = markdown_to_html(decoded_text)

    try:
        existing_user = Prognostic.query.filter_by(user_email=user_email).first()
        if existing_user:
            existing_user.text = transformed_text
            existing_user.booking_button_name = booking_button_name
            existing_user.booking_button_redirection = booking_button_redirection
            db.session.commit()
            elapsed_time = time.time() - start_time  # Calculate execution time
            response = jsonify({'message': 'User updated successfully!', 'user_id': str(existing_user.user_id)})
            response.status_code = 200

            # Log the request and response (without the text)
            extra_data = {
                "event_time": time.time(),
                "method": request.method,
                "url": request.url,
                "remote_addr": request.remote_addr,
                "headers": dict(request.headers),
                "request_body": {
                    "user_email": user_email,
                    "booking_button_name": booking_button_name,
                    "booking_button_redirection": booking_button_redirection,
                    "text": "Not produced, its too big",
                },
                "response_status": response.status_code,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("User updated successfully", extra_data)

            # Log the text content separately
            # logger.info(f"Text content for {user_email}: {transformed_text}")

            return response
        else:
            new_user = Prognostic(
                user_id=user_uuid,
                user_email=user_email,
                text=transformed_text,
                booking_button_name=booking_button_name,
                booking_button_redirection=booking_button_redirection
            )
            db.session.add(new_user)
            db.session.commit()
            elapsed_time = time.time() - start_time  # Calculate execution time
            response = jsonify({'message': 'User added successfully!', 'user_id': str(new_user.user_id)})
            response.status_code = 201

            # Log the request and response (without the text)
            extra_data = {
                "event_time": time.time(),
                "method": request.method,
                "url": request.url,
                "remote_addr": request.remote_addr,
                "headers": dict(request.headers),
                "request_body": {
                    "user_email": user_email,
                    "booking_button_name": booking_button_name,
                    "booking_button_redirection": booking_button_redirection,
                    "text": "Not produced, its too big"
                },
                "response_status": response.status_code,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("User added successfully", extra_data)

            # Log the text content separately
            # logger.info(f"Text content for {user_email}: {transformed_text}")

            return response
    except Exception as e:
        db.session.rollback()
        response = jsonify({'error': str(e)})
        response.status_code = 400

        # Log the error
        extra_data = {
            "event_time": time.time(),
            "method": request.method,
            "url": request.url,
            "remote_addr": request.remote_addr,
            "headers": dict(request.headers),
            "request_body": {
                "user_email": user_email
            },
            "response_status": response.status_code,
            "error": str(e),
            "elapsed_time": f"{time.time() - start_time:.4f} seconds",
        }
        log_custom_message("Error while inserting user", extra_data)

        return response


@app.route('/get_user', methods=['POST'])
def get_user():
    start_time = time.time()  # Start tracking time
    data = request.get_json()
    user_email = data.get('user_email')

    if not user_email:
        response = jsonify({"error": "Email parameter is required"})
        response.status_code = 400
        # Log the request and response (without user text content)
        extra_data = {
            "event_time": time.time(),
            "method": request.method,
            "url": request.url,
            "remote_addr": request.remote_addr,
            "headers": dict(request.headers),
            "request_body": data,
            "response_status": response.status_code,
            "elapsed_time": f"{time.time() - start_time:.4f} seconds",
        }
        log_custom_message("Get user failed", extra_data)
        return response

    try:
        user = Prognostic.query.filter_by(user_email=user_email).first()

        if user:
            response_data = {
                "success": True,
                "text": user.text,
                "user_email": user.user_email,
                "booking_button_name": user.booking_button_name,
                "booking_button_redirection": user.booking_button_redirection,
                "length": len(user.text)
            }
            elapsed_time = time.time() - start_time  # Calculate execution time
            response = jsonify(response_data)
            response.status_code = 200

            # Log the request and response (without user text content)
            extra_data = {
                "event_time": time.time(),
                "method": request.method,
                "url": request.url,
                "remote_addr": request.remote_addr,
                "headers": dict(request.headers),
                "response_status": response.status_code,
                "response_body": {
                    "success": True,
                    "user_email": user.user_email,
                    "text": "Not produced, its too big",
                    "booking_button_name": user.booking_button_name,
                    "booking_button_redirection": user.booking_button_redirection,
                    "length": len(user.text)  # Log only the length of the text, not the text itself
                },
                "user_email": user_email,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("Get user operation", extra_data)

            # Log the text content separately
            # logger.info(f"Text content for {user_email}: {user.text}")

            return response
        else:
            elapsed_time = time.time() - start_time  # Calculate execution time
            response = jsonify({"success": False, "message": "User not found"})
            response.status_code = 404

            # Log the request and response (without user text content)
            extra_data = {
                "event_time": time.time(),
                "method": request.method,
                "url": request.url,
                "remote_addr": request.remote_addr,
                "headers": dict(request.headers),
                "request_body": data,
                "response_status": response.status_code,
                "response_body": response.get_json(),
                "user_email": user_email,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("User not found", extra_data)
            return response
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.status_code = 400

        # Log the error
        extra_data = {
            "event_time": time.time(),
            "method": request.method,
            "url": request.url,
            "remote_addr": request.remote_addr,
            "headers": dict(request.headers),
            "request_body": data,
            "response_status": response.status_code,
            "response_body": response.get_json(),
            "user_email": user_email,
            "error": str(e),
            "elapsed_time": f"{time.time() - start_time:.4f} seconds",
        }
        log_custom_message("Error while fetching user", extra_data)
        return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
