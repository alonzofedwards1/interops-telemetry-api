import os
import sqlite3
import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.auth.security import hash_password

DEFAULT_DB_PATH = os.environ.get("USER_DB_PATH", "./users.db")


class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    password_hash: str


class UserStore:
    _instance = None

    def __new__(cls, db_path: str = DEFAULT_DB_PATH):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path
            cls._instance._init_db()
        return cls._instance

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    password_hash TEXT NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_by_email(self, email: str) -> Optional[User]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT id, name, email, role, password_hash FROM users WHERE lower(email)=lower(?)",
                (email,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return User(id=row[0], name=row[1], email=row[2], role=row[3], password_hash=row[4])
        finally:
            conn.close()

    def create_user(self, name: str, email: str, password: str, role: str) -> User:
        new_user = User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            password_hash=hash_password(password),
        )
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO users (id, name, email, role, password_hash) VALUES (?, ?, ?, ?, ?)",
                (new_user.id, new_user.name, new_user.email, new_user.role, new_user.password_hash),
            )
            conn.commit()
            return new_user
        finally:
            conn.close()

    def update_password(self, email: str, new_password: str) -> bool:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "UPDATE users SET password_hash=? WHERE lower(email)=lower(?)",
                (hash_password(new_password), email),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def ensure_seed_user(self) -> None:
        admin_email = "admin@interoplens.io"
        existing = self.get_by_email(admin_email)
        if existing:
            return
        self.create_user(
            name="Interoplens Admin",
            email=admin_email,
            password="admin123",
            role="admin",
        )


def get_user_store() -> UserStore:
    return UserStore()
