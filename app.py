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


# Existing model class for the 'prognostic_psych' table
class PrognosticPsych(db.Model):
    __tablename__ = 'prognostic_psych'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid.uuid4)
    user_email = db.Column(db.String, unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Auto-generated on insert
    booking_button_name = db.Column(db.Text, nullable=True)  # Can be NULL
    booking_button_redirection = db.Column(db.Text, nullable=True)  # Can be NULL


# New model classes for results_one and results_two tables
class ResultsOne(db.Model):
    __tablename__ = 'results_one'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid.uuid4)
    user_email = db.Column(db.String, unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Auto-generated on insert
    booking_button_name = db.Column(db.Text, nullable=True)  # Can be NULL
    booking_button_redirection = db.Column(db.Text, nullable=True)  # Can be NULL


class ResultsTwo(db.Model):
    __tablename__ = 'results_two'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid.uuid4)
    user_email = db.Column(db.String, unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Auto-generated on insert
    booking_button_name = db.Column(db.Text, nullable=True)  # Can be NULL
    booking_button_redirection = db.Column(db.Text, nullable=True)  # Can be NULL


class UserAudio(db.Model):
    __tablename__ = 'user_audio'

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String, unique=True, nullable=False)
    audio_link = db.Column(db.Text, nullable=True)
    audio_link_two = db.Column(db.Text, nullable=True)  # New field for second audio
    exit_message = db.Column(db.Text, nullable=True)
    headline = db.Column(db.Text, nullable=True)

    # NEW FIELDS ADDED EXACTLY LIKE THE 'headline' FIELD:
    company_name = db.Column(db.Text, nullable=True)
    Industry = db.Column(db.Text, nullable=True)
    Products_services = db.Column(db.Text, nullable=True)
    Business_description = db.Column(db.Text, nullable=True)
    primary_goal = db.Column(db.Text, nullable=True)
    target_audience = db.Column(db.Text, nullable=True)
    pain_points = db.Column(db.Text, nullable=True)
    offer_name = db.Column(db.Text, nullable=True)
    offer_price = db.Column(db.Text, nullable=True)
    offer_description = db.Column(db.Text, nullable=True)
    primary_benefits = db.Column(db.Text, nullable=True)
    offer_goal = db.Column(db.Text, nullable=True)
    Offer_topic = db.Column(db.Text, nullable=True)
    target_url = db.Column(db.Text, nullable=True)
    testimonials = db.Column(db.Text, nullable=True)

    # ADDING THE THREE EXTRA COLUMNS:
    email_1 = db.Column(db.Text, nullable=True)
    email_2 = db.Column(db.Text, nullable=True)
    salesletter = db.Column(db.Text, nullable=True)


