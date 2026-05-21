SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Reservations;
DROP TABLE IF EXISTS Order_Details;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS Menu_Items;
DROP TABLE IF EXISTS Employees;
DROP TABLE IF EXISTS Customers;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE Customers (
    customer_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(64) NOT NULL,
    preferences TEXT,
    PRIMARY KEY (customer_id),
    UNIQUE KEY uk_customers_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Employees (
    employee_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL,
    shift VARCHAR(128) NOT NULL,
    PRIMARY KEY (employee_id),
    CONSTRAINT chk_employees_role CHECK (role IN ('Admin', 'Staff', 'Chef', 'Cashier'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Menu_Items (
    item_id INT NOT NULL AUTO_INCREMENT,
    item_name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(128) NOT NULL,
    availability VARCHAR(32) NOT NULL,
    PRIMARY KEY (item_id),
    UNIQUE KEY uk_menu_item_name (item_name),
    CONSTRAINT chk_menu_price CHECK (price >= 0),
    CONSTRAINT chk_menu_availability CHECK (availability IN ('Available', 'Unavailable'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Orders (
    order_id INT NOT NULL AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_time VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES Customers (customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_orders_status CHECK (status IN ('Pending', 'Preparing', 'Served', 'Completed')),
    CONSTRAINT chk_orders_total CHECK (total_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Order_Details (
    order_detail_id INT NOT NULL AUTO_INCREMENT,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_detail_id),
    CONSTRAINT fk_od_order FOREIGN KEY (order_id) REFERENCES Orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_od_item FOREIGN KEY (item_id) REFERENCES Menu_Items (item_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_od_qty CHECK (quantity > 0),
    CONSTRAINT chk_od_price CHECK (price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Reservations (
    reservation_id INT NOT NULL AUTO_INCREMENT,
    customer_id INT NOT NULL,
    `date` DATE NOT NULL,
    `time` TIME NOT NULL,
    table_number INT NOT NULL,
    PRIMARY KEY (reservation_id),
    CONSTRAINT fk_res_customer FOREIGN KEY (customer_id) REFERENCES Customers (customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_res_table CHECK (table_number > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Inventory (
    inventory_id INT NOT NULL AUTO_INCREMENT,
    item_name VARCHAR(255) NOT NULL,
    stock_quantity INT NOT NULL,
    last_updated VARCHAR(32) NOT NULL,
    PRIMARY KEY (inventory_id),
    UNIQUE KEY uk_inventory_item (item_name),
    CONSTRAINT chk_inv_stock CHECK (stock_quantity >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Payments (
    payment_id INT NOT NULL AUTO_INCREMENT,
    order_id INT NOT NULL,
    payment_method VARCHAR(32) NOT NULL,
    payment_status VARCHAR(32) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (payment_id),
    UNIQUE KEY uk_payments_order (order_id),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES Orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_pay_method CHECK (payment_method IN ('Cash', 'Card', 'UPI', 'Wallet')),
    CONSTRAINT chk_pay_status CHECK (payment_status IN ('Pending', 'Paid', 'Failed', 'Refunded')),
    CONSTRAINT chk_pay_amount CHECK (amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
