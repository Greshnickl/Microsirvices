from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from database import Database
from models import *

app = Flask(__name__)
CORS(app)
db = Database()

# API Routes
@app.route('/ghosts', methods=['GET'])
def get_ghosts():
    """Get all ghost types"""
    try:
        ghosts = db.get_ghosts()
        
        response = {
            'ghosts': [{
                'id': ghost.id,
                'name': ghost.name,
                'typeASymptoms': ghost.type_a_symptoms
            } for ghost in ghosts]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ghosts/<ghost_id>', methods=['GET'])
def get_ghost(ghost_id):
    """Get ghost by ID"""
    try:
        ghost = db.get_ghost(ghost_id)
        if not ghost:
            return jsonify({'error': 'Ghost not found'}), 404
        
        response = {
            'id': ghost.id,
            'name': ghost.name,
            'typeASymptoms': ghost.type_a_symptoms
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ghosts', methods=['POST'])
def create_ghost():
    """Create a new ghost type"""
    try:
        data = request.get_json()
        req = CreateGhostRequest(**data)
        
        # Validate input
        if not req.name:
            return jsonify({'error': 'Ghost name is required'}), 400
        
        # Create ghost
        ghost_id = db.generate_uuid()
        ghost = Ghost(
            id=ghost_id,
            name=req.name,
            type_a_symptoms=req.type_a_symptoms,
            type_b_symptoms=req.type_b_symptoms,
            type_c_symptoms=req.type_c_symptoms
        )
        
        db.create_ghost(ghost)
        
        return jsonify({'id': ghost_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ghosts/<ghost_id>', methods=['PATCH'])
def update_ghost(ghost_id):
    """Update ghost type"""
    try:
        data = request.get_json()
        req = UpdateGhostRequest(**data)
        
        # Check if ghost exists
        existing_ghost = db.get_ghost(ghost_id)
        if not existing_ghost:
            return jsonify({'error': 'Ghost not found'}), 404
        
        # Prepare update data
        update_data = {}
        if req.name is not None:
            update_data['name'] = req.name
        if req.type_a_symptoms is not None:
            update_data['type_a_symptoms'] = req.type_a_symptoms
        if req.type_b_symptoms is not None:
            update_data['type_b_symptoms'] = req.type_b_symptoms
        if req.type_c_symptoms is not None:
            update_data['type_c_symptoms'] = req.type_c_symptoms
        
        # Update ghost
        db.update_ghost(ghost_id, update_data)
        
        # Return updated ghost
        updated_ghost = db.get_ghost(ghost_id)
        
        return jsonify({
            'id': updated_ghost.id,
            'name': updated_ghost.name
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.get_ghosts()
        return jsonify({
            'status': 'OK',
            'service': 'Ghost Service Python',
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'service': 'Ghost Service Python',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3007, debug=True)