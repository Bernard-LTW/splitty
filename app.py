from collections import defaultdict
import datetime
from jose import jwt, JWTError, ExpiredSignatureError
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, flash
from data.db_models import Trip, People, trip_participants
from data.db_manager import DBHandler
from token_management import generate_token

app = Flask(__name__)
db = DBHandler("sqlite:///data/splitty_dev.sqlite")

app.config['SECRET_KEY'] = 'TOKEN_ENCR'


def get_user_details():
    token = request.cookies.get('admin_token')
    if not token:
        return None, None
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = payload["user_id"]
        username = payload["username"]
        return user_id, username
    except JWTError:
        return None, None


@app.before_request
def check_admin_token():
    excluded_routes = ['login','static']

    # Skip token check if the current route is excluded
    if request.endpoint in excluded_routes:
        return

    token = request.cookies.get('admin_token')  # Check for the admin token

    if not token:
        #flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))  # Redirect to login if no token

    try:
        # Verify token
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        request.admin_id = payload["user_id"]
        request.admin_name = payload["username"]

    except ExpiredSignatureError:
        #flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for('login'))  # Redirect to login if token expired

    except JWTError:
        #flash("Invalid token. Please log in again.", "warning")
        return redirect(url_for('login'))  # Redirect to login for any other errors

def get_logged_in_admin_name():
    return getattr(request, 'admin_name', None)  # Safely get admin_name from request

@app.route('/')
def index():
    admin_name = get_logged_in_admin_name()
    trips = db.get_all_trips()
    return render_template('index.html', trips=trips, admin_name=admin_name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = db.get_admin(username)
        if admin and db.login_admin(admin, password):
            token = generate_token(admin)
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('admin_token', token, httponly=True)
            return resp
    return render_template('login.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('admin_token', '', expires=0)
    return resp



@app.route('/add_trip', methods=['POST'])
def add_trip():
    trip_name = request.form['trip_name']
    destination = request.form['destination']
    start_date = request.form['start_date']  # New field for start date
    end_date = request.form['end_date']      # New field for end date
    currency = request.form['currency']

    db.add_trip(trip_name, destination, start_date, end_date, currency)
    return redirect(url_for('index'))  # Redirect to the homepage or wherever appropriate

@app.route('/trip/<int:trip_id>')
def trip(trip_id):
    trip = db.get_trip(trip_id)
    participants = trip.participants

    transactions_by_date = defaultdict(list)

    for transaction in trip.transactions:
        transaction_date = transaction.date.strftime("%Y-%m-%d")  # Format the date as needed
        transactions_by_date[transaction_date].append(transaction)
    return render_template('trip_details.html', trip=trip, transactions_by_date=transactions_by_date, participants=participants)

@app.route('/manage_people')
def manage_people():
    user_id, username = get_user_details()

    users = db.get_all_users()
    return render_template('manage_people.html', users=users, username=username, user_id=user_id)

@app.route('/add_participant', methods=['POST'])
def add_existing_people():
    user_ids = request.form.getlist('user_ids')
    trip_id = request.form['trip_id']
    for user_id in user_ids:
        db.add_user_to_trip(trip_id, user_id)
    return redirect(url_for('trip', trip_id=trip_id))


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    trip_id = request.form['trip_id']
    payer_id = request.form['payer_id']
    amount = float(request.form['total'])
    description = request.form['description']
    date = request.form['date']
    time = request.form['time']

    # Combine date and time into a datetime object
    transaction_dt_str = date + ' ' + time
    transaction_dt = datetime.datetime.strptime(transaction_dt_str, '%Y-%m-%d %H:%M')

    # Initialize a list to hold amounts owed
    amounts_owed = {}
    participants = []  # This will store all the selected participants

    # Iterate through all possible participant IDs and capture their owed amounts
    for user in request.form:
        if user.startswith('amount_owed_'):
            participant_id = user.split('_')[-1]  # Get the ID from the input name
            amount_owed = float(request.form[user]) if request.form[user] else 0.0

            # Only add to amounts owed if the amount is greater than zero
            if amount_owed > 0:
                amounts_owed[participant_id] = amount_owed
                participants.append(participant_id)  # Keep track of participants with amounts owed

    db.add_transaction(trip_id, payer_id, amount, description, transaction_dt, participants, amounts_owed)
    return redirect(url_for('trip', trip_id=trip_id))


@app.route('/non_participants/<int:trip_id>', methods=['GET'])
def get_existing_users(trip_id):
    users = db.get_all_non_participants(trip_id)

    users_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
    return jsonify(users_list)

@app.route('/fetch_users', methods=['GET'])
def fetch_users():
    users = db.get_all_users() # Fetch all users
    users_data = [{"id": user.id, "name": user.name} for user in users]
    print(users_data)
    return jsonify(users=users_data)

@app.route('/calculate_debts', methods=['GET', 'POST'])
def calculate_debts():
    debt_summary = None  # Initialize an empty debt summary

    if request.method == 'POST':
        trip_id = request.form.get('trip_id')

        # Calculate debts if trip_id is valid
        if trip_id:
            try:
                trip_id = int(trip_id)  # Convert to integer
                debt_summary = db.get_trip_debt_summary(trip_id)
            except ValueError:
                # Handle invalid trip ID input (e.g., non-integer)
                debt_summary = {"Error": "Invalid Trip ID. Please enter a numeric ID."}

    return render_template('testing.html', debt_summary=debt_summary)

if __name__ == '__main__':
    app.run(debug=True)



#TODO: Add ability to add new users
#TODO: Add debt calc to bottom of trip page, add payments and more
#TODO: Add ability to add payments
#TODO: Add manage trips page