def create_table_and_index_if_not_exists():
    with app.app_context():
        inspector = inspect(db.engine)

        # Check and create 'prognostic' table if not exists
        if 'prognostic' not in inspector.get_table_names():
            db.create_all()
            logger.info("Table 'prognostic' created.")
        else:
            logger.info("Table 'prognostic' already exists.")

        # Now check and create 'prognostic_psych' table
        if 'prognostic_psych' not in inspector.get_table_names():
            # Create only the PrognosticPsych table
            PrognosticPsych.__table__.create(db.engine)
            logger.info("Table 'prognostic_psych' created.")
        else:
            logger.info("Table 'prognostic_psych' already exists.")

        # Now check and create 'results_one' table
        if 'results_one' not in inspector.get_table_names():
            # Create only the ResultsOne table
            ResultsOne.__table__.create(db.engine)
            logger.info("Table 'results_one' created.")
        else:
            logger.info("Table 'results_one' already exists.")

        # Now check and create 'results_two' table
        if 'results_two' not in inspector.get_table_names():
            # Create only the ResultsTwo table
            ResultsTwo.__table__.create(db.engine)
            logger.info("Table 'results_two' created.")
        else:
            logger.info("Table 'results_two' already exists.")

        # Check and create 'user_audio' table
        if 'user_audio' not in inspector.get_table_names():
            UserAudio.__table__.create(db.engine)
            logger.info("Table 'user_audio' created.")
        else:
            logger.info("Table 'user_audio' already exists.")

        with db.engine.connect() as connection:
            # For each table, check and add columns and indexes
            for table_name in ['prognostic_psych', 'results_one', 'results_two']:
                # Check for 'created_at' column and add it if necessary
                created_at_exists = connection.execute(text(f"""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = 'created_at';
                """)).fetchone()

                if not created_at_exists:
                    connection.execute(text(f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
                    """))
                    logger.info(f"'created_at' column added to '{table_name}'.")
                    connection.commit()
                else:
                    logger.info(f"'created_at' column already exists in '{table_name}'.")

                # Check for 'booking_button_name' column and add it if necessary
                booking_button_name_exists = connection.execute(text(f"""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = 'booking_button_name';
                """)).fetchone()

                if not booking_button_name_exists:
                    connection.execute(text(f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN booking_button_name TEXT;
                    """))
                    connection.commit()
                    logger.info(f"'booking_button_name' column added to '{table_name}'.")
                else:
                    logger.info(f"'booking_button_name' column already exists in '{table_name}'.")

                # Check for 'booking_button_redirection' column and add it if necessary
                booking_button_redirection_exists = connection.execute(text(f"""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = 'booking_button_redirection';
                """)).fetchone()

                if not booking_button_redirection_exists:
                    connection.execute(text(f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN booking_button_redirection TEXT;
                    """))
                    connection.commit()
                    logger.info(f"'booking_button_redirection' column added to '{table_name}'.")
                else:
                    logger.info(f"'booking_button_redirection' column already exists in '{table_name}'.")

                # Check if index on 'user_email' exists and create it if necessary
                index_name = f'idx_user_email_{table_name}'
                index_exists = connection.execute(text(f"""
                    SELECT indexname FROM pg_indexes WHERE tablename = '{table_name}' AND indexname = '{index_name}';
                """)).fetchone()

                if not index_exists:
                    create_index_query = text(f"""
                        CREATE INDEX {index_name} ON {table_name} (user_email);
                    """)
                    try:
                        connection.execute(create_index_query)
                        connection.commit()  # Explicitly commit the transaction
                        logger.info(f"Index '{index_name}' created.")
                    except Exception as e:
                        logger.error(f"Failed to create index on '{table_name}': {e}")
                else:
                    logger.info(f"Index '{index_name}' already exists.")

            # Check for audio_link_two in user_audio
            audio_link_two_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'audio_link_two';
            """)).fetchone()

            if not audio_link_two_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN audio_link_two TEXT;
                """))
                connection.commit()
                logger.info("'audio_link_two' column added to 'user_audio'.")
            else:
                logger.info("'audio_link_two' column already exists in 'user_audio'.")

            # NOW check for 'exit_message' in user_audio
            exit_msg_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'exit_message';
            """)).fetchone()

            if not exit_msg_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN exit_message TEXT;
                """))
                connection.commit()
                logger.info("'exit_message' column added to 'user_audio'.")
            else:
                logger.info("'exit_message' column already exists in 'user_audio'.")

            # NOW check for 'headline' in user_audio
            headline_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'headline';
            """)).fetchone()

            if not headline_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN headline TEXT;
                """))
                connection.commit()
                logger.info("'headline' column added to 'user_audio'.")
            else:
                logger.info("'headline' column already exists in 'user_audio'.")

            # Check the newly added fields using the same pattern as 'headline':
            # company_name
            company_name_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'company_name';
            """)).fetchone()

            if not company_name_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN company_name TEXT;
                """))
                connection.commit()
                logger.info("'company_name' column added to 'user_audio'.")
            else:
                logger.info("'company_name' column already exists in 'user_audio'.")

            # Industry
            Industry_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'Industry';
            """)).fetchone()

            if not Industry_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN "Industry" TEXT;
                """))
                connection.commit()
                logger.info("'Industry' column added to 'user_audio'.")
            else:
                logger.info("'Industry' column already exists in 'user_audio'.")

            # Products_services
            Products_services_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'Products_services';
            """)).fetchone()

            if not Products_services_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN "Products_services" TEXT;
                """))
                connection.commit()
                logger.info("'Products_services' column added to 'user_audio'.")
            else:
                logger.info("'Products_services' column already exists in 'user_audio'.")

            # Business_description
            Business_description_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'Business_description';
            """)).fetchone()

            if not Business_description_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN "Business_description" TEXT;
                """))
                connection.commit()
                logger.info("'Business_description' column added to 'user_audio'.")
            else:
                logger.info("'Business_description' column already exists in 'user_audio'.")

            # primary_goal
            primary_goal_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'primary_goal';
            """)).fetchone()

            if not primary_goal_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN primary_goal TEXT;
                """))
                connection.commit()
                logger.info("'primary_goal' column added to 'user_audio'.")
            else:
                logger.info("'primary_goal' column already exists in 'user_audio'.")

            # target_audience
            target_audience_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'target_audience';
            """)).fetchone()

            if not target_audience_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN target_audience TEXT;
                """))
                connection.commit()
                logger.info("'target_audience' column added to 'user_audio'.")
            else:
                logger.info("'target_audience' column already exists in 'user_audio'.")

            # pain_points
            pain_points_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'pain_points';
            """)).fetchone()

            if not pain_points_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN pain_points TEXT;
                """))
                connection.commit()
                logger.info("'pain_points' column added to 'user_audio'.")
            else:
                logger.info("'pain_points' column already exists in 'user_audio'.")

            # offer_name
            offer_name_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'offer_name';
            """)).fetchone()

            if not offer_name_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN offer_name TEXT;
                """))
                connection.commit()
                logger.info("'offer_name' column added to 'user_audio'.")
            else:
                logger.info("'offer_name' column already exists in 'user_audio'.")

            # offer_price
            offer_price_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'offer_price';
            """)).fetchone()

            if not offer_price_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN offer_price TEXT;
                """))
                connection.commit()
                logger.info("'offer_price' column added to 'user_audio'.")
            else:
                logger.info("'offer_price' column already exists in 'user_audio'.")

            # offer_description
            offer_description_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'offer_description';
            """)).fetchone()

            if not offer_description_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN offer_description TEXT;
                """))
                connection.commit()
                logger.info("'offer_description' column added to 'user_audio'.")
            else:
                logger.info("'offer_description' column already exists in 'user_audio'.")

            # primary_benefits
            primary_benefits_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'primary_benefits';
            """)).fetchone()

            if not primary_benefits_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN primary_benefits TEXT;
                """))
                connection.commit()
                logger.info("'primary_benefits' column added to 'user_audio'.")
            else:
                logger.info("'primary_benefits' column already exists in 'user_audio'.")

            # offer_goal
            offer_goal_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'offer_goal';
            """)).fetchone()

            if not offer_goal_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN offer_goal TEXT;
                """))
                connection.commit()
                logger.info("'offer_goal' column added to 'user_audio'.")
            else:
                logger.info("'offer_goal' column already exists in 'user_audio'.")

            # Offer_topic
            Offer_topic_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'Offer_topic';
            """)).fetchone()

            if not Offer_topic_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN "Offer_topic" TEXT;
                """))
                connection.commit()
                logger.info("'Offer_topic' column added to 'user_audio'.")
            else:
                logger.info("'Offer_topic' column already exists in 'user_audio'.")

            # target_url
            target_url_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'target_url';
            """)).fetchone()

            if not target_url_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN target_url TEXT;
                """))
                connection.commit()
                logger.info("'target_url' column added to 'user_audio'.")
            else:
                logger.info("'target_url' column already exists in 'user_audio'.")

            # testimonials
            testimonials_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'testimonials';
            """)).fetchone()

            if not testimonials_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN testimonials TEXT;
                """))
                connection.commit()
                logger.info("'testimonials' column added to 'user_audio'.")
            else:
                logger.info("'testimonials' column already exists in 'user_audio'.")

            # NOW check for the 3 new columns: email_1, email_2, salesletter
            email_1_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'email_1';
            """)).fetchone()

            if not email_1_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN email_1 TEXT;
                """))
                connection.commit()
                logger.info("'email_1' column added to 'user_audio'.")
            else:
                logger.info("'email_1' column already exists in 'user_audio'.")

            email_2_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'email_2';
            """)).fetchone()

            if not email_2_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN email_2 TEXT;
                """))
                connection.commit()
                logger.info("'email_2' column added to 'user_audio'.")
            else:
                logger.info("'email_2' column already exists in 'user_audio'.")

            salesletter_exists = connection.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_audio' AND column_name = 'salesletter';
            """)).fetchone()

            if not salesletter_exists:
                connection.execute(text("""
                    ALTER TABLE user_audio
                    ADD COLUMN salesletter TEXT;
                """))
                connection.commit()
                logger.info("'salesletter' column added to 'user_audio'.")
            else:
                logger.info("'salesletter' column already exists in 'user_audio'.")


