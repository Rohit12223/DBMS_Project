DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Reservations;
DROP TABLE IF EXISTS Order_Details;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS Menu_Items;
DROP TABLE IF EXISTS Employees;
DROP TABLE IF EXISTS Customers;

CREATE TABLE Customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    preferences TEXT
);

CREATE TABLE Employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Admin', 'Staff', 'Chef', 'Cashier')),
    shift TEXT NOT NULL
);

CREATE TABLE Menu_Items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE,
    price REAL NOT NULL CHECK (price >= 0),
    category TEXT NOT NULL,
    availability TEXT NOT NULL CHECK (availability IN ('Available', 'Unavailable'))
);

CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_time TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Pending', 'Preparing', 'Served', 'Completed')),
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE Order_Details (
    order_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price REAL NOT NULL CHECK (price >= 0),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (item_id) REFERENCES Menu_Items(item_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE Reservations (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    table_number INTEGER NOT NULL CHECK (table_number > 0),
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Inventory (
    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE,
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    last_updated TEXT NOT NULL
);

CREATE TABLE Payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL UNIQUE,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Cash', 'Card', 'UPI', 'Wallet')),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('Pending', 'Paid', 'Failed', 'Refunded')),
    amount REAL NOT NULL CHECK (amount >= 0),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE
);
