from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from sqlalchemy import inspect
from models import db, bcrypt, User, Motorcycle, Maintenance, Trip
from datetime import datetime, timedelta


# -----------------------------------------------------
# APP FACTORY
# -----------------------------------------------------
def create_app():
    app = Flask(__name__)
    CORS(app)

    # --- Configuration ---
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///motorcycle.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # ⚠️ Replace in production

    # --- Initialize Extensions ---
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)

    # -------------------------------------------------
    # ROUTES
    # -------------------------------------------------

    @app.route('/')
    def home():
        return jsonify({"message": "Motorcycle Maintenance API is running with Auth!"})

    # ------------------------------
    # USER REGISTRATION
    # ------------------------------
    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password required"}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "User already exists"}), 400

        user = User(username=data.get('username', data['email']), email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "✅ User registered successfully"}), 201

    # ------------------------------
    # USER LOGIN
    # ------------------------------
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if not user or not user.check_password(data.get('password')):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token}), 200

    # ------------------------------
    # USER PROFILE
    # ------------------------------
    @app.route('/profile', methods=['GET'])
    @jwt_required()
    def profile():
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })

    # ------------------------------
    # MOTORCYCLE ROUTES
    # ------------------------------
    @app.route('/motorcycles', methods=['GET', 'POST'])
    @jwt_required()
    def motorcycles_route():
        user_id = int(get_jwt_identity())

        if request.method == 'GET':
            motorcycles = Motorcycle.query.filter_by(user_id=user_id).all()
            result = [
                {
                    "id": m.id,
                    "make": m.make,
                    "model": m.model,
                    "year": m.year,
                    "mileage": m.mileage
                }
                for m in motorcycles
            ]
            return jsonify(result)

        if request.method == 'POST':
            data = request.get_json()
            motorcycle = Motorcycle(
                user_id=user_id,
                make=data["make"],
                model=data["model"],
                year=data.get("year", 0),
                mileage=data.get("mileage", 0)
            )
            db.session.add(motorcycle)
            db.session.commit()
            return jsonify({"message": "✅ Motorcycle added successfully"}), 201

    # ------------------------------
    # MAINTENANCE (Add + Get)
    # ------------------------------
    @app.route('/maintenance/<int:motorcycle_id>', methods=['POST', 'GET'])
    @jwt_required()
    def maintenance(motorcycle_id):
        user_id = int(get_jwt_identity())
        motorcycle = Motorcycle.query.filter_by(id=motorcycle_id, user_id=user_id).first()
        if not motorcycle:
            return jsonify({"error": "Motorcycle not found"}), 404

        if request.method == 'GET':
            records = Maintenance.query.filter_by(motorcycle_id=motorcycle_id).all()
            result = [
                {
                    "id": r.id,
                    "date": r.date,
                    "description": r.description,
                    "cost": r.cost,
                    "mileage": r.mileage
                }
                for r in records
            ]
            return jsonify(result), 200

        if request.method == 'POST':
            data = request.get_json()
            try:
                record = Maintenance(
                    motorcycle_id=motorcycle_id,
                    date=data["date"],
                    description=data["description"],
                    cost=float(data.get("cost", 0)),
                    mileage=int(data.get("mileage", 0))
                )
                db.session.add(record)
                db.session.commit()
                return jsonify({"message": "✅ Maintenance record added successfully"}), 201
            except Exception as e:
                import traceback
                traceback.print_exc()
                return jsonify({"error": str(e)}), 500

    # ------------------------------
    # SERVICE REMINDERS
    # ------------------------------
    @app.route('/reminders', methods=['GET'])
    @jwt_required()
    def service_reminders():
        """Calculate next service mileage/date for each motorcycle."""
        user_id = int(get_jwt_identity())
        motorcycles = Motorcycle.query.filter_by(user_id=user_id).all()
        reminders = []

        for m in motorcycles:
            last_record = (
                Maintenance.query.filter_by(motorcycle_id=m.id)
                .order_by(Maintenance.date.desc())
                .first()
            )

            next_due_mileage = (m.mileage or 0) + 5000
            next_due_date = "N/A"
            last_service_date = "N/A"

            if last_record:
                last_service_date = last_record.date
                try:
                    last_service_dt = datetime.strptime(last_record.date, "%Y-%m-%d")
                    next_due_date = (last_service_dt + timedelta(days=180)).strftime("%Y-%m-%d")
                except Exception:
                    next_due_date = "N/A"
                next_due_mileage = (last_record.mileage or 0) + 5000

            reminders.append({
                "motorcycle": f"{m.make} {m.model}",
                "current_mileage": m.mileage,
                "next_due_mileage": next_due_mileage,
                "next_due_date": next_due_date,
                "last_service": last_service_date,
            })

        return jsonify(reminders), 200

    # ------------------------------
    # WHOAMI
    # ------------------------------
    @app.route('/whoami', methods=['GET'])
    @jwt_required()
    def whoami():
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"id": user.id, "email": user.email, "username": user.username})

    return app


# -----------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        print("📋 Tables:", inspector.get_table_names())
        print("✅ Database tables verified.")
    app.run(host="0.0.0.0", port=5001, debug=True)