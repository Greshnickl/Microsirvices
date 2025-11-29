import psycopg2
import json
from psycopg2.extras import RealDictCursor
from models import InventoryItem
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
                database=os.getenv('DB_NAME', 'inventorydb'),
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
                    CREATE TABLE IF NOT EXISTS inventory (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL,
                        item_id VARCHAR(36) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        durability INTEGER NOT NULL,
                        max_durability INTEGER NOT NULL,
                        equipped BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory (user_id);
                    CREATE INDEX IF NOT EXISTS idx_inventory_item_id ON inventory (item_id);
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_inventory_user_item ON inventory (user_id, item_id);
                """)
                self.connection.commit()
                print("✅ Database tables created")
                
                # Seed initial data for testing
                self.seed_data()
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise

    def seed_data(self):
        """Seed initial inventory data for testing"""
        try:
            with self.connection.cursor() as cursor:
                # Check if data already exists
                cursor.execute("SELECT COUNT(*) as count FROM inventory")
                result = cursor.fetchone()
                
                if result[0] == 0:
                    # Insert sample inventory items
                    sample_items = [
                        {
                            'id': self.generate_uuid(),
                            'user_id': 'uuid-user-1',
                            'item_id': 'uuid-item1',
                            'name': 'EMF Reader',
                            'durability': 7,
                            'max_durability': 10,
                            'equipped': False
                        },
                        {
                            'id': self.generate_uuid(),
                            'user_id': 'uuid-user-1',
                            'item_id': 'uuid-item2',
                            'name': 'Flashlight',
                            'durability': 3,
                            'max_durability': 5,
                            'equipped': True
                        },
                        {
                            'id': self.generate_uuid(),
                            'user_id': 'uuid-user-2',
                            'item_id': 'uuid-item3',
                            'name': 'Thermometer',
                            'durability': 8,
                            'max_durability': 10,
                            'equipped': False
                        }
                    ]
                    
                    for item in sample_items:
                        cursor.execute("""
                            INSERT INTO inventory (id, user_id, item_id, name, durability, max_durability, equipped)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            item['id'],
                            item['user_id'],
                            item['item_id'],
                            item['name'],
                            item['durability'],
                            item['max_durability'],
                            item['equipped']
                        ))
                    
                    self.connection.commit()
                    print("✅ Sample inventory data seeded")
                    
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Seeding data failed: {e}")

    def generate_uuid(self):
        return str(uuid.uuid4())

    def get_user_inventory(self, user_id: str):
        """Get all items in user's inventory"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, user_id, item_id, name, durability, max_durability, equipped,
                           created_at, updated_at
                    FROM inventory 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                
                results = cursor.fetchall()
                items = []
                
                for result in results:
                    item = InventoryItem(
                        id=result['id'],
                        user_id=result['user_id'],
                        item_id=result['item_id'],
                        name=result['name'],
                        durability=result['durability'],
                        max_durability=result['max_durability'],
                        equipped=result['equipped'],
                        created_at=result['created_at'].isoformat() + "Z",
                        updated_at=result['updated_at'].isoformat() + "Z"
                    )
                    items.append(item)
                
                return items
                
        except Exception as e:
            raise e

    def add_item_to_inventory(self, user_id: str, item_data: dict):
        """Add a new item to user's inventory"""
        try:
            with self.connection.cursor() as cursor:
                # Check if user already has this item
                cursor.execute("""
                    SELECT id FROM inventory WHERE user_id = %s AND item_id = %s
                """, (user_id, item_data['item_id']))
                
                existing_item = cursor.fetchone()
                
                if existing_item:
                    raise Exception("User already has this item in inventory")
                
                # Insert new item
                inventory_id = self.generate_uuid()
                max_durability = item_data.get('max_durability', item_data['durability'])
                
                cursor.execute("""
                    INSERT INTO inventory (id, user_id, item_id, name, durability, max_durability, equipped)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    inventory_id,
                    user_id,
                    item_data['item_id'],
                    item_data['name'],
                    item_data['durability'],
                    max_durability,
                    False  # Default to not equipped
                ))
                
                self.connection.commit()
                return inventory_id
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def update_inventory_item(self, user_id: str, update_data: dict):
        """Update item in user's inventory"""
        try:
            with self.connection.cursor() as cursor:
                # Build dynamic update query
                set_clauses = []
                params = []
                
                if 'durability' in update_data and update_data['durability'] is not None:
                    set_clauses.append("durability = %s")
                    params.append(update_data['durability'])
                
                if 'equipped' in update_data and update_data['equipped'] is not None:
                    set_clauses.append("equipped = %s")
                    params.append(update_data['equipped'])
                
                # Always update the updated_at timestamp
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                
                if not set_clauses:
                    return 0  # Nothing to update
                
                params.extend([user_id, update_data['item_id']])
                
                query = f"UPDATE inventory SET {', '.join(set_clauses)} WHERE user_id = %s AND item_id = %s"
                cursor.execute(query, params)
                self.connection.commit()
                
                return cursor.rowcount
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def remove_item_from_inventory(self, user_id: str, item_id: str):
        """Remove item from user's inventory"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM inventory 
                    WHERE user_id = %s AND item_id = %s
                """, (user_id, item_id))
                
                self.connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            self.connection.rollback()
            raise e

    def get_inventory_item(self, user_id: str, item_id: str):
        """Get specific item from user's inventory"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, user_id, item_id, name, durability, max_durability, equipped,
                           created_at, updated_at
                    FROM inventory 
                    WHERE user_id = %s AND item_id = %s
                """, (user_id, item_id))
                
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return InventoryItem(
                    id=result['id'],
                    user_id=result['user_id'],
                    item_id=result['item_id'],
                    name=result['name'],
                    durability=result['durability'],
                    max_durability=result['max_durability'],
                    equipped=result['equipped'],
                    created_at=result['created_at'].isoformat() + "Z",
                    updated_at=result['updated_at'].isoformat() + "Z"
                )
                
        except Exception as e:
            raise e

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()