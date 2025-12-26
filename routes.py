"""
API route handlers for the Minyan Finder API.
"""
from flask import request, jsonify
from flask_restx import Resource
from datetime import datetime
from models import Broadcast
from utils import calculate_distance, validate_coordinates, validate_minyan_type


def register_routes(api, get_db_session_func):
    """Register all API routes."""
    
    @api.route('/broadcasts')
    class Broadcasts(Resource):
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
    
    @api.route('/broadcasts/nearby')
    class NearbyBroadcasts(Resource):
        def get(self):
            """Find nearby broadcasts."""
            db_session = get_db_session_func()
            try:
                # Get query parameters
                latitude = request.args.get('latitude', type=float)
                longitude = request.args.get('longitude', type=float)
                radius = request.args.get('radius', type=float)
                minyan_type = request.args.get('minyanType', type=str)
                
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
        def put(self, broadcast_id):
            """Update a broadcast."""
            db_session = get_db_session_func()
            try:
                # Find broadcast
                broadcast = db_session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
                
                if not broadcast:
                    return {'error': 'Broadcast not found'}, 404
                
                data = request.get_json()
                
                # Update fields if provided
                if 'latitude' in data or 'longitude' in data:
                    new_lat = data.get('latitude', broadcast.latitude)
                    new_lon = data.get('longitude', broadcast.longitude)
                    
                    is_valid, error_msg = validate_coordinates(new_lat, new_lon)
                    if not is_valid:
                        return {'error': error_msg}, 400
                    
                    broadcast.latitude = new_lat
                    broadcast.longitude = new_lon
                
                if 'earliestTime' in data:
                    try:
                        earliest_time = datetime.fromisoformat(data['earliestTime'].replace('Z', '+00:00'))
                        broadcast.earliest_time = earliest_time
                    except (ValueError, AttributeError) as e:
                        return {'error': f'Invalid earliestTime format: {str(e)}'}, 400
                
                if 'latestTime' in data:
                    try:
                        latest_time = datetime.fromisoformat(data['latestTime'].replace('Z', '+00:00'))
                        broadcast.latest_time = latest_time
                    except (ValueError, AttributeError) as e:
                        return {'error': f'Invalid latestTime format: {str(e)}'}, 400
                
                # Validate time order
                if broadcast.latest_time <= broadcast.earliest_time:
                    return {'error': 'latestTime must be after earliestTime'}, 400
                
                db_session.commit()
                
                return {'message': 'Broadcast updated successfully'}, 200
                
            except Exception as e:
                db_session.rollback()
                return {'error': f'Failed to update broadcast: {str(e)}'}, 400
        
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

