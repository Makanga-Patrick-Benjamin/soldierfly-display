from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///larvae_monitoring.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LarvaeData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tray_number = db.Column(db.Integer, nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LarvaeData Tray {self.tray_number} - {self.timestamp}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper Functions
def get_latest_tray_data(tray_number):
    # This helper function assumes it's still needed for individual tray data retrieval.
    # It fetches the most recent entry for a given tray.
    return LarvaeData.query.filter_by(tray_number=tray_number).order_by(LarvaeData.timestamp.desc()).first()

def calculate_weight_distribution_backend(weights_array):
    weight_bins = {
        "80-90": 0, "90-100": 0, "100-110": 0,
        "110-120": 0, "120-130": 0, "130-140": 0, "140+": 0
    }
    for weight in weights_array:
        if 80 <= weight < 90: weight_bins["80-90"] += 1
        elif 90 <= weight < 100: weight_bins["90-100"] += 1
        elif 100 <= weight < 110: weight_bins["100-110"] += 1
        elif 110 <= weight < 120: weight_bins["110-120"] += 1
        elif 120 <= weight < 130: weight_bins["120-130"] += 1
        elif 130 <= weight < 140: weight_bins["130-140"] += 1
        else: weight_bins["140+"] += 1
    return list(weight_bins.keys()), list(weight_bins.values())


# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
            
        try:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')

# Updated get_tray_data route to fetch data for the last 30 days
# Add these routes to your existing Flask app

