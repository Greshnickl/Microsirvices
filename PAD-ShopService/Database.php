<?php
class Database {
    private $connection;
    
    public function __construct() {
        $host = getenv('DB_HOST') ?: 'mysql';
        $dbname = getenv('DB_NAME') ?: 'shopdb';
        $username = getenv('DB_USER') ?: 'root';
        $password = getenv('DB_PASSWORD') ?: 'password';
        
        $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8mb4";
        
        try {
            $this->connection = new PDO($dsn, $username, $password, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ]);
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            throw $e;
        }
    }
    
    public function getConnection() {
        return $this->connection;
    }
    
    public function initialize() {
        $sql = "
            CREATE TABLE IF NOT EXISTS items (
                id VARCHAR(36) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                durability INT NOT NULL,
                price_amount DECIMAL(10,2) NOT NULL,
                price_currency VARCHAR(10) DEFAULT 'CRD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_id VARCHAR(36) NOT NULL,
                price_amount DECIMAL(10,2) NOT NULL,
                price_currency VARCHAR(10) DEFAULT 'CRD',
                effective_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            );
        ";
        
        $this->connection->exec($sql);
        
        // Seed initial data
        $this->seedData();
    }
    
    private function seedData() {
        // Check if data already exists
        $stmt = $this->connection->query("SELECT COUNT(*) as count FROM items");
        $result = $stmt->fetch();
        
        if ($result['count'] == 0) {
            $items = [
                [
                    'id' => $this->generateUUID(),
                    'title' => 'EMF Reader',
                    'description' => 'Detects electromagnetic fields.',
                    'durability' => 5,
                    'price_amount' => 50.00,
                    'price_currency' => 'CRD'
                ],
                [
                    'id' => $this->generateUUID(),
                    'title' => 'Thermometer',
                    'description' => 'Measures temperature.',
                    'durability' => 10,
                    'price_amount' => 30.00,
                    'price_currency' => 'CRD'
                ]
            ];
            
            foreach ($items as $item) {
                $sql = "INSERT INTO items (id, title, description, durability, price_amount, price_currency) 
                        VALUES (:id, :title, :description, :durability, :price_amount, :price_currency)";
                $stmt = $this->connection->prepare($sql);
                $stmt->execute($item);
                
                // Add to price history
                $historySql = "INSERT INTO price_history (item_id, price_amount, price_currency) 
                              VALUES (:item_id, :price_amount, :price_currency)";
                $historyStmt = $this->connection->prepare($historySql);
                $historyStmt->execute([
                    'item_id' => $item['id'],
                    'price_amount' => $item['price_amount'],
                    'price_currency' => $item['price_currency']
                ]);
            }
        }
    }
    
    private function generateUUID() {
        return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
        );
    }
}
?>