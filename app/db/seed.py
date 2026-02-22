from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.domain.models import Role, User, Credential
from app.services.credential_service import CredentialService
import os
import sys


def main():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        for r in ["admin", "user"]:
            existing = db.query(Role).filter(Role.name == r).one_or_none()
            if not existing:
                db.add(Role(name=r))
        db.commit()
        if os.getenv("ENVIRONMENT", "local") == "local":
            admin = db.query(User).filter(User.email == "admin@example.com").one_or_none()
            if not admin:
                admin = User(email="admin@example.com", display_name="Admin", is_active=True)
                db.add(admin)
                db.commit()
                db.refresh(admin)
            admin_role = db.query(Role).filter(Role.name == "admin").one_or_none()
            if admin_role and admin_role not in admin.roles:
                admin.roles.append(admin_role)
                db.commit()
            service = CredentialService(db)
            existing_password = (
                db.query(Credential)
                .filter(Credential.user_id == admin.id, Credential.label == "password", Credential.revoked.is_(False))
                .one_or_none()
            )
            password_plaintext = None
            force_pw = os.getenv("ADMIN_BOOTSTRAP_PASSWORD_FORCE", "").lower() in ("1", "true", "yes")
            if force_pw or not existing_password:
                configured_pw = os.getenv("ADMIN_BOOTSTRAP_PASSWORD")
                if configured_pw:
                    password_plaintext = configured_pw
                else:
                    password_plaintext = service.generate_secret()
                service.set_password(admin.id, password_plaintext)
                db.commit()
            existing_bootstrap = (
                db.query(Credential)
                .filter(Credential.user_id == admin.id, Credential.label == "bootstrap", Credential.revoked.is_(False))
                .one_or_none()
            )
            api_key_plaintext = None
            if not existing_bootstrap:
                cred_id, api_key_plaintext = service.create(admin.id, "bootstrap")
                db.commit()
            if password_plaintext:
                sys.stdout.write(f"BOOTSTRAP_ADMIN_EMAIL={admin.email}\n")
                sys.stdout.write(f"BOOTSTRAP_ADMIN_PASSWORD={password_plaintext}\n")
            if api_key_plaintext:
                sys.stdout.write(f"BOOTSTRAP_ADMIN_API_KEY={api_key_plaintext}\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