# Call the function to create the tables and indexes if not present
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
            "event_time": time.time(),
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
            elapsed_time = time.time() - start_time
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
            elapsed_time = time.time() - start_time
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
            return response

    except Exception as e:
        db.session.rollback()
        response = jsonify({'error': str(e)})
        response.status_code = 400

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
    start_time = time.time()  
    data = request.get_json()
    user_email = data.get('user_email')

    if not user_email:
        response = jsonify({"error": "Email parameter is required"})
        response.status_code = 400
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
            elapsed_time = time.time() - start_time
            response = jsonify(response_data)
            response.status_code = 200

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
                    "length": len(user.text)
                },
                "user_email": user_email,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("Get user operation", extra_data)

            return response
        else:
            elapsed_time = time.time() - start_time
            response = jsonify({"success": False, "message": "User not found"})
            response.status_code = 404

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

# Existing endpoints for 'prognostic_psych' table
@cross_origin()
@app.route('/insert_user_psych', methods=['POST'])
def insert_user_psych():
    start_time = time.time()  
    data = request.json
    user_email = data.get('user_email')
    text_content = data.get('text')
    booking_button_name = data.get('booking_button_name')
    booking_button_redirection = data.get('booking_button_redirection')

    if not user_email:
        response = jsonify({'error': 'user_email is required'})
        response.status_code = 400
        extra_data = {
            "event_time": time.time(),  
            "method": request.method,
            "url": request.url,
            "remote_addr": request.remote_addr,
            "headers": dict(request.headers),
            "response_status": response.status_code,
            "elapsed_time": f"{time.time() - start_time:.4f} seconds",
        }
        log_custom_message("Insert user psych failed", extra_data)
        return response

    decoded_text = urllib.parse.unquote(text_content)
    user_uuid = uuid.uuid4()
    transformed_text = markdown_to_html(decoded_text)

    try:
        existing_user = PrognosticPsych.query.filter_by(user_email=user_email).first()
        if existing_user:
            existing_user.text = transformed_text
            existing_user.booking_button_name = booking_button_name
            existing_user.booking_button_redirection = booking_button_redirection
            db.session.commit()
            elapsed_time = time.time() - start_time
            response = jsonify({'message': 'User psych updated successfully!', 'user_id': str(existing_user.user_id)})
            response.status_code = 200

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
            log_custom_message("User psych updated successfully", extra_data)
            return response
        else:
            new_user = PrognosticPsych(
                user_id=user_uuid,
                user_email=user_email,
                text=transformed_text,
                booking_button_name=booking_button_name,
                booking_button_redirection=booking_button_redirection
            )
            db.session.add(new_user)
            db.session.commit()
            elapsed_time = time.time() - start_time
            response = jsonify({'message': 'User psych added successfully!', 'user_id': str(new_user.user_id)})
            response.status_code = 201

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
            log_custom_message("User psych added successfully", extra_data)
            return response
    except Exception as e:
        db.session.rollback()
        response = jsonify({'error': str(e)})
        response.status_code = 400

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
        log_custom_message("Error while inserting user psych", extra_data)
        return response


