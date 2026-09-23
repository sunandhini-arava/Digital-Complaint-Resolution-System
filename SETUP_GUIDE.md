# Complaint Management System — Enhanced
## Full Setup Guide (From Scratch)

---

## What's Included

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.0 |
| Database | MySQL 8.0+ |
| Auth | JWT (PyJWT) + bcrypt |
| ML | scikit-learn, TextBlob, sentence-transformers |
| Frontend | Vanilla HTML/CSS/JS (no build step needed) |

### User Roles
| Role | Dashboard | Capabilities |
|------|-----------|--------------|
| `student` / `faculty` | student-dashboard | Submit & track own complaints |
| `administration` | admin-dashboard | View/update/filter all complaints |
| `admin` (Super Admin) | super-admin-dashboard | Full access + user management + reports |

---

## Prerequisites

Install these before starting:

1. **Python 3.10 or higher** — https://python.org/downloads
2. **MySQL 8.0 or higher** — https://dev.mysql.com/downloads/mysql/
3. **Git** (optional) — https://git-scm.com

Verify your installs:
```bash
python --version   # should be 3.10+
mysql --version    # should be 8.0+
pip --version
```

---

## Step 1 — Project Setup

Place the `cms-enhanced` project folder wherever you like, e.g. `C:\Projects\cms-enhanced` or `~/projects/cms-enhanced`.

```
cms-enhanced/
└── backend/
    ├── app.py
    ├── config.py
    ├── requirements.txt
    ├── setup_database.sql
    ├── seed_admin.py
    ├── .env.example
    ├── ml_models/
    │   ├── *.py  (model code)
    │   └── *.pkl (pre-trained models)
    ├── static/
    │   ├── css/styles.css
    │   └── js/*.js
    ├── templates/
    │   └── *.html
    └── uploads/    ← created automatically
```

---

## Step 2 — Create a Python Virtual Environment

```bash
# Windows
cd cms-enhanced\backend
python -m venv venv
venv\Scripts\activate

# macOS / Linux
cd cms-enhanced/backend
python3 -m venv venv
source venv/bin/activate
```

Your terminal prompt should now start with `(venv)`.

---

## Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, PyMySQL, bcrypt, PyJWT, scikit-learn, TextBlob, etc.

If sentence-transformers takes too long or you have limited RAM, you can skip it — the smart search and duplicate detection will fall back gracefully. To install without it:
```bash
pip install Flask Flask-CORS PyMySQL bcrypt PyJWT python-dotenv scikit-learn pandas numpy textblob nltk joblib
```

---

## Step 4 — Configure the Database

### 4a. Start MySQL

```bash
# Windows (if installed as a service)
net start mysql

# macOS (Homebrew)
brew services start mysql

# Linux
sudo systemctl start mysql
```

### 4b. Log in to MySQL

```bash
mysql -u root -p
```

Enter your MySQL root password when prompted.

### 4c. Create the database and tables

```sql
source /path/to/cms-enhanced/backend/setup_database.sql
```

Or paste the SQL file content directly.

Verify:
```sql
SHOW DATABASES;
USE complaint_management;
SHOW TABLES;
-- Should show: users, complaints, complaint_updates
```

---

## Step 5 — Configure Environment Variables

```bash
# In cms-enhanced/backend/
cp .env.example .env
```

Edit `.env` with your real values:

```env
SECRET_KEY=change-this-to-a-random-string
JWT_SECRET_KEY=another-random-string

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_mysql_password
MYSQL_DB=complaint_management

FLASK_DEBUG=False
PORT=5000
```

> **Security:** Never commit `.env` to Git. Add it to `.gitignore`.

Alternatively, you can edit `config.py` directly and set the values inline.

---

## Step 6 — Set the Super Admin Password

```bash
python seed_admin.py
```

Follow the prompts. This creates user `ADMIN001` with the password you choose.

---

## Step 7 — (Optional) Re-train ML Models

Pre-trained `.pkl` files are included. If you want to retrain with your own data:

```bash
python ml_models/train_models.py
```

