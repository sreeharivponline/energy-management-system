from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import login_user, login_required, logout_user, current_user # type: ignore
from database import db, User, Officer, EnergyData, Admin
from auth import AuthUser, hash_password, check_password
from sklearn.ensemble import IsolationForest
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.pdfgen import canvas # type: ignore
import os
from predictions import generate_user_predictions
from bill_calculator import calculate_kseb_bill
import json

def init_routes(app):
    @app.route('/')
    def home():
        """Redirect to the login page."""
        return render_template('index.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration."""
        if request.method == 'POST':
            username = request.form['username']
            password = hash_password(request.form['password'])
            full_name = request.form['full_name']
            address = request.form['address']
            city = request.form['city']
            phone_number = request.form['phone_number']

            # Validate phone number
            if not phone_number.isdigit() or len(phone_number) < 10:
                flash('Phone number must be at least 10 digits!')
                return redirect(url_for('register'))

            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists!')
                return redirect(url_for('register'))

            # Assign user to an officer based on city
            officer = Officer.query.filter_by(city=city).first()
            new_user = User(
                username=username,
                password=password,
                role='user',
                full_name=full_name,
                address=address,
                city=city,
                phone_number=phone_number,
                officer_id=officer.id if officer else None
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle login for Admin, User, and Officer."""
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            admin = Admin.query.filter_by(username=username).first()
            user = User.query.filter_by(username=username).first()
            officer = Officer.query.filter_by(username=username).first()

            # Debug login attempts
            print(f"Login attempt - Username: {username}")
            print(f"Admin found: {admin}")
            print(f"User found: {user}")
            print(f"Officer found: {officer}")
            if admin:
                print(f"Admin password match: {check_password(password, admin.password)}")
            if user:
                print(f"User password match: {check_password(password, user.password)}")
            if officer:
                print(f"Officer password match: {check_password(password, officer.password)}")

            if admin and check_password(password, admin.password):
                login_user(AuthUser(f"admin:{admin.id}", 'admin', is_officer=False))
                return redirect(url_for('admin_dashboard'))
            elif user and check_password(password, user.password):
                login_user(AuthUser(f"user:{user.id}", user.role, is_officer=False))
                return redirect(url_for('user_dashboard'))
            elif officer and check_password(password, officer.password):
                login_user(AuthUser(f"officer:{officer.id}", 'kseb', is_officer=True))
                return redirect(url_for('kseb_dashboard'))
            flash('Invalid credentials!')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """Handle logout for all users."""
        logout_user()
        return redirect(url_for('home'))

    @app.route('/user/dashboard', methods=['GET', 'POST'])
    @login_required
    def user_dashboard():
        """Display the user dashboard with energy consumption data and handle new data submission."""
        if current_user.role != 'user':
            flash('Invalid user type for user dashboard!', 'error')
            return redirect(url_for('login'))

        try:
            user_type, user_id = current_user.id.split(':')
            user = User.query.get(int(user_id))
            user_id = int(user_id)
            if user_type != 'user':
                flash('Invalid user type for user dashboard!', 'error')
                return redirect(url_for('login'))
        except (ValueError, TypeError) as e:
            print(f"Error parsing user ID from {current_user.id}: {str(e)}")
            flash('Error loading user data!', 'error')
            return redirect(url_for('login'))

        # Handle form submission (POST)
        if request.method == 'POST':
            date_str = request.form.get('date')
            consumption = request.form.get('consumption')

            try:
                # Convert date string to datetime object
                date = datetime.strptime(date_str, '%Y-%m-%d')
                consumption = float(consumption)  # Ensure consumption is a number
                if consumption < 0:
                    raise ValueError("Consumption cannot be negative")

                # Add new entry to database
                new_entry = EnergyData(user_id=user_id, date=date, consumption=consumption)
                db.session.add(new_entry)
                db.session.commit()
                flash('New energy data added successfully!', 'success')
            except ValueError as e:
                flash(f'Invalid input: {str(e)}', 'error')
            except Exception as e:
                flash(f'Error adding data: {str(e)}', 'error')

            return redirect(url_for('user_dashboard'))

        # Display dashboard (GET)
        energy_data = EnergyData.query.filter_by(user_id=user_id).all()

        if not energy_data:
            flash('No energy data available. Please add data below.', 'warning')
            return render_template('user_dashboard.html', 
                                data=energy_data, 
                                latest_consumption=0, 
                                bill_dict=None, 
                                user=user)
        latest_entry = energy_data[-1]
        latest_consumption = latest_entry.consumption
        bill_dict = calculate_kseb_bill(latest_consumption, billing_cycle=1, phase='single')

        return render_template('user_dashboard.html', 
                            data=energy_data, 
                            latest_consumption=latest_consumption, 
                            bill_dict=bill_dict, 
                            user=user)

    @app.route('/user/upload', methods=['POST'])
    @login_required
    def upload_data():
        """Handle CSV file upload for user energy data."""
        if current_user.role != 'user':
            return redirect(url_for('login'))

        # Extract the actual user ID
        try:
            user_type, user_id = current_user.id.split(':')
            user_id = int(user_id)
            if user_type != 'user':
                flash('Invalid user type!')
                return redirect(url_for('login'))
        except (ValueError, TypeError) as e:
            print(f"Error parsing user ID from {current_user.id}: {str(e)}")
            flash('Error loading user data!')
            return redirect(url_for('login'))

        file = request.files['file']
        if not file or not file.filename.endswith('.csv'):
            flash('Please upload a valid CSV file!')
            return redirect(url_for('user_dashboard'))

        try:
            df = pd.read_csv(file)
            required_columns = ['date', 'consumption']
            if not all(col in df.columns for col in required_columns):
                flash('CSV must contain "date" and "consumption" columns!')
                return redirect(url_for('user_dashboard'))

            for _, row in df.iterrows():
                try:
                    date = datetime.strptime(row['date'], '%d-%m-%Y')
                    consumption = float(row['consumption'])
                    if consumption < 0:
                        flash('Consumption cannot be negative!')
                        return redirect(url_for('user_dashboard'))
                    energy = EnergyData(
                        user_id=user_id,
                        date=date,
                        consumption=consumption
                    )
                    db.session.add(energy)
                except (ValueError, TypeError) as e:
                    flash(f'Error processing row: {row.to_dict()}. Error: {str(e)}')
                    return redirect(url_for('user_dashboard'))
            db.session.commit()
            flash('Data uploaded successfully!')
        except Exception as e:
            flash(f'Error processing CSV file: {str(e)}')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user/predictions', methods=['GET', 'POST'])
    @login_required
    def predictions():
        """Display energy usage predictions and handle appliance operations."""
        if current_user.role != 'user':
            flash('Invalid user type for predictions!', 'error')
            return redirect(url_for('login'))

        try:
            user_type, user_id = current_user.id.split(':')
            user_id = int(user_id)
            if user_type != 'user':
                flash('Invalid user type for predictions!', 'error')
                return redirect(url_for('login'))
        except (ValueError, TypeError) as e:
            print(f"Error parsing user ID from {current_user.id}: {str(e)}")
            flash('Error loading user data!', 'error')
            return redirect(url_for('login'))

        # Initialize appliances list
        if 'appliances' not in session or not isinstance(session['appliances'], list):
            session['appliances'] = []
        else:
            for appliance in session['appliances']:
                appliance.setdefault('quantity', 1)
            session.modified = True

        # Base prediction
        energy_data = EnergyData.query.filter_by(user_id=user_id).all()
        final_date = datetime.now() + timedelta(days=60)
        base_predicted_usage = 0
        base_estimated_bill = 0

        if energy_data:
            latest_consumption = energy_data[-1].consumption
            base_predicted_usage = latest_consumption * 2
            bill_data = calculate_kseb_bill(base_predicted_usage, billing_cycle=2, phase='single')
            base_estimated_bill = bill_data['total']

        # Appliance bill calculation
        appliance_usage = 0
        appliance_estimated_bill = 0

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add_appliance':
                appliance_type = request.form.get('appliance_type')
                hours = request.form.get('hours', type=float)
                quantity = request.form.get('quantity', type=int)

                if hours <= 0 or hours > 24:
                    flash('Hours must be between 0 and 24!', 'error')
                elif quantity < 1:
                    flash('Number of appliances must be at least 1!', 'error')
                else:
                    appliance_map = {
                        'fan': {'name': 'Fan (50W)', 'power': 0.05},
                        'bulb': {'name': 'LED Bulb (10W)', 'power': 0.01},
                        'tv': {'name': 'TV (100W)', 'power': 1.0},
                        'fridge': {'name': 'Fridge (150W)', 'power': 1.5},
                        'washing_machine': {'name': 'Washing Machine (200W)', 'power': 2.0},
                        'geyser': {'name': 'Geyser (250W)', 'power': 2.5},
                        'ac': {'name': 'AC (1.5 Ton - 1.5kW)', 'power': 3.0}
                    }

                    if appliance_type in appliance_map:
                        session['appliances'].append({
                            'name': appliance_map[appliance_type]['name'],
                            'power': appliance_map[appliance_type]['power'],
                            'hours': hours,
                            'quantity': quantity
                        })
                        session.modified = True
                        flash('Appliance added successfully!', 'success')
                    else:
                        flash('Invalid appliance selected!', 'error')

            elif action == 'delete_appliance':
                index = int(request.form.get('index'))
                try:
                    session['appliances'].pop(index)
                    session.modified = True
                    flash('Appliance removed successfully!', 'success')
                except IndexError:
                    flash('Invalid appliance index!', 'error')

            elif action == 'reset_appliances':
                session['appliances'] = []
                session.modified = True
                flash('Appliance list cleared.', 'success')
                return redirect(url_for('predictions'))

            elif action == 'calculate_bill':
                for appliance in session['appliances']:
                    qty = appliance.get('quantity', 1)
                    usage = appliance['power'] * appliance['hours'] * qty * 60
                    appliance_usage += usage

                if appliance_usage > 0:
                    bill_data = calculate_kseb_bill(appliance_usage, billing_cycle=2, phase='single')
                    appliance_estimated_bill = bill_data['total']
                    flash('Appliance bill calculated successfully!', 'success')
                else:
                    flash('No appliances to calculate!', 'error')

        return render_template('predictions.html',
                            final_date=final_date,
                            base_predicted_usage=base_predicted_usage,
                            base_estimated_bill=base_estimated_bill,
                            appliance_usage=appliance_usage,
                            appliance_estimated_bill=appliance_estimated_bill,
                            appliances=session['appliances'],
                            user=current_user)

    @app.route('/user/report')
    @login_required
    def generate_report():
        """Generate a PDF report of the user's energy consumption."""
        if current_user.role != 'user':
            return redirect(url_for('login'))

        # Extract actual user ID
        try:
            user_type, user_id = current_user.id.split(':')
            user_id = int(user_id)
            if user_type != 'user':
                flash('Invalid user type!')
                return redirect(url_for('login'))
        except (ValueError, TypeError) as e:
            print(f"Error parsing user ID from {current_user.id}: {str(e)}")
            flash('Error loading user data!')
            return redirect(url_for('login'))

        # Fetch user and data
        user = User.query.get(user_id)
        data = EnergyData.query.filter_by(user_id=user_id).order_by(EnergyData.date).all()

        report_path = f"report_{user_id}.pdf"
        c = canvas.Canvas(report_path, pagesize=letter)
        width, height = letter
        y = height - 50

        # Header section
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Energy Consumption Report")
        y -= 20
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 30

        # User Details
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "User Details:")
        y -= 18
        c.setFont("Helvetica", 11)
        c.drawString(60, y, f"Full Name: {user.full_name}")
        y -= 16
        c.drawString(60, y, f"Username: {user.username}")
        y -= 16
        c.drawString(60, y, f"Phone: {user.phone_number}")
        y -= 16
        c.drawString(60, y, f"Address: {user.address}")
        y -= 30

        # Table Header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Date")
        c.drawString(200, y, "Consumption (kWh)")
        y -= 15
        c.line(50, y, 400, y)
        y -= 10

        # Data Entries
        c.setFont("Helvetica", 11)
        total_consumption = 0
        for entry in data:
            if y < 80:  # Create new page if near bottom
                c.showPage()
                y = height - 50
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Date")
                c.drawString(200, y, "Consumption (kWh)")
                y -= 15
                c.line(50, y, 400, y)
                y -= 10
                c.setFont("Helvetica", 11)
            
            c.drawString(50, y, entry.date.strftime('%Y-%m-%d'))
            c.drawString(200, y, f"{entry.consumption:.2f}")
            total_consumption += entry.consumption
            y -= 16

        # Summary
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Total Consumption: {total_consumption:.2f} kWh")

        c.save()
        return send_file(report_path, as_attachment=True)

    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        """Display the admin dashboard with officer and user data."""
        if current_user.role != 'admin':
            return redirect(url_for('login'))

        print(f"Admin dashboard accessed by: {current_user.id}")  # Debug
        
        officers = Officer.query.all()
        users = User.query.all() 
        total_consumption = db.session.query(db.func.sum(EnergyData.consumption)).scalar() or 0

        # City-wise usage for plots
        cities = set(officer.city for officer in officers)
        city_usage = {}
        for city in cities:
            city_users = User.query.join(Officer).filter(Officer.city == city).all()
            city_user_ids = [user.id for user in city_users]
            city_consumption = db.session.query(db.func.sum(EnergyData.consumption)).filter(EnergyData.user_id.in_(city_user_ids)).scalar() or 0
            city_usage[city] = city_consumption

        # Officer-wise user usage with bill calculation
        officer_usage = {}
        for officer in officers:
            officer_users = User.query.filter_by(officer_id=officer.id).all()
            user_usage = {}
            for user in officer_users:
                user_consumption = db.session.query(db.func.sum(EnergyData.consumption)).filter_by(user_id=user.id).scalar() or 0
                bill = calculate_kseb_bill(user_consumption, billing_cycle=1, phase='single')
                user_usage[user.username] = {
                    'consumption': user_consumption,
                    'cost': bill['total']
                }
            officer_usage[officer.username] = user_usage

        # Prepare data for Chart.js (city-wise usage)
        city_labels = list(city_usage.keys())
        city_data = list(city_usage.values())

        return render_template(
            'admin_dashboard.html',
            officers=officers,
            users=users,
            total=total_consumption,
            officer_usage=officer_usage,
            city_labels=json.dumps(city_labels),
            city_data=json.dumps(city_data)
        )

    @app.route('/admin/add_officer', methods=['GET', 'POST'])
    @login_required
    def add_officer():
        """Add a new officer (admin only)."""
        if current_user.role != 'admin':
            return redirect(url_for('login'))

        if request.method == 'POST':
            username = request.form['username']
            password = hash_password(request.form['password'])
            full_name = request.form['full_name']
            city = request.form['city']

            if Officer.query.filter_by(username=username).first():
                flash('Officer username already exists!')
                return redirect(url_for('add_officer'))

            new_officer = Officer(
                username=username,
                password=password,
                full_name=full_name,
                city=city
            )
            db.session.add(new_officer)
            db.session.commit()
            flash('Officer added successfully!')
            return redirect(url_for('admin_dashboard'))
        return render_template('add_officer.html')

    @app.route('/admin/edit_officer/<int:officer_id>', methods=['GET', 'POST'])
    @login_required
    def edit_officer(officer_id):
        """Edit an existing officer (admin only)."""
        if current_user.role != 'admin':
            return redirect(url_for('login'))

        officer = Officer.query.get_or_404(officer_id)
        if request.method == 'POST':
            new_username = request.form['username']
            if Officer.query.filter_by(username=new_username).first() and new_username != officer.username:
                flash('Officer username already exists!')
                return redirect(url_for('edit_officer', officer_id=officer_id))

            officer.username = new_username
            officer.full_name = request.form['full_name']
            officer.city = request.form['city']
            if request.form['password']:
                officer.password = hash_password(request.form['password'])

            db.session.commit()
            flash('Officer updated successfully!')
            return redirect(url_for('admin_dashboard'))
        return render_template('edit_officer.html', officer=officer)

    @app.route('/admin/delete_officer/<int:officer_id>', methods=['POST'])
    @login_required
    def delete_officer(officer_id):
        """Delete an officer and reassign their users (admin only)."""
        if current_user.role != 'admin':
            return redirect(url_for('login'))

        officer = Officer.query.get_or_404(officer_id)
        officer = Officer.query.get(officer_id)
        # Reassign users to another officer or set to None
        users = User.query.filter_by(officer_id=officer_id).all()
        for user in users:
            user.officer_id = None  # Could reassign to another officer if needed
        db.session.delete(officer)
        db.session.commit()
        flash('Officer deleted!')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/add_user', methods=['GET', 'POST'])
    @login_required
    def add_user():
        """Add a new user (admin only)."""
        if current_user.role != 'admin':
            return redirect(url_for('login'))

        if request.method == 'POST':
            username = request.form['username']
            password = hash_password(request.form['password'])
            full_name = request.form['full_name']
            address = request.form['address']
            city = request.form['city']
            phone_number = request.form['phone_number']

            if not phone_number.isdigit() or len(phone_number) < 10:
                flash('Phone number must be at least 10 digits!')
                return redirect(url_for('add_user'))

            if User.query.filter_by(username=username).first():
                flash('Username already exists!')
                return redirect(url_for('add_user'))

            officer = Officer.query.filter_by(city=city).first()
            new_user = User(
                username=username,
                password=password,
                role='user',
                full_name=full_name,
                address=address,
                city=city,
                phone_number=phone_number,
                officer_id=officer.id if officer else None
            )
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!')
            return redirect(url_for('admin_dashboard'))
        officers = Officer.query.all()
        return render_template('add_user.html', officers=officers)

    @app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
    @login_required
    def delete_user(user_id):
        """Delete a user and their energy data (admin only)."""
        if current_user.role != 'admin':
            return redirect(url_for('login'))

        user = User.query.get_or_404(user_id)
        # Delete associated energy data
        EnergyData.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        flash('User deleted!')
        return redirect(url_for('admin_dashboard'))

    @app.route('/kseb/dashboard')
    @login_required
    def kseb_dashboard():
        """Display the officer dashboard with user data, usage history, and anomalies."""
        if current_user.role != 'kseb' or not current_user.is_officer:
            return redirect(url_for('login'))

        # Extract officer ID from "officer:3"
        try:
            user_type, officer_id = current_user.id.split(':')
            officer_id = int(officer_id)
            if user_type != 'officer':
                flash('Invalid user type for officer dashboard!')
                return redirect(url_for('login'))
        except (ValueError, TypeError) as e:
            print(f"Error parsing officer ID from {current_user.id}: {str(e)}")
            flash('Error loading officer data!')
            return redirect(url_for('login'))

        # Get officer record
        officer = Officer.query.get(officer_id)
        if not officer:
            flash('Officer not found!')
            return redirect(url_for('login'))

        # Get all users under this officer
        users = User.query.filter_by(officer_id=officer.id).all()
        user_ids = [user.id for user in users]

        # Total consumption for all users
        total_consumption = db.session.query(db.func.sum(EnergyData.consumption)).filter(EnergyData.user_id.in_(user_ids)).scalar() or 0

        # Anomaly detection
        anomalies = detect_anomalies(officer.id)

        # User-specific data
        user_usage = {}
        for user in users:
            user_consumption = db.session.query(db.func.sum(EnergyData.consumption)).filter_by(user_id=user.id).scalar() or 0
            bill = calculate_kseb_bill(user_consumption, billing_cycle=1, phase='single')
            
            # Get history
            history = EnergyData.query.filter_by(user_id=user.id).order_by(EnergyData.date).all()

            user_usage[user.username] = {
                'id': user.id,
                'full_name': user.full_name,
                'consumption': user_consumption,
                'cost': bill['total'],
                'history': history
            }

        # Data for Chart.js
        user_labels = list(user_usage.keys())
        user_consumption_data = [user_usage[u]['consumption'] for u in user_labels]
        user_cost_data = [user_usage[u]['cost'] for u in user_labels]

        return render_template(
            'kseb_dashboard.html',
            total=total_consumption,
            officer = officer,
            users=users,
            user_usage=user_usage,
            user_labels=json.dumps(user_labels),
            user_consumption_data=json.dumps(user_consumption_data),
            user_cost_data=json.dumps(user_cost_data),
            anomalies=anomalies
        )
    
    @app.route('/kseb/add_user', methods=['GET', 'POST'])
    @login_required
    def kseb_add_user():
        if current_user.role != 'kseb':
            return redirect(url_for('login'))

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            full_name = request.form['full_name']
            address = request.form['address']
            city = request.form['city']
            phone_number = request.form['phone_number']
            
            user_type, officer_id = current_user.id.split(':')
            new_user = User(
                username=username,
                password_hash=hash_password(password),
                full_name=full_name,
                address=address,
                city=city,
                phone_number=phone_number,
                officer_id=int(officer_id)
            )
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('kseb_dashboard'))

        return render_template('add_user.html')

    @app.route('/kseb/add_consumption', methods=['POST'])
    @login_required
    def add_consumption():
        if current_user.role != 'kseb':
            return redirect(url_for('login'))

        user_id = request.form['user_id']
        date = request.form['date']
        consumption = request.form['consumption']

        new_entry = EnergyData(
            user_id=user_id,
            date=datetime.strptime(date, '%Y-%m-%d'),
            consumption=float(consumption)
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Consumption entry added!', 'success')
        return redirect(url_for('kseb_dashboard'))

    @app.route('/kseb/delete_consumption/<int:entry_id>', methods=['POST'])
    @login_required
    def delete_consumption(entry_id):
        if current_user.role != 'kseb':
            return redirect(url_for('login'))

        entry = EnergyData.query.get(entry_id)
        if entry:
            db.session.delete(entry)
            db.session.commit()
            flash('Entry deleted!', 'success')
        else:
            flash('Entry not found.', 'error')

        return redirect(url_for('kseb_dashboard'))


def detect_anomalies(officer_id):
    """Detect anomalies in energy consumption for users under the given officer."""
    users = User.query.filter_by(officer_id=officer_id).all()
    user_ids = [user.id for user in users]

    data = EnergyData.query.filter(EnergyData.user_id.in_(user_ids)).all()
    if not data:
        return []

    df = pd.DataFrame([(d.consumption) for d in data], columns=['consumption'])
    if len(df) < 2:
        return []

    try:
        model = IsolationForest(contamination=0.1)
        anomalies = model.fit_predict(df)
        anomalous_entries = [d for d, a in zip(data, anomalies) if a == -1]
        result = []
        for entry in anomalous_entries:
            user = User.query.get(entry.user_id)
            result.append({
                'user_id': user.id,
                'username': user.username,
                'date': entry.date,
                'consumption': entry.consumption
            })
        return result
    except Exception as e:
        print(f"Error in anomaly detection: {str(e)}")
        return []