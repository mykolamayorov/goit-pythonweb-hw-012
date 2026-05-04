"""
SQLAlchemy models.

This module defines the database models used by the application.

Models:
- User: application user with authentication/authorization fields
- Contact: contact entity scoped to a specific user

Notes:
- Users have roles: "user" or "admin".
- Contacts always belong to a user via user_id foreign key.
- Refresh tokens are stored as a hash (refresh_token_hash) for security.
"""

from datetime import date

from sqlalchemy import String, Date, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    User model.

    Fields:
    - id: Primary key
    - email: Unique user email
    - hashed_password: Hashed password
    - is_verified: Email verification flag
    - avatar_url: Cloudinary URL or default avatar URL
    - refresh_token_hash: SHA-256 hash of refresh token (rotation support)
    - role: Role string ("user" or "admin")

    Relationships:
    - contacts: List of contacts owned by this user
    """

    __tablename__ = "users"
    __table_args__ = ()  # important for Sphinx autodoc import stability

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    refresh_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")

    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Contact(Base):
    """
    Contact model.

    Fields:
    - id: Primary key
    - first_name: Contact first name
    - last_name: Contact last name
    - email: Contact email
    - phone: Contact phone
    - birthday: Date of birth
    - extra_data: Optional notes
    - user_id: Owner user id (FK to users.id)

    Relationship:
    - user: Owner User
    """

    __tablename__ = "contacts"
    __table_args__ = ()  # important for Sphinx autodoc import stability

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    first_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)

    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    extra_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="contacts")