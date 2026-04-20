# Cooperative Management System API

A FastAPI-based backend for managing cooperative societies with features for member management, loan processing, payment tracking, and contribution management.

## 🎯 What This Project Does

This is a comprehensive **Cooperative Management API** that enables:

- 👥 **Member Management** - Register, authenticate, and manage member profiles
- 💰 **Loan System** - Create loans with automatic interest calculations, track repayment
- 💳 **Payment Processing** - Record payments, update balances, auto-complete loans
- 📊 **Contribution Tracking** - Monitor member contributions
- 🔐 **Authentication** - JWT-based auth with role-based access (Admin/Member)
- 📋 **Policy Management** - Create and manage cooperative policies

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.9+
- MySQL Server
- pip

### Setup

```bash
# 1. Clone & navigate
git clone https://github.com/yourusername/cooperative_simulation_based_bn.git
cd cooperative_simulation_based_bn

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your database credentials

# 5. Create database
mysql -u root -p
CREATE DATABASE cooperative_db;
EXIT;

# 6. Run migrations
alembic upgrade head

# 7. Start server
uvicorn app.main:app --reload
```

**API Documentation**: http://localhost:8000/docs (Swagger UI)

---

## 📋 API Endpoints (24 Total)

### Authentication (2)
```
POST   /auth/register              Register new member
POST   /auth/login                 Login, get JWT token
```

### Members (2)
```
GET    /members/member_profile     Get logged-in member's profile
GET    /members/total_contribution/me   Get total contribution
```

### Loans (5)
```
POST   /loans/member/{member_id}   Create loan (Admin)
GET    /loans                      Get all loans (Admin)
GET    /loans/me                   Get my loans (Member)
GET    /loans/{loan_id}            Get specific loan
PUT    /loans/{loan_id}/status     Update loan status (Admin)
```

### Payments (5)
```
POST   /payments/loan/{loan_id}/member/{member_id}   Record payment (Admin)
GET    /payments                                      Get all payments (Admin)
GET    /payments/me                                   Get my payments (Member)
GET    /payments/loan/{loan_id}                       Get payments for loan
```

### Contributions (3)
```
POST   /admin/members/{member_id}/member_contribution   Add contribution
GET    /member_contribution/members                     Get all contributions
PUT    /admin/members/member_contribution/{id}         Update contribution
```

### Admin Routes (4)
```
GET    /admin/members                         Get all members
GET    /admin/members/{member_id}            Get member details
PUT    /admin/members/{member_id}/role       Change member role
PUT    /admin/members/{member_id}/member_status   Update status
```

### Policies (3)
```
POST   /policies                   Create policy
GET    /policies                   Get all policies
GET    /policies/{policy_id}       Get specific policy
```

---

## 💡 Key Business Logic

### Loan Management
```
1. Admin creates loan for member
2. System calculates:
   - interest_payable = loan_amount × (interest_rate / 100)
   - repayment_amount = loan_amount + interest_payable
   - loan_balance = repayment_amount (initially)
3. Loan starts with status: pending
4. Admin activates loan (status: active)
5. Member makes payments
```

### Payment Processing
```
1. Member/Admin records payment
2. System validates:
   ✓ Loan is active
   ✓ Payment ≤ loan_balance (no overpayment)
   ✓ Payment ≤ repayment_amount
3. System updates:
   - amount_paid += payment_amount
   - loan_balance -= payment_amount
4. If loan_balance ≤ 0, mark as completed
```

### Member Restrictions
- **One Active Loan**: Cannot get new loan while current is active
- **View Own Data**: Members can only view their own loans/payments
- **Admin Records All Payments**: Only admins can record payments in the system
- **Admin Only**: Only admins can create loans and record payments

### Loan Example
```
Loan Amount: 5000
Interest Rate: 10%
Interest: 500
Repayment: 5500

Payment 1: 2000 → Balance: 3500
Payment 2: 3500 → Balance: 0 ✓ (Auto-completed)
```

---

## 🏗️ Technology Stack

- **Framework**: FastAPI
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic
- **Migrations**: Alembic
- **Server**: Uvicorn
- **Security**: bcrypt (password hashing)

---

## 📁 Project Structure

```
app/
├── main.py                  # FastAPI app entry point
├── dependencies.py          # Global dependencies
│
├── core/
│   ├── config.py           # Configuration settings
│   └── security.py         # JWT & password hashing
│
├── db/
│   ├── database.py         # SQLAlchemy setup
│   └── migrations/         # Alembic migrations
│
├── models/                 # SQLAlchemy ORM models
│   ├── members.py
│   ├── loans.py
│   ├── payments.py
│   ├── member_contributions.py
│   ├── cooperatives.py
│   └── policies.py
│
├── schemas/                # Pydantic DTOs for validation
│   ├── member.py
│   ├── loan.py
│   ├── payment.py
│   └── ...
│
├── routers/                # API route handlers
│   ├── auth_routes.py
│   ├── loan_routes.py
│   ├── payment_routes.py
│   ├── admin_routes.py
│   └── ...
│
├── services/               # Business logic
│   ├── auth_service.py
│   ├── loan_service.py
│   ├── payment_service.py
│   └── ...
│
├── middleware/             # Custom middleware
│   ├── authorization.py
│   └── validations.py
│
└── enums/                  # Enumerations
    ├── member.py
    ├── loans.py
    └── policies.py
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Required
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/cooperative_db
SECRET_KEY=your-super-secret-key-change-in-production

# Optional
API_HOST=127.0.0.1
API_PORT=8000
```

