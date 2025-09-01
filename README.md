# Soldier Fly Larvae Monitoring System

A web-based dashboard for real-time monitoring of soldier fly larvae growth metrics across multiple trays, built with Flask and SQLite.

![Dashboard Preview](https://soldierfly-fly-monitor.onrender.com) *Dashboard layout*

## Features

- **Multi-Tray Monitoring**: Track multi trays simultaneously
- **Real-Time Metrics**:
  - Average length, width, area, and weight
  - Total larvae count
- **Data Visualization**:
  - Growth trend charts (30-day history)
  - Weight distribution Density plot
- **User Authentication**:
  - Secure login/registration
  - Session management
- **API Integration**:
  - RESTful endpoints for data ingestion
  - JSON data format support
- **Image display**:
  - Classified images for evidence purposes


## Technologies

- **Backend**: Python/Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, Chart.js
- **Database**: SQLite
- **Authentication**: Flask-Login, Werkzeug Security

## Installation

1. **Clone Repository**:
```bash
    git clone https://github.com/Makanga-Patrick-Benjamin/soldierfly-display.git
    cd soldierfly-display
```

2. **Activate your virtual environment. this can be for venv or conda**:
```bash
    python3 -m venv myenv #for python venv environment
    source myenv/bin/activate
```
```bash
    conda create --name myenv #for conda environment
    conda activate "myenv"
```
3. **Requiremets installation**:
```bash
    pip install -r requirements.txt
    python3 BSFwebdashboard,py
```
4. **Access Application:**
- http://localhost:8000

## 3. **Default credentials:**
- **user name:** admin
- **password:** admin123

