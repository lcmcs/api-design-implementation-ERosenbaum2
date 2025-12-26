"""
Main Flask application for the Minyan Finder API.
"""
from flask import Flask, jsonify, g
from flask_restx import Api, Resource
from flask_cors import CORS
from models import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from routes import register_routes
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Register root endpoint BEFORE Flask-RESTX Api to ensure it takes precedence
# Use unique endpoint name to avoid conflict with Flask-RESTX's "root" endpoint
@app.route('/', methods=['GET'], endpoint='api_root')
def root():
    """Root endpoint with API information."""
    return jsonify({
        'message': 'Welcome to the Minyan Finder API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'api_docs': '/docs',
            'broadcasts': {
                'create': 'POST /broadcasts',
                'find_nearby': 'GET /broadcasts/nearby',
                'update': 'PUT /broadcasts/{id}',
                'delete': 'DELETE /broadcasts/{id}'
            }
        },
        'documentation': '/docs'
    }), 200

# Configure API
api = Api(
    app,
    version='1.0.0',
    title='Minyan Finder API',
    description='A RESTful API for finding nearby people who need a minyan (prayer group)',
    doc='/docs'  # Swagger UI endpoint
)

# Initialize database engine
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Strip whitespace and handle postgres:// URLs
    database_url = database_url.strip()
    if not database_url:
        print("Warning: DATABASE_URL is empty after stripping whitespace")
        engine = None
        Session = None
    else:
        # Convert postgres:// to postgresql:// (required for SQLAlchemy 2.0+)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            print("Database connection established successfully")
        except Exception as e:
            print(f"ERROR: Failed to create database engine: {e}")
            print(f"Database URL (first 100 chars): {database_url[:100]}")
            print("Application will start but database operations will fail.")
            engine = None
            Session = None
else:
    print("Warning: DATABASE_URL environment variable is not set")
    engine = None
    Session = None


def get_db_session():
    """Get database session for current request."""
    if 'db_session' not in g:
        if Session:
            g.db_session = Session()
        else:
            raise ValueError("Database not configured. Please set DATABASE_URL environment variable.")
    return g.db_session


@app.teardown_appcontext
def close_db(error):
    """Close database session after request."""
    db_session = g.pop('db_session', None)
    if db_session:
        db_session.close()


# Register routes
if Session:
    register_routes(api, get_db_session)

# Health check endpoint
@api.route('/health', methods=['GET'])
class Health(Resource):
    def get(self):
        """Health check endpoint."""
        return {'status': 'healthy', 'service': 'minyan-finder-api'}, 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')

