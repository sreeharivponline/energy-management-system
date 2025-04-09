# add_officers.py
from database import db, Officer, init_db
from auth import hash_password
from app import app

with app.app_context():
    init_db(app)
    officers = [
        Officer(
            username='officer_ernakulam',
            password=hash_password('officerpass1'),
            full_name='KSEB Officer Ernakulam',
            city='Ernakulam'
        ),
        Officer(
            username='officer_kozhikode',
            password=hash_password('officerpass2'),
            full_name='KSEB Officer Kozhikode',
            city='Kozhikode'
        ),
        Officer(
            username='officer_thrissur',
            password=hash_password('officerpass3'),
            full_name='KSEB Officer Thrissur',
            city='Thrissur'
        )
    ]
    for officer in officers:
        db.session.add(officer)
    db.session.commit()
    print("Officers added successfully!")