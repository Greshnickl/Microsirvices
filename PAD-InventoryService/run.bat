@echo off
echo Starting Python Inventory Service...
docker-compose down
docker-compose up --build