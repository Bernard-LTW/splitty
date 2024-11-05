from data.db_manager import DBHandler
from data.db_models import Admin
from secure_password import hash_input as hash_password

db = DBHandler("sqlite:///splitty_dev.sqlite")


def new_admin(username, password):
    new_admin = Admin(username=username, password=hash_password(password))
    db.session.add(new_admin)
    db.session.commit()
    print(f"New admin {username} added successfully.")


def ask_for_admin():
    username = input("Enter new admin username: ")
    password = input("Enter new admin password: ")
    new_admin(username, password)

ask_for_admin()