Also download NLTK data if not present:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

---

## Step 8 — Run the Application

```bash
python app.py
```

You should see:
```
✅ Loaded ML model: classifier
✅ Loaded ML model: priority_predictor
...
✅ 6/6 ML models loaded successfully
 * Running on http://127.0.0.1:5000
```

Open your browser: **http://localhost:5000**

---

## Step 9 — First Login

Use the Super Admin credentials you set in Step 6:
- **User ID:** `ADMIN001`
- **Password:** *(the password you chose)*

From the Super Admin dashboard you can:
- Create students, faculty, and administration users
- View and manage all complaints
- See reports and analytics

---

## Step 10 — Creating Other Users

1. Log in as Super Admin
2. Go to **User Management → Add User**
3. Fill in User ID, name, email, type, and **date of birth**
4. The user receives a temporary password = `{user_id}{birthdate-without-dashes}` (e.g. `STU2024001200205151`)
5. The user visits `/activate.html`, enters their User ID + birthdate, and sets a new password

---

## API Endpoints Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/check-user` | Check if user ID exists |
| POST | `/api/auth/activate` | Activate account |
| POST | `/api/auth/login` | Login, returns JWT token |
| POST | `/api/auth/reset-password` | Change password (auth required) |

### Complaints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/complaints` | Create complaint |
| GET | `/api/complaints/my` | Get my complaints |
| GET | `/api/complaints` | Get all complaints (admin) |
| GET | `/api/complaints/:id` | Get complaint details |
| PUT | `/api/complaints/:id/update` | Update complaint (admin) |
| DELETE | `/api/complaints/:id` | Delete complaint (super admin) |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List users (super admin) |
| POST | `/api/users` | Create user (super admin) |
| PUT | `/api/users/:id` | Update user (super admin) |
| DELETE | `/api/users/:id` | Delete user (super admin) |

### Statistics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats/dashboard` | Dashboard statistics |

### ML APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ml/suggest-category` | Auto-suggest complaint category |
| POST | `/api/ml/suggest-priority` | Suggest priority |
| POST | `/api/ml/analyze-sentiment` | Sentiment analysis |
| POST | `/api/ml/check-duplicates` | Check for duplicate complaints |
| POST | `/api/ml/predict-resolution-time` | Estimate resolution time |
| POST | `/api/ml/smart-search` | Semantic search |
| POST | `/api/ml/analyze-all` | All ML analyses in one call |
| GET | `/api/ml/status` | Check which models are loaded |

### Utility
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/uploads/:filename` | Download attachment |

---

## Troubleshooting

### "Access denied for user" (MySQL error)
- Check `.env` MYSQL_PASSWORD matches your actual MySQL password
- Ensure the MySQL user has access to `complaint_management` database:
  ```sql
  GRANT ALL PRIVILEGES ON complaint_management.* TO 'root'@'localhost';
  FLUSH PRIVILEGES;
  ```

### ML models not loading
- Run `python ml_models/train_models.py` to regenerate `.pkl` files
- The app still runs without ML models — features just degrade gracefully

### Port 5000 already in use
- Change `PORT=5001` in `.env`
- On macOS, AirPlay Receiver uses port 5000 — disable it in System Preferences → Sharing

### "Module not found" errors
- Ensure your virtual environment is activated: `(venv)` should appear in your terminal
- Run `pip install -r requirements.txt` again

### Windows PATH issues
- Use `python` not `python3` on Windows
- Use `venv\Scripts\activate` (not `source venv/bin/activate`)

---

## Production Deployment Notes

For production use:

1. Set `FLASK_DEBUG=False` in `.env`
2. Use a proper WSGI server: `pip install gunicorn` → `gunicorn -w 4 app:app`
3. Use strong random values for `SECRET_KEY` and `JWT_SECRET_KEY`
4. Use a dedicated MySQL user with limited permissions (not root)
5. Set up HTTPS with nginx or a reverse proxy
6. Move `UPLOAD_FOLDER` to a location outside the project root
