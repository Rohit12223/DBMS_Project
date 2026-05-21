# Restaurant Management System

A complete full-stack Restaurant Management System built with Flask, HTML, CSS, and SQLite/MySQL.

## Technologies Used

- Python
- Flask
- HTML5
- CSS3
- SQLite
- MySQL
- Jinja2

## Project Structure

```text
DBMS_project
|-- app/
|   |-- static/
|   |   `-- css/
|   |       `-- style.css
|   |-- templates/
|   |   |-- analytics.html
|   |   |-- base.html
|   |   |-- billing.html
|   |   |-- customers.html
|   |   |-- dashboard.html
|   |   |-- employees.html
|   |   |-- inventory.html
|   |   |-- login.html
|   |   |-- menu.html
|   |   |-- orders.html
|   |   `-- reservations.html
|   |-- __init__.py
|   |-- db.py
|   `-- routes.py
|-- instance/
|-- app.py
|-- requirements.txt
|-- schema.sql
|-- schema_mysql.sql
|-- run_mysql.bat
`-- README.md
```

## Features

- Admin, staff, and customer login flow using Flask sessions
- CRUD operations for menu items, customers, employees, and inventory
- Order creation with multiple menu items
- Automatic order total calculation
- Inventory deduction after order placement
- Reservation management
- Billing and payment tracking
- Customer order history
- Daily and weekly sales analytics
- Normalized SQL schema with primary keys, foreign keys, and constraints

## Database Tables

The app uses the exact required tables:

- `Customers`
- `Employees`
- `Menu_Items`
- `Orders`
- `Order_Details`
- `Reservations`
- `Inventory`
- `Payments`

## How to Run with SQLite

1. Open a terminal in your project folder

```bash
cd "C:\Users\hp\OneDrive\Documents\DBMS_project"
```

2. Create a virtual environment

```bash
python -m venv .venv
```

3. Activate the virtual environment

```bash
.venv\Scripts\activate
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Run the application:

```powershell
python app.py
```

6. Open the browser at:

```text
http://127.0.0.1:5000
```

## Default Admin Login

- Username: `Rohit`
- Password: `Rohit123`

## How to Run with MySQL

1. Make sure MySQL Server is running.
2. Open a terminal in `C:\Users\hp\OneDrive\Documents\DBMS_PROJECT
`
3. Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

5. Start the Flask app with MySQL settings:

```powershell
$env:RMS_DB_ENGINE="mysql"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD=""
$env:MYSQL_DATABASE="restaurantdb"
python app.py
```

If your MySQL root user has a password, put it here:

```powershell
$env:MYSQL_PASSWORD="your_password"
```

The app will automatically create the `restaurantdb` database and required tables if they do not exist.

You can also double-click `run_mysql.bat`. If your MySQL has a password, edit `run_mysql.bat` and fill in `set MYSQL_PASSWORD=your_password`.

## Notes

- SQLite is available for simple local testing.
- MySQL is available for DBMS project/demo use.
- For SQLite reset, delete `instance\restaurant_rms.db` and start the app again.
- For MySQL reset, drop the `restaurantdb` database from MySQL and start the app again.

## Author

**J. Rohit Venkata Manikanta**

LinkedIn: 
https://www.linkedin.com/in/rohit-venkata-manikanta-jannu-a576a9379
