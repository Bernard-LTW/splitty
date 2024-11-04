from collections import defaultdict
from sqlalchemy.orm import Session
from data.db_models import Trip, Transaction, TransactionParticipant, Payment, People

def calculate_net_debts(session: Session, trip_id: int):
    # Dictionary to store the net debt relationships
    debts = defaultdict(lambda: defaultdict(float))

    # Query all unsettled transaction participants for the specified trip
    trip_transactions = (
        session.query(TransactionParticipant)
        .join(Transaction)
        .filter(Transaction.trip_id == trip_id, TransactionParticipant.settled.is_(False))
        .all()
    )

    # Calculate debts based on unsettled transactions
    for tp in trip_transactions:
        transaction = tp.transaction
        payer_id = transaction.payer_id
        debtor_id = tp.user_id
        amount_owed = tp.amount_owed

        # Skip if debtor is the same as payer
        if debtor_id != payer_id:
            debts[debtor_id][payer_id] += amount_owed

    # Query all payments made in this trip to offset debts
    trip = session.query(Trip).filter(Trip.id == trip_id).one()

    payments_query = session.query(Payment).filter(Payment.trip_id == trip_id)

    payments = payments_query.all()

    # Subtract payments from the debts
    for payment in payments:
        debtor_id = payment.debtor_id
        creditor_id = payment.creditor_id
        amount_paid = payment.amount

        # Reduce the debt amount by the payment amount, if there’s an existing debt
        if debts[debtor_id][creditor_id] > 0:
            debts[debtor_id][creditor_id] -= amount_paid

            # If the debt goes negative, it means the payment exceeds the debt,
            # so we transfer the balance to the creditor's owed amount to debtor.
            if debts[debtor_id][creditor_id] < 0:
                debts[creditor_id][debtor_id] += abs(debts[debtor_id][creditor_id])
                debts[debtor_id][creditor_id] = 0

    # Consolidate debts so each pair has a single net amount
    for debtor_id, creditors in debts.items():
        for creditor_id, amount in list(creditors.items()):
            if debts[creditor_id][debtor_id] > 0:
                # Find the net debt amount between debtor and creditor
                if amount > debts[creditor_id][debtor_id]:
                    debts[debtor_id][creditor_id] -= debts[creditor_id][debtor_id]
                    debts[creditor_id][debtor_id] = 0
                else:
                    debts[creditor_id][debtor_id] -= amount
                    debts[debtor_id][creditor_id] = 0

    # For readability, transform debt IDs into names
    debt_summary = {}
    for debtor_id, creditors in debts.items():
        debtor_name = session.query(People.name).filter(People.id == debtor_id).scalar()
        debt_summary[debtor_name] = {
            session.query(People.name).filter(People.id == creditor_id).scalar(): amount
            for creditor_id, amount in creditors.items() if amount > 0
        }

    print(debt_summary)
    return debt_summary