import psycopg2
import json
from psycopg2.extras import RealDictCursor
from models import Lobby, Player
import os

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
                database=os.getenv('DB_NAME', 'lobbydb'),
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
                    CREATE TABLE IF NOT EXISTS lobbies (
                        id VARCHAR(36) PRIMARY KEY,
                        host_user_id VARCHAR(36) NOT NULL,
                        map_id VARCHAR(36) NOT NULL,
                        difficulty VARCHAR(50) NOT NULL,
                        max_players INTEGER NOT NULL,
                        players JSONB NOT NULL DEFAULT '[]',
                        status VARCHAR(50) DEFAULT 'open',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.connection.commit()
                print("✅ Database tables created")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise

    def create_lobby(self, lobby: Lobby) -> str:
        """Create a new lobby"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO lobbies (id, host_user_id, map_id, difficulty, max_players, players, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    lobby.id,
                    lobby.host_user_id,
                    lobby.map_id,
                    lobby.difficulty,
                    lobby.max_players,
                    json.dumps([asdict(p) for p in lobby.players]),
                    lobby.status
                ))
                self.connection.commit()
                return lobby.id
        except Exception as e:
            self.connection.rollback()
            raise e

    def get_lobby(self, lobby_id: str) -> Lobby:
        """Get lobby by ID"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM lobbies WHERE id = %s", (lobby_id,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                # Convert JSON players to Player objects
                players_data = result['players']
                players = [Player(**player_data) for player_data in players_data]
                
                return Lobby(
                    id=result['id'],
                    host_user_id=result['host_user_id'],
                    map_id=result['map_id'],
                    difficulty=result['difficulty'],
                    max_players=result['max_players'],
                    players=players,
                    status=result['status'],
                    created_at=result['created_at'].isoformat() + "Z"
                )
        except Exception as e:
            raise e

    def update_lobby(self, lobby: Lobby):
        """Update lobby data"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE lobbies 
                    SET players = %s, status = %s
                    WHERE id = %s
                """, (
                    json.dumps([asdict(p) for p in lobby.players]),
                    lobby.status,
                    lobby.id
                ))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def get_all_lobbies(self):
        """Get all lobbies (for debugging)"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM lobbies ORDER BY created_at DESC")
                return cursor.fetchall()
        except Exception as e:
            raise e

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()