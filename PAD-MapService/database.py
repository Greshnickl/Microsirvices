import psycopg2
import json
from psycopg2.extras import RealDictCursor
from models import Map, Room, Connection, MapObject, HidingSpot
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
                database=os.getenv('DB_NAME', 'mapdb'),
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
                    CREATE TABLE IF NOT EXISTS maps (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS rooms (
                        id VARCHAR(36) PRIMARY KEY,
                        map_id VARCHAR(36) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        FOREIGN KEY (map_id) REFERENCES maps(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS connections (
                        id SERIAL PRIMARY KEY,
                        map_id VARCHAR(36) NOT NULL,
                        from_room VARCHAR(36) NOT NULL,
                        to_room VARCHAR(36) NOT NULL,
                        FOREIGN KEY (map_id) REFERENCES maps(id) ON DELETE CASCADE,
                        FOREIGN KEY (from_room) REFERENCES rooms(id) ON DELETE CASCADE,
                        FOREIGN KEY (to_room) REFERENCES rooms(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS map_objects (
                        id VARCHAR(36) PRIMARY KEY,
                        map_id VARCHAR(36) NOT NULL,
                        room_id VARCHAR(36) NOT NULL,
                        type VARCHAR(100) NOT NULL,
                        meta JSONB DEFAULT '{}',
                        FOREIGN KEY (map_id) REFERENCES maps(id) ON DELETE CASCADE,
                        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS hiding_spots (
                        id VARCHAR(36) PRIMARY KEY,
                        map_id VARCHAR(36) NOT NULL,
                        room_id VARCHAR(36) NOT NULL,
                        meta JSONB DEFAULT '{}',
                        FOREIGN KEY (map_id) REFERENCES maps(id) ON DELETE CASCADE,
                        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                    );
                """)
                self.connection.commit()
                print("✅ Database tables created")
                
                # Seed initial data
                self.seed_data()
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise

    def seed_data(self):
        """Seed initial map data"""
        try:
            with self.connection.cursor() as cursor:
                # Check if data already exists
                cursor.execute("SELECT COUNT(*) as count FROM maps")
                result = cursor.fetchone()
                
                if result[0] == 0:
                    # Insert sample map
                    map_id = self.generate_uuid()
                    cursor.execute(
                        "INSERT INTO maps (id, name) VALUES (%s, %s)",
                        (map_id, "Willow Street House")
                    )
                    
                    # Insert sample rooms
                    room1_id = self.generate_uuid()
                    room2_id = self.generate_uuid()
                    cursor.execute(
                        "INSERT INTO rooms (id, map_id, name) VALUES (%s, %s, %s)",
                        (room1_id, map_id, "Kitchen")
                    )
                    cursor.execute(
                        "INSERT INTO rooms (id, map_id, name) VALUES (%s, %s, %s)",
                        (room2_id, map_id, "Living Room")
                    )
                    
                    # Insert sample connection
                    cursor.execute(
                        "INSERT INTO connections (map_id, from_room, to_room) VALUES (%s, %s, %s)",
                        (map_id, room1_id, room2_id)
                    )
                    
                    # Insert sample object
                    object_id = self.generate_uuid()
                    cursor.execute(
                        "INSERT INTO map_objects (id, map_id, room_id, type, meta) VALUES (%s, %s, %s, %s, %s)",
                        (object_id, map_id, room1_id, "Mirror", json.dumps({"reflective": True}))
                    )
                    
                    # Insert sample hiding spot
                    hiding_id = self.generate_uuid()
                    cursor.execute(
                        "INSERT INTO hiding_spots (id, map_id, room_id, meta) VALUES (%s, %s, %s, %s)",
                        (hiding_id, map_id, room2_id, json.dumps({"cover": "car"}))
                    )
                    
                    self.connection.commit()
                    print("✅ Sample data seeded")
                    
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Seeding data failed: {e}")

    def generate_uuid(self):
        return str(uuid.uuid4())

    def get_maps(self, page=1, page_size=20):
        """Get paginated list of maps"""
        try:
            offset = (page - 1) * page_size
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get total count
                cursor.execute("SELECT COUNT(*) as total FROM maps")
                total = cursor.fetchone()['total']
                
                # Get maps
                cursor.execute("""
                    SELECT id, name, created_at, updated_at 
                    FROM maps 
                    ORDER BY name 
                    LIMIT %s OFFSET %s
                """, (page_size, offset))
                maps = cursor.fetchall()
                
                return {
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'maps': [{'id': m['id'], 'name': m['name']} for m in maps]
                }
                
        except Exception as e:
            raise e

    def get_map(self, map_id):
        """Get full map details"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get map basic info
                cursor.execute("SELECT id, name, created_at, updated_at FROM maps WHERE id = %s", (map_id,))
                map_data = cursor.fetchone()
                
                if not map_data:
                    return None
                
                # Get rooms
                cursor.execute("SELECT id, name FROM rooms WHERE map_id = %s", (map_id,))
                rooms = [Room(id=r['id'], name=r['name']) for r in cursor.fetchall()]
                
                # Get connections
                cursor.execute("SELECT from_room, to_room FROM connections WHERE map_id = %s", (map_id,))
                connections = [Connection(from_room=c['from_room'], to_room=c['to_room']) for c in cursor.fetchall()]
                
                # Get objects
                cursor.execute("SELECT id, room_id, type, meta FROM map_objects WHERE map_id = %s", (map_id,))
                objects = [MapObject(id=o['id'], room_id=o['room_id'], type=o['type'], meta=o['meta']) for o in cursor.fetchall()]
                
                # Get hiding spots
                cursor.execute("SELECT id, room_id, meta FROM hiding_spots WHERE map_id = %s", (map_id,))
                hiding_spots = [HidingSpot(id=h['id'], room_id=h['room_id'], meta=h['meta']) for h in cursor.fetchall()]
                
                return Map(
                    id=map_data['id'],
                    name=map_data['name'],
                    rooms=rooms,
                    connections=connections,
                    objects=objects,
                    hiding_spots=hiding_spots,
                    created_at=map_data['created_at'].isoformat() + "Z",
                    updated_at=map_data['updated_at'].isoformat() + "Z"
                )
                
        except Exception as e:
            raise e

    def create_map(self, map_obj: Map):
        """Create a new map"""
        try:
            with self.connection.cursor() as cursor:
                # Insert map
                cursor.execute(
                    "INSERT INTO maps (id, name) VALUES (%s, %s)",
                    (map_obj.id, map_obj.name)
                )
                
                # Insert rooms
                for room in map_obj.rooms:
                    cursor.execute(
                        "INSERT INTO rooms (id, map_id, name) VALUES (%s, %s, %s)",
                        (room.id, map_obj.id, room.name)
                    )
                
                self.connection.commit()
                return map_obj.id
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def update_map(self, map_id: str, name: str):
        """Update map name"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE maps SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (name, map_id)
                )
                self.connection.commit()
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()