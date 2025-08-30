from app import app, db, LarvaeData, User
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# This script is meant to be run once during deployment to create the database tables.
# It should be called from the Render build or start command.

# The Flask application context is necessary for SQLAlchemy to function correctly
with app.app_context():
    # Create all database tables based on the models defined in app.py
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully!")

    # Check if any users exist. If not, create a default admin user.
    # This prevents creating a duplicate user on every deployment.
    if not db.session.query(User).first():
        print("Creating a default admin user...")
        # You should replace 'admin' and 'password' with more secure credentials
        admin_user = User(username='admin')
        admin_user.set_password('admin123')  # Remember to use a strong password
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created.")
    else:
        print("Users already exist. Skipping default user creation.")

    # Check if there is any larvae data. If not, add some dummy data.
    if not db.session.query(LarvaeData).first():
        print("Populating dummy data...")
        from random import uniform, randint

        def populate_dummy_data():
            # Clear old dummy data to prevent duplicates on every run
            db.session.query(LarvaeData).delete()

            # Add data for tray 1
            # for i in range(1, 15):
            #     timestamp = datetime.utcnow() - timedelta(days=15 - i)
            #     db.session.add(LarvaeData(
            #         tray_number=1,
            #         length=round(uniform(10, 20), 1),
            #         width=round(uniform(2, 4), 1),
            #         area=round(uniform(20, 80), 1),
            #         weight=round(uniform(90, 150), 1),
            #         count=randint(100, 500),
            #         timestamp=timestamp
            #     ))

            # # Add data for tray 2
            # for i in range(1, 12):
            #     timestamp = datetime.utcnow() - timedelta(days=11 - i)
            #     db.session.add(LarvaeData(
            #         tray_number=2,
            #         length=round(uniform(12, 22), 1),
            #         width=round(uniform(2.5, 4.5), 1),
            #         area=round(uniform(25, 90), 1),
            #         weight=round(uniform(95, 160), 1),
            #         count=randint(80, 400),
            #         timestamp=timestamp
            #     ))

            # # Add data for tray 3
            # for i in range(1, 12):
            #     timestamp = datetime.utcnow() - timedelta(days=11 - i)
            #     db.session.add(LarvaeData(
            #         tray_number=3,
            #         length=round(uniform(9, 18), 1),
            #         width=round(uniform(1.8, 3.8), 1),
            #         area=round(uniform(18, 70), 1),
            #         weight=round(uniform(85, 145), 1),
            #         count=randint(120, 600),
            #         timestamp=timestamp
            #     ))

            # # Add dummy data for new trays (e.g., 156, 256, 356) to ensure they appear
            # for tray in [156, 256, 356]:
            #     for i in range(1, 7):
            #         timestamp = datetime.utcnow() - timedelta(days=6 - i)
            #         db.session.add(LarvaeData(
            #             tray_number=tray,
            #             length=round(uniform(15, 25), 1),
            #             width=round(uniform(3, 5), 1),
            #             area=round(uniform(30, 100), 1),
            #             weight=round(uniform(100, 180), 1),
            #             count=randint(150, 700),
            #             timestamp=timestamp
            #         ))
            db.session.commit()
            print("Dummy data added successfully.")
    else:
        print("Data already exists. Skipping dummy data population.")
    
print("Database initialization script finished.")
