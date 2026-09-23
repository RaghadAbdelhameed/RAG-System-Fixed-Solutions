"""
Run this once to create the first Super Admin account.

    python seed_super_admin.py

It will ask for a name, email, and password, then insert the account
directly (bypassing the temp-password email flow, since there's no admin
yet to have sent it).
"""
import getpass
from app.database import SessionLocal, Base, engine
from app.models import Account, Role
from app.security import hash_password

Base.metadata.create_all(bind=engine)


def main():
    db = SessionLocal()
    try:
        full_name = input("Full name: ").strip()
        email = input("Email: ").strip()
        password = getpass.getpass("Password (min 8 chars): ").strip()

        if db.query(Account).filter(Account.email == email).first():
            print("An account with this email already exists.")
            return

        account = Account(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=Role.super_admin,
            must_change_password=False,
            organization_id=None,
        )
        db.add(account)
        db.commit()
        print(f"✅ Super admin '{full_name}' created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
