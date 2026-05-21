from datetime import datetime, timedelta
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for

from .db import get_db


ORDER_STATUSES = ["Pending", "Preparing", "Served", "Completed"]
PAYMENT_METHODS = ["Cash", "Card", "UPI", "Wallet"]
PAYMENT_STATUSES = ["Pending", "Paid", "Failed", "Refunded"]
EMPLOYEE_ROLES = ["Admin", "Staff", "Chef", "Cashier"]


def login_required(roles=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            current_role = session.get("role")
            if not current_role:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            if roles and current_role not in roles:
                flash("You do not have access to that page.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def parse_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")


def parse_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid integer.")


def calculate_order_total(order_items):
    return round(sum(item["quantity"] * item["price"] for item in order_items), 2)


def update_inventory_for_order(db, order_items):
    inventory_rows = db.execute("SELECT inventory_id, item_name, stock_quantity FROM Inventory").fetchall()
    inventory_by_name = {row["item_name"].strip().lower(): row for row in inventory_rows}

    for item in order_items:
        inventory_row = inventory_by_name.get(item["item_name"].strip().lower())
        if inventory_row:
            if inventory_row["stock_quantity"] < item["quantity"]:
                raise ValueError(f"Not enough inventory for {item['item_name']}.")
            db.execute(
                """
                UPDATE Inventory
                SET stock_quantity = ?, last_updated = ?
                WHERE inventory_id = ?
                """,
                (
                    inventory_row["stock_quantity"] - item["quantity"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    inventory_row["inventory_id"],
                ),
            )


def get_customer_history(db, customer_id):
    return db.execute(
        """
        SELECT Orders.order_id, Orders.order_time, Orders.status, Orders.total_amount,
               COALESCE(Payments.payment_status, 'Pending') AS payment_status
        FROM Orders
        LEFT JOIN Payments ON Orders.order_id = Payments.order_id
        WHERE Orders.customer_id = ?
        ORDER BY Orders.order_time DESC
        """,
        (customer_id,),
    ).fetchall()


def get_dashboard_data(db):
    summary = {
        "customers": db.execute("SELECT COUNT(*) AS total FROM Customers").fetchone()["total"],
        "employees": db.execute("SELECT COUNT(*) AS total FROM Employees").fetchone()["total"],
        "menu_items": db.execute("SELECT COUNT(*) AS total FROM Menu_Items").fetchone()["total"],
        "orders": db.execute("SELECT COUNT(*) AS total FROM Orders").fetchone()["total"],
        "reservations": db.execute("SELECT COUNT(*) AS total FROM Reservations").fetchone()["total"],
        "inventory_low": db.execute(
            "SELECT COUNT(*) AS total FROM Inventory WHERE stock_quantity <= 5"
        ).fetchone()["total"],
    }

    recent_orders = db.execute(
        """
        SELECT Orders.order_id, Customers.name AS customer_name, Orders.order_time,
               Orders.status, Orders.total_amount
        FROM Orders
        LEFT JOIN Customers ON Orders.customer_id = Customers.customer_id
        ORDER BY Orders.order_time DESC
        LIMIT 5
        """
    ).fetchall()

    status_counts = db.execute(
        """
        SELECT status, COUNT(*) AS total
        FROM Orders
        GROUP BY status
        ORDER BY status
        """
    ).fetchall()
    return summary, recent_orders, status_counts


def register_routes(app):
    @app.route("/")
    def home():
        if session.get("role"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        db = get_db()
        if request.method == "POST":
            user_type = request.form.get("user_type", "").strip()
            name = request.form.get("name", "").strip()

            if user_type == "admin":
                username = request.form.get("username", "").strip()
                password = request.form.get("password", "").strip()
                if (
                    username == app.config["ADMIN_USERNAME"]
                    and password == app.config["ADMIN_PASSWORD"]
                ):
                    session.clear()
                    session["role"] = "Admin"
                    session["display_name"] = "Administrator"
                    flash("Admin login successful.", "success")
                    return redirect(url_for("dashboard"))
                flash("Invalid admin credentials.", "danger")

            elif user_type == "staff":
                employee_id = request.form.get("employee_id", "").strip()
                if not employee_id or not name:
                    flash("Employee ID and name are required for staff login.", "warning")
                else:
                    employee = db.execute(
                        """
                        SELECT employee_id, name, role
                        FROM Employees
                        WHERE employee_id = ? AND LOWER(name) = LOWER(?)
                        """,
                        (employee_id, name),
                    ).fetchone()
                    if employee:
                        session.clear()
                        session["role"] = employee["role"]
                        session["display_name"] = employee["name"]
                        session["employee_id"] = employee["employee_id"]
                        flash("Staff login successful.", "success")
                        return redirect(url_for("dashboard"))
                    flash("Staff record not found.", "danger")

            elif user_type == "customer":
                phone = request.form.get("phone", "").strip()
                preferences = request.form.get("preferences", "").strip()
                if not name or not phone:
                    flash("Customer name and phone are required.", "warning")
                else:
                    customer = db.execute(
                        "SELECT customer_id, name FROM Customers WHERE phone = ?",
                        (phone,),
                    ).fetchone()
                    if customer is None:
                        cursor = db.execute(
                            """
                            INSERT INTO Customers (name, phone, preferences)
                            VALUES (?, ?, ?)
                            """,
                            (name, phone, preferences),
                        )
                        db.commit()
                        customer_id = cursor.lastrowid
                        display_name = name
                    else:
                        customer_id = customer["customer_id"]
                        display_name = customer["name"]
                    session.clear()
                    session["role"] = "Customer"
                    session["display_name"] = display_name
                    session["customer_id"] = customer_id
                    flash("Customer login successful.", "success")
                    return redirect(url_for("dashboard"))
            else:
                flash("Please choose a valid user type.", "warning")

        return render_template(
            "login.html",
            admin_username=app.config["ADMIN_USERNAME"],
            admin_password=app.config["ADMIN_PASSWORD"],
        )

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required()
    def dashboard():
        db = get_db()
        summary, recent_orders, status_counts = get_dashboard_data(db)
        customer_history = []
        if session.get("role") == "Customer" and session.get("customer_id"):
            customer_history = get_customer_history(db, session["customer_id"])
        return render_template(
            "dashboard.html",
            summary=summary,
            recent_orders=recent_orders,
            status_counts=status_counts,
            customer_history=customer_history,
        )

    @app.route("/menu", methods=["GET", "POST"])
    @login_required()
    def menu_management():
        db = get_db()
        if request.method == "POST":
            if session.get("role") not in ["Admin", "Staff"]:
                flash("Only staff and admin can manage the menu.", "danger")
                return redirect(url_for("menu_management"))
            try:
                item_name = request.form.get("item_name", "").strip()
                category = request.form.get("category", "").strip()
                price = parse_float(request.form.get("price"), "Price")
                availability = request.form.get("availability", "Available").strip()
                if not item_name or not category:
                    raise ValueError("Item name and category are required.")

                db.execute(
                    """
                    INSERT INTO Menu_Items (item_name, price, category, availability)
                    VALUES (?, ?, ?, ?)
                    """,
                    (item_name, price, category, availability),
                )
                db.commit()
                flash("Menu item added successfully.", "success")
            except Exception as error:
                db.rollback()
                flash(str(error), "danger")
            return redirect(url_for("menu_management"))

        menu_items = db.execute(
            "SELECT * FROM Menu_Items ORDER BY category, item_name"
        ).fetchall()
        return render_template("menu.html", menu_items=menu_items)

    @app.route("/menu/edit/<int:item_id>", methods=["POST"])
    @login_required(["Admin", "Staff"])
    def edit_menu_item(item_id):
        db = get_db()
        try:
            item_name = request.form.get("item_name", "").strip()
            category = request.form.get("category", "").strip()
            price = parse_float(request.form.get("price"), "Price")
            availability = request.form.get("availability", "Available").strip()
            if not item_name or not category:
                raise ValueError("Item name and category are required.")

            db.execute(
                """
                UPDATE Menu_Items
                SET item_name = ?, price = ?, category = ?, availability = ?
                WHERE item_id = ?
                """,
                (item_name, price, category, availability, item_id),
            )
            db.commit()
            flash("Menu item updated successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(str(error), "danger")
        return redirect(url_for("menu_management"))

    @app.route("/menu/delete/<int:item_id>", methods=["POST"])
    @login_required(["Admin"])
    def delete_menu_item(item_id):
        db = get_db()
        try:
            db.execute("DELETE FROM Menu_Items WHERE item_id = ?", (item_id,))
            db.commit()
            flash("Menu item deleted successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(f"Unable to delete menu item: {error}", "danger")
        return redirect(url_for("menu_management"))

    @app.route("/customers", methods=["GET", "POST"])
    @login_required(["Admin", "Staff"])
    def customer_management():
        db = get_db()
        if request.method == "POST":
            try:
                name = request.form.get("name", "").strip()
                phone = request.form.get("phone", "").strip()
                preferences = request.form.get("preferences", "").strip()
                if not name or not phone:
                    raise ValueError("Customer name and phone are required.")

                db.execute(
                    """
                    INSERT INTO Customers (name, phone, preferences)
                    VALUES (?, ?, ?)
                    """,
                    (name, phone, preferences),
                )
                db.commit()
                flash("Customer added successfully.", "success")
            except Exception as error:
                db.rollback()
                flash(str(error), "danger")
            return redirect(url_for("customer_management"))

        customers = db.execute("SELECT * FROM Customers ORDER BY name").fetchall()
        customer_histories = {
            customer["customer_id"]: get_customer_history(db, customer["customer_id"])
            for customer in customers
        }
        return render_template(
            "customers.html",
            customers=customers,
            customer_histories=customer_histories,
        )

    @app.route("/customers/edit/<int:customer_id>", methods=["POST"])
    @login_required(["Admin", "Staff"])
    def edit_customer(customer_id):
        db = get_db()
        try:
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            preferences = request.form.get("preferences", "").strip()
            if not name or not phone:
                raise ValueError("Customer name and phone are required.")

            db.execute(
                """
                UPDATE Customers
                SET name = ?, phone = ?, preferences = ?
                WHERE customer_id = ?
                """,
                (name, phone, preferences, customer_id),
            )
            db.commit()
            flash("Customer updated successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(str(error), "danger")
        return redirect(url_for("customer_management"))

    @app.route("/customers/delete/<int:customer_id>", methods=["POST"])
    @login_required(["Admin"])
    def delete_customer(customer_id):
        db = get_db()
        try:
            db.execute("DELETE FROM Customers WHERE customer_id = ?", (customer_id,))
            db.commit()
            flash("Customer deleted successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(f"Unable to delete customer: {error}", "danger")
        return redirect(url_for("customer_management"))

    @app.route("/employees", methods=["GET", "POST"])
    @login_required(["Admin"])
    def employee_management():
        db = get_db()
        if request.method == "POST":
            try:
                name = request.form.get("name", "").strip()
                role = request.form.get("role", "").strip()
                shift = request.form.get("shift", "").strip()
                if not name or not role or not shift:
                    raise ValueError("Employee name, role, and shift are required.")
                if role not in EMPLOYEE_ROLES:
                    raise ValueError("Please choose a valid employee role.")

                db.execute(
                    """
                    INSERT INTO Employees (name, role, shift)
                    VALUES (?, ?, ?)
                    """,
                    (name, role, shift),
                )
                db.commit()
                flash("Employee added successfully.", "success")
            except Exception as error:
                db.rollback()
                flash(str(error), "danger")
            return redirect(url_for("employee_management"))

        employees = db.execute("SELECT * FROM Employees ORDER BY role, name").fetchall()
        return render_template(
            "employees.html",
            employees=employees,
            employee_roles=EMPLOYEE_ROLES,
        )

    @app.route("/employees/edit/<int:employee_id>", methods=["POST"])
    @login_required(["Admin"])
    def edit_employee(employee_id):
        db = get_db()
        try:
            name = request.form.get("name", "").strip()
            role = request.form.get("role", "").strip()
            shift = request.form.get("shift", "").strip()
            if not name or not role or not shift:
                raise ValueError("Employee name, role, and shift are required.")

            db.execute(
                """
                UPDATE Employees
                SET name = ?, role = ?, shift = ?
                WHERE employee_id = ?
                """,
                (name, role, shift, employee_id),
            )
            db.commit()
            flash("Employee updated successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(str(error), "danger")
        return redirect(url_for("employee_management"))

    @app.route("/employees/delete/<int:employee_id>", methods=["POST"])
    @login_required(["Admin"])
    def delete_employee(employee_id):
        db = get_db()
        try:
            db.execute("DELETE FROM Employees WHERE employee_id = ?", (employee_id,))
            db.commit()
            flash("Employee deleted successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(f"Unable to delete employee: {error}", "danger")
        return redirect(url_for("employee_management"))

    @app.route("/orders", methods=["GET", "POST"])
    @login_required()
    def order_management():
        db = get_db()
        if request.method == "POST":
            try:
                if session.get("role") == "Customer":
                    customer_id = session.get("customer_id")
                else:
                    selected_customer_id = request.form.get("customer_id", "").strip()
                    new_customer_name = request.form.get("new_customer_name", "").strip()
                    new_customer_phone = request.form.get("new_customer_phone", "").strip()
                    new_customer_preferences = request.form.get("new_customer_preferences", "").strip()

                    if selected_customer_id:
                        customer_id = parse_int(selected_customer_id, "Customer")
                    else:
                        if not new_customer_name or not new_customer_phone:
                            raise ValueError(
                                "Select an existing customer or enter a new customer name and phone."
                            )
                        existing_customer = db.execute(
                            "SELECT customer_id FROM Customers WHERE phone = ?",
                            (new_customer_phone,),
                        ).fetchone()
                        if existing_customer:
                            customer_id = existing_customer["customer_id"]
                        else:
                            cursor = db.execute(
                                """
                                INSERT INTO Customers (name, phone, preferences)
                                VALUES (?, ?, ?)
                                """,
                                (
                                    new_customer_name,
                                    new_customer_phone,
                                    new_customer_preferences,
                                ),
                            )
                            customer_id = cursor.lastrowid
                item_ids = request.form.getlist("item_id")
                if not item_ids:
                    raise ValueError("Please add at least one menu item to the order.")

                order_items = []
                for item_id in item_ids:
                    quantity = parse_int(request.form.get(f"quantity_{item_id}"), "Quantity")
                    if quantity <= 0:
                        raise ValueError("Quantity must be greater than zero.")
                    menu_item = db.execute(
                        "SELECT * FROM Menu_Items WHERE item_id = ?",
                        (item_id,),
                    ).fetchone()
                    if menu_item is None:
                        raise ValueError("A selected menu item does not exist.")
                    if menu_item["availability"] != "Available":
                        raise ValueError(f"{menu_item['item_name']} is currently unavailable.")
                    order_items.append(
                        {
                            "item_id": menu_item["item_id"],
                            "item_name": menu_item["item_name"],
                            "quantity": quantity,
                            "price": float(menu_item["price"]),
                        }
                    )

                if not order_items:
                    raise ValueError("No valid order items were submitted.")

                update_inventory_for_order(db, order_items)
                total_amount = calculate_order_total(order_items)
                order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor = db.execute(
                    """
                    INSERT INTO Orders (customer_id, order_time, status, total_amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (customer_id, order_time, "Pending", total_amount),
                )
                order_id = cursor.lastrowid

                for item in order_items:
                    db.execute(
                        """
                        INSERT INTO Order_Details (order_id, item_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                        """,
                        (order_id, item["item_id"], item["quantity"], item["price"]),
                    )

                db.execute(
                    """
                    INSERT INTO Payments (order_id, payment_method, payment_status, amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, "Cash", "Pending", total_amount),
                )
                db.commit()
                flash("Order created successfully.", "success")
            except Exception as error:
                db.rollback()
                flash(str(error), "danger")
            return redirect(url_for("order_management"))

        customers = db.execute("SELECT * FROM Customers ORDER BY name").fetchall()
        menu_items = db.execute(
            "SELECT * FROM Menu_Items WHERE availability = 'Available' ORDER BY category, item_name"
        ).fetchall()
        if session.get("role") == "Customer":
            orders = db.execute(
                """
                SELECT Orders.*, Customers.name AS customer_name
                FROM Orders
                LEFT JOIN Customers ON Orders.customer_id = Customers.customer_id
                WHERE Orders.customer_id = ?
                ORDER BY Orders.order_time DESC
                """,
                (session.get("customer_id"),),
            ).fetchall()
        else:
            orders = db.execute(
                """
                SELECT Orders.*, Customers.name AS customer_name
                FROM Orders
                LEFT JOIN Customers ON Orders.customer_id = Customers.customer_id
                ORDER BY Orders.order_time DESC
                """
            ).fetchall()
        order_details = {
            order["order_id"]: db.execute(
                """
                SELECT Order_Details.*, Menu_Items.item_name
                FROM Order_Details
                JOIN Menu_Items ON Order_Details.item_id = Menu_Items.item_id
                WHERE order_id = ?
                """,
                (order["order_id"],),
            ).fetchall()
            for order in orders
        }
        return render_template(
            "orders.html",
            customers=customers,
            menu_items=menu_items,
            orders=orders,
            order_details=order_details,
            order_statuses=ORDER_STATUSES,
        )

    @app.route("/orders/update/<int:order_id>", methods=["POST"])
    @login_required(["Admin", "Staff"])
    def update_order(order_id):
        db = get_db()
        try:
            status = request.form.get("status", "").strip()
            if status not in ORDER_STATUSES:
                raise ValueError("Invalid order status selected.")

            db.execute(
                "UPDATE Orders SET status = ? WHERE order_id = ?",
                (status, order_id),
            )
            db.commit()
            flash("Order status updated successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(str(error), "danger")
        return redirect(url_for("order_management"))

    @app.route("/reservations", methods=["GET", "POST"])
    @login_required()
    def reservations():
        db = get_db()
        if request.method == "POST":
            try:
                if session.get("role") == "Customer":
                    customer_id = session.get("customer_id")
                else:
                    customer_id = parse_int(request.form.get("customer_id"), "Customer")
                reservation_date = request.form.get("date", "").strip()
                reservation_time = request.form.get("time", "").strip()
                table_number = parse_int(request.form.get("table_number"), "Table number")
                if not reservation_date or not reservation_time:
                    raise ValueError("Reservation date and time are required.")

                db.execute(
                    """
                    INSERT INTO Reservations (customer_id, `date`, `time`, table_number)
                    VALUES (?, ?, ?, ?)
                    """,
                    (customer_id, reservation_date, reservation_time, table_number),
                )
                db.commit()
                flash("Reservation created successfully.", "success")
            except Exception as error:
                db.rollback()
                flash(str(error), "danger")
            return redirect(url_for("reservations"))

        customers = db.execute("SELECT * FROM Customers ORDER BY name").fetchall()
        reservations_list = db.execute(
            """
            SELECT Reservations.*, Customers.name AS customer_name
            FROM Reservations
            JOIN Customers ON Reservations.customer_id = Customers.customer_id
            ORDER BY `date` ASC, `time` ASC
            """
        ).fetchall()
        return render_template(
            "reservations.html",
            customers=customers,
            reservations=reservations_list,
        )

    @app.route("/reservations/delete/<int:reservation_id>", methods=["POST"])
    @login_required(["Admin", "Staff"])
    def delete_reservation(reservation_id):
        db = get_db()
        try:
            db.execute("DELETE FROM Reservations WHERE reservation_id = ?", (reservation_id,))
            db.commit()
            flash("Reservation deleted successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(f"Unable to delete reservation: {error}", "danger")
        return redirect(url_for("reservations"))

    @app.route("/inventory", methods=["GET", "POST"])
    @login_required(["Admin", "Staff"])
    def inventory():
        db = get_db()
        if request.method == "POST":
            try:
                item_name = request.form.get("item_name", "").strip()
                stock_quantity = parse_int(request.form.get("stock_quantity"), "Stock quantity")
                if not item_name:
                    raise ValueError("Inventory item name is required.")

                db.execute(
                    """
                    INSERT INTO Inventory (item_name, stock_quantity, last_updated)
                    VALUES (?, ?, ?)
                    """,
                    (item_name, stock_quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
                db.commit()
                flash("Inventory item added successfully.", "success")
            except Exception as error:
                db.rollback()
                flash(str(error), "danger")
            return redirect(url_for("inventory"))

        inventory_items = db.execute("SELECT * FROM Inventory ORDER BY item_name").fetchall()
        return render_template("inventory.html", inventory_items=inventory_items)

    @app.route("/inventory/update/<int:inventory_id>", methods=["POST"])
    @login_required(["Admin", "Staff"])
    def update_inventory(inventory_id):
        db = get_db()
        try:
            item_name = request.form.get("item_name", "").strip()
            stock_quantity = parse_int(request.form.get("stock_quantity"), "Stock quantity")
            if not item_name:
                raise ValueError("Inventory item name is required.")
            db.execute(
                """
                UPDATE Inventory
                SET item_name = ?, stock_quantity = ?, last_updated = ?
                WHERE inventory_id = ?
                """,
                (
                    item_name,
                    stock_quantity,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    inventory_id,
                ),
            )
            db.commit()
            flash("Inventory updated successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(str(error), "danger")
        return redirect(url_for("inventory"))

    @app.route("/inventory/delete/<int:inventory_id>", methods=["POST"])
    @login_required(["Admin"])
    def delete_inventory(inventory_id):
        db = get_db()
        try:
            db.execute("DELETE FROM Inventory WHERE inventory_id = ?", (inventory_id,))
            db.commit()
            flash("Inventory item deleted successfully.", "success")
        except Exception as error:
            db.rollback()
            flash(f"Unable to delete inventory item: {error}", "danger")
        return redirect(url_for("inventory"))

    @app.route("/billing", methods=["GET", "POST"])
    @login_required(["Admin", "Staff"])
    def billing():
        db = get_db()
        if request.method == "POST":
            try:
                payment_id = parse_int(request.form.get("payment_id"), "Payment")
                payment_method = request.form.get("payment_method", "").strip()
                payment_status = request.form.get("payment_status", "").strip()
                if payment_method not in PAYMENT_METHODS:
                    raise ValueError("Invalid payment method.")
                if payment_status not in PAYMENT_STATUSES:
                    raise ValueError("Invalid payment status.")

                db.execute(
                    """
                    UPDATE Payments
                    SET payment_method = ?, payment_status = ?
                    WHERE payment_id = ?
                    """,
                    (payment_method, payment_status, payment_id),
                )
                db.commit()
                flash("Payment updated successfully.", "success")
            except Exception as error:
                db.rollback()
                flash(str(error), "danger")
            return redirect(url_for("billing"))

        payments = db.execute(
            """
            SELECT Payments.*, Orders.status AS order_status, Customers.name AS customer_name
            FROM Payments
            JOIN Orders ON Payments.order_id = Orders.order_id
            LEFT JOIN Customers ON Orders.customer_id = Customers.customer_id
            ORDER BY Payments.payment_id DESC
            """
        ).fetchall()
        return render_template(
            "billing.html",
            payments=payments,
            payment_methods=PAYMENT_METHODS,
            payment_statuses=PAYMENT_STATUSES,
        )

    @app.route("/analytics")
    @login_required(["Admin", "Staff"])
    def analytics():
        db = get_db()
        today = datetime.now().date()
        daily_sales = db.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM Payments
            WHERE payment_status = 'Paid'
              AND order_id IN (
                SELECT order_id FROM Orders WHERE DATE(order_time) = ?
              )
            """,
            (today.strftime("%Y-%m-%d"),),
        ).fetchone()["total"]

        weekly_sales = db.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM Payments
            WHERE payment_status = 'Paid'
              AND order_id IN (
                SELECT order_id
                FROM Orders
                WHERE DATE(order_time) BETWEEN ? AND ?
              )
            """,
            (
                (today - timedelta(days=6)).strftime("%Y-%m-%d"),
                today.strftime("%Y-%m-%d"),
            ),
        ).fetchone()["total"]

        top_items = db.execute(
            """
            SELECT Menu_Items.item_name, SUM(Order_Details.quantity) AS total_quantity
            FROM Order_Details
            JOIN Menu_Items ON Order_Details.item_id = Menu_Items.item_id
            GROUP BY Menu_Items.item_name
            ORDER BY total_quantity DESC
            LIMIT 5
            """
        ).fetchall()

        daily_breakdown = db.execute(
            """
            SELECT DATE(Orders.order_time) AS sales_date, COALESCE(SUM(Payments.amount), 0) AS total
            FROM Orders
            LEFT JOIN Payments ON Orders.order_id = Payments.order_id
            WHERE Payments.payment_status = 'Paid'
            GROUP BY DATE(Orders.order_time)
            ORDER BY sales_date DESC
            LIMIT 7
            """
        ).fetchall()
        return render_template(
            "analytics.html",
            daily_sales=daily_sales,
            weekly_sales=weekly_sales,
            top_items=top_items,
            daily_breakdown=daily_breakdown,
        )
