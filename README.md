# Billway API (Backend)

The powerful Django REST Framework backend for the **Billway** billing and invoicing application.

## Features

- **Authentication:** Secure JWT-based authentication using `djangorestframework-simplejwt`.
- **Customer Management:** Full CRUD for managing client profiles and contact information.
- **Product & Inventory Management:** 
  - Hierarchical categories.
  - Automated stock tracking and validation.
  - Barcode and tax percentage support.
- **Invoice Engine (Zero-Trust):** 
  - The backend natively calculates all line totals, discounts, and taxes securely without trusting client-side math.
  - Automatically deducts stock upon invoice generation.
  - Generates beautiful, dynamic PDF invoices using `xhtml2pdf`.
- **Payment Ledger:** 
  - Tracks partial and full payments against invoices.
  - Automatically updates invoice statuses (`UNPAID`, `PARTIAL`, `PAID`) using Django Signals.
- **Reporting & Analytics:** 
  - Aggregates sales data, collected revenue, and pending balances.
  - Generates sales trend data using `TruncDate` and ranks top-performing products.

## Tech Stack
- **Python 3.10+**
- **Django 5.1.4**
- **Django REST Framework**
- **SQLite** (Default) / PostgreSQL ready
- **xhtml2pdf** (For Invoice PDF generation)

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shahasil12/billway_api.git
   cd billway_api
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a Superuser (for Admin access):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://127.0.0.1:8000/api/`

## API Endpoints

- `/api/token/` - JWT Authentication
- `/api/customers/` - Customer CRUD
- `/api/categories/` - Category CRUD
- `/api/products/` - Product CRUD
- `/api/invoices/` - Invoice Generation
- `/api/invoices/<id>/pdf/` - Download Invoice PDF
- `/api/payments/` - Payment Ledger
- `/api/reports/` - Analytics and Sales Trends
