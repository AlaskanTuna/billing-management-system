# src/webapp.py

import config

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
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

class EnergyReader(db.Model):
    __tablename__ = config.DB_TABLE_NAME
    id = db.Column(db.BigInteger, primary_key=True)
    customer_id = db.Column(db.String(255), nullable=True, index=True)
    Timestamp = db.Column(db.TIMESTAMP, nullable=False)
    Total_Positive_Real_Energy_kWh = db.Column(db.Float, nullable=True)

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
        customers = db.session.query(EnergyReader.customer_id).distinct().all()
        customer_list = [customer[0] for customer in customers if customer[0] is not None]
        return jsonify(customer_list)
    except Exception as e:
        print(f"Customer Fetch Error: {e}")
        return jsonify({"error": "Failed to fetch customers from database."}), 500

@app.route('/api/daily-readings')
@login_required
def daily_readings():
    """ 
    Fetches the daily readings for a specific customer.
    """
    customer_id = request.args.get("customer_id")
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not all([customer_id, year, month]):
        return jsonify({"error": "Missing required parameters."}), 400

    try:
        # Create a subquery to get the first reading of each day
        subquery = db.session.query(
            EnergyReader,
            func.row_number().over(
                partition_by=cast(EnergyReader.Timestamp, Date),
                order_by=EnergyReader.Timestamp.asc()
            ).label('row_num')
        ).filter(
            EnergyReader.customer_id == customer_id,
            func.extract('year', EnergyReader.Timestamp) == year,
            func.extract('month', EnergyReader.Timestamp) == month
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

# RUN WEBAPP

if __name__ == "__main__":
    app.run(debug=True)