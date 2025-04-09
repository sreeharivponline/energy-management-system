# add_sample_data.py
from database import db, Admin, User, Officer, EnergyData
from auth import hash_password
from app import app
from datetime import datetime

with app.app_context():
    # Clear existing data
    db.drop_all()
    db.create_all()

    # Add Officers (city-wise)
    officer1 = Officer(
        username='kseb_ernakulam',
        password=hash_password('ksebpassword1'),
        full_name='KSEB Officer Ernakulam',
        city='Ernakulam'
    )
    officer2 = Officer(
        username='kseb_kozhikode',
        password=hash_password('ksebpassword2'),
        full_name='KSEB Officer Kozhikode',
        city='Kozhikode'
    )
    officer3 = Officer(
        username='kseb_thrissur',
        password=hash_password('ksebpassword3'),
        full_name='KSEB Officer Thrissur',
        city='Thrissur'
    )
    db.session.add_all([officer1, officer2, officer3])

    # Add Admin (using the Admin model)
    admin = Admin(
        username='admin1',
        password=hash_password('adminpassword')
    )
    db.session.add(admin)

    # Add Users
    user1 = User(
        username='user1@example.com',
        password=hash_password('user1password'),
        role='user',
        full_name='Anil Kumar',
        address='123 MG Road',
        city='Ernakulam',
        phone_number='9876543210',
        officer_id=1  # Assigned to Ernakulam officer
    )
    user2 = User(
        username='user2@example.com',
        password=hash_password('user2password'),
        role='user',
        full_name='Priya Menon',
        address='45 Beach Road',
        city='Kozhikode',
        phone_number='8765432109',
        officer_id=2  # Assigned to Kozhikode officer
    )
    user3 = User(
        username='user3@example.com',
        password=hash_password('user3password'),
        role='user',
        full_name='Suresh Nair',
        address='78 Temple Street',
        city='Thrissur',
        phone_number='7654321098',
        officer_id=3  # Assigned to Thrissur officer
    )
    db.session.add_all([user1, user2, user3])

    # Add Energy Data
    energy_data = [
        EnergyData(user_id=1, date=datetime(2025, 3, 23), consumption=100),
        EnergyData(user_id=1, date=datetime(2025, 3, 24), consumption=105),
        EnergyData(user_id=1, date=datetime(2025, 3, 25), consumption=110),
        EnergyData(user_id=2, date=datetime(2025, 3, 23), consumption=90),
        EnergyData(user_id=2, date=datetime(2025, 3, 24), consumption=95),
        EnergyData(user_id=2, date=datetime(2025, 3, 25), consumption=100),
        EnergyData(user_id=3, date=datetime(2025, 3, 23), consumption=500),  # Anomaly
        EnergyData(user_id=3, date=datetime(2025, 3, 24), consumption=85),
        EnergyData(user_id=3, date=datetime(2025, 3, 25), consumption=90),
    ]
    db.session.add_all(energy_data)

    db.session.commit()
    print("Sample data added successfully!")
