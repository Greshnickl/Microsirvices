<?php
require_once 'Database.php';
require_once 'ItemController.php';

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, PATCH, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$db = new Database();
$controller = new ItemController($db);

$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

// Маршрутизация
switch (true) {
    case $path === '/items' && $method === 'GET':
        $controller->getItems();
        break;
        
    case preg_match('/\/items\/([a-f0-9-]+)$/', $path, $matches) && $method === 'GET':
        $controller->getItem($matches[1]);
        break;
        
    case preg_match('/\/items\/([a-f0-9-]+)\/prices$/', $path, $matches) && $method === 'GET':
        $controller->getPriceHistory($matches[1]);
        break;
        
    case $path === '/items' && $method === 'POST':
        $controller->createItem();
        break;
        
    case preg_match('/\/items\/([a-f0-9-]+)\/price$/', $path, $matches) && $method === 'PATCH':
        $controller->updatePrice($matches[1]);
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