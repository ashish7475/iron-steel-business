from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, LaborRate, Receipt, ReceiptItem
from datetime import datetime, timedelta
import bcrypt
import os

class AuthController:
    @staticmethod
    def login():
        """Handle user login"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            access_token = create_access_token(identity=username)
            return jsonify({
                'access_token': access_token,
                'username': username
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    @staticmethod
    @jwt_required()
    def update_password():
        """Allow the logged-in user to update their password"""
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': 'All fields are required'}), 400
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user or not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Current password is incorrect'}), 401

        user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'})

class LaborRateController:
    @staticmethod
    @jwt_required()
    def get_labor_rate():
        """Get current labor rate"""
        rate = LaborRate.query.first()
        return jsonify({'rate_per_kg': rate.rate_per_kg if rate else 0.0})

    @staticmethod
    @jwt_required()
    def update_labor_rate():
        """Update labor rate"""
        data = request.get_json()
        new_rate = data.get('rate_per_kg')
        
        if new_rate is None or new_rate < 0:
            return jsonify({'error': 'Valid rate required'}), 400
        
        rate = LaborRate.query.first()
        if rate:
            rate.rate_per_kg = new_rate
        else:
            rate = LaborRate(rate_per_kg=new_rate)
            db.session.add(rate)
        
        db.session.commit()
        return jsonify({'message': 'Labor rate updated', 'rate_per_kg': new_rate})

class ReceiptController:
    @staticmethod
    @jwt_required()
    def get_receipts():
        """Get receipts with optional date range filter, customer filter, and sorting"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date = request.args.get('date')  # Keep for backward compatibility
        customer = request.args.get('customer')
        sort_by = request.args.get('sort_by', 'date')  # date, labor_cost
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc
        
        # Build query
        query = Receipt.query
        
        # Apply date filtering (priority: date range > single date)
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Receipt.date >= start_dt, Receipt.date <= end_dt)
        elif date:
            query = query.filter_by(date=datetime.strptime(date, '%Y-%m-%d').date())
        
        # Apply customer filter
        if customer:
            query = query.filter(Receipt.customer_name.ilike(f'%{customer}%'))
        
        # Apply sorting
        if sort_by == 'labor_cost':
            if sort_order == 'asc':
                query = query.order_by(Receipt.total_labor_cost.asc())
            else:
                query = query.order_by(Receipt.total_labor_cost.desc())
        else:  # sort by date
            if sort_order == 'asc':
                query = query.order_by(Receipt.date.asc(), Receipt.time.asc())
            else:
                query = query.order_by(Receipt.date.desc(), Receipt.time.desc())
        
        receipts = query.all()
        
        result = []
        for receipt in receipts:
            receipt_data = {
                'id': receipt.id,
                'customer_name': receipt.customer_name,
                'notes': receipt.notes,
                'date': receipt.date.strftime('%Y-%m-%d'),
                'time': receipt.time.strftime('%H:%M:%S'),
                'total_weight': receipt.total_weight,
                'total_labor_cost': receipt.total_labor_cost,
                'created_at': receipt.created_at.isoformat(),
                'items': []
            }
            
            for item in receipt.items:
                receipt_data['items'].append({
                    'id': item.id,
                    'item_name': item.item_name,
                    'weight_kg': item.weight_kg,
                    'dimension': item.dimension or '',
                    'labor_cost': item.labor_cost
                })
            
            result.append(receipt_data)
        
        return jsonify(result)

    @staticmethod
    @jwt_required()
    def create_receipt():
        """Create new receipt with items - always uses current date"""
        data = request.get_json()
        
        # Validate required fields
        if not data.get('items') or len(data['items']) == 0:
            return jsonify({'error': 'At least one item required'}), 400
        
        # Get current labor rate
        labor_rate = LaborRate.query.first()
        if not labor_rate:
            return jsonify({'error': 'Labor rate not configured'}), 400
        
        # Calculate totals
        total_weight = 0
        total_labor_cost = 0
        
        # Validate items
        for item in data['items']:
            if not item.get('item_name') or not item.get('weight_kg'):
                return jsonify({'error': 'Item name and weight required for all items'}), 400
            
            weight = float(item['weight_kg'])
            if weight <= 0:
                return jsonify({'error': 'Weight must be positive'}), 400
            
            total_weight += weight
            total_labor_cost += weight * labor_rate.rate_per_kg
        
        # Create receipt with current date
        receipt = Receipt(
            customer_name=data.get('customer_name', ''),
            notes=data.get('notes', ''),
            date=datetime.now().date(),  # Always use current date
            time=datetime.now().time(),
            total_weight=total_weight,
            total_labor_cost=total_labor_cost
        )
        
        db.session.add(receipt)
        db.session.flush()  # Get the receipt ID
        
        # Create receipt items
        for item_data in data['items']:
            item = ReceiptItem(
                receipt_id=receipt.id,
                item_name=item_data['item_name'],
                weight_kg=float(item_data['weight_kg']),
                dimension=item_data.get('dimension', ''),  # Optional dimension field
                labor_cost=float(item_data['weight_kg']) * labor_rate.rate_per_kg
            )
            db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Receipt created successfully',
            'receipt_id': receipt.id
        }), 201

    @staticmethod
    @jwt_required()
    def delete_receipt(receipt_id):
        """Delete receipt by ID"""
        receipt = Receipt.query.get_or_404(receipt_id)
        db.session.delete(receipt)
        db.session.commit()
        return jsonify({'message': 'Receipt deleted successfully'})