@app.route('/get_user_psych', methods=['POST'])
def get_user_psych():
    start_time = time.time()  
    data = request.get_json()
    user_email = data.get('user_email')

    if not user_email:
        response = jsonify({"error": "Email parameter is required"})
        response.status_code = 400
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
        log_custom_message("Get user psych failed", extra_data)
        return response

    try:
        user = PrognosticPsych.query.filter_by(user_email=user_email).first()

        if user:
            response_data = {
                "success": True,
                "text": user.text,
                "user_email": user.user_email,
                "booking_button_name": user.booking_button_name,
                "booking_button_redirection": user.booking_button_redirection,
                "length": len(user.text)
            }
            elapsed_time = time.time() - start_time
            response = jsonify(response_data)
            response.status_code = 200

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
                    "length": len(user.text)
                },
                "user_email": user_email,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("Get user psych operation", extra_data)

            return response
        else:
            elapsed_time = time.time() - start_time
            response = jsonify({"success": False, "message": "User not found"})
            response.status_code = 404

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
            log_custom_message("User psych not found", extra_data)
            return response
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.status_code = 400

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
        log_custom_message("Error while fetching user psych", extra_data)
        return response


# New endpoints for inserting/updating users in the 'results_one' and 'results_two' tables
@cross_origin()
@app.route('/insert_user_one', methods=['POST'])
def insert_user_one():
    start_time = time.time()  
    data = request.json
    user_email = data.get('user_email')
    text_content = data.get('text')
    booking_button_name = data.get('booking_button_name')
    booking_button_redirection = data.get('booking_button_redirection')

    if not user_email:
        response = jsonify({'error': 'user_email is required'})
        response.status_code = 400
        extra_data = {
            "event_time": time.time(),  
            "method": request.method,
            "url": request.url,
            "remote_addr": request.remote_addr,
            "headers": dict(request.headers),
            "response_status": response.status_code,
            "elapsed_time": f"{time.time() - start_time:.4f} seconds",
        }
        log_custom_message("Insert user one failed", extra_data)
        return response

    decoded_text = urllib.parse.unquote(text_content)
    user_uuid = uuid.uuid4()
    transformed_text = markdown_to_html(decoded_text)

    try:
        existing_user = ResultsOne.query.filter_by(user_email=user_email).first()
        if existing_user:
            existing_user.text = transformed_text
            existing_user.booking_button_name = booking_button_name
            existing_user.booking_button_redirection = booking_button_redirection
            db.session.commit()
            elapsed_time = time.time() - start_time
            response = jsonify({'message': 'User one updated successfully!', 'user_id': str(existing_user.user_id)})
            response.status_code = 200

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
            log_custom_message("User one updated successfully", extra_data)
            return response
        else:
            new_user = ResultsOne(
                user_id=user_uuid,
                user_email=user_email,
                text=transformed_text,
                booking_button_name=booking_button_name,
                booking_button_redirection=booking_button_redirection
            )
            db.session.add(new_user)
            db.session.commit()
            elapsed_time = time.time() - start_time
            response = jsonify({'message': 'User one added successfully!', 'user_id': str(new_user.user_id)})
            response.status_code = 201

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
            log_custom_message("User one added successfully", extra_data)
            return response
    except Exception as e:
        db.session.rollback()
        response = jsonify({'error': str(e)})
        response.status_code = 400

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
        log_custom_message("Error while inserting user one", extra_data)
        return response


