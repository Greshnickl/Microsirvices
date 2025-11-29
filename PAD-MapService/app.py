from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from database import Database
from models import *

app = Flask(__name__)
CORS(app)
db = Database()

# API Routes
@app.route('/maps', methods=['GET'])
def get_maps():
    """Get paginated list of maps"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        
        result = db.get_maps(page, page_size)
        
        return jsonify({
            'total': result['total'],
            'page': result['page'],
            'pageSize': result['page_size'],
            'maps': result['maps']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/maps/<map_id>', methods=['GET'])
def get_map(map_id):
    """Get full map details"""
    try:
        map_obj = db.get_map(map_id)
        if not map_obj:
            return jsonify({'error': 'Map not found'}), 404
        
        response = {
            'id': map_obj.id,
            'name': map_obj.name,
            'rooms': [{'id': r.id, 'name': r.name} for r in map_obj.rooms],
            'connections': [{'from': c.from_room, 'to': c.to_room} for c in map_obj.connections],
            'objects': [{
                'id': o.id,
                'roomId': o.room_id,
                'type': o.type,
                'meta': o.meta
            } for o in map_obj.objects],
            'hidingSpots': [{
                'id': h.id,
                'roomId': h.room_id,
                'meta': h.meta
            } for h in map_obj.hiding_spots]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/maps', methods=['POST'])
def create_map():
    """Create a new map"""
    try:
        data = request.get_json()
        req = CreateMapRequest(**data)
        
        # Validate input
        if not req.name:
            return jsonify({'error': 'Map name is required'}), 400
        
        # Create map
        map_id = db.generate_uuid()
        rooms = []
        
        # Create rooms from request
        for room_data in req.rooms:
            room_id = db.generate_uuid()
            rooms.append(Room(id=room_id, name=room_data.get('name', 'Unnamed Room')))
        
        map_obj = Map(id=map_id, name=req.name, rooms=rooms)
        
        db.create_map(map_obj)
        
        return jsonify({'mapId': map_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/maps/<map_id>', methods=['PATCH'])
def update_map(map_id):
    """Update map details"""
    try:
        data = request.get_json()
        req = UpdateMapRequest(**data)
        
        # Check if map exists
        existing_map = db.get_map(map_id)
        if not existing_map:
            return jsonify({'error': 'Map not found'}), 404
        
        # Validate input
        if not req.name:
            return jsonify({'error': 'No fields to update'}), 400
        
        # Update map
        db.update_map(map_id, req.name)
        
        # Return updated map
        updated_map = db.get_map(map_id)
        
        return jsonify({
            'id': updated_map.id,
            'name': updated_map.name
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.get_maps()
        return jsonify({
            'status': 'OK',
            'service': 'Map Service Python',
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'service': 'Map Service Python',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3006, debug=True)