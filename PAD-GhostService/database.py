import psycopg2
import json
from psycopg2.extras import RealDictCursor
from models import Ghost
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
                database=os.getenv('DB_NAME', 'ghostdb'),
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
                    CREATE TABLE IF NOT EXISTS ghosts (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        type_a_symptoms JSONB DEFAULT '[]',
                        type_b_symptoms JSONB DEFAULT '[]',
                        type_c_symptoms JSONB DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        """Seed initial ghost data"""
        try:
            with self.connection.cursor() as cursor:
                # Check if data already exists
                cursor.execute("SELECT COUNT(*) as count FROM ghosts")
                result = cursor.fetchone()
                
                if result[0] == 0:
                    # Insert sample ghosts
                    sample_ghosts = [
                        {
                            'id': self.generate_uuid(),
                            'name': 'Banshee',
                            'type_a_symptoms': ['Screams', 'Breaks mirrors', 'EMF Level 5']
                        },
                        {
                            'id': self.generate_uuid(),
                            'name': 'Spirit',
                            'type_a_symptoms': ['Ghost Writing', 'Spirit Box', 'Freezing Temperatures']
                        },
                        {
                            'id': self.generate_uuid(),
                            'name': 'Demon',
                            'type_a_symptoms': ['Ghost Writing', 'Freezing Temperatures', 'Crucifix effective']
                        }
                    ]
                    
                    for ghost in sample_ghosts:
                        cursor.execute(
                            "INSERT INTO ghosts (id, name, type_a_symptoms) VALUES (%s, %s, %s)",
                            (ghost['id'], ghost['name'], json.dumps(ghost['type_a_symptoms']))
                        )
                    
                    self.connection.commit()
                    print("✅ Sample ghost data seeded")
                    
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Seeding data failed: {e}")

    def generate_uuid(self):
        return str(uuid.uuid4())

    def get_ghosts(self):
        """Get all ghosts"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, type_a_symptoms, type_b_symptoms, type_c_symptoms, 
                           created_at, updated_at 
                    FROM ghosts 
                    ORDER BY name
                """)
                ghosts_data = cursor.fetchall()
                
                ghosts = []
                for ghost_data in ghosts_data:
                    ghost = Ghost(
                        id=ghost_data['id'],
                        name=ghost_data['name'],
                        type_a_symptoms=ghost_data['type_a_symptoms'],
                        type_b_symptoms=ghost_data['type_b_symptoms'],
                        type_c_symptoms=ghost_data['type_c_symptoms'],
                        created_at=ghost_data['created_at'].isoformat() + "Z",
                        updated_at=ghost_data['updated_at'].isoformat() + "Z"
                    )
                    ghosts.append(ghost)
                
                return ghosts
                
        except Exception as e:
            raise e

    def get_ghost(self, ghost_id):
        """Get ghost by ID"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, type_a_symptoms, type_b_symptoms, type_c_symptoms,
                           created_at, updated_at 
                    FROM ghosts 
                    WHERE id = %s
                """, (ghost_id,))
                ghost_data = cursor.fetchone()
                
                if not ghost_data:
                    return None
                
                return Ghost(
                    id=ghost_data['id'],
                    name=ghost_data['name'],
                    type_a_symptoms=ghost_data['type_a_symptoms'],
                    type_b_symptoms=ghost_data['type_b_symptoms'],
                    type_c_symptoms=ghost_data['type_c_symptoms'],
                    created_at=ghost_data['created_at'].isoformat() + "Z",
                    updated_at=ghost_data['updated_at'].isoformat() + "Z"
                )
                
        except Exception as e:
            raise e

    def create_ghost(self, ghost: Ghost):
        """Create a new ghost"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ghosts (id, name, type_a_symptoms, type_b_symptoms, type_c_symptoms)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    ghost.id,
                    ghost.name,
                    json.dumps(ghost.type_a_symptoms),
                    json.dumps(ghost.type_b_symptoms),
                    json.dumps(ghost.type_c_symptoms)
                ))
                self.connection.commit()
                return ghost.id
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def update_ghost(self, ghost_id: str, update_data: dict):
        """Update ghost data"""
        try:
            with self.connection.cursor() as cursor:
                # Build dynamic update query
                set_clauses = []
                params = []
                
                if 'name' in update_data and update_data['name'] is not None:
                    set_clauses.append("name = %s")
                    params.append(update_data['name'])
                
                if 'type_a_symptoms' in update_data and update_data['type_a_symptoms'] is not None:
                    set_clauses.append("type_a_symptoms = %s")
                    params.append(json.dumps(update_data['type_a_symptoms']))
                
                if 'type_b_symptoms' in update_data and update_data['type_b_symptoms'] is not None:
                    set_clauses.append("type_b_symptoms = %s")
                    params.append(json.dumps(update_data['type_b_symptoms']))
                
                if 'type_c_symptoms' in update_data and update_data['type_c_symptoms'] is not None:
                    set_clauses.append("type_c_symptoms = %s")
                    params.append(json.dumps(update_data['type_c_symptoms']))
                
                # Always update the updated_at timestamp
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                
                if not set_clauses:
                    return  # Nothing to update
                
                params.append(ghost_id)
                
                query = f"UPDATE ghosts SET {', '.join(set_clauses)} WHERE id = %s"
                cursor.execute(query, params)
                self.connection.commit()
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()