class SummaryController:
    @staticmethod
    def get_summary():
        try:
            # Get current date
            today = datetime.now().date()
            
            # Get today's receipts
            today_receipts = Receipt.query.filter(Receipt.date == today).all()
            
            # Calculate totals
            total_receipts = len(today_receipts)
            total_weight = sum(receipt.total_weight for receipt in today_receipts)
            total_labor_cost = sum(receipt.total_labor_cost for receipt in today_receipts)
            
            # Get labor rate
            labor_rate = LaborRate.query.first()
            current_rate = labor_rate.rate_per_kg if labor_rate else 0.0
            
            return jsonify({
                'total_receipts': total_receipts,
                'total_weight': total_weight,
                'total_labor_cost': total_labor_cost,
                'current_labor_rate': current_rate,
                'date': today.isoformat()
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def get_monthly_summary():
        try:
            # Get current month
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Get monthly receipts
            monthly_receipts = Receipt.query.filter(
                extract('month', Receipt.date) == current_month,
                extract('year', Receipt.date) == current_year
            ).all()
            
            # Calculate totals
            total_receipts = len(monthly_receipts)
            total_weight = sum(receipt.total_weight for receipt in monthly_receipts)
            total_labor_cost = sum(receipt.total_labor_cost for receipt in monthly_receipts)
            
            return jsonify({
                'total_receipts': total_receipts,
                'total_weight': total_weight,
                'total_labor_cost': total_labor_cost,
                'month': current_month,
                'year': current_year
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def export_data():
        try:
            # Get filter parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            customer_filter = request.args.get('customer')
            
            # Build query
            query = Receipt.query
            
            if start_date and end_date:
                query = query.filter(Receipt.date.between(start_date, end_date))
            elif start_date:
                query = query.filter(Receipt.date >= start_date)
            elif end_date:
                query = query.filter(Receipt.date <= end_date)
            
            if customer_filter:
                query = query.filter(Receipt.customer_name.ilike(f'%{customer_filter}%'))
            
            receipts = query.order_by(Receipt.date.desc()).all()
            
            # Prepare data for export
            export_data = []
            for receipt in receipts:
                receipt_data = {
                    'id': receipt.id,
                    'customer_name': receipt.customer_name,
                    'date': receipt.date.isoformat(),
                    'time': receipt.time.isoformat(),
                    'total_weight': receipt.total_weight,
                    'total_labor_cost': receipt.total_labor_cost,
                    'notes': receipt.notes,
                    'items': []
                }
                
                for item in receipt.items:
                    item_data = {
                        'item_name': item.item_name,
                        'weight_kg': item.weight_kg,
                        'dimension': item.dimension,
                        'labor_cost': item.labor_cost
                    }
                    receipt_data['items'].append(item_data)
                
                export_data.append(receipt_data)
            
            return jsonify(export_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

class DatabaseController:
    @staticmethod
    def get_database_stats():
        """Get database statistics for admin monitoring"""
        try:
            # Count records
            user_count = User.query.count()
            receipt_count = Receipt.query.count()
            item_count = ReceiptItem.query.count()
            labor_rate_count = LaborRate.query.count()
            
            # Get database file info
            db_path = 'iron_steel_business.db'
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                db_size_mb = round(db_size / (1024 * 1024), 2)
            else:
                db_size_mb = 0
            
            # Get recent activity
            recent_receipts = Receipt.query.order_by(Receipt.created_at.desc()).limit(5).all()
            recent_activity = []
            for receipt in recent_receipts:
                recent_activity.append({
                    'id': receipt.id,
                    'customer': receipt.customer_name,
                    'date': receipt.date.isoformat(),
                    'total_weight': receipt.total_weight,
                    'total_labor_cost': receipt.total_labor_cost
                })
            
            return jsonify({
                'database_stats': {
                    'users': user_count,
                    'receipts': receipt_count,
                    'items': item_count,
                    'labor_rates': labor_rate_count,
                    'database_size_mb': db_size_mb
                },
                'recent_activity': recent_activity,
                'last_updated': datetime.now().isoformat()
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def get_table_data():
        """Get data from specific tables for admin viewing"""
        try:
            table_name = request.args.get('table', 'receipt')
            
            if table_name == 'user':
                data = User.query.all()
                result = [{'id': u.id, 'username': u.username, 'created_at': u.created_at.isoformat()} for u in data]
            elif table_name == 'receipt':
                data = Receipt.query.order_by(Receipt.created_at.desc()).limit(50).all()
                result = [{
                    'id': r.id, 
                    'customer_name': r.customer_name,
                    'date': r.date.isoformat(),
                    'total_weight': r.total_weight,
                    'total_labor_cost': r.total_labor_cost,
                    'created_at': r.created_at.isoformat()
                } for r in data]
            elif table_name == 'labor_rate':
                data = LaborRate.query.all()
                result = [{'id': lr.id, 'rate_per_kg': lr.rate_per_kg, 'updated_at': lr.updated_at.isoformat()} for lr in data]
            else:
                return jsonify({'error': 'Invalid table name'}), 400
            
            return jsonify({
                'table': table_name,
                'count': len(result),
                'data': result
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500 