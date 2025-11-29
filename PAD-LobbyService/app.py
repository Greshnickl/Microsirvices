from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from database import Database
from models import *

app = Flask(__name__)
CORS(app)
db = Database()

# Helper functions
def find_player_in_lobby(lobby: Lobby, user_id: str) -> Player:
    """Find player in lobby by user_id"""
    for player in lobby.players:
        if player.user_id == user_id:
            return player
    return None

# API Routes
@app.route('/lobbies', methods=['POST'])
def create_lobby():
    """Create a new lobby"""
    try:
        data = request.get_json()
        req = CreateLobbyRequest(**data)
        
        # Validate input
        if not all([req.host_user_id, req.map_id, req.difficulty, req.max_players]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create lobby
        lobby_id = str(uuid.uuid4())
        lobby = Lobby(
            id=lobby_id,
            host_user_id=req.host_user_id,
            map_id=req.map_id,
            difficulty=req.difficulty,
            max_players=req.max_players
        )
        
        db.create_lobby(lobby)
        
        # Return response
        response = {
            'id': lobby.id,
            'difficulty': lobby.difficulty,
            'mapId': lobby.map_id,
            'players': [asdict(player) for player in lobby.players],
            'status': lobby.status
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/lobbies/<lobby_id>/join', methods=['POST'])
def join_lobby(lobby_id):
    """Join an existing lobby"""
    try:
        data = request.get_json()
        req = JoinLobbyRequest(**data)
        
        lobby = db.get_lobby(lobby_id)
        if not lobby:
            return jsonify({'error': 'Lobby not found'}), 404
        
        # Check if user is already in lobby
        if find_player_in_lobby(lobby, req.user_id):
            return jsonify({'error': 'User already in lobby'}), 400
        
        # Check if lobby is full
        if len(lobby.players) >= lobby.max_players:
            return jsonify({'error': 'Lobby is full'}), 400
        
        # Check if lobby is open
        if lobby.status != 'open':
            return jsonify({'error': 'Lobby is not open for joining'}), 400
        
        # Add player to lobby
        new_player = Player(user_id=req.user_id)
        lobby.players.append(new_player)
        
        # Update lobby status if full
        if len(lobby.players) >= lobby.max_players:
            lobby.status = 'active'
        
        db.update_lobby(lobby)
        
        response = {
            'id': lobby.id,
            'players': [{'userId': p.user_id} for p in lobby.players]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/lobbies/<lobby_id>/leave', methods=['POST'])
def leave_lobby(lobby_id):
    """Leave a lobby"""
    try:
        data = request.get_json()
        req = LeaveLobbyRequest(**data)
        
        lobby = db.get_lobby(lobby_id)
        if not lobby:
            return jsonify({'error': 'Lobby not found'}), 404
        
        # Find and remove player
        player_to_remove = find_player_in_lobby(lobby, req.user_id)
        if not player_to_remove:
            return jsonify({'error': 'User not in lobby'}), 400
        
        lobby.players = [p for p in lobby.players if p.user_id != req.user_id]
        
        # Update lobby status
        if len(lobby.players) == 0:
            lobby.status = 'closed'
        elif lobby.status == 'active' and len(lobby.players) < lobby.max_players:
            lobby.status = 'open'
        
        # If host leaves, assign new host
        if req.user_id == lobby.host_user_id and lobby.players:
            lobby.host_user_id = lobby.players[0].user_id
        
        db.update_lobby(lobby)
        
        return jsonify({'left': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/lobbies/<lobby_id>/players/<user_id>', methods=['PATCH'])
def update_player(lobby_id, user_id):
    """Update player state"""
    try:
        data = request.get_json()
        req = UpdatePlayerRequest(**data)
        
        lobby = db.get_lobby(lobby_id)
        if not lobby:
            return jsonify({'error': 'Lobby not found'}), 404
        
        player = find_player_in_lobby(lobby, user_id)
        if not player:
            return jsonify({'error': 'Player not found in lobby'}), 404
        
        # Update player fields
        if req.sanity is not None:
            player.sanity = max(0.0, min(100.0, req.sanity))
        if req.dead is not None:
            player.dead = req.dead
        
        db.update_lobby(lobby)
        
        response = {
            'userId': player.user_id,
            'sanity': player.sanity,
            'dead': player.dead
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/lobbies/<lobby_id>/items/bring', methods=['POST'])
def bring_item(lobby_id):
    """Bring item into lobby"""
    try:
        data = request.get_json()
        req = BringItemRequest(**data)
        
        lobby = db.get_lobby(lobby_id)
        if not lobby:
            return jsonify({'error': 'Lobby not found'}), 404
        
        player = find_player_in_lobby(lobby, req.user_id)
        if not player:
            return jsonify({'error': 'Player not found in lobby'}), 404
        
        # Add item to player's items
        if req.inventory_id not in player.items:
            player.items.append(req.inventory_id)
        
        db.update_lobby(lobby)
        
        return jsonify({'added': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/lobbies/<lobby_id>', methods=['GET'])
def get_lobby(lobby_id):
    """Get current lobby state"""
    try:
        lobby = db.get_lobby(lobby_id)
        if not lobby:
            return jsonify({'error': 'Lobby not found'}), 404
        
        response = {
            'id': lobby.id,
            'difficulty': lobby.difficulty,
            'mapId': lobby.map_id,
            'players': [{
                'userId': p.user_id,
                'sanity': p.sanity,
                'dead': p.dead
            } for p in lobby.players],
            'status': lobby.status
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.get_all_lobbies()
        return jsonify({
            'status': 'OK',
            'service': 'Lobby Service Python',
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'service': 'Lobby Service Python',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3005, debug=True)