import sqlalchemy as db
from sqlalchemy import MetaData
from sqlalchemy.orm import Session
from data.db_models import People, Trip, Transaction, TransactionParticipant, trip_participants, Payment
from data.debt_manager import calculate_net_debts


class DBHandler:
    def __init__(self,path):
        self.engine = db.create_engine(path, echo=False)
        self.session = Session(self.engine)
        self.metadata = MetaData()
        #print(self.metadata.tables.keys())

    def add_sample_data(self):
        user1 = People(name="Alice", email="alice.alice@gmail.com")
        user2 = People(name="Bob", email="bob.bob@gmail.com")
        user3 = People(name="Charlie", email="charlie.b@gmail.com")

        trip1 = Trip(name="Trip to Paris", destination="Paris", currency="EUR")
        trip2 = Trip(name="Trip to London", destination="London", currency="GBP")

        trip1.participants.append(user1)
        trip1.participants.append(user2)
        trip2.participants.append(user2)
        trip2.participants.append(user3)

        self.session.add(user1)
        self.session.add(user2)
        self.session.add(user3)
        self.session.add(trip1)
        self.session.add(trip2)

        self.session.commit()
        print("Sample data added successfully")
        return

    def get_all_trips(self):
        trips = self.session.query(Trip).all()
        return trips

    def add_trip(self, trip_name, destination, start_date, end_date, currency):
        trip = Trip(name=trip_name, destination=destination, currency=currency)
        self.session.add(trip)
        self.session.commit()
        return

    def get_trip(self, trip_id):
        trip = self.session.query(Trip).filter(Trip.id == trip_id).first()
        return trip

    def add_user_to_trip(self, trip_id, user_id):
        trip = self.session.query(Trip).filter(Trip.id == trip_id).first()
        user = self.session.query(People).filter(People.id == user_id).first()
        trip.participants.append(user)
        self.session.commit()
        return

    def add_transaction(self, trip_id, payer_id, amount, description, date, participants, amounts_owed):
        # Create a transaction
        transaction = Transaction(trip_id=trip_id, payer_id=payer_id, amount=amount, description=description, date=date)

        # Add the transaction to the session first
        self.session.add(transaction)
        self.session.commit()  # Commit to get the transaction ID

        for participant_id in participants:
            amount_owed = amounts_owed[participant_id]
            transaction_participant = TransactionParticipant(transaction_id=transaction.id, user_id=participant_id, amount_owed=amount_owed)
            self.session.add(transaction_participant)

        self.session.commit()  # Commit the transaction and participants
        return transaction  # Optionally return the created transaction

    def get_all_non_participants(self, trip_id):
        trip = self.session.query(Trip).filter(Trip.id == trip_id).first()
        participants = trip.participants
        all_users = self.session.query(People).all()
        non_participants = [user for user in all_users if user not in participants]
        return non_participants

    def get_all_users(self):
        users = self.session.query(People).all()
        return users

    def get_default_user(self):
        user = self.session.query(People).filter(People.name == "Bob").first()
        return user

    def get_user(self, user_id):
        user = self.session.query(People).filter(People.id == user_id).first()
        return user

    def get_trip_debt_summary(self, trip_id):
        return calculate_net_debts(self.session, trip_id)

    def add_payment(self, trip_id, debtor_id, creditor_id, amount, date):
        payment = Payment(trip_id=trip_id, debtor_id=debtor_id, creditor_id=creditor_id, amount=amount, date=date)
        self.session.add(payment)
        self.session.commit()
        return payment
