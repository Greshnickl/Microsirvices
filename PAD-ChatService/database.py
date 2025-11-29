import psycopg2
import json
from psycopg2.extras import RealDictCursor
from models import ChatMessage
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.init_db()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'chatdb'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'password'),
                port=os.getenv('DB_PORT', '5432')
            )
            print("✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def init_db(self):
        """Initialize database tables"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id VARCHAR(36) PRIMARY KEY,
                        lobby_id VARCHAR(36) NOT NULL,
                        sender_id VARCHAR(36) NOT NULL,
                        sender_name VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_chat_lobby_id ON chat_messages (lobby_id);
                    CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_messages (timestamp DESC);
                """)
                self.connection.commit()
                print("✅ Database tables created")
                
                # Seed initial data for testing
                self.seed_data()
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise

    def seed_data(self):
        """Seed initial chat data for testing"""
        try:
            with self.connection.cursor() as cursor:
                # Check if data already exists
                cursor.execute("SELECT COUNT(*) as count FROM chat_messages")
                result = cursor.fetchone()
                
                if result[0] == 0:
                    # Insert sample chat messages
                    sample_messages = [
                        {
                            'id': self.generate_uuid(),
                            'lobby_id': 'uuid-lobby-1',
                            'sender_id': 'uuid-user1',
                            'sender_name': 'Danik',
                            'message': 'Anyone see ghost activity?',
                            'timestamp': '2025-10-23T19:40:00Z'
                        },
                        {
                            'id': self.generate_uuid(),
                            'lobby_id': 'uuid-lobby-1',
                            'sender_id': 'uuid-user2',
                            'sender_name': 'Vlad',
                            'message': 'Yes, EMF 5 in the basement!',
                            'timestamp': '2025-10-23T19:41:00Z'
                        },
                        {
                            'id': self.generate_uuid(),
                            'lobby_id': 'uuid-lobby-2',
                            'sender_id': 'uuid-user3',
                            'sender_name': 'Catalin',
                            'message': 'Starting investigation in the living room',
                            'timestamp': '2025-10-23T19:42:00Z'
                        }
                    ]
                    
                    for msg in sample_messages:
                        cursor.execute("""
                            INSERT INTO chat_messages (id, lobby_id, sender_id, sender_name, message, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            msg['id'],
                            msg['lobby_id'],
                            msg['sender_id'],
                            msg['sender_name'],
                            msg['message'],
                            msg['timestamp']
                        ))
                    
                    self.connection.commit()
                    print("✅ Sample chat data seeded")
                    
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Seeding data failed: {e}")

    def generate_uuid(self):
        return str(uuid.uuid4())

    def get_chat_history(self, lobby_id: str, limit: int = 100):
        """Get chat history for a lobby"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, lobby_id, sender_id, sender_name, message, timestamp
                    FROM chat_messages 
                    WHERE lobby_id = %s
                    ORDER BY timestamp ASC
                    LIMIT %s
                """, (lobby_id, limit))
                
                results = cursor.fetchall()
                messages = []
                
                for result in results:
                    message = ChatMessage(
                        id=result['id'],
                        lobby_id=result['lobby_id'],
                        sender_id=result['sender_id'],
                        sender_name=result['sender_name'],
                        message=result['message'],
                        timestamp=result['timestamp'].isoformat() + "Z"
                    )
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            raise e

    def save_message(self, message: ChatMessage):
        """Save a new chat message"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO chat_messages (id, lobby_id, sender_id, sender_name, message, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    message.id,
                    message.lobby_id,
                    message.sender_id,
                    message.sender_name,
                    message.message,
                    message.timestamp
                ))
                self.connection.commit()
                return True
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def clear_chat_history(self, lobby_id: str):
        """Clear all messages for a lobby"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM chat_messages 
                    WHERE lobby_id = %s
                """, (lobby_id,))
                
                self.connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def get_lobby_stats(self, lobby_id: str):
        """Get statistics for a lobby"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as message_count,
                        COUNT(DISTINCT sender_id) as unique_senders,
                        MIN(timestamp) as first_message,
                        MAX(timestamp) as last_message
                    FROM chat_messages 
                    WHERE lobby_id = %s
                """, (lobby_id,))
                
                return cursor.fetchone()
                
        except Exception as e:
            raise e

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()