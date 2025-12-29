"""
API route handlers for the Minyan Finder API.
"""
from flask import request, jsonify
from flask_restx import Resource, fields, reqparse
from datetime import datetime
from models import Broadcast
from utils import calculate_distance, validate_coordinates, validate_minyan_type
import time
import sys
import logging

logger = logging.getLogger(__name__)


def register_routes(api, get_db_session_func):
    """Register all API routes."""
    
    # Define models for Swagger documentation
    broadcast_model = api.model('Broadcast', {
        'latitude': fields.Float(required=True, description='Latitude (-90 to 90)'),
        'longitude': fields.Float(required=True, description='Longitude (-180 to 180)'),
        'minyanType': fields.String(required=True, description='Type of minyan: shacharit, mincha, or maariv', enum=['shacharit', 'mincha', 'maariv']),
        'earliestTime': fields.String(required=True, description='Earliest time in ISO 8601 format (e.g., 2025-12-27T08:00:00Z)'),
        'latestTime': fields.String(required=True, description='Latest time in ISO 8601 format (e.g., 2025-12-27T09:00:00Z)')
    })
    
    broadcast_update_model = api.model('BroadcastUpdate', {
        'latitude': fields.Float(required=False, description='Latitude (-90 to 90)'),
        'longitude': fields.Float(required=False, description='Longitude (-180 to 180)'),
        'earliestTime': fields.String(required=False, description='Earliest time in ISO 8601 format'),
        'latestTime': fields.String(required=False, description='Latest time in ISO 8601 format')
    })
    
    broadcast_response_model = api.model('BroadcastResponse', {
        'id': fields.String(description='Broadcast ID'),
        'message': fields.String(description='Success message')
    })
    
    @api.route('/broadcasts')
    class Broadcasts(Resource):
        @api.expect(broadcast_model)
        @api.marshal_with(broadcast_response_model, code=201)
        @api.doc(description='Create a new broadcast when looking for a minyan')
        def post(self):
            """Create a new broadcast."""
            db_session = get_db_session_func()
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['latitude', 'longitude', 'minyanType', 'earliestTime', 'latestTime']
                for field in required_fields:
                    if field not in data:
                        return {'error': f'Missing required field: {field}'}, 400
                
                # Validate coordinates
                is_valid, error_msg = validate_coordinates(data['latitude'], data['longitude'])
                if not is_valid:
                    return {'error': error_msg}, 400
                
                # Validate minyan type
                is_valid, error_msg = validate_minyan_type(data['minyanType'])
                if not is_valid:
                    return {'error': error_msg}, 400
                
                # Parse and validate times
                try:
                    earliest_time = datetime.fromisoformat(data['earliestTime'].replace('Z', '+00:00'))
                    latest_time = datetime.fromisoformat(data['latestTime'].replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    return {'error': f'Invalid time format: {str(e)}'}, 400
                
                if latest_time <= earliest_time:
                    return {'error': 'latestTime must be after earliestTime'}, 400
                
                # Create broadcast
                broadcast = Broadcast(
                    latitude=data['latitude'],
                    longitude=data['longitude'],
                    minyan_type=data['minyanType'],
                    earliest_time=earliest_time,
                    latest_time=latest_time,
                    active=True
                )
                
                db_session.add(broadcast)
                db_session.commit()
                
                return {
                    'id': broadcast.id,
                    'message': 'Broadcast created successfully'
                }, 201
                
            except Exception as e:
                db_session.rollback()
                return {'error': f'Failed to create broadcast: {str(e)}'}, 400
    
    # Define parser for nearby broadcasts query parameters
    nearby_parser = reqparse.RequestParser()
    nearby_parser.add_argument('latitude', type=float, required=True, help='Latitude of search location (-90 to 90)')
    nearby_parser.add_argument('longitude', type=float, required=True, help='Longitude of search location (-180 to 180)')
    nearby_parser.add_argument('radius', type=float, required=True, help='Search radius in miles')
    nearby_parser.add_argument('minyanType', type=str, required=False, help='Filter by minyan type (shacharit, mincha, maariv)')
    
    @api.route('/broadcasts/nearby')
    class NearbyBroadcasts(Resource):
        @api.expect(nearby_parser)
        @api.doc(description='Find nearby broadcasts within a specified radius')
        def get(self):
            """Find nearby broadcasts."""
            db_session = get_db_session_func()
            try:
                # Parse query parameters using reqparse
                args = nearby_parser.parse_args()
                latitude = args['latitude']
                longitude = args['longitude']
                radius = args['radius']
                minyan_type = args.get('minyanType')
                
                # Validate required parameters
                if latitude is None:
                    return {'error': 'Missing required parameter: latitude'}, 400
                if longitude is None:
                    return {'error': 'Missing required parameter: longitude'}, 400
                if radius is None:
                    return {'error': 'Missing required parameter: radius'}, 400
                
                # Validate coordinates
                is_valid, error_msg = validate_coordinates(latitude, longitude)
                if not is_valid:
                    return {'error': error_msg}, 400
                
                if radius < 0:
                    return {'error': 'Radius must be non-negative'}, 400
                
                # Validate minyan type if provided
                if minyan_type:
                    is_valid, error_msg = validate_minyan_type(minyan_type)
                    if not is_valid:
                        return {'error': error_msg}, 400
                
                # Query active broadcasts
                query = db_session.query(Broadcast).filter(Broadcast.active == True)
                
                # Filter by minyan type if provided
                if minyan_type:
                    query = query.filter(Broadcast.minyan_type == minyan_type)
                
                # Get all active broadcasts
                broadcasts = query.all()
                
                # Filter by distance
                nearby_broadcasts = []
                for broadcast in broadcasts:
                    distance = calculate_distance(latitude, longitude, broadcast.latitude, broadcast.longitude)
                    if distance <= radius:
                        nearby_broadcasts.append(broadcast.to_dict())
                
                return nearby_broadcasts, 200
                
            except Exception as e:
                return {'error': f'Failed to find nearby broadcasts: {str(e)}'}, 400
    
    @api.route('/broadcasts/<string:broadcast_id>')
    class BroadcastById(Resource):
        @api.param('broadcast_id', 'The broadcast ID', required=True, type='string')
        @api.expect(broadcast_update_model)
        @api.doc(description='Update an existing broadcast')
        def options(self, broadcast_id):
            """Handle CORS preflight for PUT requests."""
            logger.info(f"[OPTIONS /broadcasts/{broadcast_id}] CORS preflight request")
            sys.stdout.flush()
            return {}, 200
        
        def put(self, broadcast_id):
            """Update a broadcast."""
            start_time = time.time()
            logger.info(f"[PUT /broadcasts/{broadcast_id}] Starting request at {time.strftime('%H:%M:%S')}")
            sys.stdout.flush()
            
            try:
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Getting database session...")
                sys.stdout.flush()
                db_session = get_db_session_func()
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Database session obtained (took {time.time() - start_time:.2f}s)")
                sys.stdout.flush()
                
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Querying for broadcast with id: {broadcast_id}")
                sys.stdout.flush()
                query_start = time.time()
                broadcast = db_session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Query completed (took {time.time() - query_start:.2f}s)")
                sys.stdout.flush()
                
                if not broadcast:
                    logger.warning(f"[PUT /broadcasts/{broadcast_id}] Broadcast not found")
                    sys.stdout.flush()
                    return {'error': 'Broadcast not found'}, 404
                
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Parsing request JSON...")
                sys.stdout.flush()
                json_start = time.time()
                data = request.get_json()
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Request JSON parsed (took {time.time() - json_start:.2f}s), data: {data}")
                sys.stdout.flush()
                
                if data is None:
                    logger.warning(f"[PUT /broadcasts/{broadcast_id}] WARNING: request.get_json() returned None")
                    sys.stdout.flush()
                    data = {}
                
                # Update fields if provided
                if 'latitude' in data or 'longitude' in data:
                    logger.info(f"[PUT /broadcasts/{broadcast_id}] Updating coordinates...")
                    sys.stdout.flush()
                    new_lat = data.get('latitude', broadcast.latitude)
                    new_lon = data.get('longitude', broadcast.longitude)
                    
                    is_valid, error_msg = validate_coordinates(new_lat, new_lon)
                    if not is_valid:
                        logger.error(f"[PUT /broadcasts/{broadcast_id}] Invalid coordinates: {error_msg}")
                        sys.stdout.flush()
                        return {'error': error_msg}, 400
                    
                    broadcast.latitude = new_lat
                    broadcast.longitude = new_lon
                
                if 'earliestTime' in data:
                    logger.info(f"[PUT /broadcasts/{broadcast_id}] Updating earliestTime...")
                    sys.stdout.flush()
                    try:
                        earliest_time = datetime.fromisoformat(data['earliestTime'].replace('Z', '+00:00'))
                        broadcast.earliest_time = earliest_time
                    except (ValueError, AttributeError) as e:
                        logger.error(f"[PUT /broadcasts/{broadcast_id}] Invalid earliestTime format: {e}")
                        sys.stdout.flush()
                        return {'error': f'Invalid earliestTime format: {str(e)}'}, 400
                
                if 'latestTime' in data:
                    logger.info(f"[PUT /broadcasts/{broadcast_id}] Updating latestTime...")
                    sys.stdout.flush()
                    try:
                        latest_time = datetime.fromisoformat(data['latestTime'].replace('Z', '+00:00'))
                        broadcast.latest_time = latest_time
                    except (ValueError, AttributeError) as e:
                        logger.error(f"[PUT /broadcasts/{broadcast_id}] Invalid latestTime format: {e}")
                        sys.stdout.flush()
                        return {'error': f'Invalid latestTime format: {str(e)}'}, 400
                
                # Validate time order
                if broadcast.latest_time <= broadcast.earliest_time:
                    logger.error(f"[PUT /broadcasts/{broadcast_id}] Invalid time order")
                    sys.stdout.flush()
                    return {'error': 'latestTime must be after earliestTime'}, 400
                
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Committing to database...")
                sys.stdout.flush()
                commit_start = time.time()
                db_session.commit()
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Commit completed (took {time.time() - commit_start:.2f}s)")
                sys.stdout.flush()
                
                total_time = time.time() - start_time
                logger.info(f"[PUT /broadcasts/{broadcast_id}] Request completed successfully (total: {total_time:.2f}s)")
                sys.stdout.flush()
                return {'message': 'Broadcast updated successfully'}, 200
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[PUT /broadcasts/{broadcast_id}] ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"[PUT /broadcasts/{broadcast_id}] Traceback:\n{traceback.format_exc()}")
                sys.stdout.flush()
                try:
                    db_session.rollback()
                except:
                    pass
                return {'error': f'Failed to update broadcast: {str(e)}'}, 400
        
        @api.param('broadcast_id', 'The broadcast ID', required=True, type='string')
        @api.doc(description='Delete a broadcast')
        def delete(self, broadcast_id):
            """Delete a broadcast."""
            db_session = get_db_session_func()
            try:
                # Find broadcast
                broadcast = db_session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
                
                if not broadcast:
                    return {'error': 'Broadcast not found'}, 404
                
                db_session.delete(broadcast)
                db_session.commit()
                
                return '', 204
                
            except Exception as e:
                db_session.rollback()
                return {'error': f'Failed to delete broadcast: {str(e)}'}, 400

