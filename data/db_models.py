from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association table for many-to-many relationship
trip_participants = Table('trip_participants', Base.metadata,
    Column('trip_id', Integer, ForeignKey('trips.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class People(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

    # Relationship to access trips for a user
    trips = relationship("Trip", secondary=trip_participants, back_populates="participants")

    # One-to-many relationship with Transaction
    transactions = relationship("Transaction", back_populates="payer")

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    destination = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    currency = Column(String)

    # Many-to-many relationship with People
    participants = relationship("People", secondary=trip_participants, back_populates="trips")

    # One-to-many relationship with Transaction
    transactions = relationship("Transaction", back_populates="trip")

class TransactionParticipant(Base):
    __tablename__ = "transaction_participants"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    amount_owed = Column(Float)
    settled = Column(Boolean, default=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="participants")
    user = relationship("People")

# Update the Transaction model to include the relationship
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    payer_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)  # Total amount of the transaction
    description = Column(String)
    date = Column(DateTime)

    # Relationships
    trip = relationship("Trip", back_populates="transactions")
    payer = relationship("People", back_populates="transactions")
    participants = relationship("TransactionParticipant", back_populates="transaction")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    debtor_id = Column(Integer, ForeignKey('users.id'))
    creditor_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)  # Amount paid by debtor to creditor
    date = Column(DateTime)

    # Relationships
    trip = relationship("Trip")
    debtor = relationship("People", foreign_keys=[debtor_id])
    creditor = relationship("People", foreign_keys=[creditor_id])