from app import app, db, User, bcrypt

with app.app_context():
    hashedpassword = bcrypt.generate_password_hash("admin").decode("utf-8")
    user = User(
        name="admin",
        username="admin",
        email="admin@gmail.com",
        password=hashedpassword,
        phone_number="9876543210",
        is_superuser=True,
    )
    db.session.add(user)
    db.session.commit()
    #     db.create_all()
    print("Created")
