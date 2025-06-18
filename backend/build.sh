#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python -c "
import sqlite3
import os

# Create instance directory if it doesn't exist
os.makedirs('instance', exist_ok=True)

# Initialize database
from app import app
with app.app_context():
    from models import init_db
    init_db(app)
    print('Database initialized successfully!')
" 