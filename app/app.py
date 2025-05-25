from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime,  timedelta
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
    length = db.Column(db.Float)
    width = db.Column(db.Float)
    area = db.Column(db.Float)
    weight = db.Column(db.Float)
    count = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_latest_tray_data(tray_number):
    return LarvaeData.query.filter_by(tray_number=tray_number)\
                          .order_by(LarvaeData.timestamp.desc())\
                          .first()

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

# Update the get_tray_data route
@app.route('/get_tray_data/<int:tray_number>')
@login_required
def get_tray_data(tray_number):
    try:
        # Get all historical data for growth trends
        all_data = LarvaeData.query.filter_by(tray_number=tray_number)\
                                  .order_by(LarvaeData.timestamp.asc())\
                                  .all()

        if not all_data:
            return jsonify({"error": "No data found"}), 404

        # Calculate daily growth data
        growth_data = {
            "days": [],
            "length": [],
            "weight": []
        }

        # Using a dictionary to keep track of the latest entry per day
        daily_latest_data = {} # Key: day_number, Value: LarvaeData entry
        
        if all_data:
            # Find the earliest timestamp as day 0
            start_date = all_data[0].timestamp.date()
            
            for entry in all_data:
                # Calculate days since first measurement
                day_number = (entry.timestamp.date() - start_date).days + 1
                
                # Only keep the latest measurement per day
                if day_number > len(growth_data["days"]):
                    growth_data["days"].append(day_number)
                    growth_data["length"].append(entry.length)
                    growth_data["weight"].append(entry.weight)
                else:
                    # Update existing day with latest data
                    growth_data["length"][-1] = entry.length
                    growth_data["weight"][-1] = entry.weight
                    
        # Get latest metrics
        latest = all_data[-1] if all_data else None

        # Generate weight distribution
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
            "metrics": {
                "length": latest.length,
                "width": latest.width,
                "area": latest.area,
                "weight": latest.weight,
                "count": latest.count
            },
            "growthData": {
                "days": growth_data["days"],
                "length": growth_data["length"],
                "weight": growth_data["weight"]
            },
            "weightDistribution": {
                "ranges": list(weight_bins.keys()),
                "counts": list(weight_bins.values())
            },
            "timestamp": latest.timestamp.isoformat() if latest else datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_combined_tray_data')
@login_required
def get_combined_tray_data():
    try:
        # Get data from all trays
        tray1_data = LarvaeData.query.filter_by(tray_number=1).all()
        tray2_data = LarvaeData.query.filter_by(tray_number=2).all()
        tray3_data = LarvaeData.query.filter_by(tray_number=3).all()
        
        # Combine all data
        all_data = tray1_data + tray2_data + tray3_data
        
        if not all_data:
            return jsonify({"error": "No data found"}), 404

        # Calculate combined metrics (averages)
        latest_entries = [
            get_latest_tray_data(1),
            get_latest_tray_data(2),
            get_latest_tray_data(3)
        ]
        
        combined_metrics = {
            "length": round(sum(e.length for e in latest_entries)/3, 1),
            "width": round(sum(e.width for e in latest_entries)/3, 1),
            "area": round(sum(e.area for e in latest_entries)/3, 1),
            "weight": round(sum(e.weight for e in latest_entries)/3, 1),
            "count": sum(e.count for e in latest_entries)
        }

        # Calculate combined growth data (by day)
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

# Add this new route
@app.route('/get_comparison_data')
@login_required
def get_comparison_data():
    try:
        trays_data_for_comparison = {}
        # Iterate through each tray number you want to compare
        for tray_num in [1, 2, 3]: # Assuming you have trays 1, 2, and 3
            # Fetch all historical data for the current tray
            all_tray_data = LarvaeData.query.filter_by(tray_number=tray_num)\
                                          .order_by(LarvaeData.timestamp.asc())\
                                          .all()

            if not all_tray_data:
                # If a tray has no data, skip it or include empty data for it
                # For comparison, it's better to include it so frontend can show 'no data' or skip its line
                trays_data_for_comparison[str(tray_num)] = {
                    'latest': {'length': 0.0, 'width': 0.0, 'area': 0.0, 'weight': 0.0, 'count': 0},
                    'growthData': {'days': [], 'length': [], 'weight': []},
                    'allWeights': [] # Empty list for weight distribution if no data
                }
                continue # Move to the next tray

            # --- Process Growth Data for this Tray ---
            growth_data_for_tray = {
                "days": [],
                "length": [],
                "weight": []
            }
            daily_latest_data = {} # Key: day_number, Value: LarvaeData entry

            start_date = all_tray_data[0].timestamp.date()
            for entry in all_tray_data:
                day_number = (entry.timestamp.date() - start_date).days + 1
                daily_latest_data[day_number] = entry # Overwrite with the latest entry for this day

            for day in sorted(daily_latest_data.keys()):
                entry = daily_latest_data[day]
                growth_data_for_tray["days"].append(day)
                growth_data_for_tray["length"].append(entry.length)
                growth_data_for_tray["weight"].append(entry.weight)

            # --- Process All Individual Weights for this Tray's Distribution ---
            all_individual_weights = [entry.weight for entry in all_tray_data]

            # --- Get Latest Metrics for this Tray ---
            latest_entry = all_tray_data[-1]

            trays_data_for_comparison[str(tray_num)] = {
                'latest': {
                    'length': latest_entry.length,
                    'width': latest_entry.width,
                    'area': latest_entry.area,
                    'weight': latest_entry.weight,
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
    tray_data = {
        1: get_latest_tray_data(1),
        2: get_latest_tray_data(2),
        3: get_latest_tray_data(3)
    }
    return render_template('dashboard.html', tray_data=tray_data)

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
    if not User.query.first():
        test_user = User(username='admin')
        test_user.set_password('admin123')
        db.session.add(test_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)