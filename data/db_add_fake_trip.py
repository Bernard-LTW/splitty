from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from data.db_models import Trip, Transaction, TransactionParticipant, Payment, People
from data.db_manager import DBHandler

def create_sample_data(session: Session):
    # Step 1: Add a new trip
    new_trip = Trip(
        name="Weekend Getaway",
        destination="Lake Tahoe",
        start_date=datetime(2024, 11, 10),
        end_date=datetime(2024, 11, 12),
        currency="USD"
    )
    session.add(new_trip)
    session.commit()  # Commit to assign an ID to new_trip

    # Step 2: Add three new people
    person1 = People(name="Bernard", email="alice@example.com")
    person2 = People(name="Grace", email="bob@example.com")
    person3 = People(name="Leo", email="charlie@example.com")
    session.add_all([person1, person2, person3])
    session.commit()  # Commit to assign IDs to the new people

    # Step 3: Associate people with the trip
    new_trip.participants.extend([person1, person2, person3])
    session.commit()

    # Step 4: Create ten transactions
    transactions = [
        Transaction(
            trip_id=new_trip.id,
            payer_id=person1.id,
            amount=120.0,
            description="Gas for trip",
            date=new_trip.start_date + timedelta(hours=2)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person2.id,
            amount=200.0,
            description="Grocery shopping",
            date=new_trip.start_date + timedelta(hours=4)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person3.id,
            amount=80.0,
            description="Snacks",
            date=new_trip.start_date + timedelta(hours=5)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person1.id,
            amount=150.0,
            description="Dinner",
            date=new_trip.start_date + timedelta(hours=6)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person2.id,
            amount=50.0,
            description="Breakfast",
            date=new_trip.start_date + timedelta(hours=20)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person3.id,
            amount=90.0,
            description="Souvenirs",
            date=new_trip.start_date + timedelta(hours=22)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person1.id,
            amount=70.0,
            description="Lunch",
            date=new_trip.start_date + timedelta(hours=24)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person2.id,
            amount=60.0,
            description="Drinks",
            date=new_trip.start_date + timedelta(hours=26)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person3.id,
            amount=130.0,
            description="Taxi fare",
            date=new_trip.end_date - timedelta(hours=5)
        ),
        Transaction(
            trip_id=new_trip.id,
            payer_id=person1.id,
            amount=110.0,
            description="Accommodation",
            date=new_trip.end_date - timedelta(hours=2)
        ),
    ]
    session.add_all(transactions)
    session.commit()  # Commit to save transactions

    # Step 5: Create transaction participants
    for transaction in transactions:
        # Split the transaction among all participants for simplicity
        amount_per_person = transaction.amount / 3
        for person in [person1, person2, person3]:
            # Each participant owes a portion unless they are the payer
            if person.id != transaction.payer_id:
                tp = TransactionParticipant(
                    transaction_id=transaction.id,
                    user_id=person.id,
                    amount_owed=amount_per_person
                )
                session.add(tp)
    session.commit()  # Commit to save transaction participants

    print("Sample trip, people, and transactions created successfully.")

# Assuming 'session' is your SQLAlchemy session
# create_sample_data(session)
db = DBHandler("sqlite:///splitty_dev.sqlite")
create_sample_data(db.session)

db.add_payment(3,5,4, 20.0, datetime(2024, 11, 11, 12, 0, 0))