@cross_origin()
@app.route('/insert_user_two', methods=['POST'])
def insert_user_two():
    start_time = time.time()  
    data = request.json
    user_email = data.get('user_email')
    text_content = data.get('text')
    booking_button_name = data.get('booking_button_name')
    booking_button_redirection = data.get('booking_button_redirection')

    if not user_email:
        response = jsonify({'error': 'user_email is required'})
        response.status_code = 400
        extra_data = {
            "event_time": time.time(),  
            "method": request.method,
            "url": request.url,
            "remote_addr": request.remote_addr,
            "headers": dict(request.headers),
            "response_status": response.status_code,
            "elapsed_time": f"{time.time() - start_time:.4f} seconds",
        }
        log_custom_message("Insert user two failed", extra_data)
        return response

    decoded_text = urllib.parse.unquote(text_content)
    user_uuid = uuid.uuid4()
    transformed_text = markdown_to_html(decoded_text)

    try:
        existing_user = ResultsTwo.query.filter_by(user_email=user_email).first()
        if existing_user:
            existing_user.text = transformed_text
            existing_user.booking_button_name = booking_button_name
            existing_user.booking_button_redirection = booking_button_redirection
            db.session.commit()
            elapsed_time = time.time() - start_time
            response = jsonify({'message': 'User two updated successfully!', 'user_id': str(existing_user.user_id)})
            response.status_code = 200

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
            log_custom_message("User two updated successfully", extra_data)
            return response
        else:
            new_user = ResultsTwo(
                user_id=user_uuid,
                user_email=user_email,
                text=transformed_text,
                booking_button_name=booking_button_name,
                booking_button_redirection=booking_button_redirection
            )
            db.session.add(new_user)
            db.session.commit()
            elapsed_time = time.time() - start_time
            response = jsonify({'message': 'User two added successfully!', 'user_id': str(new_user.user_id)})
            response.status_code = 201

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
            log_custom_message("User two added successfully", extra_data)
            return response
    except Exception as e:
        db.session.rollback()
        response = jsonify({'error': str(e)})
        response.status_code = 400

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
        log_custom_message("Error while inserting user two", extra_data)
        return response


