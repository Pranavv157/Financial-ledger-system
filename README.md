# 💳 Financial Ledger System

A production-inspired financial ledger backend built with Django and PostgreSQL that demonstrates how modern payment systems maintain correctness, consistency, auditability, and concurrency safety.

This project implements core fintech patterns such as double-entry accounting, transactional integrity, idempotent transfers, reconciliation, audit logging, and transaction reversals.

---

## 🚀 Why This Project?

Financial systems cannot afford:

- Double spending
- Lost updates
- Partial transactions
- Balance inconsistencies
- Missing audit trails

This project focuses on solving those problems using real-world backend engineering practices.

---

# 🏗 Architecture

```text
Client
   │
   ▼
REST API Layer
   │
   ▼
Service Layer
   │
   ├── Validation
   ├── Business Rules
   ├── Idempotency
   ├── Balance Checks
   └── Transfer Processing
   │
   ▼
PostgreSQL
```

The codebase follows a layered architecture:

```text
Views
  ↓
Services
  ↓
Selectors
  ↓
Models
```

This keeps business logic isolated from API and database concerns.

---

# ⚙️ Core Features

## 💸 Money Transfers

Supports secure account-to-account transfers with:

- Input validation
- Balance validation
- Atomic processing
- Idempotency protection
- Audit logging

---

## 📒 Double Entry Accounting

Every transfer generates balanced ledger entries.

```text
Debit  = Credit
```

Example:

```text
Account A  → Debit 100
Account B  → Credit 100
```

This guarantees financial correctness.

---

## 🔒 ACID Transactions

All transfers execute inside:

```python
transaction.atomic()
```

Guarantees:

- All-or-nothing execution
- No partial updates
- Automatic rollback on failure

---

## ⚡ Concurrency Protection

To prevent race conditions and double spending:

```python
select_for_update()
```

is used to lock accounts during transfers.

Benefits:

- Prevents lost updates
- Prevents balance corruption
- Handles concurrent requests safely

---

## 🛡 Idempotency Protection

Every transfer uses a unique:

```text
reference_id
```

Duplicate requests return the existing transaction instead of creating a new one.

This prevents accidental double charges caused by:

- Network retries
- Client retries
- Duplicate submissions

---

## 📊 Cached Balance Strategy

The system maintains two balance sources:

### Source of Truth

```text
TransactionEntry
```

Immutable ledger records.

### Cached Balance

```text
LedgerAccount.balance
```

Used for fast balance retrieval.

Benefits:

- O(1) balance reads
- Ledger-backed correctness

---

## 🔍 Reconciliation System

Financial systems periodically verify that:

```text
Cached Balance
      ==
Ledger Balance
```

This project includes reconciliation jobs that:

- Recompute balances from ledger entries
- Detect inconsistencies
- Automatically repair corrupted balances
- Generate audit records

---

## 🔁 Transaction Reversals

Transactions are never deleted.

Instead, reversals create compensating ledger entries.

Example:

```text
Original:
A → B : 100

Reversal:
B → A : 100
```

This preserves a complete audit trail.

---

## 🧾 Audit Logging

Critical operations are recorded:

- Transfers
- Reversals
- Reconciliation corrections

Provides operational traceability and debugging support.

---

# 🧠 Engineering Challenges Solved

| Problem | Solution |
|----------|----------|
| Race Conditions | Row-Level Locking |
| Lost Updates | ACID Transactions |
| Double Spending | Idempotency Keys |
| Partial Transfers | Atomic Transactions |
| Balance Corruption | Reconciliation |
| Missing Audit Trail | Structured Audit Logs |
| Duplicate Requests | Reference-Based Idempotency |

---

# 🧪 Testing

The project includes automated tests covering:

### Transfer Processing

- Successful transfers
- Insufficient funds
- Invalid transfers
- Idempotency behavior

### Consistency

- Ledger balance correctness
- Cached balance correctness
- Reconciliation repair logic

### Reliability

- Atomic rollback verification
- Transaction reversal validation

---

# 📈 Concurrency Testing

Load tested using Locust to validate:

- Concurrent transfer processing
- Row-level locking behavior
- Balance consistency
- Transaction correctness under load

Verification performed after testing:

```text
Ledger Balance == Cached Balance
```

for all accounts.

---

# 📡 API Endpoints

## Create Transfer

```http
POST /ledger/transfers/
```

Example:

```json
{
    "sender_id": 1,
    "receiver_id": 2,
    "amount": "100",
    "reference_id": "uuid"
}
```

---

## Get Account Balance

```http
GET /ledger/accounts/{id}/balance/
```

---

## Get Transaction History

```http
GET /ledger/accounts/{id}/transactions/
```

Supports pagination.

---

## Get Transfer Status

```http
GET /ledger/transfers/{reference_id}/
```

---

# 🛠 Tech Stack

### Backend

- Python
- Django
- Django REST Framework

### Database

- PostgreSQL

### Infrastructure

- Docker
- Docker Compose

### Testing

- Django Test Framework
- Locust

---

# 📂 Project Structure

```text
apps/
│
├── ledger/
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   ├── serializers.py
│   ├── validators.py
│   ├── reconciliation.py
│   ├── ledger_selectors.py
│   └── audit.py
│
└── users/
```

---

# 🚀 Getting Started

### Clone Repository

```bash
git clone <repository-url>
cd ledger_system
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Migrations

```bash
python manage.py migrate
```

### Start Server

```bash
python manage.py runserver
```

---

# 📚 Concepts Demonstrated

- Double Entry Accounting
- ACID Transactions
- Row-Level Locking
- Concurrency Control
- Idempotency
- Reconciliation
- Audit Logging
- Transaction Reversals
- Service Layer Pattern
- Pagination
- Load Testing
- Dockerized Development

---

# 💼 What This Demonstrates

This project showcases the ability to design and implement systems that are:

- Correct
- Consistent
- Auditable
- Concurrency Safe
- Production-Oriented

while applying backend engineering principles commonly used in payment and fintech platforms.

---

## Performance Results

- Load tested with 500 concurrent users using Locust
- Processed 3,400+ transfer requests
- Maintained ledger consistency under concurrent load
- Zero failed financial transactions
- Zero balance mismatches after reconciliation

  
# 👨‍💻 Author

**Pranav Shinde**
