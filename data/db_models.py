from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime, Float, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

# Association table for many-to-many relationship
trip_participants = Table(
    'trip_participants', Base.metadata,
    Column('trip_id', Integer, ForeignKey('trips.id', ondelete="RESTRICT"), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete="RESTRICT"), primary_key=True)
)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True)
    password = Column(String(255))

class People(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)

    # Relationship to access trips for a user
    trips = relationship("Trip", secondary=trip_participants, back_populates="participants")

    # One-to-many relationship with Transaction
    transactions = relationship("Transaction", back_populates="payer")

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    destination = Column(String(255))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    currency = Column(String(10))

    # Many-to-many relationship with People
    participants = relationship("People", secondary=trip_participants, back_populates="trips")

    # One-to-many relationship with Transaction
    transactions = relationship("Transaction", back_populates="trip", cascade="all, delete-orphan")

    # One-to-many relationship with Payment
    payments = relationship("Payment", cascade="all, delete-orphan", back_populates="trip")

    # Hybrid property to calculate total spending
    @hybrid_property
    def total_spending(self):
        return sum(transaction.amount for transaction in self.transactions)

    @total_spending.expression
    def total_spending(cls):
        return func.coalesce(func.sum(Transaction.amount), 0.0).label("total_spending")

class TransactionParticipant(Base):
    __tablename__ = "transaction_participants"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id', ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey('users.id', ondelete="RESTRICT"))
    amount_owed = Column(Float)
    settled = Column(Boolean, default=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="participants")
    user = relationship("People")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id', ondelete="CASCADE"))
    payer_id = Column(Integer, ForeignKey('users.id', ondelete="RESTRICT"))
    amount = Column(Float)
    description = Column(String(255))
    date = Column(DateTime)

    # Relationships
    trip = relationship("Trip", back_populates="transactions")
    payer = relationship("People", back_populates="transactions")
    participants = relationship("TransactionParticipant", back_populates="transaction", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id', ondelete="CASCADE"))
    debtor_id = Column(Integer, ForeignKey('users.id', ondelete="RESTRICT"))
    creditor_id = Column(Integer, ForeignKey('users.id', ondelete="RESTRICT"))
    amount = Column(Float)
    date = Column(DateTime)

    # Relationships
    trip = relationship("Trip", overlaps="payments")
    debtor = relationship("People", foreign_keys=[debtor_id])
    creditor = relationship("People", foreign_keys=[creditor_id])