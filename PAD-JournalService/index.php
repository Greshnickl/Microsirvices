<?php
require_once 'Database.php';
require_once 'JournalController.php';

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, PATCH, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$db = new Database();
$controller = new JournalController($db);

$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

// Маршрутизация
switch (true) {
    case $path === '/journals' && $method === 'POST':
        $controller->createJournal();
        break;
        
    case preg_match('/\/journals\/([a-f0-9-]+)$/', $path, $matches) && $method === 'GET':
        $controller->getJournal($matches[1]);
        break;
        
    case preg_match('/\/lobbies\/([a-f0-9-]+)\/journals$/', $path, $matches) && $method === 'GET':
        $controller->getLobbyJournals($matches[1]);
        break;
        
    case preg_match('/\/journals\/([a-f0-9-]+)\/finalize$/', $path, $matches) && $method === 'POST':
        $controller->finalizeJournal($matches[1]);
        break;
        
    case $path === '/health' && $method === 'GET':
        $controller->health();
        break;
        
    default:
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint not found']);
        break;
}
?>