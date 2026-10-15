# ShopEase — Online Shopping System

A beginner-friendly full-stack college project built with Python Flask, HTML, CSS, JavaScript, and SQLite. It includes registration/login, product search, shopping cart, checkout using Cash on Delivery, order history, and an admin dashboard.

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- Internet connection for the sample product photos (optional)

## Run on Windows / VS Code
1. Extract the ZIP file.
2. Open the `online_shopping_project` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again. Or use `.\.venv\Scripts\python.exe -m pip ...` without activation.
6. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
7. Start the website:
   ```powershell
   py app.py
   ```
8. Open `http://127.0.0.1:5000` in Edge or Chrome.

## Demo admin account
- Email: `admin@shop.local`
- Password: `Admin123!`

Use **Admin** in the navigation bar to add/edit products and update order status. Change the demo password and secret key before deploying anywhere public.

## Database
The app uses SQLite by default and automatically creates `instance/shop.db` on first run. This is intentional so the project works without installing a separate database server. To use MySQL later, install a MySQL driver and change `DATABASE_URL` to a suitable SQLAlchemy MySQL URL.

## Project structure
- `app.py` — Flask backend, database models, and routes
- `templates/` — HTML pages
- `static/css/style.css` — responsive styling
- `static/js/main.js` — small frontend interactions
- `requirements.txt` — Python dependencies

## Included functionality
- Register, login, logout (passwords are hashed)
- Product list, search, category filter, product details
- Add/update/remove cart items
- Login-protected checkout and order history
- Cash on Delivery demo checkout
- Admin product CRUD and order status updates
- Stock validation and stock deduction when an order is placed

## Important
This is an educational starter project, not production-ready commerce software. Before public deployment add CSRF protection, rate limiting, email verification/password reset, secure production configuration, HTTPS, stronger validation, backups, and a real payment provider integration. The built-in demo admin credentials are for local testing only.
