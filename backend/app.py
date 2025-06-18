from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from datetime import timedelta
from dotenv import load_dotenv
from models import init_db
from controllers import AuthController, LaborRateController, ReceiptController, SummaryController

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iron_steel_business.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
init_db(app)
jwt = JWTManager(app)
CORS(app)  # Enable CORS for all routes

# API Routes
@app.route('/api/login', methods=['POST'])
def login():
    return AuthController.login()

@app.route('/api/update-password', methods=['POST'])
def update_password():
    return AuthController.update_password()

@app.route('/api/labor-rate', methods=['GET'])
def get_labor_rate():
    return LaborRateController.get_labor_rate()

@app.route('/api/labor-rate', methods=['PUT'])
def update_labor_rate():
    return LaborRateController.update_labor_rate()

@app.route('/api/receipts', methods=['GET'])
def get_receipts():
    return ReceiptController.get_receipts()

@app.route('/api/receipts', methods=['POST'])
def create_receipt():
    return ReceiptController.create_receipt()

@app.route('/api/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    return ReceiptController.delete_receipt(receipt_id)

@app.route('/api/summary', methods=['GET'])
def get_summary():
    return SummaryController.get_summary()

@app.route('/api/monthly-summary', methods=['GET'])
def get_monthly_summary():
    return SummaryController.get_monthly_summary()

@app.route('/api/export', methods=['GET'])
def export_data():
    return SummaryController.export_data()

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok', 'message': 'Iron & Steel Business API is running'}

if __name__ == '__main__':
    # Only show startup message in development
    if os.getenv('FLASK_ENV') == 'development':
        print("🚀 Starting Iron & Steel Business API Server...")
        print("📍 API will be available at: http://localhost:5000")
        print("🔑 Default login: admin / admin123")
        print("⏹️  Press Ctrl+C to stop the server\n")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # Production mode - no debug output
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 