# New endpoints for retrieving users from the 'results_one' and 'results_two' tables
@app.route('/get_user_one', methods=['POST'])
def get_user_one():
    start_time = time.time()  
    data = request.get_json()
    user_email = data.get('user_email')

    if not user_email:
        response = jsonify({"error": "Email parameter is required"})
        response.status_code = 400
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
        log_custom_message("Get user one failed", extra_data)
        return response

    try:
        user = ResultsOne.query.filter_by(user_email=user_email).first()

        if user:
            response_data = {
                "success": True,
                "text": user.text,
                "user_email": user.user_email,
                "booking_button_name": user.booking_button_name,
                "booking_button_redirection": user.booking_button_redirection,
                "length": len(user.text)
            }
            elapsed_time = time.time() - start_time
            response = jsonify(response_data)
            response.status_code = 200

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
                    "length": len(user.text)  
                },
                "user_email": user_email,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("Get user one operation", extra_data)
            return response
        else:
            elapsed_time = time.time() - start_time
            response = jsonify({"success": False, "message": "User not found"})
            response.status_code = 404

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
            log_custom_message("User one not found", extra_data)
            return response
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.status_code = 400

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
        log_custom_message("Error while fetching user one", extra_data)
        return response


@app.route('/get_user_two', methods=['POST'])
def get_user_two():
    start_time = time.time()  
    data = request.get_json()
    user_email = data.get('user_email')

    if not user_email:
        response = jsonify({"error": "Email parameter is required"})
        response.status_code = 400
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
        log_custom_message("Get user two failed", extra_data)
        return response

    try:
        user = ResultsTwo.query.filter_by(user_email=user_email).first()

        if user:
            response_data = {
                "success": True,
                "text": user.text,
                "user_email": user.user_email,
                "booking_button_name": user.booking_button_name,
                "booking_button_redirection": user.booking_button_redirection,
                "length": len(user.text)
            }
            elapsed_time = time.time() - start_time
            response = jsonify(response_data)
            response.status_code = 200

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
                    "length": len(user.text)  
                },
                "user_email": user_email,
                "elapsed_time": f"{elapsed_time:.4f} seconds",
            }
            log_custom_message("Get user two operation", extra_data)
            return response
        else:
            elapsed_time = time.time() - start_time
            response = jsonify({"success": False, "message": "User not found"})
            response.status_code = 404

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
            log_custom_message("User two not found", extra_data)
            return response
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.status_code = 400

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
        log_custom_message("Error while fetching user two", extra_data)
        return response


