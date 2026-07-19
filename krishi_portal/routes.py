import mimetypes
from pathlib import Path
from functools import wraps
from hmac import compare_digest
from uuid import uuid4

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from krishi_portal import db
from krishi_portal.mailer import send_admin_email, send_email
from krishi_portal.models import AdminAccount, Application, ApplicationCompletion, Service, User


main_bp = Blueprint("main", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to submit a service enquiry.", "warning")
            return redirect(url_for("main.login", next=request.full_path.rstrip("?")))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("is_admin"):
            flash("Administrator access is required.", "warning")
            return redirect(url_for("main.login", next=request.path))
        if not session.get("admin_id"):
            admin = db.session.scalar(select(AdminAccount).order_by(AdminAccount.id).limit(1))
            if admin is None:
                session.clear()
                flash("Administrator account configuration is unavailable.", "danger")
                return redirect(url_for("main.login"))
            session["admin_id"] = admin.id
        return view(**kwargs)

    return wrapped_view


def password_matches(user, submitted_password):
    """Support Werkzeug hashes and migrate a legacy plain-text password on login."""
    try:
        if check_password_hash(user.password, submitted_password):
            return True
    except (ValueError, TypeError):
        pass

    if compare_digest(user.password or "", submitted_password):
        user.password = generate_password_hash(submitted_password)
        db.session.commit()
        return True
    return False


@main_bp.route("/")
def home():
    featured_services = db.session.scalars(
        select(Service)
        .order_by(Service.service_id)
        .limit(6)
    ).all()
    stats = {
        "services": db.session.scalar(select(func.count(Service.service_id))) or 0,
        "applications": db.session.scalar(select(func.count(Application.id))) or 0,
        "users": db.session.scalar(select(func.count(User.user_id))) or 0,
    }
    return render_template("home.html", services=featured_services, stats=stats)


@main_bp.route("/services")
def services():
    query = request.args.get("q", "").strip()
    statement = select(Service)
    if query:
        search_term = f"%{query}%"
        statement = statement.where(
            or_(Service.title.ilike(search_term), Service.short_desc.ilike(search_term))
        )
    all_services = db.session.scalars(statement.order_by(Service.service_id)).all()
    return render_template("services.html", services=all_services, query=query)


@main_bp.route("/services/<int:service_id>")
def service_detail(service_id):
    service = db.get_or_404(Service, service_id)
    return render_template("service_detail.html", service=service)


@main_bp.route("/gallery")
def gallery():
    all_services = db.session.scalars(select(Service).order_by(Service.service_id)).all()
    return render_template("gallery.html", services=all_services)


@main_bp.route("/my-applications")
@login_required
def my_applications():
    applications = db.session.scalars(
        select(Application)
        .where(Application.user_id == g.user.user_id)
        .order_by(Application.created_at.desc())
    ).all()
    return render_template("my_applications.html", applications=applications)


@main_bp.route("/about-us")
def about():
    return render_template("about.html")


@main_bp.route("/documents")
def documents():
    all_services = db.session.scalars(select(Service).order_by(Service.service_id)).all()
    return render_template("documents.html", services=all_services)


@main_bp.route("/contact-us", methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all((name, email, phone, subject, message)):
            flash("Please complete all required fields.", "danger")
        else:
            delivered = send_admin_email(
                f"Contact request: {subject}",
                f"Name: {name}\nEmail: {email}\nPhone: {phone}\nSubject: {subject}\n\nMessage:\n{message}",
                reply_to=email,
            )
            if delivered:
                flash("Thank you. Your message has been sent to our support team.", "success")
                return redirect(url_for("main.contact_us"))
            flash("We could not send your message right now. Please use the email or phone number below.", "warning")

    return render_template("contact_us.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user or session.get("is_admin"):
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin = db.session.scalar(select(AdminAccount).where(AdminAccount.email == email))
        if admin and check_password_hash(admin.password_hash, password):
            session.clear()
            session["is_admin"] = True
            session["admin_id"] = admin.id
            flash("Welcome to the administrator dashboard.", "success")
            return redirect(url_for("main.admin_dashboard"))

        user = db.session.scalar(select(User).where(User.email == email))

        if user is None or not password_matches(user, password):
            flash("Invalid email address or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user.user_id
            flash(f"Welcome back, {user.name}.", "success")
            next_url = request.form.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("main.home")
            return redirect(next_url)

    return render_template("login.html", next_url=request.args.get("next", ""))


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        existing_user = db.session.scalar(select(User).where(User.email == email))
        if not all((name, email, phone, password, confirm_password)):
            flash("Please complete all required fields.", "danger")
        elif existing_user:
            flash("An account already exists for this email address. Please log in.", "warning")
        elif password != confirm_password:
            flash("The passwords do not match.", "danger")
        elif len(password) < 8:
            flash("Your password must contain at least 8 characters.", "danger")
        else:
            user = User(
                name=name,
                email=email,
                phone=phone,
                password=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            session.clear()
            session["user_id"] = user.user_id
            flash(f"Welcome, {user.name}. Your account has been created.", "success")
            return redirect(url_for("main.home"))

    return render_template("register.html")


@main_bp.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))


@main_bp.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "services": db.session.scalar(select(func.count(Service.service_id))) or 0,
        "applications": db.session.scalar(select(func.count(Application.id))) or 0,
        "users": db.session.scalar(select(func.count(User.user_id))) or 0,
        "pending": db.session.scalar(
            select(func.count(Application.id)).where(Application.status != "Completed")
        ) or 0,
    }
    applications = db.session.scalars(
        select(Application).order_by(Application.created_at.desc()).limit(50)
    ).all()
    return render_template("admin_dashboard.html", stats=stats, applications=applications)


@main_bp.post("/admin/applications/<int:application_id>/status")
@admin_required
def update_application_status(application_id):
    application = db.get_or_404(Application, application_id)
    status = request.form.get("status", "")
    if status not in {"Enquiry", "Submitted", "Completed"}:
        flash("Invalid application status.", "danger")
        return redirect(url_for("main.admin_dashboard"))

    if status != "Completed":
        application.status = status
        db.session.commit()
        flash(f"Application marked as {status.lower()}.", "success")
        return redirect(url_for("main.admin_dashboard"))

    attachment = None
    comment = request.form.get("completion_comment", "").strip()
    uploaded = request.files.get("completion_file")
    completion = application.completion or ApplicationCompletion(application=application)
    if uploaded and uploaded.filename:
        filename = secure_filename(uploaded.filename)
        extension = Path(filename).suffix.lower()
        if extension not in {".pdf", ".png", ".jpg", ".jpeg"}:
            flash("Only PDF, PNG, JPG, and JPEG completion files are allowed.", "danger")
            return redirect(url_for("main.admin_dashboard"))
        completion_dir = Path(current_app.static_folder) / "completions"
        completion_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{application.app_id}_{filename}"
        file_path = completion_dir / stored_name
        uploaded.save(file_path)
        application.document_path = f"completions/{stored_name}"
        completion.file_path = application.document_path
        completion.original_filename = filename
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        attachment = (str(file_path), filename, mime_type)

    completion.comment = comment or None
    if completion.id is None:
        db.session.add(completion)
    application.status = "Completed"
    db.session.commit()

    comment_text = f"\n\nAdministrator comment:\n{comment}" if comment else ""
    delivered = send_email(
        application.email,
        f"Application completed: {application.app_id}",
        f"Hello {application.name},\n\nYour application for {application.service_name} "
        f"has been completed.\nApplication ID: {application.app_id}{comment_text}"
        f"\n\nRegards,\nKrishi E-Government Services",
        attachment=attachment,
    )
    flash(
        "Application completed and the citizen was emailed." if delivered
        else "Application completed, but the citizen email could not be delivered.",
        "success" if delivered else "warning",
    )
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/analytics")
@admin_required
def admin_analytics():
    rows = db.session.execute(
        select(
            Application.service_name,
            func.count(Application.id),
            func.sum(case((Application.status == "Completed", 1), else_=0)),
        ).group_by(Application.service_name).order_by(Application.service_name)
    ).all()
    chart = {
        "labels": [row[0] for row in rows],
        "enquiries": [int(row[1] or 0) for row in rows],
        "completed": [int(row[2] or 0) for row in rows],
    }
    return render_template("admin_analytics.html", chart=chart)


@main_bp.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    admin = db.get_or_404(AdminAccount, session["admin_id"])
    if request.method == "POST":
        action = request.form.get("action")
        if action == "profile":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            if not name or not email:
                flash("Name and email are required.", "danger")
            else:
                admin.name, admin.email = name, email
                db.session.commit()
                flash("Administrator profile updated.", "success")
        elif action == "password":
            old_password = request.form.get("old_password", "")
            new_password = request.form.get("new_password", "")
            if not check_password_hash(admin.password_hash, old_password):
                flash("Current password is incorrect.", "danger")
            elif len(new_password) < 8:
                flash("New password must contain at least 8 characters.", "danger")
            else:
                admin.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash("Administrator password updated.", "success")
        return redirect(url_for("main.admin_settings"))
    services = db.session.scalars(select(Service).order_by(Service.service_id)).all()
    return render_template("admin_settings.html", admin=admin, services=services)


@main_bp.route("/admin/services/<int:service_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_service(service_id):
    service = db.get_or_404(Service, service_id)
    if request.method == "POST":
        service.title = request.form.get("title", "").strip()
        service.short_desc = request.form.get("short_desc", "").strip()
        service.documents = request.form.get("documents", "").strip()
        service.is_active = request.form.get("is_active") == "on"
        image = request.files.get("image")
        if image and image.filename:
            filename = secure_filename(image.filename)
            if Path(filename).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                flash("Service image must be PNG, JPG, JPEG, or WEBP.", "danger")
                return render_template("admin_edit_service.html", service=service)
            image.save(Path(current_app.static_folder) / "images" / filename)
            service.image = filename
        db.session.commit()
        flash("Service updated successfully.", "success")
        return redirect(url_for("main.admin_settings"))
    return render_template("admin_edit_service.html", service=service)


@main_bp.post("/admin/services/<int:service_id>/delete")
@admin_required
def admin_delete_service(service_id):
    service = db.get_or_404(Service, service_id)
    try:
        db.session.delete(service)
        db.session.commit()
        flash("Service deleted.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("This service has applications and cannot be deleted.", "warning")
    return redirect(url_for("main.admin_settings"))


@main_bp.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    all_services = db.session.scalars(select(Service).order_by(Service.service_id)).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()
        service_id = request.form.get("service_id", type=int)

        selected_service = db.session.get(Service, service_id) if service_id else None
        if not all((name, email, mobile, message, selected_service)):
            flash("Please complete all required fields and select a service.", "danger")
        else:
            application = Application(
                app_id=f"KRI-{uuid4().hex[:12].upper()}",
                user_id=g.user.user_id,
                name=name,
                email=email,
                mobile=mobile,
                service_id=selected_service.service_id,
                service_name=selected_service.title,
                total_amount=selected_service.base_price or 0,
                status="Enquiry",
                upload_text=message,
                payment_status="Pending",
                service=selected_service,
            )
            db.session.add(application)
            db.session.commit()
            delivered = send_admin_email(
                f"New service enquiry: {application.app_id}",
                f"Application ID: {application.app_id}\n"
                f"User ID: {g.user.user_id}\nName: {name}\nEmail: {email}\nMobile: {mobile}\n"
                f"Service: {selected_service.title}\n\nEnquiry:\n{message}",
                reply_to=email,
            )
            if delivered:
                flash("Your enquiry was saved and emailed to the administration team.", "success")
            else:
                flash("Your enquiry was saved, but the email notification could not be sent.", "warning")
            return redirect(url_for("main.contact"))

    return render_template("contact.html", services=all_services)
