<?php
class Database {
    private $connection;
    
    public function __construct() {
        $host = getenv('DB_HOST') ?: 'mysql';
        $dbname = getenv('DB_NAME') ?: 'journaldb';
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
            CREATE TABLE IF NOT EXISTS journals (
                id VARCHAR(36) PRIMARY KEY,
                lobby_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                guess_ghost_type_id VARCHAR(36),
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finalized_at TIMESTAMP NULL,
                actual_ghost_type_id VARCHAR(36),
                awarded_amount DECIMAL(10,2) DEFAULT 0,
                awarded_currency VARCHAR(10) DEFAULT 'CRD',
                INDEX idx_lobby_id (lobby_id),
                INDEX idx_user_id (user_id)
            );
            
            CREATE TABLE IF NOT EXISTS observations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                journal_id VARCHAR(36) NOT NULL,
                symptom TEXT NOT NULL,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (journal_id) REFERENCES journals(id) ON DELETE CASCADE,
                INDEX idx_journal_id (journal_id)
            );
        ";
        
        $this->connection->exec($sql);
    }
    
    public function generateUUID() {
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