# Soldier Fly Larvae Monitoring System

A web-based dashboard for real-time monitoring of soldier fly larvae growth metrics across multiple trays, built with Flask and SQLite.

![Dashboard Preview](https://via.placeholder.com/800x400.png?text=Dashboard+Preview) *Example dashboard layout*

## Features

- **Multi-Tray Monitoring**: Track 3 trays simultaneously
- **Real-Time Metrics**:
  - Average length, width, area, and weight
  - Total larvae count
- **Data Visualization**:
  - Growth trend charts (10-day history)
  - Weight distribution histograms
- **User Authentication**:
  - Secure login/registration
  - Session management
- **API Integration**:
  - RESTful endpoints for data ingestion
  - JSON data format support

## Technologies

- **Backend**: Python/Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, Chart.js
- **Database**: SQLite
- **Authentication**: Flask-Login, Werkzeug Security

## Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/Makanga-Patrick-Benjamin/soldierfly-display.git
   cd soldierfly-monitoring
   pip install -r requirements.txt

2. **On linux to run the website**:
```bash
    python3 -m venv venv
    source venv/bin/activate
    python3 app.py
```
## 3. **Default credentials:**:
    user name: admin
    password: admin123