Generate a strong SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔐 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Authentication**: Token-based access
- **Role-Based Access**: Admin vs Member roles
- **Input Validation**: Pydantic schema validation
- **CORS Protection**: Configured origins
- **Exception Handling**: No sensitive data leakage
- **Authorization Middleware**: Resource-level access control

---

## 🛠️ Development Commands

### Database Migrations
```bash
# Create new migration (auto-detect changes)
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Apply all pending migrations (project command)
python migrate.py

# If schema already exists and migration history is missing, align version table
python migrate.py --stamp-head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_loans.py

# Run with coverage
pytest --cov=app
```

### Code Quality
```bash
# Format code
black app/

# Check style
flake8 app/

# Type checking
mypy app/
```

---

## 📊 Database Schema

| Table | Purpose |
|-------|---------|
| `members` | User accounts (admin/member roles) |
| `loans` | Loan records with calculations |
| `payments` | Payment history & tracking |
| `member_contributions` | Contribution tracking |
| `cooperative_societies` | Cooperative information |
| `policies` | Cooperative policies |

---

## 🚀 API Usage Examples

### Register & Login

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass"
  }'
# Response: {"access_token": "...", "token_type": "bearer"}
```

### Create Loan (Admin)

```bash
curl -X POST http://localhost:8000/loans/member/1 \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_amount": 5000,
    "interest_rate": 10,
    "repayment_period": 12
  }'
```

### Make Payment (Admin)

```bash
curl -X POST http://localhost:8000/payments/loan/1/member/1 \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"amount_paid": 2000}'
```

### View Loans (Member)

```bash
curl -X GET http://localhost:8000/loans/me \
  -H "Authorization: Bearer <member_token>"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection error | Ensure MySQL is running, check DATABASE_URL in .env, verify database exists |
| Module not found | Activate virtual environment, run from project root |
| Migration failed | `alembic downgrade base` then `alembic upgrade head` |
| JWT token issues | Login again to get fresh token |
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` (Mac/Linux) or change port |

---

## 🚢 Deployment

### Vercel
```bash
# Project includes vercel.json
vercel
```

### Docker
```bash
docker build -t cooperative-api .
docker run -p 8000:8000 cooperative-api
```

### Production Checklist
- [ ] Change SECRET_KEY to strong random value
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS
- [ ] Update CORS origins in app/main.py
- [ ] Implement rate limiting
- [ ] Add request logging
- [ ] Enable database backups
- [ ] Use strong database passwords

---

## 📝 Interactive API Docs

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **Alternative ReDoc**: http://localhost:8000/redoc

---

## 🔄 Complete Workflow Example

```
1. Admin creates account (registers as admin role or via seed)
2. Member registers
3. Member logs in
4. Admin creates loan for member
5. Admin marks loan as active
6. Member views their loans
7. Member gives payment to admin
8. Admin records payment via /payments/loan/{id}/member/{id}
9. System auto-completes when fully paid
10. Member can now get new loan
```

---

## 📚 For Detailed Information

- **Setup Guide**: See detailed environment setup and database configuration in project files
- **API Reference**: Full endpoint documentation with request/response examples at `/docs`
- **Development**: Refer to inline code comments and docstrings
- **Features**: See complete feature list and business rules in documentation

---

## 🔗 Useful Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Pydantic Validation](https://docs.pydantic.dev/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [JWT Authentication](https://python-jose.readthedocs.io/)

---

## ⚡ Performance Tips

- Responses typically < 100ms
- Database queries indexed on foreign keys
- Connection pooling enabled
- Use pagination for large result sets
- Consider caching policies (rarely change)

---

## 🌱 Database Seeding

Use the included seeding CLI to load deterministic development data:

```bash
# Seed all stages
python seed.py

# Run DB readiness checks only
python seed.py --preflight-only

# Reset seeded tables then reseed
python seed.py --reset

# Seed only selected stages
python seed.py --only cooperatives,members,policies

# Seed larger member pools
python seed.py --members-per-coop 5
```

Seed stages:

- cooperatives
- members
- policies
- contributions
- loans
- payments
- scenarios

Safety guard:

- The seeder refuses to run when `APP_ENV`, `ENVIRONMENT`, `FASTAPI_ENV`, or `STAGE` indicates `prod` or `production`.
- Override intentionally with:

```bash
python seed.py --allow-production
```

Notes:

- Seeding is idempotent and can be re-run safely.
- Use `--reset` for a clean local development cycle.
- Seeding runs DB preflight checks first (connectivity + required tables).

---

## 📄 License

See LICENSE file for details.

## 👤 Author

Final Project - Cooperative Management System

## 🤝 Contributing

Found a bug or want a feature? Please open an issue or submit a pull request!