##########################
# AUDIO ENDPOINTS
##########################
@cross_origin()
@app.route('/insert_audio', methods=['POST'])
def insert_audio():
    """
    Example JSON body:
    {
      "user_email": "someone@example.com",
      "audio_link": "https://drive.google.com/uc?export=download&id=FOO",
      "audio_link_two": "https://drive.google.com/uc?export=download&id=BAR",
      "exit_message": "some optional text"
      "headline": "some optional text"
      -- plus new fields below, following the same pattern
    }
    """
    data = request.json
    user_email = data.get('user_email')
    audio_link = data.get('audio_link')
    audio_link_two = data.get('audio_link_two')
    exit_message = data.get('exit_message', '')
    headline = data.get('headline', '')

    # NEW FIELDS EXACTLY LIKE HEADLINE
    company_name = data.get('company_name', '')
    Industry = data.get('Industry', '')
    Products_services = data.get('Products_services', '')
    Business_description = data.get('Business_description', '')
    primary_goal = data.get('primary_goal', '')
    target_audience = data.get('target_audience', '')
    pain_points = data.get('pain_points', '')
    offer_name = data.get('offer_name', '')
    offer_price = data.get('offer_price', '')
    offer_description = data.get('offer_description', '')
    primary_benefits = data.get('primary_benefits', '')
    offer_goal = data.get('offer_goal', '')
    Offer_topic = data.get('Offer_topic', '')
    target_url = data.get('target_url', '')
    testimonials = data.get('testimonials', '')
    email_1 = data.get('email_1', '')
    email_2 = data.get('email_2', '')
    salesletter = data.get('salesletter', '')

    if not user_email or not audio_link:
        return jsonify({"error": "Missing user_email or audio_link"}), 400

    try:
        existing = UserAudio.query.filter_by(user_email=user_email).first()
        if existing:
            existing.audio_link = audio_link
            existing.audio_link_two = audio_link_two
            existing.exit_message = exit_message
            existing.headline = headline

            # Assign new fields
            existing.company_name = company_name
            existing.Industry = Industry
            existing.Products_services = Products_services
            existing.Business_description = Business_description
            existing.primary_goal = primary_goal
            existing.target_audience = target_audience
            existing.pain_points = pain_points
            existing.offer_name = offer_name
            existing.offer_price = offer_price
            existing.offer_description = offer_description
            existing.primary_benefits = primary_benefits
            existing.offer_goal = offer_goal
            existing.Offer_topic = Offer_topic
            existing.target_url = target_url
            existing.testimonials = testimonials
            existing.email_1 = email_1
            existing.email_2 = email_2
            existing.salesletter = salesletter

            db.session.commit()
            return jsonify({"message": "Audio updated successfully"}), 200
        else:
            new_audio = UserAudio(
                user_email=user_email,
                audio_link=audio_link,
                audio_link_two=audio_link_two,
                exit_message=exit_message,
                headline=headline,
                # New fields
                company_name=company_name,
                Industry=Industry,
                Products_services=Products_services,
                Business_description=Business_description,
                primary_goal=primary_goal,
                target_audience=target_audience,
                pain_points=pain_points,
                offer_name=offer_name,
                offer_price=offer_price,
                offer_description=offer_description,
                primary_benefits=primary_benefits,
                offer_goal=offer_goal,
                Offer_topic=Offer_topic,
                target_url=target_url,
                testimonials=testimonials
            )
            db.session.add(new_audio)
            db.session.commit()
            return jsonify({"message": "Audio inserted successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cross_origin()
@app.route('/get_audio', methods=['GET'])
def get_audio():
    """
    Example query param usage:
    GET /get_audio?user_email=someone@example.com
    Returns {"audio_link": "...", "audio_link_two": "...", "exit_message": "...", "headline": "...", ... } or empty if not found.
    """
    user_email = request.args.get('user_email')
    if not user_email:
        return jsonify({"error": "No user_email provided"}), 400

    try:
        record = UserAudio.query.filter_by(user_email=user_email).first()
        if record:
            return jsonify({
                "audio_link": record.audio_link,
                "audio_link_two": record.audio_link_two,
                "exit_message": record.exit_message if record.exit_message else "",
                "headline": record.headline if record.headline else "",
                # Return the new fields exactly like 'headline'
                "company_name": record.company_name if record.company_name else "",
                "Industry": record.Industry if record.Industry else "",
                "Products_services": record.Products_services if record.Products_services else "",
                "Business_description": record.Business_description if record.Business_description else "",
                "primary_goal": record.primary_goal if record.primary_goal else "",
                "target_audience": record.target_audience if record.target_audience else "",
                "pain_points": record.pain_points if record.pain_points else "",
                "offer_name": record.offer_name if record.offer_name else "",
                "offer_price": record.offer_price if record.offer_price else "",
                "offer_description": record.offer_description if record.offer_description else "",
                "primary_benefits": record.primary_benefits if record.primary_benefits else "",
                "offer_goal": record.offer_goal if record.offer_goal else "",
                "Offer_topic": record.Offer_topic if record.Offer_topic else "",
                "target_url": record.target_url if record.target_url else "",
                "testimonials": record.testimonials if record.testimonials else "",
                "email_1": record.email_1 if record.email_1 else "",
                "email_2": record.email_2 if record.email_2 else "",
                "salesletter": record.salesletter if record.salesletter else ""
            }), 200
        else:
            return jsonify({
                "audio_link": None,
                "audio_link_two": None,
                "exit_message": "",
                "headline": "",
                "company_name": "",
                "Industry": "",
                "Products_services": "",
                "Business_description": "",
                "primary_goal": "",
                "target_audience": "",
                "pain_points": "",
                "offer_name": "",
                "offer_price": "",
                "offer_description": "",
                "primary_benefits": "",
                "offer_goal": "",
                "Offer_topic": "",
                "target_url": "",
                "testimonials": "",
                "email_1": "",
                "email_2": "",
                "salesletter": ""
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
