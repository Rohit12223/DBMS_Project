@echo off
cd /d "C:\Users\hp\OneDrive\Documents\New project"
set RMS_DB_ENGINE=mysql
set MYSQL_HOST=127.0.0.1
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=Rohit45
set MYSQL_DATABASE=restaurant_project
set ADMIN_USERNAME=Rohit
set ADMIN_PASSWORD=Rohit123
call .venv\Scripts\activate
python app.py
pause
