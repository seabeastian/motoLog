from app import create_app, db, Motorcycle

app = create_app()

with app.app_context():
    db.create_all()  # ✅ Ensures the motorcycle table exists
    m1 = Motorcycle(make="Harley-Davidson", model="Street Glide", year=2023, mileage=12000)
    db.session.add(m1)
    db.session.commit()
    print("✅ Sample motorcycle added successfully.")