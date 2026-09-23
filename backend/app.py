from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
import pymysql
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from config import Config
import secrets
import logging

# ML Models imports
import sys
sys.path.insert(0, os.path.dirname(__file__))

from ml_models.complaint_classifier import ComplaintClassifier
from ml_models.priority_predictor import PriorityPredictor
from ml_models.sentiment_analyzer import SentimentAnalyzer
from ml_models.duplicate_detector import DuplicateDetector
from ml_models.resolution_time_predictor import ResolutionTimePredictor
from ml_models.smart_search import SmartSearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============= LOAD ML MODELS =============
ml_models = {}
MODEL_FILES = {
    'classifier': ('ml_models/classifier.pkl', ComplaintClassifier),
    'priority_predictor': ('ml_models/priority_predictor.pkl', PriorityPredictor),
    'sentiment_analyzer': ('ml_models/sentiment_analyzer.pkl', SentimentAnalyzer),
    'duplicate_detector': ('ml_models/duplicate_detector.pkl', DuplicateDetector),
    'resolution_predictor': ('ml_models/resolution_predictor.pkl', ResolutionTimePredictor),
    'smart_search': ('ml_models/smart_search.pkl', SmartSearch),
}

for name, (path, cls) in MODEL_FILES.items():
    try:
        ml_models[name] = cls.load(path)
        logger.info(f"✅ Loaded ML model: {name}")
    except Exception as e:
        ml_models[name] = None
        logger.warning(f"⚠️  Could not load {name}: {e}")

if all(v is None for v in ml_models.values()):
    logger.warning("No ML models loaded. Run: python ml_models/train_models.py")
else:
    loaded = sum(1 for v in ml_models.values() if v is not None)
    logger.info(f"✅ {loaded}/{len(ml_models)} ML models loaded successfully")

# Setup upload folder
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except Exception:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.expanduser('~'), 'complaint_uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ============= DATABASE =============

