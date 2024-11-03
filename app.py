from collections import defaultdict
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify
from data.db_models import Trip, People, trip_participants
from data.db_manager import DBHandler

app = Flask(__name__)
db = DBHandler("sqlite:///data/splitty_dev.sqlite")
@app.route('/')
def index():
    trips = db.get_all_trips()
    return render_template('index.html', trips=trips)

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
    return render_template('trip_details.html', trip=trip, transactions_by_date=transactions_by_date)

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
    transaction_dt = datetime.strptime(transaction_dt_str, '%Y-%m-%d %H:%M')

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

if __name__ == '__main__':
    app.run(debug=True)

#TODO: Add User Selector and Logic to base.html
#TODO: Add ability to calculate who owes who
#TODO: Add ability to add new users
#TODO: Add ability to calculate who owes who
#TODO: Add ability to exclude certain people from a single transaction and to be able to choose amount that each person owes