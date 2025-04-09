# ⚡ Energy Management System

A full-stack web application for monitoring, predicting, and managing electricity consumption. It features dashboards for Users, Admins, and KSEB Officers with intelligent features like anomaly detection, billing, and energy usage prediction using LSTM and Prophet.

## 🔧 Features

### 👤 User Dashboard
- View and track monthly energy usage
- Upload manual data or CSV
- Predict future energy consumption
- Generate energy reports (PDF)
- Calculate 2-month electricity bills using KSEB slab system

### 🛠️ Admin Dashboard
- Manage users and KSEB officers
- Monitor energy trends and anomalies
- Review prediction accuracy
- Generate system reports

### ⚙️ KSEB Officer Dashboard
- Monitor region-wise consumption
- Detect anomalies/fraud
- Handle billing and user queries
- Generate regulatory compliance reports

---

## 🚀 Deployment Instructions

### 🔗 Prerequisites
- Python 3.10+
- Git
- Virtualenv

### 🔌 Installation

```bash
# Clone the repository
git clone https://github.com/sreeharivponline/energy-management-system.git
cd energy-management-system 


# Set up virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt


# Start the Flask server
python app.py