def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def serialize_datetimes(obj):
    """Recursively convert datetime objects to strings in a dict/list."""
    if isinstance(obj, dict):
        return {k: serialize_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetimes(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return obj


# ============= DECORATORS =============

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired. Please login again.'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid', 'error': str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user['user_type'] not in ['admin', 'administration']:
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


# ============= FRONTEND ROUTES =============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/activate.html')
def activate_page():
    return render_template('activate.html')

@app.route('/student-dashboard.html')
def student_dashboard():
    return render_template('student-dashboard.html')

@app.route('/admin-dashboard.html')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/super-admin-dashboard.html')
def super_admin_dashboard():
    return render_template('super-admin-dashboard.html')


# ============= AUTH ROUTES =============

@app.route('/api/auth/check-user', methods=['POST'])
def check_user():
    data = request.json
    user_id = data.get('user_id', '').strip()
    if not user_id:
        return jsonify({'exists': False, 'message': 'User ID is required'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, is_activated, user_type FROM users WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
        if not user:
            return jsonify({'exists': False, 'message': 'User ID not found'}), 404
        return jsonify({
            'exists': True,
            'is_activated': bool(user['is_activated']),
            'user_type': user['user_type']
        }), 200
    finally:
        conn.close()


@app.route('/api/auth/activate', methods=['POST'])
def activate_account():
    data = request.json
    user_id = data.get('user_id', '').strip()
    birthdate = data.get('birthdate', '').strip()
    new_password = data.get('new_password', '')

    if not all([user_id, birthdate, new_password]):
        return jsonify({'message': 'All fields are required'}), 400
    if len(new_password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, birthdate, is_activated FROM users WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'User not found'}), 404
            if user['is_activated']:
                return jsonify({'message': 'Account already activated. Please login.'}), 400
            if str(user['birthdate']) != birthdate:
                return jsonify({'message': 'Birthdate does not match our records'}), 401

            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "UPDATE users SET password = %s, is_activated = TRUE WHERE user_id = %s",
                (hashed.decode('utf-8'), user_id)
            )
        conn.commit()
        return jsonify({'message': 'Account activated successfully! You can now login.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"Activation error: {e}")
        return jsonify({'message': 'Activation failed', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user_id = data.get('user_id', '').strip()
    password = data.get('password', '')

    if not user_id or not password:
        return jsonify({'message': 'User ID and password are required'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, password, full_name, email, user_type, is_activated "
                "FROM users WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()

        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        if not user['is_activated']:
            return jsonify({'message': 'Account not activated. Please activate your account first.'}), 403
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'message': 'Invalid credentials'}), 401

        token = jwt.encode({
            'user_id': user['user_id'],
            'user_type': user['user_type'],
            'id': user['id'],
            'full_name': user['full_name'],
            'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }, app.config['JWT_SECRET_KEY'], algorithm="HS256")

        logger.info(f"Login success: {user_id} ({user['user_type']})")
        return jsonify({
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'user_type': user['user_type']
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/auth/reset-password', methods=['POST'])
@token_required
def reset_password(current_user):
    data = request.json
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if len(new_password) < 8:
        return jsonify({'message': 'New password must be at least 8 characters'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE user_id = %s", (current_user['user_id'],))
            user = cursor.fetchone()
            if not user or not bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({'message': 'Current password is incorrect'}), 401

            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "UPDATE users SET password = %s WHERE user_id = %s",
                (hashed.decode('utf-8'), current_user['user_id'])
            )
        conn.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Password reset failed', 'error': str(e)}), 500
    finally:
        conn.close()


# ============= COMPLAINT ROUTES =============

@app.route('/api/complaints', methods=['POST'])
@token_required
def create_complaint(current_user):
    if current_user['user_type'] not in ['student', 'faculty']:
        return jsonify({'message': 'Only students and faculty can create complaints'}), 403

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()

    if not all([title, description, category]):
        return jsonify({'message': 'Title, description, and category are required'}), 400

    complaint_id = f"CMP{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(3).upper()}"

    attachment_path = None
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext in app.config['ALLOWED_EXTENSIONS']:
                filename = f"{complaint_id}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                attachment_path = filename
            else:
                return jsonify({'message': f'File type .{ext} not allowed'}), 400

    conn = get_db_connection()
    try:
        # Run ML analysis if models are loaded
        ml_data = {}
        text = f"{title} {description}"
        if ml_models.get('classifier'):
            try:
                ml_data['category_suggestion'] = ml_models['classifier'].predict(text)
            except Exception:
                pass
        if ml_models.get('priority_predictor'):
            try:
                ml_data['priority_suggestion'] = ml_models['priority_predictor'].predict_priority(text, category)
            except Exception:
                pass
        if ml_models.get('sentiment_analyzer'):
            try:
                ml_data['sentiment'] = ml_models['sentiment_analyzer'].analyze(text)
            except Exception:
                pass

        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO complaints 
                   (complaint_id, user_id, title, description, category, attachment_path)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (complaint_id, current_user['user_id'], title, description, category, attachment_path)
            )
        conn.commit()
        logger.info(f"Complaint created: {complaint_id} by {current_user['user_id']}")
        return jsonify({
            'message': 'Complaint submitted successfully',
            'complaint_id': complaint_id,
            'ml_insights': ml_data
        }), 201
    except Exception as e:
        conn.rollback()
        logger.error(f"Create complaint error: {e}")
        return jsonify({'message': 'Failed to create complaint', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/complaints/my', methods=['GET'])
@token_required
def get_my_complaints(current_user):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT c.*, u.full_name as user_name
                   FROM complaints c
                   JOIN users u ON c.user_id = u.user_id
                   WHERE c.user_id = %s
                   ORDER BY c.created_at DESC""",
                (current_user['user_id'],)
            )
            complaints = cursor.fetchall()
        return jsonify({'complaints': serialize_datetimes(complaints)}), 200
    finally:
        conn.close()


@app.route('/api/complaints', methods=['GET'])
@token_required
def get_all_complaints(current_user):
    if current_user['user_type'] not in ['admin', 'administration']:
        return jsonify({'message': 'Unauthorized'}), 403

    status = request.args.get('status')
    category = request.args.get('category')
    priority = request.args.get('priority')
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, int(request.args.get('per_page', 20)))
    offset = (page - 1) * per_page

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT c.*, u.full_name as user_name, u.user_type,
                       a.full_name as assigned_to_name
                FROM complaints c
                JOIN users u ON c.user_id = u.user_id
                LEFT JOIN users a ON c.assigned_to = a.id
                WHERE 1=1
            """
            params = []
            if status:
                query += " AND c.status = %s"
                params.append(status)
            if category:
                query += " AND c.category = %s"
                params.append(category)
            if priority:
                query += " AND c.priority = %s"
                params.append(priority)
            if search:
                query += " AND (c.title LIKE %s OR c.description LIKE %s OR c.complaint_id LIKE %s)"
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

            # Count total
            count_query = f"SELECT COUNT(*) as total FROM ({query}) as sub"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            query += " ORDER BY c.created_at DESC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            cursor.execute(query, params)
            complaints = cursor.fetchall()

        return jsonify({
            'complaints': serialize_datetimes(complaints),
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    finally:
        conn.close()


@app.route('/api/complaints/<complaint_id>', methods=['GET'])
@token_required
def get_complaint_details(current_user, complaint_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT c.*, u.full_name as user_name, u.email as user_email,
                          u.phone as user_phone, a.full_name as assigned_to_name
                   FROM complaints c
                   JOIN users u ON c.user_id = u.user_id
                   LEFT JOIN users a ON c.assigned_to = a.id
                   WHERE c.complaint_id = %s""",
                (complaint_id,)
            )
            complaint = cursor.fetchone()
            if not complaint:
                return jsonify({'message': 'Complaint not found'}), 404

            if current_user['user_type'] not in ['admin', 'administration']:
                if complaint['user_id'] != current_user['user_id']:
                    return jsonify({'message': 'Unauthorized'}), 403

            cursor.execute(
                """SELECT cu.*, u.full_name as updated_by_name
                   FROM complaint_updates cu
                   JOIN users u ON cu.updated_by = u.id
                   WHERE cu.complaint_id = %s
                   ORDER BY cu.created_at DESC""",
                (complaint_id,)
            )
            updates = cursor.fetchall()

        complaint['updates'] = updates
        return jsonify({'complaint': serialize_datetimes(complaint)}), 200
    finally:
        conn.close()


@app.route('/api/complaints/<complaint_id>/update', methods=['PUT'])
@token_required
@admin_required
def update_complaint(current_user, complaint_id):
    data = request.json
    status = data.get('status')
    priority = data.get('priority')
    admin_remarks = data.get('admin_remarks', '').strip()
    assigned_to = data.get('assigned_to')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT status FROM complaints WHERE complaint_id = %s", (complaint_id,))
            complaint = cursor.fetchone()
            if not complaint:
                return jsonify({'message': 'Complaint not found'}), 404

            old_status = complaint['status']
            update_fields = []
            params = []

            if status:
                update_fields.append("status = %s")
                params.append(status)
                if status == 'resolved':
                    update_fields.append("resolved_at = NOW()")
            if priority:
                update_fields.append("priority = %s")
                params.append(priority)
            if admin_remarks:
                update_fields.append("admin_remarks = %s")
                params.append(admin_remarks)
            if assigned_to is not None:
                update_fields.append("assigned_to = %s")
                params.append(assigned_to if assigned_to else None)

            if update_fields:
                params.append(complaint_id)
                cursor.execute(
                    f"UPDATE complaints SET {', '.join(update_fields)} WHERE complaint_id = %s",
                    params
                )

            # Log the update
            if status and status != old_status:
                cursor.execute(
                    """INSERT INTO complaint_updates 
                       (complaint_id, updated_by, update_type, old_status, new_status, message)
                       VALUES (%s, %s, 'status_change', %s, %s, %s)""",
                    (complaint_id, current_user['id'], old_status, status, admin_remarks or None)
                )
            elif admin_remarks:
                cursor.execute(
                    """INSERT INTO complaint_updates 
                       (complaint_id, updated_by, update_type, message)
                       VALUES (%s, %s, 'comment', %s)""",
                    (complaint_id, current_user['id'], admin_remarks)
                )

        conn.commit()
        return jsonify({'message': 'Complaint updated successfully'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"Update complaint error: {e}")
        return jsonify({'message': 'Update failed', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/complaints/<complaint_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_complaint(current_user, complaint_id):
    if current_user['user_type'] != 'admin':
        return jsonify({'message': 'Super admin access required'}), 403

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM complaint_updates WHERE complaint_id = %s", (complaint_id,))
            cursor.execute("DELETE FROM complaints WHERE complaint_id = %s", (complaint_id,))
        conn.commit()
        return jsonify({'message': 'Complaint deleted successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Delete failed', 'error': str(e)}), 500
    finally:
        conn.close()


# ============= USER MANAGEMENT =============

@app.route('/api/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    if current_user['user_type'] != 'admin':
        return jsonify({'message': 'Super admin access required'}), 403

    user_type = request.args.get('user_type')
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, int(request.args.get('per_page', 20)))
    offset = (page - 1) * per_page

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = ("SELECT id, user_id, full_name, email, phone, user_type, "
                     "birthdate, is_activated, created_at FROM users WHERE 1=1")
            params = []
            if user_type:
                query += " AND user_type = %s"
                params.append(user_type)
            if search:
                query += " AND (full_name LIKE %s OR user_id LIKE %s OR email LIKE %s)"
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

            count_query = f"SELECT COUNT(*) as total FROM ({query}) as sub"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            cursor.execute(query, params)
            users = cursor.fetchall()

        return jsonify({
            'users': serialize_datetimes(users),
            'pagination': {'total': total, 'page': page, 'per_page': per_page,
                           'pages': (total + per_page - 1) // per_page}
        }), 200
    finally:
        conn.close()


@app.route('/api/users', methods=['POST'])
@token_required
@admin_required
def create_user(current_user):
    if current_user['user_type'] != 'admin':
        return jsonify({'message': 'Super admin access required'}), 403

    data = request.json
    required = ['user_id', 'full_name', 'email', 'user_type', 'birthdate']
    if not all(data.get(f) for f in required):
        return jsonify({'message': 'All required fields must be provided'}), 400

    user_id = data['user_id'].strip()
    full_name = data['full_name'].strip()
    email = data['email'].strip()
    phone = data.get('phone', '').strip()
    user_type = data['user_type']
    birthdate = data['birthdate']

    temp_password = f"{user_id}{birthdate.replace('-', '')}"
    hashed = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, hashed.decode('utf-8'), full_name, email, phone, user_type, birthdate)
            )
        conn.commit()
        return jsonify({
            'message': 'User created successfully',
            'temp_password': temp_password,
            'note': 'User must activate account using their birthdate'
        }), 201
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        return jsonify({'message': 'User ID or email already exists', 'error': str(e)}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Failed to create user', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/users/<int:user_db_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_db_id):
    if current_user['user_type'] != 'admin':
        return jsonify({'message': 'Super admin access required'}), 403

    data = request.json
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            update_fields = []
            params = []
            for field in ['full_name', 'email', 'phone', 'user_type']:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])
            if update_fields:
                params.append(user_db_id)
                cursor.execute(
                    f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s",
                    params
                )
        conn.commit()
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Update failed', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/users/<int:user_db_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_db_id):
    if current_user['user_type'] != 'admin':
        return jsonify({'message': 'Super admin access required'}), 403

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_db_id,))
        conn.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Delete failed', 'error': str(e)}), 500
    finally:
        conn.close()


# ============= STATISTICS =============

@app.route('/api/stats/dashboard', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    conn = get_db_connection()
    try:
        stats = {}
        with conn.cursor() as cursor:
            if current_user['user_type'] in ['admin', 'administration']:
                cursor.execute("SELECT COUNT(*) as total FROM complaints")
                stats['total_complaints'] = cursor.fetchone()['total']

                cursor.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status")
                stats['by_status'] = cursor.fetchall()

                cursor.execute("SELECT category, COUNT(*) as count FROM complaints GROUP BY category")
                stats['by_category'] = cursor.fetchall()

                cursor.execute("SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority")
                stats['by_priority'] = cursor.fetchall()

                cursor.execute(
                    "SELECT complaint_id, title, status, priority, created_at "
                    "FROM complaints ORDER BY created_at DESC LIMIT 10"
                )
                stats['recent_complaints'] = serialize_datetimes(cursor.fetchall())

                # Resolution rate
                cursor.execute(
                    "SELECT COUNT(*) as resolved FROM complaints WHERE status = 'resolved'"
                )
                resolved = cursor.fetchone()['resolved']
                total = stats['total_complaints']
                stats['resolution_rate'] = round((resolved / total * 100) if total > 0 else 0, 1)

                # Average resolution time (days)
                cursor.execute(
                    """SELECT AVG(DATEDIFF(resolved_at, created_at)) as avg_days
                       FROM complaints WHERE resolved_at IS NOT NULL"""
                )
                avg = cursor.fetchone()['avg_days']
                stats['avg_resolution_days'] = round(float(avg), 1) if avg else 0

                if current_user['user_type'] == 'admin':
                    cursor.execute("SELECT user_type, COUNT(*) as count FROM users GROUP BY user_type")
                    stats['user_stats'] = cursor.fetchall()
                    cursor.execute("SELECT COUNT(*) as total FROM users")
                    stats['total_users'] = cursor.fetchone()['total']

                    # Monthly trend (last 6 months)
                    cursor.execute(
                        """SELECT DATE_FORMAT(created_at, '%Y-%m') as month, COUNT(*) as count
                           FROM complaints
                           WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                           GROUP BY month ORDER BY month"""
                    )
                    stats['monthly_trend'] = cursor.fetchall()

            else:
                cursor.execute(
                    "SELECT COUNT(*) as total FROM complaints WHERE user_id = %s",
                    (current_user['user_id'],)
                )
                stats['my_complaints'] = cursor.fetchone()['total']

                cursor.execute(
                    "SELECT status, COUNT(*) as count FROM complaints "
                    "WHERE user_id = %s GROUP BY status",
                    (current_user['user_id'],)
                )
                stats['my_status'] = cursor.fetchall()

                cursor.execute(
                    "SELECT complaint_id, title, status, priority, created_at "
                    "FROM complaints WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
                    (current_user['user_id'],)
                )
                stats['recent'] = serialize_datetimes(cursor.fetchall())

        return jsonify({'stats': stats}), 200
    finally:
        conn.close()


# ============= FILE DOWNLOAD =============

@app.route('/api/uploads/<filename>')
@token_required
def download_file(current_user, filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ============= ML API ROUTES =============

@app.route('/api/ml/suggest-category', methods=['POST'])
def suggest_category():
    try:
        data = request.json
        text = f"{data.get('title', '')} {data.get('description', '')}"
        if ml_models.get('classifier'):
            result = ml_models['classifier'].predict(text)
            return jsonify({'success': True, 'suggested_category': result['category'],
                            'confidence': result['confidence'], 'top_3': result['top_3']})
        return jsonify({'success': False, 'message': 'Classifier not loaded'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ml/suggest-priority', methods=['POST'])
def suggest_priority():
    try:
        data = request.json
        text = f"{data.get('title', '')} {data.get('description', '')}"
        category = data.get('category')
        if ml_models.get('priority_predictor'):
            result = ml_models['priority_predictor'].predict_priority(text, category)
            return jsonify({'success': True, 'suggested_priority': result['priority'],
                            'confidence': result['confidence'], 'reasoning': result['reasoning']})
        return jsonify({'success': False, 'message': 'Priority predictor not loaded'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ml/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    try:
        data = request.json
        text = f"{data.get('title', '')} {data.get('description', '')}"
        if ml_models.get('sentiment_analyzer'):
            result = ml_models['sentiment_analyzer'].analyze(text)
            return jsonify({'success': True, **result})
        return jsonify({'success': False, 'message': 'Sentiment analyzer not loaded'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ml/check-duplicates', methods=['POST'])
def check_duplicates():
    try:
        data = request.json
        if ml_models.get('duplicate_detector'):
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT complaint_id, title, description, category, status
                           FROM complaints WHERE status IN ('pending','in-progress')
                           ORDER BY created_at DESC LIMIT 100"""
                    )
                    recent = cursor.fetchall()
            finally:
                conn.close()

            if recent:
                ml_models['duplicate_detector'].index_complaints([
                    {'id': c['complaint_id'], 'title': c['title'],
                     'description': c['description'], 'category': c['category'],
                     'status': c['status']} for c in recent
                ])
            result = ml_models['duplicate_detector'].check_duplicate(data)
            return jsonify({'success': True, **result})
        return jsonify({'success': False, 'message': 'Duplicate detector not loaded'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ml/predict-resolution-time', methods=['POST'])
def predict_resolution_time():
    try:
        data = request.json
        if ml_models.get('resolution_predictor'):
            result = ml_models['resolution_predictor'].predict(data)
            return jsonify({'success': True, **result})
        return jsonify({'success': False, 'message': 'Resolution predictor not loaded'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ml/smart-search', methods=['POST'])
def ml_smart_search():
    try:
        data = request.json
        query = data.get('query', '')
        filters = data.get('filters', {})
        top_k = data.get('top_k', 10)

        if ml_models.get('smart_search'):
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT c.complaint_id, c.title, c.description, c.category,
                                  c.status, c.priority, c.created_at, u.full_name as user_name, u.user_type
                           FROM complaints c JOIN users u ON c.user_id = u.user_id
                           ORDER BY c.created_at DESC LIMIT 200"""
                    )
                    all_complaints = cursor.fetchall()
            finally:
                conn.close()

            if all_complaints:
                ml_models['smart_search'].index_complaints([
                    {**c, 'created_at': c['created_at'].isoformat() if c['created_at'] else None}
                    for c in all_complaints
                ])
            result = ml_models['smart_search'].search(query, filters, top_k)
            return jsonify({'success': True, **result})
        return jsonify({'success': False, 'message': 'Smart search not loaded'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ml/analyze-all', methods=['POST'])
def analyze_all():
    try:
        data = request.json
        text = f"{data.get('title', '')} {data.get('description', '')}"
        category = data.get('category')
        results = {}

        if ml_models.get('classifier'):
            results['category'] = ml_models['classifier'].predict(text)
        if ml_models.get('priority_predictor'):
            results['priority'] = ml_models['priority_predictor'].predict_priority(text, category)
        if ml_models.get('sentiment_analyzer'):
            results['sentiment'] = ml_models['sentiment_analyzer'].analyze(text)
        if ml_models.get('resolution_predictor'):
            results['resolution_time'] = ml_models['resolution_predictor'].predict(data)

        return jsonify({'success': True, 'analysis': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ml/status', methods=['GET'])
def ml_status():
    """Check which ML models are loaded."""
    return jsonify({
        'models': {name: (model is not None) for name, model in ml_models.items()}
    }), 200


# ============= HEALTH CHECK =============

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return jsonify({
        'status': 'ok' if db_ok else 'degraded',
        'database': 'connected' if db_ok else 'disconnected',
        'ml_models': sum(1 for v in ml_models.values() if v) ,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if db_ok else 503


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'message': 'Method not allowed'}), 405

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'message': 'File too large. Maximum size is 16MB'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'message': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("Starting Complaint Management System...")
    app.run(debug=app.config.get('DEBUG', False), port=app.config.get('PORT', 5000))
