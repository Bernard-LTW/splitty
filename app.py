from collections import defaultdict
import datetime
from jose import jwt, JWTError, ExpiredSignatureError
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from data.db_models import Trip, People, trip_participants
from data.db_manager import DBHandler

app = Flask(__name__)
db = DBHandler("sqlite:///data/splitty_dev.sqlite")

app.config['SECRET_KEY'] = 'your_secret_key'

# Generate a default user token
def generate_token(user):
    payload = {
        'user_id': user.id,
        'username':user.name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")

def get_user_details():
    token = request.cookies.get('user_token')
    if not token:
        return None, None
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = payload["user_id"]
        username = payload["username"]
        return user_id, username
    except JWTError:
        return None, None

# Middleware for checking token
@app.before_request
def check_user_token():
    token = request.cookies.get('user_token')

    if not token:
        # No token found, set default user
        default_user_id = db.get_default_user()  # Get the default user ID from your database
        default_token = generate_token(default_user_id)
        resp = make_response(jsonify({"message": "Default user assigned"}))
        resp.set_cookie('user_token', default_token, httponly=True)
        return resp

    else:
        try:
            # Verify token
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # Store user_id in request context if needed
            request.user_id = payload["user_id"]

        except ExpiredSignatureError:
            # Token expired, decode without expiration check to get the user_id
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"], options={"verify_exp": False})
            user_id = payload["user_id"]

            # Create a new token for the same user
            new_token = generate_token(user_id)
            resp = make_response(jsonify({"message": "Token refreshed"}))
            resp.set_cookie('user_token', new_token, httponly=True)
            return resp

        except JWTError:
            # Any other JWT errors should result in a new default token
            default_user_id = db.get_default_user()
            default_token = generate_token(default_user_id)
            resp = make_response(jsonify({"message": "Invalid token, default user assigned"}))
            resp.set_cookie('user_token', default_token, httponly=True)
            return resp

@app.route('/')
def index():
    user_id, username = get_user_details()

    trips = db.get_all_trips()
    return render_template('index.html', trips=trips, username=username, user_id=user_id)

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


@app.route('/api/non_participants/<int:trip_id>', methods=['GET'])
def get_existing_users(trip_id):
    users = db.get_all_non_participants(trip_id)

    users_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
    return jsonify(users_list)

@app.route('/api/fetch_users', methods=['GET'])
def fetch_users():
    users = db.get_all_users() # Fetch all users
    users_data = [{"id": user.id, "name": user.name} for user in users]
    print(users_data)
    return jsonify(users=users_data)

@app.route('/change_user/<int:user_id>')
def change_user(user_id):
    user = db.get_user(user_id)
    token = generate_token(user)
    resp = make_response(redirect(request.referrer))
    resp.set_cookie('user_token', token, httponly=True)
    return resp


### TESTING
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





#TODO: Remove User Selector, not needed but rather add a main password toekn system
#TODO: Add ability to calculate who owes who
#TODO: Add ability to add new users
#TODO: Add debt calc to bottom of trip page, add payments and more
#TODO: Add ability to add payments

