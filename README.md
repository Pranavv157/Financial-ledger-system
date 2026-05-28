# 💳 Ledger System — Scalable Financial Backend

A production-style financial ledger system built with Django that simulates real-world payment infrastructure.
It focuses on **correctness, consistency, scalability, and auditability** — the same principles used in modern fintech systems.

---

## 🚀 Overview

This project implements a **double-entry accounting system** with:

* Safe money transfers
* Cached balances for performance
* Reconciliation for consistency
* Transaction reversals (refunds)
* Fee handling (platform revenue)
* Audit logging for traceability
* Async processing for scalability

---

## 🧠 Core Principles

### 1. Double Entry Accounting

Every transaction creates:

* **Debit entry**
* **Credit entry**

```
Total Debit = Total Credit
```

This ensures financial correctness.

---

### 2. Ledger as Source of Truth

* `TransactionEntry` → immutable, append-only ledger ✅
* `LedgerAccount.balance` → cached value ⚡

If mismatch occurs:

```
Ledger (truth) > Cached balance (derived)
```

---

### 3. ACID Transactions

All transfers use:

* `transaction.atomic()`
* `select_for_update()` (row-level locking)

Ensures:

* No race conditions
* No lost updates
* No partial transfers

---

## 🏗 System Architecture

```
API Layer (Views)
        ↓
Service Layer (Business Logic)
        ↓
Selectors (Query Layer)
        ↓
Models (Database)
```

---

## 📦 Features Implemented

### ✅ Phase 1 — Production-Ready Basics

* Transfer API
* Account balance API
* Transaction history API
* Pagination
* Structured error handling
* Logging
* Unit testing

---

### ⚡ Phase 2 — Performance & Consistency

* Cached balance (`O(1)` reads)
* Row-level locking
* Reconciliation system
* Consistency validation

---

### 💰 Phase 3 — Financial Features

#### 🔁 Transaction Reversal

* No deletion (immutable ledger)
* Creates compensating transaction

#### 💸 Fee System

* Platform account collects fees
* Multi-entry transaction:

  ```
  Sender → DEBIT (amount + fee)
  Receiver → CREDIT (amount)
  Platform → CREDIT (fee)
  ```

#### 🧾 Audit Logging

Tracks:

* Transfers
* Reversals
* Reconciliation fixes

Stored as structured JSON metadata.

---

### 🚀 Phase 4 — Scaling (In Progress)

* Async processing with Celery + Redis
* Background task execution
* Retry mechanism

---

## 🔄 Transfer Flow

```
1. Validate input
2. Idempotency check
3. Lock accounts
4. Check balance
5. Create transaction (PENDING)
6. Create ledger entries
7. Update cached balances
8. Mark SUCCESS
9. Log audit event
```

---

## ⚠️ Key Problems Solved

| Problem              | Solution            |
| -------------------- | ------------------- |
| Race conditions      | Row-level locking   |
| Lost updates         | Atomic transactions |
| Double spending      | Idempotency keys    |
| Slow balance queries | Cached balance      |
| Data inconsistency   | Reconciliation job  |
| Fraud/debugging gaps | Audit logs          |

---

## 🧪 Testing

Includes unit tests for:

* Successful transfers
* Insufficient funds
* Idempotency
* Cached balance correctness
* Atomic rollback safety

---

## 📊 Logging Strategy

| Level     | Purpose                |
| --------- | ---------------------- |
| INFO      | Successful operations  |
| WARNING   | Business rule failures |
| ERROR     | Data inconsistencies   |
| EXCEPTION | System failures        |

---

## ⚡ Async Processing (Celery)

```
API → Queue → Worker → DB
```

Benefits:

* Fast API response
* Retry on failure
* Better scalability

---

## 🛠 Tech Stack

* Python (Django)
* Django REST Framework
* PostgreSQL (recommended)
* Redis (queue)
* Celery (async tasks)

---

## 🚀 How to Run

### 1. Clone repo

```bash
git clone <repo-url>
cd ledger_system
```

### 2. Setup environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Migrate DB

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run server

```bash
python manage.py runserver
```

### 5. Start Redis

```bash
redis-server
```

### 6. Start Celery worker

```bash
celery -A ledger_system worker --loglevel=info
```

---

## 🔮 Upcoming Features

* Idempotency safety in async systems
* Rate limiting
* Fraud detection hooks
* Webhooks/events
* Distributed transactions
* Monitoring dashboards

---

## 🧠 What This Project Demonstrates

* Backend system design
* Financial correctness guarantees
* Concurrency handling
* Performance optimization
* Production-grade architecture
* Real-world fintech patterns

---

## 💼 Why This Matters

It demonstrates the ability to design:

```
Correct + Scalable + Auditable systems
```

---

## 👨‍💻 Author

Built as a deep dive into backend engineering and financial system design.

---

## 📌 Final Note


This is a **system design project implemented in code**.
