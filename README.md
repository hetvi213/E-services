# Krishi E-Government Services Portal

A Flask web portal for discovering government services, submitting service
enquiries, tracking applications, and managing requests through an administrator
dashboard.

## Features

- Browse and search government services
- View service details, required documents, pricing, and availability
- Register and sign in as a citizen
- Submit enquiries and track application progress
- Contact the support team through email-enabled forms
- Admin dashboard for reviewing applications and updating their status
- Completion uploads and email notifications for citizens
- Service management, admin profile settings, and application analytics
- Responsive Bootstrap-based interface

## Technology

- Python 3 and Flask
- Flask-SQLAlchemy
- MySQL with PyMySQL
- Jinja templates, Bootstrap 5, and custom CSS
- SMTP email notifications

## Prerequisites

- Python 3.10 or newer
- MySQL 8 or a compatible MySQL server
- An existing `gov_services` database containing the `service`, `users`, and
  `application` tables expected by [`krishi_portal/models.py`](krishi_portal/models.py)

The application automatically creates the `admin_accounts` and
`application_completions` tables if they do not exist. It does not create the
complete database schema or seed the service catalog.

## Local Setup

1. Clone the repository and enter the project directory:

   ```powershell
   git clone https://github.com/hetvi213/E-services.git
   cd E-services
   ```

2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Update `.env` with your database credentials, administrator login, contact
   details, and optional SMTP settings.

6. Start the development server:

   ```powershell
   flask --app app run --debug
   ```

Open <http://127.0.0.1:5000> in a browser.

## Configuration

The app loads settings from `.env` through `python-dotenv`. The local `.env`
file is ignored by Git and must not be committed.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs Flask sessions and flash messages |
| `MYSQL_USER` | MySQL username |
| `MYSQL_PASSWORD` | MySQL password |
| `MYSQL_HOST` | MySQL server host |
| `MYSQL_PORT` | MySQL server port |
| `MYSQL_DATABASE` | Database name |
| `SQLALCHEMY_DATABASE_URI` | Optional complete connection URI that overrides the individual MySQL values |
| `ADMIN_LOGIN_EMAIL` | Initial administrator login email |
| `ADMIN_LOGIN_PASSWORD` | Initial administrator login password |
| `ADMIN_EMAIL` | Address that receives contact and enquiry notifications |
| `SMTP_HOST`, `SMTP_PORT` | Outgoing mail server |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Outgoing mail credentials |
| `SMTP_USE_TLS`, `SMTP_USE_SSL` | Mail transport security switches |
| `PORTAL_ADDRESS`, `PORTAL_EMAIL`, `PORTAL_PHONE` | Public contact details |

You can use a complete database URI instead of the individual `MYSQL_*`
settings:

```text
SQLALCHEMY_DATABASE_URI=mysql+pymysql://username:password@127.0.0.1:3306/gov_services?charset=utf8mb4
```

URL-encode special characters in the username or password when using a complete
URI. Values assembled from the individual variables are encoded by `config.py`.

## Administrator Access

On the first startup, the app creates an administrator account from
`ADMIN_LOGIN_EMAIL` and `ADMIN_LOGIN_PASSWORD` if no administrator exists. Use
the regular **Login** page, then open `/admin` after authentication.

Changing those environment variables later does not replace an existing admin
account. An authenticated administrator can update their details from the
settings page.

## Project Structure

```text
E-services/
|-- app.py                         # Development entry point
|-- config.py                      # Environment-driven application settings
|-- requirements.txt               # Python dependencies
|-- .env.example                   # Configuration template
`-- krishi_portal/
    |-- __init__.py                # Flask application factory
    |-- models.py                  # SQLAlchemy models
    |-- routes.py                  # Citizen and administrator routes
    |-- mailer.py                  # SMTP email helpers
    |-- templates/                 # Jinja page templates
    `-- static/                    # CSS, images, and generated uploads
```

## Security Notes

- Replace all placeholder secrets and passwords before deployment.
- Use a dedicated database user with only the permissions the app needs.
- For Gmail SMTP, use an app password rather than an account password.
- Disable Flask debug mode in production and serve the application through a
  production WSGI server.

## License

No license has been specified for this project.
