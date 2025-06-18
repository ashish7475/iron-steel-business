from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LaborRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate_per_kg = db.Column(db.Float, nullable=False, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    notes = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    total_weight = db.Column(db.Float, default=0.0)
    total_labor_cost = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('ReceiptItem', backref='receipt', lazy=True, cascade='all, delete-orphan')

class ReceiptItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    dimension = db.Column(db.String(50))  # e.g., "8x8 feet", "10 units", "2.5 meters"
    labor_cost = db.Column(db.Float, nullable=False)

def init_db(app):
    """Initialize database and create default data"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Create default user if not exists
        if not User.query.first():
            default_password = 'admin123'
            password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
            default_user = User(username='admin', password_hash=password_hash.decode('utf-8'))
            db.session.add(default_user)
            
            # Create default labor rate
            default_rate = LaborRate(rate_per_kg=10.0)  # ₹10 per kg
            db.session.add(default_rate)
            
            db.session.commit()
            print(f"Default user created: admin / {default_password}") 