from database import db, User, init_db
from auth import hash_password
from app import app

with app.app_context():
    # Add Admin
    admin = User(
        username='admin1',
        password=hash_password('adminpassword'),
        role='admin',
        full_name='Admin User',
        address='KSEB HQ',
        city='Thiruvananthapuram',
        phone_number='1234567890'
    )
    db.session.add(admin)

    # Add KSEB Officer
    kseb = User(
        username='kseb1',
        password=hash_password('ksebpassword'),
        role='kseb',
        full_name='KSEB Officer',
        address='KSEB Office',
        city='Kochi',
        phone_number='0987654321'
    )
    db.session.add(kseb)

    db.session.commit()
    print("Admin and KSEB Officer added successfully!")