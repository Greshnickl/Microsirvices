<?php
class JournalController {
    private $db;
    
    public function __construct($db) {
        $this->db = $db;
        $this->db->initialize();
    }
    
    public function createJournal() {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            if (!$input || !isset($input['lobbyId']) || !isset($input['userId'])) {
                http_response_code(400);
                echo json_encode(['error' => 'lobbyId and userId are required']);
                return;
            }
            
            $id = $this->db->generateUUID();
            $lobbyId = $input['lobbyId'];
            $userId = $input['userId'];
            $observations = $input['observations'] ?? [];
            $guessGhostTypeId = $input['guessGhostTypeId'] ?? null;
            
            $conn = $this->db->getConnection();
            
            // Start transaction
            $conn->beginTransaction();
            
            // Insert journal
            $journalSql = "INSERT INTO journals (id, lobby_id, user_id, guess_ghost_type_id) 
                          VALUES (:id, :lobby_id, :user_id, :guess_ghost_type_id)";
            $journalStmt = $conn->prepare($journalSql);
            $journalStmt->execute([
                'id' => $id,
                'lobby_id' => $lobbyId,
                'user_id' => $userId,
                'guess_ghost_type_id' => $guessGhostTypeId
            ]);
            
            // Insert observations
            if (!empty($observations)) {
                $observationSql = "INSERT INTO observations (journal_id, symptom, evidence) 
                                  VALUES (:journal_id, :symptom, :evidence)";
                $observationStmt = $conn->prepare($observationSql);
                
                foreach ($observations as $observation) {
                    $observationStmt->execute([
                        'journal_id' => $id,
                        'symptom' => $observation['symptom'],
                        'evidence' => $observation['evidence'] ?? null
                    ]);
                }
            }
            
            $conn->commit();
            
            echo json_encode(['journalId' => $id]);
            
        } catch (Exception $e) {
            $conn->rollBack();
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error: ' . $e->getMessage()]);
        }
    }
    
    public function getJournal($id) {
        try {
            $conn = $this->db->getConnection();
            
            // Get journal
            $journalStmt = $conn->prepare("
                SELECT id, lobby_id, user_id, guess_ghost_type_id, submitted_at 
                FROM journals 
                WHERE id = :id
            ");
            $journalStmt->execute(['id' => $id]);
            $journal = $journalStmt->fetch();
            
            if (!$journal) {
                http_response_code(404);
                echo json_encode(['error' => 'Journal not found']);
                return;
            }
            
            // Get observations
            $obsStmt = $conn->prepare("
                SELECT symptom, evidence 
                FROM observations 
                WHERE journal_id = :journal_id 
                ORDER BY id
            ");
            $obsStmt->execute(['journal_id' => $id]);
            $observations = $obsStmt->fetchAll();
            
            $response = [
                'id' => $journal['id'],
                'lobbyId' => $journal['lobby_id'],
                'userId' => $journal['user_id'],
                'observations' => $observations,
                'guessGhostTypeId' => $journal['guess_ghost_type_id'],
                'submittedAt' => $journal['submitted_at']
            ];
            
            echo json_encode($response);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error']);
        }
    }
    
    public function getLobbyJournals($lobbyId) {
        try {
            $conn = $this->db->getConnection();
            
            $stmt = $conn->prepare("
                SELECT id, user_id 
                FROM journals 
                WHERE lobby_id = :lobby_id 
                ORDER BY submitted_at DESC
            ");
            $stmt->execute(['lobby_id' => $lobbyId]);
            $journals = $stmt->fetchAll();
            
            $formattedJournals = array_map(function($journal) {
                return [
                    'id' => $journal['id'],
                    'userId' => $journal['user_id']
                ];
            }, $journals);
            
            echo json_encode(['journals' => $formattedJournals]);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error']);
        }
    }
    
    public function finalizeJournal($id) {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            if (!$input || !isset($input['actualGhostTypeId'])) {
                http_response_code(400);
                echo json_encode(['error' => 'actualGhostTypeId is required']);
                return;
            }
            
            $actualGhostTypeId = $input['actualGhostTypeId'];
            
            $conn = $this->db->getConnection();
            
            // Get journal to check guess
            $journalStmt = $conn->prepare("
                SELECT guess_ghost_type_id 
                FROM journals 
                WHERE id = :id AND finalized_at IS NULL
            ");
            $journalStmt->execute(['id' => $id]);
            $journal = $journalStmt->fetch();
            
            if (!$journal) {
                http_response_code(404);
                echo json_encode(['error' => 'Journal not found or already finalized']);
                return;
            }
            
            // Calculate award (simple logic: 100 base + 20 bonus for correct guess)
            $baseAward = 100;
            $bonusAward = 0;
            
            if ($journal['guess_ghost_type_id'] === $actualGhostTypeId) {
                $bonusAward = 20;
            }
            
            $totalAward = $baseAward + $bonusAward;
            
            // Update journal with finalization
            $updateStmt = $conn->prepare("
                UPDATE journals 
                SET finalized_at = NOW(), 
                    actual_ghost_type_id = :actual_ghost_type_id,
                    awarded_amount = :awarded_amount
                WHERE id = :id
            ");
            $updateStmt->execute([
                'actual_ghost_type_id' => $actualGhostTypeId,
                'awarded_amount' => $totalAward,
                'id' => $id
            ]);
            
            echo json_encode([
                'awarded' => [
                    'amount' => floatval($totalAward),
                    'currency' => 'CRD'
                ]
            ]);
            
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => 'Internal server error: ' . $e->getMessage()]);
        }
    }
    
    public function health() {
        try {
            $conn = $this->db->getConnection();
            $conn->query("SELECT 1");
            echo json_encode([
                'status' => 'OK',
                'service' => 'Journal Service PHP',
                'timestamp' => date('c')
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode([
                'status' => 'ERROR',
                'service' => 'Journal Service PHP',
                'error' => $e->getMessage()
            ]);
        }
    }
}
?>