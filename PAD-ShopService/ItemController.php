<?php
class ItemController {
    private $db;
    
    public function __construct($db) {
        $this->db = $db;
        $this->db->initialize();
    }
    
    public function getItems() {
        try {
            $page = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;
            $pageSize = isset($_GET['pageSize']) ? max(1, intval($_GET['pageSize'])) : 20;
            $offset = ($page - 1) * $pageSize;
            
            $conn = $this->db->getConnection();
            
            // Get total count
            $countStmt = $conn->query("SELECT COUNT(*) as total FROM items");
            $total = $countStmt->fetch()['total'];
            
            // Get items
            $stmt = $conn->prepare("
                SELECT id, title, description, durability, price_amount, price_currency 
                FROM items 
                ORDER BY title 
                LIMIT :limit OFFSET :offset
            ");
            $stmt->bindValue(':limit', $pageSize, PDO::PARAM_INT);
            $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
            $stmt->execute();
            $items = $stmt->fetchAll();
            
            // Format response
            $formattedItems = array_map(function($item) {
                return [
                    'id' => $item['id'],
                    'title' => $item['title'],
                    'description' => $item['description'],
                    'durability' => intval($item['durability']),
                    'price' => [
                        'amount' => floatval($item['price_amount']),
                        'currency' => $item['price_currency']
                    ]
                ];
            }, $items);
            
            echo json_encode([
                'total' => intval($total),
                'page' => $page,
                'pageSize' => $pageSize,
                'items' => $formattedItems
            ]);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error: ' . $e->getMessage()]);
        }
    }
    
    public function getItem($id) {
        try {
            $conn = $this->db->getConnection();
            $stmt = $conn->prepare("
                SELECT id, title, description, durability, price_amount, price_currency 
                FROM items 
                WHERE id = :id
            ");
            $stmt->execute(['id' => $id]);
            $item = $stmt->fetch();
            
            if (!$item) {
                http_response_code(404);
                echo json_encode(['error' => 'Item not found']);
                return;
            }
            
            $response = [
                'id' => $item['id'],
                'title' => $item['title'],
                'description' => $item['description'],
                'durability' => intval($item['durability']),
                'price' => [
                    'amount' => floatval($item['price_amount']),
                    'currency' => $item['price_currency']
                ]
            ];
            
            echo json_encode($response);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error']);
        }
    }
    
    public function getPriceHistory($id) {
        try {
            $conn = $this->db->getConnection();
            
            // Check if item exists
            $itemStmt = $conn->prepare("SELECT id FROM items WHERE id = :id");
            $itemStmt->execute(['id' => $id]);
            
            if (!$itemStmt->fetch()) {
                http_response_code(404);
                echo json_encode(['error' => 'Item not found']);
                return;
            }
            
            // Get price history
            $stmt = $conn->prepare("
                SELECT price_amount, price_currency, effective_from 
                FROM price_history 
                WHERE item_id = :id 
                ORDER BY effective_from DESC
            ");
            $stmt->execute(['id' => $id]);
            $history = $stmt->fetchAll();
            
            $formattedHistory = array_map(function($record) {
                return [
                    'price' => [
                        'amount' => floatval($record['price_amount']),
                        'currency' => $record['price_currency']
                    ],
                    'since' => $record['effective_from']
                ];
            }, $history);
            
            echo json_encode(['history' => $formattedHistory]);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error']);
        }
    }
    
    public function createItem() {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            if (!$input || !isset($input['title']) || !isset($input['price']['amount'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Invalid input data']);
                return;
            }
            
            $id = $this->generateUUID();
            $title = $input['title'];
            $description = $input['description'] ?? '';
            $durability = $input['durability'] ?? 1;
            $priceAmount = floatval($input['price']['amount']);
            $priceCurrency = $input['price']['currency'] ?? 'CRD';
            
            $conn = $this->db->getConnection();
            
            // Insert item
            $itemSql = "INSERT INTO items (id, title, description, durability, price_amount, price_currency) 
                       VALUES (:id, :title, :description, :durability, :price_amount, :price_currency)";
            $itemStmt = $conn->prepare($itemSql);
            $itemStmt->execute([
                'id' => $id,
                'title' => $title,
                'description' => $description,
                'durability' => $durability,
                'price_amount' => $priceAmount,
                'price_currency' => $priceCurrency
            ]);
            
            // Add to price history
            $historySql = "INSERT INTO price_history (item_id, price_amount, price_currency) 
                          VALUES (:item_id, :price_amount, :price_currency)";
            $historyStmt = $conn->prepare($historySql);
            $historyStmt->execute([
                'item_id' => $id,
                'price_amount' => $priceAmount,
                'price_currency' => $priceCurrency
            ]);
            
            echo json_encode(['id' => $id]);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error: ' . $e->getMessage()]);
        }
    }
    
    public function updatePrice($id) {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            if (!$input || !isset($input['price']['amount'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Invalid input data']);
                return;
            }
            
            $priceAmount = floatval($input['price']['amount']);
            $priceCurrency = $input['price']['currency'] ?? 'CRD';
            
            $conn = $this->db->getConnection();
            
            // Check if item exists
            $itemStmt = $conn->prepare("SELECT id FROM items WHERE id = :id");
            $itemStmt->execute(['id' => $id]);
            
            if (!$itemStmt->fetch()) {
                http_response_code(404);
                echo json_encode(['error' => 'Item not found']);
                return;
            }
            
            // Update item price
            $updateSql = "UPDATE items SET price_amount = :price_amount, price_currency = :price_currency WHERE id = :id";
            $updateStmt = $conn->prepare($updateSql);
            $updateStmt->execute([
                'price_amount' => $priceAmount,
                'price_currency' => $priceCurrency,
                'id' => $id
            ]);
            
            // Add to price history
            $historySql = "INSERT INTO price_history (item_id, price_amount, price_currency) 
                          VALUES (:item_id, :price_amount, :price_currency)";
            $historyStmt = $conn->prepare($historySql);
            $historyStmt->execute([
                'item_id' => $id,
                'price_amount' => $priceAmount,
                'price_currency' => $priceCurrency
            ]);
            
            // Return updated item
            $this->getItem($id);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error']);
        }
    }
    
    public function health() {
        try {
            $conn = $this->db->getConnection();
            $conn->query("SELECT 1");
            echo json_encode([
                'status' => 'OK',
                'service' => 'Shop Service PHP',
                'timestamp' => date('c')
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode([
                'status' => 'ERROR',
                'service' => 'Shop Service PHP',
                'error' => $e->getMessage()
            ]);
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