from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from database import Database
from models import *
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app, origins="*")

# Initialize SocketIO with async_mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize database
db = Database()

# Store active connections (in production, use Redis)
active_connections = {}

# REST API Routes
@app.route('/chat/<lobby_id>/history', methods=['GET'])
def get_chat_history(lobby_id):
    """Retrieve chat history for a specific lobby"""
    try:
        limit = request.args.get('limit', 100, type=int)
        messages = db.get_chat_history(lobby_id, limit)
        
        response = ChatHistoryResponse(
            lobby_id=lobby_id,
            messages=[{
                'senderId': msg.sender_id,
                'senderName': msg.sender_name,
                'message': msg.message,
                'timestamp': msg.timestamp
            } for msg in messages]
        )
        
        return jsonify(asdict(response)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<lobby_id>/send', methods=['POST'])
def send_message(lobby_id):
    """Send a chat message to the lobby"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['senderId', 'senderName', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create message
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        message = ChatMessage(
            id=message_id,
            lobby_id=lobby_id,
            sender_id=data['senderId'],
            sender_name=data['senderName'],
            message=data['message'],
            timestamp=timestamp
        )
        
        # Save to database
        db.save_message(message)
        
        # Broadcast via WebSocket
        socketio.emit('new_message', {
            'senderId': message.sender_id,
            'senderName': message.sender_name,
            'message': message.message,
            'timestamp': message.timestamp
        }, room=lobby_id)
        
        response = SendMessageResponse(
            status="sent",
            lobby_id=lobby_id,
            timestamp=timestamp
        )
        
        return jsonify(asdict(response)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<lobby_id>/clear', methods=['DELETE'])
def clear_chat(lobby_id):
    """Clear the chat history for a session"""
    try:
        # Check if lobby exists (optional - you might want to verify lobby exists)
        messages_deleted = db.clear_chat_history(lobby_id)
        
        # Notify all connected clients
        socketio.emit('chat_cleared', {
            'lobbyId': lobby_id,
            'clearedAt': datetime.utcnow().isoformat() + "Z"
        }, room=lobby_id)
        
        response = ClearChatResponse(
            message=f"Chat history cleared for lobby {lobby_id}"
        )
        
        return jsonify(asdict(response)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<lobby_id>/stats', methods=['GET'])
def get_chat_stats(lobby_id):
    """Get chat statistics for a lobby (optional endpoint)"""
    try:
        stats = db.get_lobby_stats(lobby_id)
        
        return jsonify({
            'lobbyId': lobby_id,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.get_chat_history('test-lobby', 1)
        return jsonify({
            'status': 'OK',
            'service': 'Chat Service Python',
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'active_connections': len(active_connections)
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'service': 'Chat Service Python',
            'error': str(e)
        }), 500

# WebSocket Handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {
        'event': 'connected',
        'data': {
            'status': 'connected',
            'message': 'Successfully connected to chat service'
        }
    })

@socketio.on('join_lobby')
def handle_join_lobby(data):
    """Handle joining a lobby room"""
    try:
        lobby_id = data.get('lobbyId')
        user_id = data.get('userId')
        user_name = data.get('userName')
        
        if not lobby_id:
            emit('error', {'message': 'Lobby ID is required'})
            return
        
        # Join the room
        join_room(lobby_id)
        
        # Store connection info
        active_connections[request.sid] = {
            'lobby_id': lobby_id,
            'user_id': user_id,
            'user_name': user_name
        }
        
        # Send confirmation
        emit('joined_lobby', {
            'event': 'joined_lobby',
            'data': {
                'lobbyId': lobby_id,
                'status': 'listening',
                'userId': user_id,
                'userName': user_name
            }
        })
        
        # Notify others in the lobby (optional)
        if user_name:
            socketio.emit('user_joined', {
                'event': 'user_joined',
                'data': {
                    'userId': user_id,
                    'userName': user_name,
                    'timestamp': datetime.utcnow().isoformat() + "Z"
                }
            }, room=lobby_id, skip_sid=request.sid)
        
        print(f"User {user_name} ({user_id}) joined lobby {lobby_id}")
        
    except Exception as e:
        emit('error', {'message': f'Failed to join lobby: {str(e)}'})

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message via WebSocket"""
    try:
        lobby_id = data.get('lobbyId')
        sender_id = data.get('senderId')
        sender_name = data.get('senderName')
        message = data.get('message')
        
        if not all([lobby_id, sender_id, sender_name, message]):
            emit('error', {'message': 'Missing required fields'})
            return
        
        # Create and save message
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        chat_message = ChatMessage(
            id=message_id,
            lobby_id=lobby_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message=message,
            timestamp=timestamp
        )
        
        db.save_message(chat_message)
        
        # Broadcast to all in the lobby
        socketio.emit('new_message', {
            'event': 'new_message',
            'data': {
                'senderId': sender_id,
                'senderName': sender_name,
                'message': message,
                'timestamp': timestamp
            }
        }, room=lobby_id)
        
        print(f"Message sent in lobby {lobby_id} by {sender_name}")
        
    except Exception as e:
        emit('error', {'message': f'Failed to send message: {str(e)}'})

@socketio.on('leave_lobby')
def handle_leave_lobby(data):
    """Handle leaving a lobby room"""
    try:
        lobby_id = data.get('lobbyId')
        user_id = data.get('userId')
        user_name = data.get('userName')
        
        if lobby_id:
            leave_room(lobby_id)
            
            # Notify others in the lobby (optional)
            if user_name:
                socketio.emit('user_left', {
                    'event': 'user_left',
                    'data': {
                        'userId': user_id,
                        'userName': user_name,
                        'timestamp': datetime.utcnow().isoformat() + "Z"
                    }
                }, room=lobby_id, skip_sid=request.sid)
        
        # Remove from active connections
        if request.sid in active_connections:
            del active_connections[request.sid]
        
        emit('left_lobby', {
            'event': 'left_lobby',
            'data': {
                'lobbyId': lobby_id,
                'status': 'left'
            }
        })
        
        print(f"User left lobby {lobby_id}")
        
    except Exception as e:
        emit('error', {'message': f'Failed to leave lobby: {str(e)}'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    connection_info = active_connections.get(request.sid)
    if connection_info:
        lobby_id = connection_info.get('lobby_id')
        user_name = connection_info.get('user_name')
        
        # Notify others in the lobby
        if lobby_id and user_name:
            socketio.emit('user_left', {
                'event': 'user_left',
                'data': {
                    'userId': connection_info.get('user_id'),
                    'userName': user_name,
                    'timestamp': datetime.utcnow().isoformat() + "Z"
                }
            }, room=lobby_id, skip_sid=request.sid)
        
        # Remove from active connections
        del active_connections[request.sid]
    
    print(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3010, debug=True)