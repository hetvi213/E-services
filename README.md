# Krishi E-Government Services Portal

A responsive Flask and Bootstrap 5 portal connected to the existing `gov_services` MySQL schema. It reads active records from `service` and stores enquiries in `application`.

## Local setup

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and enter your local MySQL credentials. Flask loads `.env` automatically when `python-dotenv` is installed. You can configure individual `MYSQL_*` values or provide a complete URI:

   ```text
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://username:password@127.0.0.1:3306/gov_services?charset=utf8mb4
   ```

   URL-encode special characters in usernames/passwords when using the complete URI. The individual environment variables are safely encoded by `config.py`.

3. Start the app:

   ```powershell
   flask --app app run --debug
   ```

Open `http://127.0.0.1:5000`. The home page shows the first six active services; the catalog shows all active services alphabetically.

## Structure

- `app.py` - development entry point
- `config.py` - environment-driven MySQL connection
- `krishi_portal/models.py` - SQLAlchemy models
- `krishi_portal/routes.py` - page routes and enquiry handling
- `krishi_portal/templates/` - Jinja templates
- `krishi_portal/static/` - custom styling
