"""
CRUD operations for contacts.

This module contains database operations for Contact entities:
- create contact (scoped to user_id)
- list contacts (scoped to user_id) with optional search filters
- get contact by id/email (scoped to user_id)
- update and delete contact
- list upcoming birthdays (scoped to user_id)

Notes:
- All queries are scoped by user_id to enforce "only own contacts" rule.
- Search uses case-insensitive partial matches (ilike).
- Upcoming birthdays compares month/day and works across year boundary.
"""

from datetime import date, timedelta

from sqlalchemy import and_, extract, or_
from sqlalchemy.orm import Session

from app.models import Contact
from app.schemas import ContactCreate, ContactUpdate


def create_contact(db: Session, user_id: int, contact_in: ContactCreate) -> Contact:
    """
    Create a new contact for a given user.

    :param db: SQLAlchemy DB session.
    :param user_id: Owner user id for the contact.
    :param contact_in: ContactCreate payload.
    :return: Created Contact instance.
    """
    contact = Contact(**contact_in.model_dump(), user_id=user_id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contacts(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    """
    List contacts for a specific user with optional search and pagination.

    Search parameters are case-insensitive partial matches:
    - first_name
    - last_name
    - email

    :param db: SQLAlchemy DB session.
    :param user_id: Current user's id (scope).
    :param skip: Pagination offset.
    :param limit: Pagination limit.
    :param first_name: Optional first name filter.
    :param last_name: Optional last name filter.
    :param email: Optional email filter.
    :return: List of contacts belonging to the given user.
    """
    query = db.query(Contact).filter(Contact.user_id == user_id)

    filters = []
    if first_name:
        filters.append(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        filters.append(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        filters.append(Contact.email.ilike(f"%{email}%"))

    if filters:
        query = query.filter(and_(*filters))

    return query.offset(skip).limit(limit).all()


def get_contact_by_id(db: Session, user_id: int, contact_id: int) -> Contact | None:
    """
    Get a contact by id scoped to a given user.

    :param db: SQLAlchemy DB session.
    :param user_id: Current user's id (scope).
    :param contact_id: Contact id.
    :return: Contact instance if found, else None.
    """
    return (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.id == contact_id)
        .first()
    )


def get_contact_by_email(db: Session, user_id: int, email: str) -> Contact | None:
    """
    Get a contact by email scoped to a given user.

    :param db: SQLAlchemy DB session.
    :param user_id: Current user's id (scope).
    :param email: Contact email to search.
    :return: Contact instance if found, else None.
    """
    return (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.email == email)
        .first()
    )


def update_contact(db: Session, contact: Contact, contact_in: ContactUpdate) -> Contact:
    """
    Update a contact with provided fields (partial update supported).

    :param db: SQLAlchemy DB session.
    :param contact: Contact instance to update.
    :param contact_in: ContactUpdate payload (only provided fields are applied).
    :return: Updated Contact instance.
    """
    data = contact_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact: Contact) -> None:
    """
    Delete a contact.

    :param db: SQLAlchemy DB session.
    :param contact: Contact instance to delete.
    :return: None.
    """
    db.delete(contact)
    db.commit()


def get_upcoming_birthdays(db: Session, user_id: int, days: int = 7) -> list[Contact]:
    """
    Get contacts (scoped to user_id) whose birthday falls within the next N days.

    Logic:
    - Compares month/day of birthday independent of year.
    - Works across year boundary (e.g., Dec 30 -> Jan 02).

    :param db: SQLAlchemy DB session.
    :param user_id: Current user's id (scope).
    :param days: Number of days ahead to include.
    :return: List of matching contacts.
    """
    today = date.today()
    upcoming_days = [today + timedelta(days=i) for i in range(days)]

    conditions = [
        and_(
            extract("month", Contact.birthday) == d.month,
            extract("day", Contact.birthday) == d.day,
        )
        for d in upcoming_days
    ]

    return (
        db.query(Contact)
        .filter(Contact.user_id == user_id)
        .filter(or_(*conditions))
        .all()
    )