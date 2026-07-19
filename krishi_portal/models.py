from datetime import datetime

from krishi_portal import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AdminAccount(db.Model):
    __tablename__ = "admin_accounts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="Administrator")
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Service(db.Model):
    __tablename__ = "service"

    service_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    short_desc = db.Column(db.Text, nullable=False)
    base_price = db.Column(db.Numeric(12, 2), nullable=True)
    documents = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=True)

    # Compatibility properties keep the presentation layer clean and descriptive.
    @property
    def id(self):
        return self.service_id

    @property
    def name(self):
        return self.title

    @property
    def description(self):
        return self.short_desc

    @property
    def image_filename(self):
        """Return only the filename portion of the database image value."""
        if not self.image:
            return None
        return self.image.replace("\\", "/").split("/")[-1]

    @property
    def availability(self):
        """Provide a stable availability label without requiring a schema change."""
        modes = (
            ("online", "Online Available"),
            ("both", "Online + Centre"),
            ("centre", "Centre Only"),
        )
        return modes[(self.service_id - 1) % len(modes)]

    @property
    def service_icon(self):
        icons = {
            1: "bi-passport",
            2: "bi-person-vcard",
            3: "bi-credit-card-2-front",
            4: "bi-shop",
            5: "bi-hearts",
            6: "bi-house-check",
            7: "bi-cash-coin",
            8: "bi-cup-hot",
            9: "bi-building-gear",
            10: "bi-pencil-square",
            11: "bi-receipt-cutoff",
            12: "bi-shield-check",
            13: "bi-person-heart",
            14: "bi-check2-square",
            15: "bi-file-earmark-lock",
            16: "bi-lightbulb",
            17: "bi-people",
            18: "bi-megaphone",
            19: "bi-houses",
            20: "bi-car-front",
            21: "bi-basket",
        }
        return icons.get(self.service_id, "bi-file-earmark-text")

    @property
    def icon_theme(self):
        return ("blue", "red", "green", "gold")[self.service_id % 4]

    @property
    def document_category(self):
        if self.service_id in {4, 8, 9, 11, 15, 17, 18}:
            return "business"
        if self.service_id in {6, 16, 19, 21}:
            return "property"
        return "personal"

    @property
    def document_list(self):
        """Return clean document names from the comma-separated DB value."""
        if not self.documents:
            return []
        return [item.strip() for item in self.documents.split(",") if item.strip()]


class Application(db.Model):
    __tablename__ = "application"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    app_id = db.Column(db.String(100), nullable=False, unique=True)
    service_id = db.Column(db.Integer, db.ForeignKey("service.service_id"), nullable=False)
    service_name = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(50), nullable=False, default="Enquiry")
    upload_text = db.Column(db.Text, nullable=True)
    uploaded_files = db.Column(db.Text, nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)
    document_path = db.Column(db.String(500), nullable=True)
    payment_status = db.Column(db.String(50), nullable=False, default="Pending")
    payment_method = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    service = db.relationship("Service", backref=db.backref("applications", lazy=True))
    user = db.relationship("User", backref=db.backref("applications", lazy=True))