@app.route('/get_tray_data/<int:tray_number>')
@login_required
def get_tray_data(tray_number):
    try:
        # Get all historical data for the specified tray
        tray_data = LarvaeData.query.filter_by(tray_number=tray_number)\
                                  .order_by(LarvaeData.timestamp.asc())\
                                  .all()

        if not tray_data:
            return jsonify({"error": f"No data found for tray {tray_number}"}), 404

        # Process growth data
        growth_data = {"days": [], "length": [], "weight": []}
        daily_data = {}
        
        if tray_data:
            start_date = tray_data[0].timestamp.date()
            for entry in tray_data:
                day_number = (entry.timestamp.date() - start_date).days + 1
                daily_data[day_number] = entry  # Keep latest entry per day

            for day in sorted(daily_data.keys()):
                entry = daily_data[day]
                growth_data["days"].append(day)
                growth_data["length"].append(entry.length)
                growth_data["weight"].append(entry.weight)

        # Get latest metrics
        latest_entry = tray_data[-1] if tray_data else None

        # Calculate weight distribution
        weight_bins = {
            "80-90": 0, "90-100": 0, "100-110": 0,
            "110-120": 0, "120-130": 0, "130-140": 0, "140+": 0
        }
        
        for entry in tray_data:
            weight = entry.weight
            if 80 <= weight < 90: weight_bins["80-90"] += 1
            elif 90 <= weight < 100: weight_bins["90-100"] += 1
            elif 100 <= weight < 110: weight_bins["100-110"] += 1
            elif 110 <= weight < 120: weight_bins["110-120"] += 1
            elif 120 <= weight < 130: weight_bins["120-130"] += 1
            elif 130 <= weight < 140: weight_bins["130-140"] += 1
            else: weight_bins["140+"] += 1

        return jsonify({
            "metrics": {
                "length": latest_entry.length if latest_entry else 0,
                "width": latest_entry.width if latest_entry else 0,
                "area": latest_entry.area if latest_entry else 0,
                "weight": latest_entry.weight if latest_entry else 0,
                "count": latest_entry.count if latest_entry else 0
            },
            "growthData": growth_data,
            "weightDistribution": {
                "ranges": list(weight_bins.keys()),
                "counts": list(weight_bins.values())
            },
            "timestamp": latest_entry.timestamp.isoformat() if latest_entry else datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_combined_tray_data')
@login_required
def get_combined_tray_data():
    try:
        # Get all unique tray numbers
        tray_numbers = [result[0] for result in db.session.query(LarvaeData.tray_number).distinct().all()]

        if not tray_numbers:
            return jsonify({"error": "No tray data available"}), 404

        # Get data from all trays
        all_data = []
        latest_entries = []
        
        for tray_num in tray_numbers:
            tray_data = LarvaeData.query.filter_by(tray_number=tray_num).all()
            all_data.extend(tray_data)
            latest_entry = LarvaeData.query.filter_by(tray_number=tray_num)\
                                         .order_by(LarvaeData.timestamp.desc())\
                                         .first()
            if latest_entry:
                latest_entries.append(latest_entry)

        if not all_data:
            return jsonify({"error": "No data available"}), 404

        # Calculate combined metrics
        combined_metrics = {
            "length": round(sum(e.length for e in latest_entries)/len(latest_entries), 1) if latest_entries else 0,
            "width": round(sum(e.width for e in latest_entries)/len(latest_entries), 1) if latest_entries else 0,
            "area": round(sum(e.area for e in latest_entries)/len(latest_entries), 1) if latest_entries else 0,
            "weight": round(sum(e.weight for e in latest_entries)/len(latest_entries), 1) if latest_entries else 0,
            "count": sum(e.count for e in latest_entries) if latest_entries else 0
        }

        # Calculate combined growth data
        growth_data = {"days": [], "length": [], "weight": []}
        day_data = defaultdict(list)
        
        for entry in all_data:
            day = (entry.timestamp.date() - all_data[0].timestamp.date()).days + 1
            day_data[day].append(entry)
        
        for day, entries in sorted(day_data.items()):
            growth_data["days"].append(day)
            growth_data["length"].append(round(sum(e.length for e in entries)/len(entries), 1))
            growth_data["weight"].append(round(sum(e.weight for e in entries)/len(entries), 1))

        # Combined weight distribution
        weight_bins = {
            "80-90": 0, "90-100": 0, "100-110": 0,
            "110-120": 0, "120-130": 0, "130-140": 0, "140+": 0
        }
        
        for entry in all_data:
            weight = entry.weight
            if 80 <= weight < 90: weight_bins["80-90"] += 1
            elif 90 <= weight < 100: weight_bins["90-100"] += 1
            elif 100 <= weight < 110: weight_bins["100-110"] += 1
            elif 110 <= weight < 120: weight_bins["110-120"] += 1
            elif 120 <= weight < 130: weight_bins["120-130"] += 1
            elif 130 <= weight < 140: weight_bins["130-140"] += 1
            else: weight_bins["140+"] += 1

        return jsonify({
            "metrics": combined_metrics,
            "growthData": growth_data,
            "weightDistribution": {
                "ranges": list(weight_bins.keys()),
                "counts": list(weight_bins.values())
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_comparison_data')
@login_required
def get_comparison_data():
    try:
        trays_data_for_comparison = {}
        
        # Dynamically get all unique tray numbers from the database
        unique_trays = LarvaeData.query.with_entities(LarvaeData.tray_number).distinct().all()
        
        # Iterate through each unique tray number found
        for (tray_num,) in unique_trays: 
            # Fetch all historical data for the current tray, ordered by timestamp
            all_tray_data = LarvaeData.query.filter_by(tray_number=tray_num)\
                                          .order_by(LarvaeData.timestamp.asc())\
                                          .all()

            if not all_tray_data:
                # If a tray has no data, include empty data for it so the frontend can handle it
                trays_data_for_comparison[str(tray_num)] = {
                    'latest': {'length': 0.0, 'width': 0.0, 'area': 0.0, 'weight': 0.0, 'count': 0},
                    'growthData': {'days': [], 'length': [], 'weight': []},
                    'allWeights': [] # Empty list for weight distribution if no data
                }
                continue # Move to the next tray

            # --- Process Growth Data for this Tray: Get latest measurement per day ---
            growth_data_for_tray = {
                "days": [],
                "length": [],
                "weight": []
            }
            daily_latest_data = {} # Key: day_number, Value: LarvaeData entry (the latest for that day)

            start_date = all_tray_data[0].timestamp.date() # Start date for this specific tray

            for entry in all_tray_data:
                day_number = (entry.timestamp.date() - start_date).days + 1
                # Overwrite with the current entry; since data is sorted ascending,
                # the last entry for a specific day will be the latest.
                daily_latest_data[day_number] = entry

            # Populate growth_data lists from the processed daily data
            for day in sorted(daily_latest_data.keys()):
                entry = daily_latest_data[day]
                growth_data_for_tray["days"].append(round(day, 1))
                growth_data_for_tray["length"].append(round(entry.length, 1))
                growth_data_for_tray["weight"].append(round(entry.weight, 1))

            # --- Process All Individual Weights for this Tray's Distribution ---
            all_individual_weights = [entry.weight for entry in all_tray_data]

            # --- Get Latest Metrics for this Tray ---
            latest_entry = all_tray_data[-1]

            trays_data_for_comparison[str(tray_num)] = {
                'latest': {
                    'length': round(latest_entry.length, 1),
                    'width': round(latest_entry.width, 1),
                    'area': round(latest_entry.area, 1),
                    'weight': round(latest_entry.weight, 1),
                    'count': latest_entry.count
                },
                'growthData': growth_data_for_tray,
                'allWeights': all_individual_weights # This is the key for comparison weight distribution
            }

        return jsonify({
            'trays': trays_data_for_comparison,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        # Log the error for debugging purposes
        app.logger.error(f"Error in get_comparison_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    # Dynamically get all unique tray numbers from the database
    unique_tray_numbers_raw = LarvaeData.query.with_entities(LarvaeData.tray_number).distinct().all()
    
    # Convert list of tuples to a sorted list of integers
    unique_tray_numbers = sorted([tray_num for (tray_num,) in unique_tray_numbers_raw])

    # Create a dictionary to hold the tray numbers to be passed to the template.
    # The actual data for each tray will be fetched by JavaScript via AJAX.
    tray_data_for_template = {}
    for tray_num in unique_tray_numbers:
        tray_data_for_template[tray_num] = {} # Empty dict, frontend only needs the keys

    return render_template('dashboard.html', tray_data=tray_data_for_template)


@app.route('/api/data', methods=['POST'])
@login_required
def receive_data():
    try:
        data = request.json
        new_entry = LarvaeData(
            tray_number=data['tray_number'],
            length=data['length'],
            width=data['width'],
            area=data['area'],
            weight=data['weight'],
            count=data['count']
        )
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"status": "success", "message": "Data stored"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))


# Database initialization
with app.app_context():
    db.create_all()
    # Create test user if none exists
    if not User.query.filter_by(username='testuser').first():
        admin_user = User(username='testuser')
        admin_user.set_password('password')
        db.session.add(admin_user)
        db.session.commit()
        print("Test user 'testuser' with password 'password' created.")

    # Optional: Add some dummy data for new trays (e.g., 156, 256, 356) if the database is empty
    if not LarvaeData.query.first():
        print("Adding dummy data for demonstration.")
        from random import uniform, randint
        
        # Add data for tray 1
        for i in range(1, 10):
            timestamp = datetime.utcnow() - timedelta(days=9 - i)
            db.session.add(LarvaeData(
                tray_number=1,
                length=round(uniform(10, 20), 1),
                width=round(uniform(2, 4), 1),
                area=round(uniform(20, 80), 1),
                weight=round(uniform(90, 150), 1),
                count=randint(100, 500),
                timestamp=timestamp
            ))
        
        # Add data for tray 2
        for i in range(1, 8):
            timestamp = datetime.utcnow() - timedelta(days=7 - i)
            db.session.add(LarvaeData(
                tray_number=2,
                length=round(uniform(12, 22), 1),
                width=round(uniform(2.5, 4.5), 1),
                area=round(uniform(25, 90), 1),
                weight=round(uniform(95, 160), 1),
                count=randint(80, 400),
                timestamp=timestamp
            ))

        # Add data for tray 3
        for i in range(1, 12):
            timestamp = datetime.utcnow() - timedelta(days=11 - i)
            db.session.add(LarvaeData(
                tray_number=3,
                length=round(uniform(9, 18), 1),
                width=round(uniform(1.8, 3.8), 1),
                area=round(uniform(18, 70), 1),
                weight=round(uniform(85, 145), 1),
                count=randint(120, 600),
                timestamp=timestamp
            ))
            
        # Add dummy data for new trays (e.g., 156, 256, 356) to ensure they appear
        for tray in [156, 256, 356]:
            for i in range(1, 7):
                timestamp = datetime.utcnow() - timedelta(days=6 - i)
                db.session.add(LarvaeData(
                    tray_number=tray,
                    length=round(uniform(15, 25), 1),
                    width=round(uniform(3, 5), 1),
                    area=round(uniform(30, 100), 1),
                    weight=round(uniform(100, 180), 1),
                    count=randint(150, 700),
                    timestamp=timestamp
                ))
        db.session.commit()
        print("Dummy data added for demonstration including new trays.")


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=8000, debug=True)