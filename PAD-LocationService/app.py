from flask import Flask, request, jsonify
from flask_cors import CORS
from database import Database
from models import *
from datetime import datetime

app = Flask(__name__)
CORS(app)
db = Database()

# API Routes
@app.route('/location/track', methods=['POST'])
def track_location():
    """Append a location sample for a user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['userId', 'lobbyId', 'roomId', 'at']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create location sample
        location = LocationSample(
            user_id=data['userId'],
            lobby_id=data['lobbyId'],
            room_id=data['roomId'],
            is_speaking=data.get('isSpeaking', False),
            group=data.get('group', []),
            is_hiding=data.get('isHiding', False),
            at=data['at']
        )
        
        # Store location
        db.track_location(location)
        
        return jsonify({'accepted': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/location/lobbies/<lobby_id>/users/<user_id>/latest', methods=['GET'])
def get_latest_location(lobby_id, user_id):
    """Get the latest known location for a user"""
    try:
        latest_location = db.get_latest_location(user_id, lobby_id)
        
        if not latest_location:
            return jsonify({'error': 'No location data found for user in this lobby'}), 404
        
        response = LatestLocationResponse(
            room_id=latest_location['room_id'],
            is_alone=latest_location['is_alone'],
            last_seen_at=latest_location['last_seen_at']
        )
        
        return jsonify(asdict(response)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Additional endpoints for debugging and monitoring
@app.route('/location/lobbies/<lobby_id>/users/<user_id>/history', methods=['GET'])
def get_location_history(lobby_id, user_id):
    """Get location history for a user (for debugging)"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = db.get_location_history(user_id, lobby_id, limit)
        
        return jsonify({
            'user_id': user_id,
            'lobby_id': lobby_id,
            'history': [asdict(loc) for loc in history]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/location/lobbies/<lobby_id>/locations', methods=['GET'])
def get_lobby_locations(lobby_id):
    """Get latest locations of all users in a lobby (for debugging)"""
    try:
        locations = db.get_lobby_locations(lobby_id)
        
        return jsonify({
            'lobby_id': lobby_id,
            'locations': locations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.get_lobby_locations('test')
        return jsonify({
            'status': 'OK',
            'service': 'Location Service Python',
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'service': 'Location Service Python',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3008, debug=True)