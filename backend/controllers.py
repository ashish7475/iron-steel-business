from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, LaborRate, Receipt, ReceiptItem
from datetime import datetime, timedelta
import bcrypt

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
    @jwt_required()
    def get_summary():
        """Get daily summary statistics"""
        date = request.args.get('date')
        
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            receipts = Receipt.query.filter_by(date=target_date).all()
        else:
            target_date = datetime.now().date()
            receipts = Receipt.query.filter_by(date=target_date).all()
        
        total_receipts = len(receipts)
        total_weight = sum(receipt.total_weight for receipt in receipts)
        total_labor_cost = sum(receipt.total_labor_cost for receipt in receipts)
        
        return jsonify({
            'date': target_date.strftime('%Y-%m-%d'),
            'total_receipts': total_receipts,
            'total_weight': total_weight,
            'total_labor_cost': total_labor_cost
        })

    @staticmethod
    @jwt_required()
    def get_monthly_summary():
        """Get monthly summary statistics"""
        year = request.args.get('year', datetime.now().year)
        month = request.args.get('month', datetime.now().month)
        
        # Get first and last day of month
        first_day = datetime(int(year), int(month), 1).date()
        if int(month) == 12:
            last_day = datetime(int(year) + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(int(year), int(month) + 1, 1).date() - timedelta(days=1)
        
        receipts = Receipt.query.filter(
            Receipt.date >= first_day,
            Receipt.date <= last_day
        ).all()
        
        total_receipts = len(receipts)
        total_weight = sum(receipt.total_weight for receipt in receipts)
        total_labor_cost = sum(receipt.total_labor_cost for receipt in receipts)
        
        # Group by date for daily breakdown
        daily_breakdown = {}
        for receipt in receipts:
            date_str = receipt.date.strftime('%Y-%m-%d')
            if date_str not in daily_breakdown:
                daily_breakdown[date_str] = {
                    'receipts': 0,
                    'weight': 0,
                    'labor_cost': 0
                }
            daily_breakdown[date_str]['receipts'] += 1
            daily_breakdown[date_str]['weight'] += receipt.total_weight
            daily_breakdown[date_str]['labor_cost'] += receipt.total_labor_cost
        
        return jsonify({
            'year': int(year),
            'month': int(month),
            'total_receipts': total_receipts,
            'total_weight': total_weight,
            'total_labor_cost': total_labor_cost,
            'daily_breakdown': daily_breakdown
        })

    @staticmethod
    @jwt_required()
    def export_data():
        """Export data as CSV with same filters as get_receipts"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date = request.args.get('date')  # Keep for backward compatibility
        customer = request.args.get('customer')
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query (same logic as get_receipts)
        query = Receipt.query
        
        # Apply date filtering
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Receipt.date >= start_dt, Receipt.date <= end_dt)
            filename = f"receipts_{start_date}_to_{end_date}.csv"
        elif date:
            query = query.filter_by(date=datetime.strptime(date, '%Y-%m-%d').date())
            filename = f"receipts_{date}.csv"
        else:
            filename = "all_receipts.csv"
        
        # Apply customer filter
        if customer:
            query = query.filter(Receipt.customer_name.ilike(f'%{customer}%'))
            filename = f"receipts_customer_{customer}_{filename}"
        
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
        
        # Generate CSV content
        csv_content = "Date,Time,Receipt ID,Customer,Total Weight (kg),Total Labor Cost (₹),Items\n"
        
        for receipt in receipts:
            items_str = "; ".join([f"{item.item_name} ({item.weight_kg}kg{f' - {item.dimension}' if item.dimension else ''})" for item in receipt.items])
            csv_content += f"{receipt.date},{receipt.time},{receipt.id},{receipt.customer_name or ''},{receipt.total_weight},{receipt.total_labor_cost},\"{items_str}\"\n"
        
        return jsonify({
            'filename': filename,
            'content': csv_content,
            'total_records': len(receipts)
        }) 