from flask import Flask, request, jsonify
from flask_cors import CORS
from database import Database
from models import *
from datetime import datetime

app = Flask(__name__)
CORS(app)
db = Database()

# API Routes
@app.route('/inventory/<user_id>', methods=['GET'])
def get_inventory(user_id):
    """Retrieve the list of items owned by a player"""
    try:
        items = db.get_user_inventory(user_id)
        
        response = InventoryResponse(
            user_id=user_id,
            items=[{
                'id': item.item_id,
                'name': item.name,
                'durability': item.durability,
                'maxDurability': item.max_durability,
                'equipped': item.equipped
            } for item in items]
        )
        
        return jsonify(asdict(response)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/inventory/<user_id>/add', methods=['POST'])
def add_item(user_id):
    """Add a new item to the player's inventory"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['itemId', 'name', 'durability']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Prepare item data
        item_data = {
            'item_id': data['itemId'],
            'name': data['name'],
            'durability': data['durability'],
            'max_durability': data.get('maxDurability', data['durability'])
        }
        
        # Add item to inventory
        inventory_id = db.add_item_to_inventory(user_id, item_data)
        
        response = AddItemResponse(
            message="Item added successfully",
            inventory_id=inventory_id
        )
        
        return jsonify(asdict(response)), 201
        
    except Exception as e:
        if "already has this item" in str(e):
            return jsonify({'error': 'Item already exists in inventory'}), 400
        return jsonify({'error': str(e)}), 500

@app.route('/inventory/<user_id>/update', methods=['PATCH'])
def update_item(user_id):
    """Update item durability or equipped status"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'itemId' not in data:
            return jsonify({'error': 'Missing required field: itemId'}), 400
        
        # Validate that at least one field to update is provided
        if 'durability' not in data and 'equipped' not in data:
            return jsonify({'error': 'No fields to update. Provide durability or equipped'}), 400
        
        # Prepare update data
        update_data = {
            'item_id': data['itemId']
        }
        
        if 'durability' in data:
            update_data['durability'] = data['durability']
        
        if 'equipped' in data:
            update_data['equipped'] = data['equipped']
        
        # Update item
        rows_updated = db.update_inventory_item(user_id, update_data)
        
        if rows_updated == 0:
            return jsonify({'error': 'Item not found in inventory'}), 404
        
        # Get updated item
        updated_item = db.get_inventory_item(user_id, data['itemId'])
        
        response = UpdateItemResponse(
            item_id=updated_item.item_id,
            durability=updated_item.durability,
            equipped=updated_item.equipped,
            status="updated"
        )
        
        return jsonify(asdict(response)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/inventory/<user_id>/remove/<item_id>', methods=['DELETE'])
def remove_item(user_id, item_id):
    """Remove an item from the player's inventory"""
    try:
        # Remove item from inventory
        rows_deleted = db.remove_item_from_inventory(user_id, item_id)
        
        if rows_deleted == 0:
            return jsonify({'error': 'Item not found in inventory'}), 404
        
        response = RemoveItemResponse(
            message="Item removed successfully",
            removed_item_id=item_id
        )
        
        return jsonify(asdict(response)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.get_user_inventory('uuid-user-1')
        return jsonify({
            'status': 'OK',
            'service': 'Inventory Service Python',
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'service': 'Inventory Service Python',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3009, debug=True)