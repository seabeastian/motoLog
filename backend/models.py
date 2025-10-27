from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Initialize extensions (bound in app.py)
db = SQLAlchemy()
bcrypt = Bcrypt()


# ------------------------------
# USER MODEL
# ------------------------------
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relationships
    motorcycles = db.relationship("Motorcycle", backref="user", lazy=True)
    trips = db.relationship("Trip", backref="user", lazy=True)

    # Password utilities
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


# ------------------------------
# MOTORCYCLE MODEL
# ------------------------------
class Motorcycle(db.Model):
    __tablename__ = "motorcycle"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    make = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(80), nullable=True)

    # Relationships
    maintenance_records = db.relationship("Maintenance", backref="motorcycle", lazy=True)
    trips = db.relationship("Trip", backref="motorcycle", lazy=True)


# ------------------------------
# MAINTENANCE MODEL
# ------------------------------
class Maintenance(db.Model):
    __tablename__ = "maintenance"

    id = db.Column(db.Integer, primary_key=True)
    motorcycle_id = db.Column(db.Integer, db.ForeignKey("motorcycle.id"), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    cost = db.Column(db.Float, nullable=True)
    mileage = db.Column(db.Integer, nullable=True)


# ------------------------------
# TRIP MODEL
# ------------------------------
class Trip(db.Model):
    __tablename__ = "trip"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    motorcycle_id = db.Column(db.Integer, db.ForeignKey("motorcycle.id"), nullable=False)
    start_location = db.Column(db.String(120), nullable=False)
    end_location = db.Column(db.String(120), nullable=False)
    distance_km = db.Column(db.Float, nullable=True)
    date = db.Column(db.String(50), nullable=False)