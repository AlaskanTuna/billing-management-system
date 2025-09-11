# src/webapp.py

try:
    import config
except ImportError:
    from src import config

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
from sqlalchemy import func, cast, Date

# GLOBAL VARIABLES

app = Flask(__name__, template_folder=config.TEMPLATES_DIR, static_folder=config.STATIC_DIR)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# USER MODEL

class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {
    "admin": {
        "password": "admin"
    }
}
admin_user = User(id="admin")

@login_manager.user_loader
def load_user(user_id):
    """ 
    Loads a user from the user ID.
    """
    if user_id == "admin":
        return admin_user
    return None

# DB MODEL

class SolarBillingReader(db.Model):
    __tablename__ = config.DB_TABLE_NAME
    id = db.Column(db.BigInteger, primary_key=True)
    customer_fk_id = db.Column(db.BigInteger, db.ForeignKey('customers.id'), nullable=False)
    Timestamp = db.Column(db.TIMESTAMP, nullable=False)
    Total_Positive_Real_Energy_kWh = db.Column(db.Float, nullable=True)
    customer = db.relationship('Customer')

class Customer(db.Model):
    __tablename__ = config.CUSTOMERS_TABLE_NAME
    id = db.Column(db.BigInteger, primary_key=True)
    lee_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    capacity = db.Column(db.Numeric(10, 2), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    registration_date = db.Column(db.Date, server_default=db.func.current_date())
    last_modified = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    status = db.Column(db.String(20), default="active")

# API ROUTES

@app.route('/')
def index():
    """ 
    Redirects to the login page. 
    """
    return redirect(url_for("login"))

@app.route('/login', methods=["GET", "POST"])
def login():
    """ 
    Logs in a user.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check credentials
        if username in users and users[username]["password"] == password:
            login_user(admin_user)
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials", 401
    return render_template("login.html")

@app.route('/dashboard')
@login_required
def dashboard():
    """ 
    Displays the dashboard.
    """
    return render_template("dashboard.html")

@app.route('/logout')
@login_required
def logout():
    """ 
    Logs out the current user.
    """
    logout_user()
    return redirect(url_for("login"))

@app.route('/test-db')
def test_db():
    """ 
    Tests the database connection.
    """
    from sqlalchemy import text

    try:
        db.session.execute(text('SELECT 1'))
        return "<h1>Database connected successfully.</h1>"
    except Exception as e:
        return f"<h1>Database failed to connect:</h1><p>{e}</p>"

@app.route('/api/customers')
@login_required
def get_customers():
    """ 
    Fetches the list of customers.
    """
    try:
        customers = db.session.query(Customer.lee_no).order_by(Customer.lee_no).all()
        customer_list = [c[0] for c in customers if c[0] is not None]
        return jsonify(customer_list)
    except Exception as e:
        print(f"Customer Fetch Error: {e}")
        return jsonify({"error": "Failed to fetch customers from database."}), 500

@app.route('/customers')
@login_required
def customers():
    """ 
    Displays the list of all customers and summary statistics.
    """
    try:
        # Fetch all customers ordered by name
        all_customers = Customer.query.order_by(Customer.name).all()
        total_customers = len(all_customers)

        # Calculate the start of the week
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        # Query for customers registered >= start of the week
        new_customers_this_week = db.session.query(Customer).filter(
            Customer.registration_date >= start_of_week
        ).count()

        return render_template(
            "user_management.html", 
            customers=all_customers,
            total_customers=total_customers,
            new_customers_this_week=new_customers_this_week
        )
    except Exception as e:
        print(f"Customer Fetch Error: {e}")
        flash("Could not load customer statistics.", "error")
        return render_template("user_management.html", customers=[], error="Could not fetch customer list.")

@app.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    """
    Handles the creation of a new customer.
    """
    if request.method == 'POST':
        try:
            new_customer = Customer(
                lee_no=request.form['lee_no'],
                name=request.form['name'],
                address=request.form['address'],
                capacity=request.form['capacity'],
                brand=request.form['brand'],
                email=request.form['email'],
                phone=request.form['phone'],
                status=request.form['status'],
            )
            db.session.add(new_customer)
            db.session.commit()
            flash(f"Customer '{new_customer.name}' created successfully.", "success")
            return redirect(url_for('customers'))
        except Exception as e:
            db.session.rollback()
            print(f"Customer Creation Error: {e}")
            flash(f"Customer Creation Error: A customer with the same LEE_NO might already exist.", "error")
    return render_template("new_customer.html")

@app.route('/api/get-all-customers')
@login_required 
def get_all_customers_for_loggers():
    """
    API endpoint for field loggers. 
    @return: JSON list of all customers
    """
    try:
        customers = Customer.query.with_entities(
            Customer.id, 
            Customer.lee_no, 
            Customer.name
        ).order_by(Customer.lee_no).all()

        customer_list = [
            {"id": c.id, "code": c.lee_no, "name": c.name}
            for c in customers
        ]
        return jsonify(customer_list)
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": "Failed to fetch customer list"}), 500

@app.route('/api/daily-readings')
@login_required
def daily_readings():
    """ 
    Fetches the daily readings for a specific customer.
    """
    lee_no = request.args.get("customer_id")
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not all([lee_no, year, month]):
        return jsonify({"error": "Missing required parameters."}), 400

    try:
        # Create a subquery to get the first reading of each day
        subquery = db.session.query(
            SolarBillingReader,
            func.row_number().over(
                partition_by=cast(SolarBillingReader.Timestamp, Date),
                order_by=SolarBillingReader.Timestamp.asc()
            ).label('row_num')
        ).join(Customer).filter(
            Customer.lee_no == lee_no,
            func.extract('year', SolarBillingReader.Timestamp) == year,
            func.extract('month', SolarBillingReader.Timestamp) == month
        ).subquery()

        # Select from the subquery only the rows where row_num is 1
        daily_first_readings = db.session.query(subquery).filter(subquery.c.row_num == 1).all()

        # Format the readings into JSON object for the frontend
        readings_dict = {
            reading.Timestamp.strftime('%Y-%m-%d'): reading.Total_Positive_Real_Energy_kWh
            for reading in daily_first_readings
        }
        return jsonify(readings_dict)
    except Exception as e:
        print(f"Daily Reading Error: {e}")
        return jsonify({"error": "Failed to fetch daily readings from database."}), 500

@app.route('/api/v1/loggers/customers')
def api_v1_get_customers_for_loggers():
    """
    A secure API endpoint for loggers to fetch the customer list.
    """
    provided_key = request.headers.get('X-API-Key')

    # Validate key from logger
    if not provided_key or provided_key != config.API_SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        customers = Customer.query.with_entities(
            Customer.id, 
            Customer.lee_no, 
            Customer.name
        ).order_by(Customer.lee_no).all()

        customer_list = [
            {"id": c.id, "code": c.lee_no, "name": c.name}
            for c in customers
        ]
        return jsonify(customer_list)
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": "Failed to fetch customer list"}), 500

# RUN WEBAPP

if __name__ == "__main__":
    app.run(debug=True)