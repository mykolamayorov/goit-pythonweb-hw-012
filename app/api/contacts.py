"""
Contacts API router.

CRUD endpoints for contacts with the following rules:
- All endpoints require authenticated user (JWT access token).
- Contacts are scoped to the current user (each user can access only their own contacts).
- Email verification is required for contact operations.
- Supports search via query parameters: first_name, last_name, email.
- Provides endpoint for upcoming birthdays in the next N days.

Endpoints (prefix /api/contacts):
- POST   /api/contacts
- GET    /api/contacts
- GET    /api/contacts/{contact_id}
- PUT    /api/contacts/{contact_id}
- DELETE /api/contacts/{contact_id}
- GET    /api/contacts/birthdays?days=7
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import ContactCreate, ContactUpdate, ContactResponse
from app.auth.deps import require_verified_user
from app.models import User

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_in: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    """
    Create a new contact for the current verified user.

    :param contact_in: ContactCreate payload.
    :param db: SQLAlchemy DB session.
    :param current_user: Current verified user (JWT + verified email).
    :return: Created contact.
    :raises HTTPException: 400 if contact with the same email already exists for this user.
    """
    existing = crud.get_contact_by_email(db, current_user.id, str(contact_in.email))
    if existing:
        raise HTTPException(status_code=400, detail="Contact with this email already exists")
    return crud.create_contact(db, current_user.id, contact_in)


@router.get("", response_model=list[ContactResponse])
def list_contacts(
    skip: int = 0,
    limit: int = 100,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    """
    List contacts for the current verified user.

    Supports pagination and optional search filters (case-insensitive, partial match).

    :param skip: Pagination offset.
    :param limit: Pagination limit.
    :param first_name: Optional search filter for first name.
    :param last_name: Optional search filter for last name.
    :param email: Optional search filter for email.
    :param db: SQLAlchemy DB session.
    :param current_user: Current verified user.
    :return: List of contacts belonging only to current user.
    """
    return crud.get_contacts(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )


@router.get("/birthdays", response_model=list[ContactResponse])
def upcoming_birthdays(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    """
    List contacts with upcoming birthdays for the current user.

    :param days: Number of days ahead to check (allowed range: 1..30). Default: 7.
    :param db: SQLAlchemy DB session.
    :param current_user: Current verified user.
    :return: List of contacts whose birthday occurs within the next N days.
    :raises HTTPException: 400 if days is outside allowed range.
    """
    if days < 1 or days > 30:
        raise HTTPException(status_code=400, detail="days must be between 1 and 30")
    return crud.get_upcoming_birthdays(db, user_id=current_user.id, days=days)


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    """
    Get a single contact by ID (only if it belongs to current user).

    :param contact_id: Contact ID.
    :param db: SQLAlchemy DB session.
    :param current_user: Current verified user.
    :return: Contact object.
    :raises HTTPException: 404 if contact not found (or belongs to another user).
    """
    contact = crud.get_contact_by_id(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    contact_in: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    """
    Update an existing contact (only if it belongs to current user).

    :param contact_id: Contact ID.
    :param contact_in: ContactUpdate payload (partial fields allowed).
    :param db: SQLAlchemy DB session.
    :param current_user: Current verified user.
    :return: Updated contact.
    :raises HTTPException: 404 if contact not found.
    :raises HTTPException: 400 if new email already exists for this user.
    """
    contact = crud.get_contact_by_id(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact_in.email and str(contact_in.email) != contact.email:
        existing = crud.get_contact_by_email(db, current_user.id, str(contact_in.email))
        if existing:
            raise HTTPException(status_code=400, detail="Contact with this email already exists")

    return crud.update_contact(db, contact, contact_in)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    """
    Delete a contact by ID (only if it belongs to current user).

    :param contact_id: Contact ID.
    :param db: SQLAlchemy DB session.
    :param current_user: Current verified user.
    :return: None (204 No Content).
    :raises HTTPException: 404 if contact not found.
    """
    contact = crud.get_contact_by_id(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    crud.delete_contact(db, contact)
    return None