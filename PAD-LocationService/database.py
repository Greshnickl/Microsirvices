import psycopg2
import json
from psycopg2.extras import RealDictCursor
from models import LocationSample, LocationHistory
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
                database=os.getenv('DB_NAME', 'locationdb'),
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
                    CREATE TABLE IF NOT EXISTS location_history (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL,
                        lobby_id VARCHAR(36) NOT NULL,
                        room_id VARCHAR(36) NOT NULL,
                        is_speaking BOOLEAN DEFAULT FALSE,
                        group_users JSONB DEFAULT '[]',
                        is_hiding BOOLEAN DEFAULT FALSE,
                        recorded_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_location_user_lobby ON location_history (user_id, lobby_id);
                    CREATE INDEX IF NOT EXISTS idx_location_lobby ON location_history (lobby_id);
                    CREATE INDEX IF NOT EXISTS idx_location_recorded_at ON location_history (recorded_at DESC);
                """)
                self.connection.commit()
                print("✅ Database tables created")
                
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise

    def track_location(self, location: LocationSample):
        """Store a location sample"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO location_history 
                    (user_id, lobby_id, room_id, is_speaking, group_users, is_hiding, recorded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    location.user_id,
                    location.lobby_id,
                    location.room_id,
                    location.is_speaking,
                    json.dumps(location.group),
                    location.is_hiding,
                    location.at
                ))
                self.connection.commit()
                return True
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def get_latest_location(self, user_id: str, lobby_id: str):
        """Get the latest location for a user in a lobby"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT room_id, is_speaking, group_users, is_hiding, recorded_at
                    FROM location_history 
                    WHERE user_id = %s AND lobby_id = %s 
                    ORDER BY recorded_at DESC 
                    LIMIT 1
                """, (user_id, lobby_id))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                # Calculate if user is alone (group is empty or only contains themselves)
                group_users = result['group_users'] or []
                is_alone = len(group_users) == 0 or (len(group_users) == 1 and group_users[0] == user_id)
                
                return {
                    'room_id': result['room_id'],
                    'is_alone': is_alone,
                    'last_seen_at': result['recorded_at'].isoformat() + "Z"
                }
                
        except Exception as e:
            raise e

    def get_location_history(self, user_id: str, lobby_id: str, limit: int = 10):
        """Get location history for a user in a lobby"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT user_id, lobby_id, room_id, is_speaking, group_users, is_hiding, 
                           recorded_at, created_at
                    FROM location_history 
                    WHERE user_id = %s AND lobby_id = %s 
                    ORDER BY recorded_at DESC 
                    LIMIT %s
                """, (user_id, lobby_id, limit))
                
                results = cursor.fetchall()
                history = []
                
                for result in results:
                    location = LocationHistory(
                        user_id=result['user_id'],
                        lobby_id=result['lobby_id'],
                        room_id=result['room_id'],
                        is_speaking=result['is_speaking'],
                        group=result['group_users'],
                        is_hiding=result['is_hiding'],
                        recorded_at=result['recorded_at'].isoformat() + "Z",
                        created_at=result['created_at'].isoformat() + "Z"
                    )
                    history.append(location)
                
                return history
                
        except Exception as e:
            raise e

    def get_lobby_locations(self, lobby_id: str):
        """Get latest locations of all users in a lobby"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # This query gets the latest location for each user in the lobby
                cursor.execute("""
                    SELECT DISTINCT ON (user_id) 
                        user_id, room_id, is_speaking, group_users, is_hiding, recorded_at
                    FROM location_history 
                    WHERE lobby_id = %s 
                    ORDER BY user_id, recorded_at DESC
                """, (lobby_id,))
                
                results = cursor.fetchall()
                locations = []
                
                for result in results:
                    group_users = result['group_users'] or []
                    is_alone = len(group_users) == 0 or (len(group_users) == 1 and group_users[0] == result['user_id'])
                    
                    locations.append({
                        'user_id': result['user_id'],
                        'room_id': result['room_id'],
                        'is_speaking': result['is_speaking'],
                        'is_alone': is_alone,
                        'is_hiding': result['is_hiding'],
                        'last_seen_at': result['recorded_at'].isoformat() + "Z"
                    })
                
                return locations
                
        except Exception as e:
            raise e

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()